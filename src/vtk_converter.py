"""
削孔検層CSVファイルをVTKファイルに変換するモジュール
LMR座標計算機能と統合
"""

import csv
import os
import math
import datetime
from typing import Tuple, List, Optional
import pandas as pd

# ヘッドレス環境対応
os.environ['DISPLAY'] = ''

try:
    # VTKのオフスクリーンレンダリングを有効化
    import vtk
    VTK_AVAILABLE = True
except ImportError:
    VTK_AVAILABLE = False
    print("Warning: VTK library not available. VTK conversion features will be disabled.")

from .lmr_coordinate_calculator import LMRCoordinateCalculator


class VTKConverter:
    """削孔検層データをVTK形式に変換するクラス"""
    
    # Z標高の定義
    Z_ELEVATIONS = {
        'L': 17.3,  # L側のZ標高
        'M': 21.3,  # M側（天端）のZ標高  
        'R': 17.3   # R側のZ標高
    }
    
    def __init__(self, config_path=None):
        """
        初期化
        
        Args:
            config_path: 設定ファイルのパス（省略時はデフォルト）
        """
        # 設定ファイルから値を読み込む
        try:
            from .config_loader import ConfigLoader
            loader = ConfigLoader(config_path)
            
            # Z標高を設定ファイルから取得
            self.Z_ELEVATIONS = loader.get_z_elevations()
            
        except (ImportError, FileNotFoundError):
            # 設定ファイルが読めない場合はデフォルト値を使用
            self.Z_ELEVATIONS = {
                'L': 17.3,
                'M': 21.3,
                'R': 17.3
            }
        
        # LMR座標計算機を初期化
        self.calculator = LMRCoordinateCalculator(config_path)
        
    def detect_lmr_type(self, filename: str) -> Optional[str]:
        """
        ファイル名からL/M/Rタイプを検出
        
        Args:
            filename: ファイル名
            
        Returns:
            'L', 'M', 'R'のいずれか、検出できない場合はNone
        """
        base = os.path.basename(filename)
        name, _ = os.path.splitext(base)
        
        # アンダースコアで分割してチェック
        parts = name.split('_')
        for part in parts:
            if part.upper() in ['L', 'M', 'R']:
                return part.upper()
        
        # ハイフンで分割してチェック
        parts = name.split('-')
        for part in parts:
            if part.upper() in ['L', 'M', 'R']:
                return part.upper()
                
        # 文字列内に含まれているかチェック
        name_upper = name.upper()
        for lmr in ['_L_', '_M_', '_R_', '-L-', '-M-', '-R-']:
            if lmr in name_upper:
                return lmr.replace('_', '').replace('-', '')
        
        # 末尾をチェック
        for lmr in ['_L', '_M', '_R', '-L', '-M', '-R']:
            if name_upper.endswith(lmr):
                return lmr[-1]
                
        return None
    
    def get_coordinates_for_lmr(
        self, 
        lmr_type: str, 
        distance_from_entrance: float
    ) -> Tuple[float, float, float, float]:
        """
        LMRタイプと坑口からの距離から座標を取得
        
        Args:
            lmr_type: 'L', 'M', 'R'のいずれか
            distance_from_entrance: トンネル坑口からの距離（m）
            
        Returns:
            (x_base, y_base, angle, z_elevation)のタプル
        """
        # 座標計算
        coords = self.calculator.calculate_coordinates(distance_from_entrance)
        
        # LMRタイプに応じた座標を取得
        if lmr_type == 'L':
            x_base = coords['L_X']
            y_base = coords['L_Y']
        elif lmr_type == 'M':
            x_base = coords['M_X']
            y_base = coords['M_Y']
        elif lmr_type == 'R':
            x_base = coords['R_X']
            y_base = coords['R_Y']
        else:
            raise ValueError(f"不正なLMRタイプ: {lmr_type}")
        
        angle = self.calculator.DIRECTION_ANGLE
        z_elevation = self.Z_ELEVATIONS[lmr_type]
        
        return x_base, y_base, angle, z_elevation
    
    def read_csv_data(
        self, 
        csv_file: str, 
        encoding: str = 'shift-jis'
    ) -> Tuple[List[float], List[float]]:
        """
        CSVファイルから穿孔長とエネルギー値を読み込む
        
        Args:
            csv_file: CSVファイルパス
            encoding: ファイルエンコーディング
            
        Returns:
            (穿孔長リスト, エネルギー値リスト)のタプル
        """
        drilling_lengths = []
        energy_values = []
        
        with open(csv_file, 'r', newline='', encoding=encoding) as file:
            reader = csv.reader(file)
            header = next(reader)
            
            # 必要な列のインデックスを取得
            try:
                length_index = header.index('穿孔長')
                energy_index = header.index('Lowess_Trend')
            except ValueError as e:
                # 別名での列を探す
                length_index = None
                energy_index = None
                
                for i, col in enumerate(header):
                    if '穿孔長' in col or 'TD' in col:
                        length_index = i
                    if 'Lowess_Trend' in col or 'Lowess' in col:
                        energy_index = i
                        
                if length_index is None or energy_index is None:
                    raise ValueError(f"必要な列が見つかりません: {e}")
            
            # データを読み込む
            for row in reader:
                try:
                    length = float(row[length_index])
                    energy = float(row[energy_index])
                    drilling_lengths.append(length)
                    energy_values.append(energy)
                except (ValueError, IndexError):
                    continue  # 無効な行はスキップ
                    
        return drilling_lengths, energy_values
    
    def calculate_3d_points(
        self,
        drilling_lengths: List[float],
        x_base: float,
        y_base: float,
        z_elevation: float,
        angle: float
    ) -> List[Tuple[float, float, float]]:
        """
        穿孔長から3D座標を計算
        
        Args:
            drilling_lengths: 穿孔長のリスト
            x_base: X基準座標
            y_base: Y基準座標
            z_elevation: Z標高
            angle: 角度（度）
            
        Returns:
            3D座標のリスト [(x, y, z), ...]
        """
        points = []
        angle_rad = angle * math.pi / 180
        
        for length in drilling_lengths:
            # X座標 = 基準X座標 - 穿孔長 * sin(角度)
            x = x_base - length * math.sin(angle_rad)
            # Y座標 = 基準Y座標 + 穿孔長 * cos(角度)
            y = y_base + length * math.cos(angle_rad)
            # Z座標は固定
            z = z_elevation
            
            points.append((x, y, z))
            
        return points
    
    def save_computed_csv(
        self,
        output_path: str,
        points: List[Tuple[float, float, float]],
        energy_values: List[float],
        lmr_type: str,
        distance_from_entrance: float
    ) -> None:
        """
        計算結果をCSVファイルに保存
        
        Args:
            output_path: 出力ファイルパス
            points: 3D座標のリスト
            energy_values: エネルギー値のリスト
            lmr_type: LMRタイプ
            distance_from_entrance: 坑口からの距離
        """
        with open(output_path, 'w', newline='', encoding='shift-jis') as f:
            writer = csv.writer(f)
            # ヘッダー情報
            writer.writerow([f"# LMRタイプ: {lmr_type}, 坑口からの距離: {distance_from_entrance}m"])
            writer.writerow(["X(m)", "Y(m)", "Z:標高(m)", "穿孔エネルギー"])
            
            # データを書き込む
            for point, energy in zip(points, energy_values):
                x, y, z = point
                writer.writerow([x, y, z, energy])
    
    def create_vtk_file(
        self,
        output_path: str,
        points: List[Tuple[float, float, float]],
        energy_values: List[float]
    ) -> bool:
        """
        VTKファイルを作成（VTKライブラリが利用できない場合は代替処理）
        
        Args:
            output_path: 出力ファイルパス
            points: 3D座標のリスト
            energy_values: エネルギー値のリスト
            
        Returns:
            成功した場合True
        """
        if len(points) < 2:
            raise ValueError("データ点が不足しています（最低2点必要）")
        
        if not VTK_AVAILABLE:
            # VTKライブラリが利用できない場合は、簡易VTKファイルを手動生成
            return self._create_simple_vtk_file(output_path, points, energy_values)
            
        # VTKポイントの作成
        vtk_points = vtk.vtkPoints()
        for point in points:
            vtk_points.InsertNextPoint(point)
        
        # ポリラインの作成
        lines = vtk.vtkCellArray()
        line = vtk.vtkPolyLine()
        line.GetPointIds().SetNumberOfIds(len(points))
        for i in range(len(points)):
            line.GetPointIds().SetId(i, i)
        lines.InsertNextCell(line)
        
        # PolyDataの作成
        poly_data = vtk.vtkPolyData()
        poly_data.SetPoints(vtk_points)
        poly_data.SetLines(lines)
        
        # エネルギー値を属性として追加
        energy_array = vtk.vtkDoubleArray()
        energy_array.SetName("Energy")
        for energy in energy_values:
            energy_array.InsertNextValue(energy)
        poly_data.GetPointData().AddArray(energy_array)
        
        # ファイルに書き込む
        writer = vtk.vtkPolyDataWriter()
        writer.SetFileName(output_path)
        writer.SetInputData(poly_data)
        writer.Write()
        
        return True
    
    def _create_simple_vtk_file(
        self,
        output_path: str,
        points: List[Tuple[float, float, float]],
        energy_values: List[float]
    ) -> bool:
        """
        VTKライブラリなしで簡易VTKファイルを生成
        
        Args:
            output_path: 出力ファイルパス
            points: 3D座標のリスト
            energy_values: エネルギー値のリスト
            
        Returns:
            成功した場合True
        """
        n_points = len(points)
        
        with open(output_path, 'w') as f:
            # VTKファイルヘッダー
            f.write("# vtk DataFile Version 3.0\n")
            f.write("Drill path data\n")
            f.write("ASCII\n")
            f.write("DATASET POLYDATA\n")
            
            # 点データ
            f.write(f"POINTS {n_points} float\n")
            for point in points:
                f.write(f"{point[0]} {point[1]} {point[2]}\n")
            
            # ライン（ポリライン）データ
            f.write(f"LINES 1 {n_points + 1}\n")
            f.write(f"{n_points}")
            for i in range(n_points):
                f.write(f" {i}")
            f.write("\n")
            
            # エネルギー値データ
            f.write(f"POINT_DATA {n_points}\n")
            f.write("SCALARS Energy float 1\n")
            f.write("LOOKUP_TABLE default\n")
            for energy in energy_values:
                f.write(f"{energy}\n")
        
        return True
    
    def convert_csv_to_vtk(
        self,
        csv_file: str,
        distance_from_entrance: float,
        output_vtk_path: Optional[str] = None,
        output_csv_path: Optional[str] = None,
        lmr_type: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        CSVファイルをVTK形式に変換
        
        Args:
            csv_file: 入力CSVファイルパス
            distance_from_entrance: トンネル坑口からの距離（m）
            output_vtk_path: 出力VTKファイルパス（省略時は自動生成）
            output_csv_path: 出力CSVファイルパス（省略時は自動生成）
            lmr_type: LMRタイプ（省略時はファイル名から自動検出）
            
        Returns:
            (VTKファイルパス, CSVファイルパス)のタプル
        """
        # LMRタイプの検出
        if lmr_type is None:
            lmr_type = self.detect_lmr_type(csv_file)
            if lmr_type is None:
                raise ValueError("ファイル名からL/M/Rタイプを検出できませんでした")
        
        # CSVデータの読み込み
        drilling_lengths, energy_values = self.read_csv_data(csv_file)
        
        # 座標の取得
        x_base, y_base, angle, z_elevation = self.get_coordinates_for_lmr(
            lmr_type, distance_from_entrance
        )
        
        # 3D座標の計算
        points = self.calculate_3d_points(
            drilling_lengths, x_base, y_base, z_elevation, angle
        )
        
        # 出力ファイルパスの生成
        if output_csv_path is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            base_dir = os.path.dirname(csv_file)
            base_name = os.path.splitext(os.path.basename(csv_file))[0]
            output_csv_path = os.path.join(base_dir, f"{base_name}_3d_{timestamp}.csv")
        
        if output_vtk_path is None:
            base_dir = os.path.dirname(csv_file)
            base_name = os.path.splitext(os.path.basename(csv_file))[0]
            output_vtk_path = os.path.join(base_dir, f"{base_name}.vtk")
        
        # CSV保存
        self.save_computed_csv(
            output_csv_path, points, energy_values, 
            lmr_type, distance_from_entrance
        )
        
        # VTK保存（VTKライブラリがなくても簡易版を生成）
        self.create_vtk_file(output_vtk_path, points, energy_values)
        
        return output_vtk_path, output_csv_path
    
    def generate_vtk_filename(self, csv_file: str) -> str:
        """
        標準的なVTKファイル名を生成
        
        Args:
            csv_file: CSVファイル名
            
        Returns:
            VTKファイル名
        """
        base = os.path.basename(csv_file)
        name, _ = os.path.splitext(base)
        
        # LMRタイプを取得
        lmr_type = self.detect_lmr_type(csv_file)
        if not lmr_type:
            lmr_type = "X"
        
        # 日付文字列を生成
        date_str = "00.00.00"
        
        # アンダースコアで分割
        parts = name.split('_')
        
        # YYYY_MM_DD_HH_MM_SS_L 形式を想定
        if len(parts) >= 3:
            try:
                # 最初の3つの要素が年月日
                year = parts[0]
                month = parts[1]
                day = parts[2]
                
                # 数値として妥当かチェック
                if (len(year) == 4 and year.isdigit() and 
                    month.isdigit() and day.isdigit() and
                    1 <= int(month) <= 12 and 1 <= int(day) <= 31):
                    # YY.MM.DD形式に変換
                    date_str = f"{year[-2:]}.{month.zfill(2)}.{day.zfill(2)}"
            except:
                pass
        
        return f"Drill-{lmr_type}_ana_{date_str}.vtk"