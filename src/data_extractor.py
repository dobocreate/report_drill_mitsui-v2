"""
データ抽出・部分分析モジュール
穿孔長やインデックスの範囲指定でデータを抽出
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List, Union
import streamlit as st


class DataExtractor:
    """データ抽出クラス"""
    
    def __init__(self):
        """初期化"""
        pass
    
    def extract_by_depth_range(
        self, 
        df: pd.DataFrame, 
        depth_start: float, 
        depth_end: float,
        depth_column: Optional[str] = None
    ) -> pd.DataFrame:
        """
        穿孔長の範囲でデータを抽出
        
        Parameters:
        -----------
        df : pd.DataFrame
            元データ
        depth_start : float
            開始深度 (m)
        depth_end : float
            終了深度 (m)
        depth_column : str, optional
            深度カラム名（自動検出される）
        
        Returns:
        --------
        pd.DataFrame
            抽出されたデータ
        """
        if df is None or df.empty:
            return pd.DataFrame()
        
        # 深度カラムの特定
        if depth_column is None:
            depth_column = self._find_depth_column(df)
            if depth_column is None:
                raise ValueError("深度カラムが見つかりません")
        
        # 範囲でフィルタリング
        mask = (df[depth_column] >= depth_start) & (df[depth_column] <= depth_end)
        extracted_df = df[mask].copy()
        
        # メタデータを追加
        extracted_df.attrs['extraction_type'] = 'depth_range'
        extracted_df.attrs['depth_start'] = depth_start
        extracted_df.attrs['depth_end'] = depth_end
        extracted_df.attrs['original_rows'] = len(df)
        extracted_df.attrs['extracted_rows'] = len(extracted_df)
        
        return extracted_df
    
    def extract_by_index_range(
        self, 
        df: pd.DataFrame, 
        index_start: int, 
        index_end: int
    ) -> pd.DataFrame:
        """
        インデックス（行番号）の範囲でデータを抽出
        
        Parameters:
        -----------
        df : pd.DataFrame
            元データ
        index_start : int
            開始インデックス
        index_end : int
            終了インデックス
        
        Returns:
        --------
        pd.DataFrame
            抽出されたデータ
        """
        if df is None or df.empty:
            return pd.DataFrame()
        
        # インデックスの範囲チェック
        index_start = max(0, index_start)
        index_end = min(len(df), index_end)
        
        # 範囲でスライス
        extracted_df = df.iloc[index_start:index_end].copy()
        
        # メタデータを追加
        extracted_df.attrs['extraction_type'] = 'index_range'
        extracted_df.attrs['index_start'] = index_start
        extracted_df.attrs['index_end'] = index_end
        extracted_df.attrs['original_rows'] = len(df)
        extracted_df.attrs['extracted_rows'] = len(extracted_df)
        
        return extracted_df
    
    def extract_by_energy_range(
        self, 
        df: pd.DataFrame, 
        energy_min: float, 
        energy_max: float,
        energy_column: Optional[str] = None
    ) -> pd.DataFrame:
        """
        穿孔エネルギーの範囲でデータを抽出
        
        Parameters:
        -----------
        df : pd.DataFrame
            元データ
        energy_min : float
            最小エネルギー値
        energy_max : float
            最大エネルギー値
        energy_column : str, optional
            エネルギーカラム名（自動検出される）
        
        Returns:
        --------
        pd.DataFrame
            抽出されたデータ
        """
        if df is None or df.empty:
            return pd.DataFrame()
        
        # エネルギーカラムの特定
        if energy_column is None:
            energy_column = self._find_energy_column(df)
            if energy_column is None:
                raise ValueError("エネルギーカラムが見つかりません")
        
        # 範囲でフィルタリング
        mask = (df[energy_column] >= energy_min) & (df[energy_column] <= energy_max)
        extracted_df = df[mask].copy()
        
        # メタデータを追加
        extracted_df.attrs['extraction_type'] = 'energy_range'
        extracted_df.attrs['energy_min'] = energy_min
        extracted_df.attrs['energy_max'] = energy_max
        extracted_df.attrs['original_rows'] = len(df)
        extracted_df.attrs['extracted_rows'] = len(extracted_df)
        
        return extracted_df
    
    def extract_by_percentile(
        self, 
        df: pd.DataFrame, 
        start_percentile: float, 
        end_percentile: float
    ) -> pd.DataFrame:
        """
        パーセンタイルでデータを抽出（例：上位10%～30%）
        
        Parameters:
        -----------
        df : pd.DataFrame
            元データ
        start_percentile : float
            開始パーセンタイル (0-100)
        end_percentile : float
            終了パーセンタイル (0-100)
        
        Returns:
        --------
        pd.DataFrame
            抽出されたデータ
        """
        if df is None or df.empty:
            return pd.DataFrame()
        
        # インデックス計算
        total_rows = len(df)
        start_idx = int(total_rows * start_percentile / 100)
        end_idx = int(total_rows * end_percentile / 100)
        
        # 範囲でスライス
        extracted_df = df.iloc[start_idx:end_idx].copy()
        
        # メタデータを追加
        extracted_df.attrs['extraction_type'] = 'percentile'
        extracted_df.attrs['start_percentile'] = start_percentile
        extracted_df.attrs['end_percentile'] = end_percentile
        extracted_df.attrs['original_rows'] = len(df)
        extracted_df.attrs['extracted_rows'] = len(extracted_df)
        
        return extracted_df
    
    def extract_by_condition(
        self, 
        df: pd.DataFrame, 
        conditions: Dict[str, Tuple[str, Union[float, str]]]
    ) -> pd.DataFrame:
        """
        複数条件でデータを抽出
        
        Parameters:
        -----------
        df : pd.DataFrame
            元データ
        conditions : Dict[str, Tuple[str, Union[float, str]]]
            条件辞書 {カラム名: (演算子, 値)}
            例: {'穿孔エネルギー': ('>', 500), '穿孔長': ('<=', 30)}
        
        Returns:
        --------
        pd.DataFrame
            抽出されたデータ
        """
        if df is None or df.empty:
            return pd.DataFrame()
        
        mask = pd.Series([True] * len(df))
        
        for column, (operator, value) in conditions.items():
            if column not in df.columns:
                continue
            
            if operator == '>':
                mask &= df[column] > value
            elif operator == '>=':
                mask &= df[column] >= value
            elif operator == '<':
                mask &= df[column] < value
            elif operator == '<=':
                mask &= df[column] <= value
            elif operator == '==':
                mask &= df[column] == value
            elif operator == '!=':
                mask &= df[column] != value
        
        extracted_df = df[mask].copy()
        
        # メタデータを追加
        extracted_df.attrs['extraction_type'] = 'condition'
        extracted_df.attrs['conditions'] = conditions
        extracted_df.attrs['original_rows'] = len(df)
        extracted_df.attrs['extracted_rows'] = len(extracted_df)
        
        return extracted_df
    
    def extract_anomalies(
        self, 
        df: pd.DataFrame, 
        column: str,
        method: str = 'iqr',
        threshold: float = 1.5
    ) -> pd.DataFrame:
        """
        異常値を抽出
        
        Parameters:
        -----------
        df : pd.DataFrame
            元データ
        column : str
            対象カラム
        method : str
            'iqr' または 'zscore'
        threshold : float
            閾値
        
        Returns:
        --------
        pd.DataFrame
            異常値のみのデータ
        """
        if df is None or df.empty or column not in df.columns:
            return pd.DataFrame()
        
        if method == 'iqr':
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            mask = (df[column] < lower_bound) | (df[column] > upper_bound)
        
        elif method == 'zscore':
            mean = df[column].mean()
            std = df[column].std()
            z_scores = np.abs((df[column] - mean) / std)
            mask = z_scores > threshold
        
        else:
            return pd.DataFrame()
        
        extracted_df = df[mask].copy()
        
        # メタデータを追加
        extracted_df.attrs['extraction_type'] = 'anomaly'
        extracted_df.attrs['method'] = method
        extracted_df.attrs['threshold'] = threshold
        extracted_df.attrs['original_rows'] = len(df)
        extracted_df.attrs['extracted_rows'] = len(extracted_df)
        
        return extracted_df
    
    def extract_peak_regions(
        self, 
        df: pd.DataFrame, 
        column: str,
        window_size: int = 10,
        peak_threshold: float = 0.8
    ) -> pd.DataFrame:
        """
        ピーク領域を抽出
        
        Parameters:
        -----------
        df : pd.DataFrame
            元データ
        column : str
            対象カラム
        window_size : int
            ピーク検出のウィンドウサイズ
        peak_threshold : float
            ピーク判定の閾値（最大値に対する比率）
        
        Returns:
        --------
        pd.DataFrame
            ピーク領域のデータ
        """
        if df is None or df.empty or column not in df.columns:
            return pd.DataFrame()
        
        # 移動平均を計算
        rolling_mean = df[column].rolling(window=window_size, center=True).mean()
        
        # ピークの閾値を計算
        threshold = rolling_mean.max() * peak_threshold
        
        # ピーク領域をマーク
        mask = rolling_mean >= threshold
        
        # 連続する領域を拡張
        mask = mask.rolling(window=window_size//2, center=True).max().fillna(False).astype(bool)
        
        extracted_df = df[mask].copy()
        
        # メタデータを追加
        extracted_df.attrs['extraction_type'] = 'peak'
        extracted_df.attrs['window_size'] = window_size
        extracted_df.attrs['peak_threshold'] = peak_threshold
        extracted_df.attrs['original_rows'] = len(df)
        extracted_df.attrs['extracted_rows'] = len(extracted_df)
        
        return extracted_df
    
    def split_data(
        self, 
        df: pd.DataFrame, 
        n_splits: int = 3,
        overlap: int = 0
    ) -> List[pd.DataFrame]:
        """
        データを複数の部分に分割
        
        Parameters:
        -----------
        df : pd.DataFrame
            元データ
        n_splits : int
            分割数
        overlap : int
            オーバーラップする行数
        
        Returns:
        --------
        List[pd.DataFrame]
            分割されたデータのリスト
        """
        if df is None or df.empty:
            return []
        
        total_rows = len(df)
        base_size = total_rows // n_splits
        
        splits = []
        for i in range(n_splits):
            start_idx = max(0, i * base_size - overlap)
            
            if i == n_splits - 1:
                # 最後の分割は残り全部
                end_idx = total_rows
            else:
                end_idx = min(total_rows, (i + 1) * base_size + overlap)
            
            split_df = df.iloc[start_idx:end_idx].copy()
            
            # メタデータを追加
            split_df.attrs['split_index'] = i + 1
            split_df.attrs['total_splits'] = n_splits
            split_df.attrs['overlap'] = overlap
            split_df.attrs['original_rows'] = total_rows
            
            splits.append(split_df)
        
        return splits
    
    def get_extraction_summary(self, extracted_df: pd.DataFrame) -> Dict:
        """
        抽出結果のサマリーを取得
        
        Parameters:
        -----------
        extracted_df : pd.DataFrame
            抽出されたデータ
        
        Returns:
        --------
        Dict
            サマリー情報
        """
        summary = {
            'extracted_rows': len(extracted_df),
            'extraction_type': extracted_df.attrs.get('extraction_type', 'unknown')
        }
        
        # メタデータから情報を取得
        for key, value in extracted_df.attrs.items():
            summary[key] = value
        
        # 深度情報
        depth_col = self._find_depth_column(extracted_df)
        if depth_col and depth_col in extracted_df.columns:
            summary['depth_range'] = {
                'min': extracted_df[depth_col].min(),
                'max': extracted_df[depth_col].max(),
                'mean': extracted_df[depth_col].mean()
            }
        
        # エネルギー情報
        energy_col = self._find_energy_column(extracted_df)
        if energy_col and energy_col in extracted_df.columns:
            summary['energy_stats'] = {
                'min': extracted_df[energy_col].min(),
                'max': extracted_df[energy_col].max(),
                'mean': extracted_df[energy_col].mean(),
                'std': extracted_df[energy_col].std()
            }
        
        return summary
    
    def _find_depth_column(self, df: pd.DataFrame) -> Optional[str]:
        """深度カラムを検出"""
        depth_candidates = ['穿孔長', 'TD', 'x:TD(m)', '深度', 'Depth']
        for col in depth_candidates:
            if col in df.columns:
                return col
        return None
    
    def _find_energy_column(self, df: pd.DataFrame) -> Optional[str]:
        """エネルギーカラムを検出"""
        energy_candidates = ['穿孔エネルギー', 'エネルギー', 'Energy', 'Ene-M']
        for col in energy_candidates:
            if col in df.columns:
                return col
        return None