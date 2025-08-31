"""
データローダーモジュール
CSVファイルの読み込みとエンコーディング自動検出
"""

import pandas as pd
import chardet
from pathlib import Path
from typing import Dict, List, Optional, Union
import io


class DataLoader:
    """削孔検層データの読み込みクラス"""
    
    def __init__(self):
        self.supported_encodings = ['shift_jis', 'utf-8', 'cp932']
        
    def detect_encoding(self, file_path: Union[str, Path]) -> str:
        """ファイルのエンコーディングを自動検出"""
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            
            # Shift-JISの別名を統一
            if encoding and encoding.lower() in ['shift-jis', 'sjis', 'cp932']:
                return 'shift_jis'
            return encoding or 'utf-8'
    
    def load_single_file(self, file_path: Union[str, Path], header_row: int = 0) -> pd.DataFrame:
        """単一のCSVファイルを読み込み
        
        Args:
            file_path: ファイルパス
            header_row: ヘッダー行番号（0ベース）。1を指定すると2行目からデータとして読む
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")
        
        # エンコーディング検出
        encoding = self.detect_encoding(file_path)
        
        try:
            # CSVを読み込み（header_rowパラメータを使用）
            df = pd.read_csv(file_path, encoding=encoding, header=header_row)
            
            # カラム名のクリーニング
            df.columns = [self._clean_column_name(col) for col in df.columns]
            
            # 数値カラムの型変換
            df = self._convert_numeric_columns(df)
            
            return df
            
        except Exception as e:
            # 別のエンコーディングで再試行
            for enc in self.supported_encodings:
                if enc != encoding:
                    try:
                        df = pd.read_csv(file_path, encoding=enc, header=header_row)
                        df.columns = [self._clean_column_name(col) for col in df.columns]
                        return self._convert_numeric_columns(df)
                    except:
                        continue
            
            raise ValueError(f"ファイルの読み込みに失敗しました: {file_path}\nエラー: {str(e)}")
    
    def load_from_stream(self, file_stream, header_row: int = 0) -> pd.DataFrame:
        """Streamlitのアップロードファイルから読み込み
        
        Args:
            file_stream: アップロードされたファイルストリーム
            header_row: ヘッダー行番号（0ベース）
        """
        # バイナリデータを読み込み
        bytes_data = file_stream.read()
        
        # エンコーディング検出
        result = chardet.detect(bytes_data[:10000])
        encoding = result['encoding']
        if encoding and encoding.lower() in ['shift-jis', 'sjis', 'cp932']:
            encoding = 'shift_jis'
        
        # データフレームに変換
        try:
            df = pd.read_csv(io.BytesIO(bytes_data), encoding=encoding or 'utf-8', header=header_row)
        except:
            # UTF-8で再試行
            df = pd.read_csv(io.BytesIO(bytes_data), encoding='utf-8', header=header_row)
        
        # カラム名のクリーニング
        df.columns = [self._clean_column_name(col) for col in df.columns]
        
        return self._convert_numeric_columns(df)
    
    def load_multiple_files(self, file_paths: List[Union[str, Path]], header_row: int = 0) -> Dict[str, pd.DataFrame]:
        """複数のCSVファイルを読み込み
        
        Args:
            file_paths: ファイルパスのリスト
            header_row: ヘッダー行番号（0ベース）
        """
        data_dict = {}
        
        for file_path in file_paths:
            file_path = Path(file_path)
            df = self.load_single_file(file_path, header_row=header_row)
            data_dict[file_path.name] = df
        
        return data_dict
    
    def _clean_column_name(self, column_name: str) -> str:
        """カラム名をクリーニング"""
        # 不要な空白や特殊文字を除去
        cleaned = str(column_name).strip()
        
        # よくある変換
        replacements = {
            '穿孔エネルギー': '穿孔エネルギー',
            'ｴﾈﾙｷﾞｰ': 'エネルギー',
            'Ene-L': 'Ene-L',
            'Ene-M': 'Ene-M',
            'Ene-R': 'Ene-R',
            'x:TD(m)': 'TD',
            'X(m)': 'X',
            'Y(m)': 'Y',
            'Z:標高(m)': 'Z',
            'z:SL差(m)': 'Z_SL'
        }
        
        for old, new in replacements.items():
            if old in cleaned:
                return new
        
        return cleaned
    
    def _convert_numeric_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """数値カラムを適切な型に変換"""
        numeric_columns = ['TD', 'X', 'Y', 'Z', 'Z_SL', 
                          'Ene-L', 'Ene-M', 'Ene-R', 
                          '穿孔エネルギー', 'エネルギー',
                          'H:方位角(Deg)', 'V:傾斜角(Deg)']
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def get_data_info(self, df: pd.DataFrame) -> Dict:
        """データフレームの基本情報を取得"""
        info = {
            'rows': len(df),
            'columns': len(df.columns),
            'numeric_columns': list(df.select_dtypes(include=['float64', 'int64']).columns),
            'text_columns': list(df.select_dtypes(include=['object']).columns),
            'missing_values': df.isnull().sum().to_dict(),
            'memory_usage': df.memory_usage(deep=True).sum() / 1024 / 1024  # MB
        }
        
        # 座標情報の存在確認
        info['has_coordinates'] = all(col in df.columns for col in ['X', 'Y', 'Z'])
        info['has_energy'] = any(col in df.columns for col in ['穿孔エネルギー', 'エネルギー', 'Ene-L', 'Ene-M', 'Ene-R'])
        info['has_depth'] = 'TD' in df.columns
        
        return info