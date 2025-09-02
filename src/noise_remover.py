"""
ノイズ除去モジュール
LOWESS法による穿孔エネルギー値のスムージング
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
from typing import Optional, List, Tuple, Dict
import concurrent.futures
from datetime import datetime
import os


class NoiseRemover:
    """ノイズ除去処理クラス"""
    
    def __init__(self):
        self.default_frac = 0.04  # 元スクリプトのデフォルト値
        self.default_it = 3
        self.default_delta = 0.0
        
    def apply_lowess(
        self,
        df: pd.DataFrame,
        target_column: Optional[str] = None,
        frac: float = None,
        it: int = None,
        delta: float = None
    ) -> pd.DataFrame:
        """LOWESS法によるスムージング処理
        
        Args:
            df: 入力データフレーム
            target_column: 対象カラム名（Noneの場合は自動検出）
            frac: LOWESS fraction パラメータ (0 < frac <= 1)
            it: 反復回数
            delta: デルタパラメータ
            
        Returns:
            処理済みデータフレーム（Lowess_Trend列が追加される）
        """
        
        # パラメータのデフォルト値設定
        frac = frac if frac is not None else self.default_frac
        it = it if it is not None else self.default_it
        delta = delta if delta is not None else self.default_delta
        
        # 処理対象カラムの決定
        if target_column is None:
            target_column = self._find_energy_column(df)
            if target_column is None:
                raise ValueError("エネルギー関連のカラムが見つかりません")
        
        # データのコピー作成
        result_df = df.copy()
        
        # NaN値の処理
        valid_mask = ~df[target_column].isna()
        valid_data = df[target_column][valid_mask]
        
        if len(valid_data) < 10:
            # データ数が少なすぎる場合は処理をスキップ
            result_df['Lowess_Trend'] = df[target_column]
            return result_df
        
        # インデックスの作成
        x_values = np.arange(len(valid_data))
        
        # LOWESS回帰の実行
        try:
            lowess_result = sm.nonparametric.lowess(
                valid_data.values,
                x_values,
                frac=frac,
                it=it,
                delta=delta
            )
            
            # 結果を新しい列に格納
            trend_values = np.full(len(df), np.nan)
            trend_values[valid_mask] = lowess_result[:, 1]
            result_df['Lowess_Trend'] = trend_values
            
            # 元の値との差分も計算
            result_df['Noise'] = result_df[target_column] - result_df['Lowess_Trend']
            
        except Exception as e:
            print(f"LOWESS処理中にエラーが発生しました: {str(e)}")
            result_df['Lowess_Trend'] = df[target_column]
            result_df['Noise'] = 0
        
        return result_df
    
    def apply_moving_average(
        self,
        df: pd.DataFrame,
        target_column: Optional[str] = None,
        window_size: int = 10
    ) -> pd.DataFrame:
        """移動平均によるスムージング処理
        
        Args:
            df: 入力データフレーム
            target_column: 対象カラム名
            window_size: 移動平均の窓サイズ
            
        Returns:
            処理済みデータフレーム
        """
        
        # 処理対象カラムの決定
        if target_column is None:
            target_column = self._find_energy_column(df)
            if target_column is None:
                raise ValueError("エネルギー関連のカラムが見つかりません")
        
        # データのコピー作成
        result_df = df.copy()
        
        # 移動平均の計算
        result_df['MovingAverage'] = (
            df[target_column]
            .rolling(window=window_size, center=True)
            .mean()
        )
        
        # 欠損値を元の値で補完
        result_df['MovingAverage'].fillna(df[target_column], inplace=True)
        
        return result_df
    
    def apply_median_filter(
        self,
        df: pd.DataFrame,
        target_column: Optional[str] = None,
        window_size: int = 5
    ) -> pd.DataFrame:
        """メディアンフィルタによるノイズ除去
        
        Args:
            df: 入力データフレーム
            target_column: 対象カラム名
            window_size: フィルタの窓サイズ
            
        Returns:
            処理済みデータフレーム
        """
        
        # 処理対象カラムの決定
        if target_column is None:
            target_column = self._find_energy_column(df)
            if target_column is None:
                raise ValueError("エネルギー関連のカラムが見つかりません")
        
        # データのコピー作成
        result_df = df.copy()
        
        # メディアンフィルタの適用
        result_df['MedianFiltered'] = (
            df[target_column]
            .rolling(window=window_size, center=True)
            .median()
        )
        
        # 欠損値を元の値で補完
        result_df['MedianFiltered'].fillna(df[target_column], inplace=True)
        
        return result_df
    
    def remove_outliers(
        self,
        df: pd.DataFrame,
        target_column: Optional[str] = None,
        method: str = 'iqr',
        threshold: float = 1.5
    ) -> pd.DataFrame:
        """外れ値の除去
        
        Args:
            df: 入力データフレーム
            target_column: 対象カラム名
            method: 'iqr' または 'zscore'
            threshold: 閾値（IQRの倍数またはZスコア）
            
        Returns:
            外れ値を除去したデータフレーム
        """
        
        # 処理対象カラムの決定
        if target_column is None:
            target_column = self._find_energy_column(df)
            if target_column is None:
                raise ValueError("エネルギー関連のカラムが見つかりません")
        
        # データのコピー作成
        result_df = df.copy()
        
        if method == 'iqr':
            # IQR法による外れ値検出
            Q1 = df[target_column].quantile(0.25)
            Q3 = df[target_column].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            
            # 外れ値をNaNに置換
            result_df.loc[
                (result_df[target_column] < lower_bound) | 
                (result_df[target_column] > upper_bound),
                target_column + '_cleaned'
            ] = np.nan
            
            # 線形補間で穴埋め
            result_df[target_column + '_cleaned'] = (
                result_df[target_column + '_cleaned']
                .interpolate(method='linear')
            )
            
        elif method == 'zscore':
            # Zスコア法による外れ値検出
            mean = df[target_column].mean()
            std = df[target_column].std()
            
            z_scores = np.abs((df[target_column] - mean) / std)
            
            # 外れ値をNaNに置換
            result_df.loc[z_scores > threshold, target_column + '_cleaned'] = np.nan
            
            # 線形補間で穴埋め
            result_df[target_column + '_cleaned'] = (
                result_df[target_column + '_cleaned']
                .interpolate(method='linear')
            )
        
        return result_df
    
    def _find_energy_column(self, df: pd.DataFrame) -> Optional[str]:
        """エネルギー関連のカラムを自動検出"""
        
        energy_candidates = [
            '穿孔エネルギー',
            'エネルギー',
            'Energy',
            'energy',
            '削孔エネルギー',
            'Ene-M',
            'エネルギー値'
        ]
        
        for col in energy_candidates:
            if col in df.columns:
                return col
        
        # 部分一致で検索
        for col in df.columns:
            if 'エネルギー' in col or 'energy' in col.lower():
                return col
        
        return None
    
    def process_multiple_files(
        self,
        data_dict: Dict[str, pd.DataFrame],
        frac: float = None,
        it: int = None,
        delta: float = None,
        use_parallel: bool = True
    ) -> Tuple[Dict[str, pd.DataFrame], pd.DataFrame]:
        """複数ファイルの並列処理（元スクリプトの機能を再現）
        
        Args:
            data_dict: ファイル名とデータフレームの辞書
            frac: LOWESSパラメータ
            it: 反復回数
            delta: デルタパラメータ
            use_parallel: 並列処理を使用するか
            
        Returns:
            個別処理結果の辞書と統合データフレーム
        """
        
        # パラメータのデフォルト値設定
        frac = frac if frac is not None else self.default_frac
        it = it if it is not None else self.default_it
        delta = delta if delta is not None else self.default_delta
        
        individual_results = {}
        
        if use_parallel and len(data_dict) > 1:
            # 並列処理
            with concurrent.futures.ProcessPoolExecutor() as executor:
                futures = {
                    executor.submit(self._process_single_file, df, frac, it, delta): name
                    for name, df in data_dict.items()
                }
                
                for future in concurrent.futures.as_completed(futures):
                    name = futures[future]
                    try:
                        result = future.result()
                        if result is not None:
                            individual_results[name] = result
                    except Exception as e:
                        print(f"ファイル {name} の処理中にエラー: {e}")
        else:
            # 逐次処理
            for name, df in data_dict.items():
                result = self._process_single_file(df, frac, it, delta)
                if result is not None:
                    individual_results[name] = result
        
        # 統合データの作成
        combined_data = self._create_combined_data(individual_results)
        
        return individual_results, combined_data
    
    def _process_single_file(
        self,
        df: pd.DataFrame,
        frac: float,
        it: int,
        delta: float
    ) -> Optional[pd.DataFrame]:
        """単一ファイルの処理（元スクリプトのprocess_file関数を再現）"""
        
        try:
            # 必須カラムの確認
            if '穿孔長' not in df.columns:
                print("'穿孔長' 列が見つかりません")
                return None
            
            # LOWESS処理
            result_df = self.apply_lowess(df, target_column='穿孔エネルギー', 
                                         frac=frac, it=it, delta=delta)
            
            return result_df
        except Exception as e:
            print(f"処理中にエラー: {e}")
            return None
    
    def _create_combined_data(
        self,
        individual_results: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """統合データの作成（元スクリプトの統合処理を再現）"""
        
        if not individual_results:
            return pd.DataFrame()
        
        combined_data = pd.DataFrame()
        
        for name, data in individual_results.items():
            # 必要なカラムを指定の順序で抽出
            # 順序: 穿孔長、穿孔エネルギー、Lowess_Trend
            ordered_cols = []
            if '穿孔長' in data.columns:
                ordered_cols.append('穿孔長')
            if '穿孔エネルギー' in data.columns:
                ordered_cols.append('穿孔エネルギー')
            if 'Lowess_Trend' in data.columns:
                ordered_cols.append('Lowess_Trend')
            
            if not ordered_cols:
                continue
            
            extracted_data = data[ordered_cols].copy()
            
            # カラム名にファイル名を付与
            base_name = name.replace('.csv', '')
            extracted_data.columns = [f'{base_name}_{col}' for col in extracted_data.columns]
            
            # 横方向に結合
            if combined_data.empty:
                combined_data = extracted_data
            else:
                combined_data = pd.concat([combined_data, extracted_data], axis=1)
        
        return combined_data
    
    def save_results(
        self,
        individual_results: Dict[str, pd.DataFrame],
        combined_data: pd.DataFrame,
        output_dir: str,
        encoding: str = 'shift_jis'
    ) -> Dict[str, str]:
        """処理結果の保存（元スクリプトの保存処理を再現）
        
        Returns:
            保存したファイルパスの辞書
        """
        
        saved_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 個別ファイルの保存
        for name, data in individual_results.items():
            base_name = name.replace('.csv', '')
            output_file = os.path.join(output_dir, f"{base_name}_ana_{timestamp}.csv")
            data.to_csv(output_file, index=False, encoding=encoding)
            saved_files[f'individual_{name}'] = output_file
        
        # 統合ファイルの保存
        if not combined_data.empty:
            combined_file = os.path.join(output_dir, f"combined_data_{timestamp}.csv")
            combined_data.to_csv(combined_file, index=False, encoding=encoding)
            saved_files['combined'] = combined_file
        
        return saved_files