"""
VTKファイルのシンプルレンダラー（matplotlib使用）
WSL環境でも動作する軽量な実装
"""

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional, List
import re


class VTKSimpleRenderer:
    """VTKファイルを読み込んでmatplotlibで可視化"""
    
    def __init__(self):
        self.points = []
        self.lines = []
        self.scalars = {}
        
    def parse_vtk_file(self, vtk_path: str) -> bool:
        """VTKファイルを解析"""
        try:
            with open(vtk_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # ポイント数を取得
            points_match = re.search(r'POINTS\s+(\d+)', content)
            if not points_match:
                return False
            
            num_points = int(points_match.group(1))
            
            # ポイントデータを取得
            points_start = content.find('POINTS')
            if points_start == -1:
                return False
            
            # ポイントデータの開始位置を見つける
            points_data_start = content.find('\n', points_start) + 1
            
            # ポイントを読み込み
            self.points = []
            lines = content[points_data_start:].split('\n')
            point_count = 0
            
            for line in lines:
                if point_count >= num_points:
                    break
                    
                values = line.strip().split()
                for i in range(0, len(values), 3):
                    if i + 2 < len(values):
                        try:
                            x = float(values[i])
                            y = float(values[i + 1])
                            z = float(values[i + 2])
                            self.points.append([x, y, z])
                            point_count += 1
                            if point_count >= num_points:
                                break
                        except ValueError:
                            continue
            
            # ラインデータを取得
            lines_match = re.search(r'LINES\s+(\d+)\s+(\d+)', content)
            if lines_match:
                num_lines = int(lines_match.group(1))
                lines_start = content.find('LINES')
                lines_data_start = content.find('\n', lines_start) + 1
                
                # ラインを読み込み
                self.lines = []
                lines = content[lines_data_start:].split('\n')
                line_count = 0
                
                for line in lines:
                    if line_count >= num_lines:
                        break
                        
                    values = line.strip().split()
                    if len(values) >= 2:
                        try:
                            num_vertices = int(values[0])
                            vertices = [int(values[i]) for i in range(1, min(len(values), num_vertices + 1))]
                            if len(vertices) == num_vertices:
                                self.lines.append(vertices)
                                line_count += 1
                        except (ValueError, IndexError):
                            continue
            
            # スカラーデータを取得
            scalar_match = re.search(r'SCALARS\s+(\w+)', content)
            if scalar_match:
                scalar_name = scalar_match.group(1)
                scalar_start = content.find('SCALARS')
                lookup_table_pos = content.find('LOOKUP_TABLE', scalar_start)
                
                if lookup_table_pos != -1:
                    scalar_data_start = content.find('\n', lookup_table_pos) + 1
                    scalar_lines = content[scalar_data_start:].split('\n')
                    
                    scalar_values = []
                    for line in scalar_lines:
                        if len(scalar_values) >= num_points:
                            break
                        
                        values = line.strip().split()
                        for val in values:
                            try:
                                scalar_values.append(float(val))
                                if len(scalar_values) >= num_points:
                                    break
                            except ValueError:
                                continue
                    
                    if scalar_values:
                        self.scalars[scalar_name] = scalar_values[:num_points]
            
            return True
            
        except Exception as e:
            print(f"VTKファイル解析エラー: {e}")
            return False
    
    def render_to_figure(self, 
                        title: str = "3D Trajectory",
                        colormap: str = 'viridis',
                        show_colorbar: bool = True,
                        figsize: Tuple[int, int] = (12, 9)) -> plt.Figure:
        """matplotlibのFigureオブジェクトを作成"""
        
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111, projection='3d')
        
        if not self.points:
            ax.text(0.5, 0.5, 0.5, 'No data to display', 
                   transform=ax.transAxes, ha='center')
            return fig
        
        points_array = np.array(self.points)
        x = points_array[:, 0]
        y = points_array[:, 1]
        z = points_array[:, 2]
        
        # カラーマップの設定
        colors = None
        if self.scalars:
            # 最初のスカラーデータを使用
            scalar_name = list(self.scalars.keys())[0]
            scalar_values = self.scalars[scalar_name]
            
            if len(scalar_values) == len(self.points):
                colors = scalar_values
        
        # ラインがある場合は接続線を描画
        if self.lines:
            for line_indices in self.lines:
                if len(line_indices) >= 2:
                    line_points = [self.points[i] for i in line_indices if i < len(self.points)]
                    if len(line_points) >= 2:
                        line_array = np.array(line_points)
                        ax.plot(line_array[:, 0], 
                               line_array[:, 1], 
                               line_array[:, 2], 
                               'b-', alpha=0.3, linewidth=0.5)
        
        # ポイントをプロット
        if colors is not None:
            scatter = ax.scatter(x, y, z, c=colors, cmap=colormap, s=20, alpha=0.8)
            if show_colorbar:
                cbar = plt.colorbar(scatter, ax=ax, pad=0.1, shrink=0.8)
                if self.scalars:
                    cbar.set_label(list(self.scalars.keys())[0])
        else:
            ax.scatter(x, y, z, c='blue', s=20, alpha=0.8)
        
        # ラベル設定
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_zlabel('Z (m)')
        ax.set_title(title)
        
        # グリッド表示
        ax.grid(True, alpha=0.3)
        
        # アスペクト比を調整
        try:
            # 各軸の範囲を取得
            x_range = [x.min(), x.max()]
            y_range = [y.min(), y.max()]
            z_range = [z.min(), z.max()]
            
            # 最大範囲を計算
            max_range = np.array([
                x_range[1] - x_range[0],
                y_range[1] - y_range[0],
                z_range[1] - z_range[0]
            ]).max() / 2.0
            
            # 中心点を計算
            mid_x = (x_range[1] + x_range[0]) * 0.5
            mid_y = (y_range[1] + y_range[0]) * 0.5
            mid_z = (z_range[1] + z_range[0]) * 0.5
            
            # 軸の範囲を設定
            ax.set_xlim(mid_x - max_range, mid_x + max_range)
            ax.set_ylim(mid_y - max_range, mid_y + max_range)
            ax.set_zlim(mid_z - max_range, mid_z + max_range)
        except:
            pass
        
        plt.tight_layout()
        return fig
    
    def render_vtk_to_image(self, 
                           vtk_path: str,
                           output_path: str,
                           title: Optional[str] = None,
                           dpi: int = 100) -> bool:
        """VTKファイルを画像として保存"""
        try:
            # VTKファイルを解析
            if not self.parse_vtk_file(vtk_path):
                return False
            
            # タイトルの設定
            if title is None:
                title = Path(vtk_path).stem
            
            # 図を作成
            fig = self.render_to_figure(title=title)
            
            # 画像として保存
            fig.savefig(output_path, dpi=dpi, bbox_inches='tight')
            plt.close(fig)
            
            return True
            
        except Exception as e:
            print(f"画像生成エラー: {e}")
            return False
    
    def get_data_summary(self) -> dict:
        """データのサマリー情報を取得"""
        summary = {
            'num_points': len(self.points),
            'num_lines': len(self.lines),
            'scalars': list(self.scalars.keys()),
            'bounds': None
        }
        
        if self.points:
            points_array = np.array(self.points)
            summary['bounds'] = {
                'x_min': float(points_array[:, 0].min()),
                'x_max': float(points_array[:, 0].max()),
                'y_min': float(points_array[:, 1].min()),
                'y_max': float(points_array[:, 1].max()),
                'z_min': float(points_array[:, 2].min()),
                'z_max': float(points_array[:, 2].max()),
            }
        
        return summary