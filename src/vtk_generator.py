"""
VTKファイル生成モジュール
削孔検層データから3D軌跡のVTKファイルを生成
"""

import os
# ヘッドレス環境用の設定
os.environ['VTK_BACKEND'] = 'OpenGL2'

try:
    import vtk
    VTK_AVAILABLE = True
except ImportError:
    VTK_AVAILABLE = False
    print("Warning: VTK not available. VTK features will be disabled.")

import pandas as pd
import numpy as np
from typing import Optional, List, Tuple
from pathlib import Path


class VTKGenerator:
    """VTKファイル生成クラス"""
    
    def __init__(self):
        self.vtk_version = "4.2"
        self.vtk_available = VTK_AVAILABLE
        
        if not self.vtk_available:
            print("VTK is not available. Using fallback mode.")
        
    def create_from_dataframe(
        self,
        df: pd.DataFrame,
        sampling_interval: int = 10,
        include_energy: bool = True
    ) -> bytes:
        """データフレームからVTKファイルを生成してバイナリとして返す"""
        
        # サンプリング
        if sampling_interval > 1:
            df = df.iloc[::sampling_interval].reset_index(drop=True)
        
        # 座標データの取得
        points = self._extract_coordinates(df)
        
        # エネルギーデータの取得
        energy_values = None
        if include_energy:
            energy_values = self._extract_energy_values(df)
        
        # VTKオブジェクト作成
        vtk_content = self._create_vtk_polydata(points, energy_values)
        
        return vtk_content
    
    def _extract_coordinates(self, df: pd.DataFrame) -> List[Tuple[float, float, float]]:
        """データフレームから3D座標を抽出"""
        points = []
        
        # 座標カラムの候補
        x_cols = ['X', 'X(m)', 'x', 'x:TD(m)']
        y_cols = ['Y', 'Y(m)', 'y', 'y:CL差(m)']
        z_cols = ['Z', 'Z(m)', 'z', 'Z:標高(m)', 'z:SL差(m)', 'Z_SL']
        
        # カラムを探す
        x_col = next((col for col in x_cols if col in df.columns), None)
        y_col = next((col for col in y_cols if col in df.columns), None)
        z_col = next((col for col in z_cols if col in df.columns), None)
        
        if not all([x_col, y_col, z_col]):
            # 代替: TD（深度）を使用した簡易3D軌跡
            if 'TD' in df.columns:
                td = df['TD'].values
                for i, depth in enumerate(td):
                    if not pd.isna(depth):
                        # 螺旋状の軌跡を生成（仮の座標）
                        angle = i * 0.1
                        x = np.cos(angle) * 10
                        y = np.sin(angle) * 10
                        z = -depth  # 深度は負の値
                        points.append((float(x), float(y), float(z)))
            else:
                raise ValueError("座標データが見つかりません")
        else:
            # 実際の座標を使用
            for idx in range(len(df)):
                x = df[x_col].iloc[idx]
                y = df[y_col].iloc[idx]
                z = df[z_col].iloc[idx]
                
                if not any(pd.isna([x, y, z])):
                    points.append((float(x), float(y), float(z)))
        
        return points
    
    def _extract_energy_values(self, df: pd.DataFrame) -> List[float]:
        """データフレームからエネルギー値を抽出"""
        energy_values = []
        
        # エネルギーカラムの候補
        energy_cols = ['穿孔エネルギー', 'エネルギー', 'Energy', 'Ene-M']
        
        # カラムを探す
        energy_col = next((col for col in energy_cols if col in df.columns), None)
        
        if energy_col:
            for val in df[energy_col]:
                if pd.isna(val):
                    energy_values.append(0.0)
                else:
                    energy_values.append(float(val))
        else:
            # Ene-L, Ene-M, Ene-Rの平均を使用
            if all(col in df.columns for col in ['Ene-L', 'Ene-M', 'Ene-R']):
                for idx in range(len(df)):
                    vals = [df['Ene-L'].iloc[idx], 
                           df['Ene-M'].iloc[idx], 
                           df['Ene-R'].iloc[idx]]
                    vals = [v for v in vals if not pd.isna(v)]
                    if vals:
                        energy_values.append(float(np.mean(vals)))
                    else:
                        energy_values.append(0.0)
            else:
                # ダミーデータ
                energy_values = [0.0] * len(df)
        
        return energy_values[:len(self._extract_coordinates(df))]
    
    def _create_vtk_polydata(
        self,
        points: List[Tuple[float, float, float]],
        energy_values: Optional[List[float]] = None
    ) -> bytes:
        """VTKポリデータを作成してバイナリ形式で返す"""
        
        if not self.vtk_available:
            # VTKが利用できない場合は簡易的なテキスト形式で返す
            return self._create_simple_vtk_text(points, energy_values)
        
        # VTKポイントを作成
        vtk_points = vtk.vtkPoints()
        for point in points:
            vtk_points.InsertNextPoint(point)
        
        # ポリラインを作成
        lines = vtk.vtkCellArray()
        line = vtk.vtkPolyLine()
        line.GetPointIds().SetNumberOfIds(len(points))
        for i in range(len(points)):
            line.GetPointIds().SetId(i, i)
        lines.InsertNextCell(line)
        
        # ポリデータを作成
        poly_data = vtk.vtkPolyData()
        poly_data.SetPoints(vtk_points)
        poly_data.SetLines(lines)
        
        # エネルギー値を追加
        if energy_values:
            energy_array = vtk.vtkDoubleArray()
            energy_array.SetName("Energy")
            for energy in energy_values:
                energy_array.InsertNextValue(energy)
            poly_data.GetPointData().AddArray(energy_array)
            poly_data.GetPointData().SetScalars(energy_array)
        
        # VTKファイルに書き出し（文字列として）
        writer = vtk.vtkPolyDataWriter()
        writer.SetInputData(poly_data)
        writer.WriteToOutputStringOn()
        writer.Write()
        
        return writer.GetOutputString()
    
    def _create_simple_vtk_text(
        self,
        points: List[Tuple[float, float, float]],
        energy_values: Optional[List[float]] = None
    ) -> bytes:
        """VTKが利用できない場合の簡易テキスト形式"""
        
        vtk_content = []
        vtk_content.append("# vtk DataFile Version 4.2")
        vtk_content.append("Drilling trajectory data")
        vtk_content.append("ASCII")
        vtk_content.append("DATASET POLYDATA")
        
        # Points
        vtk_content.append(f"POINTS {len(points)} float")
        for point in points:
            vtk_content.append(f"{point[0]} {point[1]} {point[2]}")
        
        # Lines
        vtk_content.append(f"LINES 1 {len(points) + 1}")
        line_data = [str(len(points))] + [str(i) for i in range(len(points))]
        vtk_content.append(" ".join(line_data))
        
        # Point data
        if energy_values:
            vtk_content.append(f"POINT_DATA {len(points)}")
            vtk_content.append("SCALARS Energy float 1")
            vtk_content.append("LOOKUP_TABLE default")
            for energy in energy_values:
                vtk_content.append(str(energy))
        
        return "\n".join(vtk_content).encode('utf-8')
    
    def save_to_file(
        self,
        df: pd.DataFrame,
        output_path: str,
        sampling_interval: int = 10,
        include_energy: bool = True
    ):
        """データフレームからVTKファイルを生成して保存"""
        
        vtk_content = self.create_from_dataframe(df, sampling_interval, include_energy)
        
        # バイナリデータをファイルに書き込み
        with open(output_path, 'wb') as f:
            f.write(vtk_content)
        
        print(f"VTKファイルを保存しました: {output_path}")
    
    def create_multiple_vtk(
        self,
        data_dict: dict,
        output_dir: str,
        sampling_interval: int = 10,
        include_energy: bool = True
    ) -> dict:
        """複数のデータフレームから複数のVTKファイルを生成"""
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        vtk_files = {}
        
        for name, df in data_dict.items():
            # ファイル名の生成
            base_name = Path(name).stem
            vtk_name = f"{base_name}.vtk"
            output_path = output_dir / vtk_name
            
            # VTKファイル生成
            self.save_to_file(df, str(output_path), sampling_interval, include_energy)
            vtk_files[vtk_name] = str(output_path)
        
        return vtk_files