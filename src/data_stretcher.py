"""
データ拡張（スケーリング）処理モジュール
穿孔長を指定した長さにスケーリングする
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
import streamlit as st


class DataStretcher:
    """データ拡張（スケーリング）処理クラス"""
    
    def __init__(self):
        """初期化"""
        pass
    
    def stretch_data(self, df: pd.DataFrame, target_length: float, 
                     original_max_length: Optional[float] = None) -> pd.DataFrame:
        """
        データの穿孔長をスケーリング
        
        Parameters:
        -----------
        df : pd.DataFrame
            処理対象のデータフレーム（'穿孔長'列を含む）
        target_length : float
            目標とする最大穿孔長 (m)
        original_max_length : float, optional
            元の最大穿孔長。Noneの場合はデータから自動取得
        
        Returns:
        --------
        pd.DataFrame
            スケーリング後のデータフレーム
        """
        if df is None or df.empty:
            return df
        
        # コピーを作成
        df_stretched = df.copy()
        
        # 元の最大穿孔長を取得
        if original_max_length is None:
            original_max_length = df['穿孔長'].max()
        
        # スケール係数を計算
        scale_factor = target_length / original_max_length
        
        # 穿孔長をスケーリング
        df_stretched['穿孔長'] = df_stretched['穿孔長'] * scale_factor
        
        # オリジナルの穿孔長を保存（参照用）
        df_stretched['元の穿孔長'] = df['穿孔長']
        df_stretched['スケール係数'] = scale_factor
        
        return df_stretched
    
    def stretch_multiple_data(self, data_dict: Dict[str, pd.DataFrame], 
                            target_lengths: Dict[str, float]) -> Dict[str, pd.DataFrame]:
        """
        複数のデータ（L/M/R）を個別にスケーリング
        
        Parameters:
        -----------
        data_dict : Dict[str, pd.DataFrame]
            処理対象のデータ辞書（キー: 'L', 'M', 'R'）
        target_lengths : Dict[str, float]
            各データの目標長さ（キー: 'L', 'M', 'R'）
        
        Returns:
        --------
        Dict[str, pd.DataFrame]
            スケーリング後のデータ辞書
        """
        stretched_data = {}
        
        for key, df in data_dict.items():
            if key in target_lengths and df is not None and not df.empty:
                target_length = target_lengths[key]
                stretched_data[key] = self.stretch_data(df, target_length)
            else:
                stretched_data[key] = df
        
        return stretched_data
    
    def get_scale_info(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        データのスケール情報を取得
        
        Parameters:
        -----------
        df : pd.DataFrame
            データフレーム
        
        Returns:
        --------
        Dict[str, float]
            スケール情報（元の長さ、現在の長さ、スケール係数）
        """
        info = {
            'current_max_length': df['穿孔長'].max() if not df.empty else 0,
            'current_min_length': df['穿孔長'].min() if not df.empty else 0,
            'data_points': len(df)
        }
        
        # スケール済みの場合は追加情報
        if '元の穿孔長' in df.columns:
            info['original_max_length'] = df['元の穿孔長'].max()
            info['scale_factor'] = df['スケール係数'].iloc[0] if 'スケール係数' in df.columns else 1.0
        
        return info
    
    def display_scale_summary(self, original_data: Dict[str, pd.DataFrame], 
                            stretched_data: Dict[str, pd.DataFrame]) -> None:
        """
        スケーリング結果のサマリーを表示
        
        Parameters:
        -----------
        original_data : Dict[str, pd.DataFrame]
            元のデータ辞書
        stretched_data : Dict[str, pd.DataFrame]
            スケーリング後のデータ辞書
        """
        summary_data = []
        
        for key in ['L', 'M', 'R']:
            if key in original_data and key in stretched_data:
                orig_df = original_data[key]
                stretch_df = stretched_data[key]
                
                if orig_df is not None and not orig_df.empty:
                    orig_max = orig_df['穿孔長'].max()
                    stretch_max = stretch_df['穿孔長'].max()
                    scale_factor = stretch_max / orig_max if orig_max > 0 else 1.0
                    
                    summary_data.append({
                        'データ': f'{key}側',
                        '元の最大長 (m)': f'{orig_max:.2f}',
                        '拡張後の最大長 (m)': f'{stretch_max:.2f}',
                        'スケール係数': f'{scale_factor:.2f}',
                        'データ点数': len(orig_df)
                    })
        
        if summary_data:
            st.table(pd.DataFrame(summary_data))