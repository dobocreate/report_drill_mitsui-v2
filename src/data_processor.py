"""
データ加工モジュール
データの間引き、補間処理を行う
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from scipy import interpolate


class DataProcessor:
    """データ加工処理クラス"""
    
    def __init__(self):
        self.default_interval = 0.02  # デフォルトの間引き間隔（m）
    
    def resample_data(
        self,
        df: pd.DataFrame,
        interval: float = 0.02,
        depth_column: Optional[str] = None,
        target_columns: Optional[list] = None
    ) -> pd.DataFrame:
        """データを指定間隔でリサンプリング（間引き）
        
        Args:
            df: 入力データフレーム
            interval: サンプリング間隔（m）
            depth_column: 深度カラム名（自動検出も可能）
            target_columns: 補間対象カラム（Noneの場合は自動選択）
            
        Returns:
            リサンプリングされたデータフレーム
        """
        
        # 深度カラムの特定
        if depth_column is None:
            depth_column = self._find_depth_column(df)
            if depth_column is None:
                raise ValueError("深度カラム（穿孔長またはTD）が見つかりません")
        
        # 補間対象カラムの決定（ノイズ除去と同じ形式にする）
        if target_columns is None:
            # 必要なカラムのみを対象とする
            target_columns = []
            
            # 穿孔エネルギー関連のカラムを追加
            if '穿孔エネルギー' in df.columns:
                target_columns.append('穿孔エネルギー')
            
            # Lowess_Trend（ノイズ除去済み）を追加
            if 'Lowess_Trend' in df.columns:
                target_columns.append('Lowess_Trend')
            
            # エネルギー関連の他のカラムも必要に応じて追加
            for col in ['エネルギー', 'Ene-M', 'Ene-L', 'Ene-R']:
                if col in df.columns and col not in target_columns:
                    target_columns.append(col)
        
        # 元データから深度の範囲を取得
        depth_min = df[depth_column].min()
        depth_max = df[depth_column].max()
        
        # 新しい深度グリッドを作成（0から開始、interval刻み）
        new_depths = np.arange(
            0,  # 0から開始
            np.floor(depth_max / interval) * interval + interval,
            interval
        )
        
        # 結果を格納するデータフレーム
        result_df = pd.DataFrame()
        result_df[depth_column] = new_depths
        
        # 各カラムに対して線形補間を実行
        for col in target_columns:
            if col in df.columns:
                # NaNを除去してから補間
                valid_idx = ~df[col].isna()
                if valid_idx.sum() > 1:  # 少なくとも2点必要
                    # 線形補間関数を作成（外挿も行う）
                    interp_func = interpolate.interp1d(
                        df.loc[valid_idx, depth_column],
                        df.loc[valid_idx, col],
                        kind='linear',
                        bounds_error=False,
                        fill_value='extrapolate'  # 範囲外は線形外挿
                    )
                    
                    # 新しいグリッドで補間
                    interpolated_values = interp_func(new_depths)
                    
                    # 元データの範囲外で外挿された値のうち、開始点より前のみ許可
                    # 終了点より後はNaNにする
                    mask = new_depths > depth_max
                    interpolated_values[mask] = np.nan
                    
                    # マイナス値を0にクリップ（物理的にマイナスのエネルギーはありえない）
                    interpolated_values = np.maximum(interpolated_values, 0)
                    
                    result_df[col] = interpolated_values
        
        # 深度を丸める（表示用）
        result_df[depth_column] = result_df[depth_column].round(3)
        
        return result_df
    
    def process_multiple_files(
        self,
        data_dict: Dict[str, pd.DataFrame],
        interval: float = 0.02
    ) -> Dict[str, pd.DataFrame]:
        """複数ファイルのリサンプリング処理
        
        Args:
            data_dict: ファイル名をキーとするデータフレームの辞書
            interval: サンプリング間隔（m）
            
        Returns:
            処理済みデータの辞書
        """
        processed_data = {}
        
        for filename, df in data_dict.items():
            try:
                processed_df = self.resample_data(df, interval=interval)
                processed_data[filename] = processed_df
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                continue
        
        return processed_data
    
    def _find_depth_column(self, df: pd.DataFrame) -> Optional[str]:
        """深度カラムを自動検出"""
        depth_columns = ['穿孔長', 'TD', 'x:TD(m)', 'Depth']
        
        for col in depth_columns:
            if col in df.columns:
                return col
        
        return None
    
    def _get_numeric_columns(self, df: pd.DataFrame, exclude: list = None) -> list:
        """数値カラムを取得（ノイズ除去と同じ形式で必要なカラムのみ）"""
        
        # 必要なカラムのみを返す
        result_cols = []
        
        # 優先順位の高いカラム
        priority_cols = ['Lowess_Trend', '穿孔エネルギー', 'エネルギー', 'Ene-M', 'Ene-L', 'Ene-R']
        
        for col in priority_cols:
            if col in df.columns:
                if exclude is None or col not in exclude:
                    result_cols.append(col)
        
        return result_cols
    
    def calculate_statistics(self, df: pd.DataFrame) -> Dict:
        """リサンプリング後の統計情報を計算"""
        stats = {
            'total_points': len(df),
            'interval': None,
            'depth_range': None,
            'columns_processed': []
        }
        
        # 深度カラムを検出
        depth_col = self._find_depth_column(df)
        if depth_col:
            depths = df[depth_col].dropna()
            if len(depths) > 1:
                # 平均間隔を計算
                intervals = depths.diff().dropna()
                stats['interval'] = intervals.mean()
                stats['depth_range'] = (depths.min(), depths.max())
        
        # 処理されたカラム
        stats['columns_processed'] = self._get_numeric_columns(df)
        
        return stats