"""
LMR穿孔データのスタート地点座標計算モジュール
トンネル坑口からの距離を基に、L側、M側、R側の座標と向きを計算
"""

import math
import pandas as pd
from typing import Tuple, Dict, Optional
import numpy as np


class LMRCoordinateCalculator:
    """LMR穿孔データのスタート地点座標を計算するクラス"""
    
    # 固定値の定義
    REFERENCE_DISTANCE = 967  # I974の値（固定）
    DIRECTION_ANGLE = 65.588  # W列の値（固定）
    
    # 基準座標（974行目の固定値）
    DEFAULT_REFERENCE_COORDS = {
        'Q': -660689.7596,   # L側X座標
        'R': 733147.0996,    # L側Y座標
        'S': -658622.871,    # M側X座標
        'T': 737699.9102,    # M側Y座標
        'U': -656556.8108,   # R側X座標
        'V': 742253.072      # R側Y座標
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
            
            # 設定値を取得
            lmr_params = loader.get_lmr_parameters()
            self.REFERENCE_DISTANCE = lmr_params['reference_distance']
            self.DIRECTION_ANGLE = lmr_params['direction_angle']
            
            # 基準座標を変換
            ref_coords = lmr_params['reference_coordinates']
            self.reference_coords = {
                'Q': ref_coords['L']['X'],
                'R': ref_coords['L']['Y'],
                'S': ref_coords['M']['X'],
                'T': ref_coords['M']['Y'],
                'U': ref_coords['R']['X'],
                'V': ref_coords['R']['Y']
            }
            
        except (ImportError, FileNotFoundError):
            # 設定ファイルが読めない場合はデフォルト値を使用
            self.REFERENCE_DISTANCE = 967
            self.DIRECTION_ANGLE = 65.588
            self.reference_coords = self.DEFAULT_REFERENCE_COORDS.copy()
    
    def calculate_coordinates(
        self,
        distance_from_entrance: float,
        direction_angle: Optional[float] = None,
        reference_distance: Optional[float] = None
    ) -> Dict[str, float]:
        """
        トンネル坑口からの距離を基に座標を計算
        
        Args:
            distance_from_entrance: トンネル坑口からの距離（I列の値、ユーザー入力）
            direction_angle: 向きの角度（省略時は固定値65.588を使用）
            reference_distance: 基準点の距離（省略時は固定値967を使用）
        
        Returns:
            計算された座標の辞書 {
                'L_X': L側X座標（Q列）,
                'L_Y': L側Y座標（R列）,
                'M_X': M側X座標（S列）,
                'M_Y': M側Y座標（T列）,
                'R_X': R側X座標（U列）,
                'R_Y': R側Y座標（V列）,
                'direction': 向き（W列）,
                'distance': 入力された距離
            }
        """
        # デフォルト値を使用
        if direction_angle is None:
            direction_angle = self.DIRECTION_ANGLE
        if reference_distance is None:
            reference_distance = self.REFERENCE_DISTANCE
        
        # 距離の差分を計算（mm単位）
        distance_diff = (distance_from_entrance - reference_distance) * 1000
        
        # 角度をラジアンに変換
        angle_rad = (90 - direction_angle) * math.pi / 180
        
        # 三角関数計算
        cos_val = math.cos(angle_rad)
        sin_val = math.sin(angle_rad)
        
        # 各座標を計算（Excel数式の再現）
        # 基準座標はすでにメートル単位なので、そのまま使用
        # Q列: =ROUND((-($I1245-$I$974)*1000*COS((90-$W1245)*PI()/180)+Q$974)/1000,3)
        l_x = round((-distance_diff * cos_val + self.reference_coords.get('Q', 0)) / 1000, 3)
        
        # R列: =ROUND((($I1245-$I$974)*1000*SIN((90-$W1245)*PI()/180)+R$974)/1000,3)
        l_y = round((distance_diff * sin_val + self.reference_coords.get('R', 0)) / 1000, 3)
        
        # S列: =ROUND((-($I1245-$I$974)*1000*COS((90-$W1245)*PI()/180)+S$974)/1000,3)
        m_x = round((-distance_diff * cos_val + self.reference_coords.get('S', 0)) / 1000, 3)
        
        # T列: =ROUND((($I1245-$I$974)*1000*SIN((90-$W1245)*PI()/180)+T$974)/1000,3)
        m_y = round((distance_diff * sin_val + self.reference_coords.get('T', 0)) / 1000, 3)
        
        # U列: =ROUND((-($I1245-$I$974)*1000*COS((90-$W1245)*PI()/180)+U$974)/1000,3)
        r_x = round((-distance_diff * cos_val + self.reference_coords.get('U', 0)) / 1000, 3)
        
        # V列: =ROUND((($I1245-$I$974)*1000*SIN((90-$W1245)*PI()/180)+V$974)/1000,3)
        r_y = round((distance_diff * sin_val + self.reference_coords.get('V', 0)) / 1000, 3)
        
        return {
            'L_X': l_x,
            'L_Y': l_y,
            'M_X': m_x,
            'M_Y': m_y,
            'R_X': r_x,
            'R_Y': r_y,
            'direction': direction_angle,
            'distance': distance_from_entrance
        }
    
    def load_reference_from_excel(self, excel_path: str, sheet_name: Optional[str] = None) -> None:
        """
        Excelファイルから基準点の座標を読み込む
        
        Args:
            excel_path: Excelファイルのパス
            sheet_name: シート名（省略時はアクティブシート）
        """
        import openpyxl
        
        wb = openpyxl.load_workbook(excel_path, data_only=True)
        sheet = wb[sheet_name] if sheet_name else wb.active
        
        # 基準点（974行目）の座標を読み込む
        self.reference_coords = {
            'Q': sheet[f'Q{self.reference_point}'].value or 0,
            'R': sheet[f'R{self.reference_point}'].value or 0,
            'S': sheet[f'S{self.reference_point}'].value or 0,
            'T': sheet[f'T{self.reference_point}'].value or 0,
            'U': sheet[f'U{self.reference_point}'].value or 0,
            'V': sheet[f'V{self.reference_point}'].value or 0
        }
        
        wb.close()
    
    def calculate_batch(
        self,
        distances: list,
        angles: list,
        reference_distance: float = 0.0
    ) -> pd.DataFrame:
        """
        複数の測点について一括計算
        
        Args:
            distances: 距離のリスト
            angles: 角度のリスト
            reference_distance: 基準点の距離
        
        Returns:
            計算結果のDataFrame
        """
        results = []
        
        for dist, angle in zip(distances, angles):
            coords = self.calculate_coordinates(dist, angle, reference_distance)
            coords['distance'] = dist
            results.append(coords)
        
        return pd.DataFrame(results)
    
    def validate_calculation(self, expected: Dict, calculated: Dict, tolerance: float = 0.001) -> bool:
        """
        計算結果の検証
        
        Args:
            expected: 期待される値
            calculated: 計算された値
            tolerance: 許容誤差
        
        Returns:
            検証結果（True: 一致、False: 不一致）
        """
        for key in ['L_X', 'L_Y', 'M_X', 'M_Y', 'R_X', 'R_Y']:
            if key in expected and key in calculated:
                if abs(expected[key] - calculated[key]) > tolerance:
                    return False
        return True