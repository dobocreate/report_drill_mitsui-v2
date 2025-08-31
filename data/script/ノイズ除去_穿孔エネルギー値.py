import pandas as pd
import numpy as np
import statsmodels.api as sm
import tkinter as tk
from tkinter import filedialog, simpledialog
from tqdm import tqdm
import os
import concurrent.futures  # 並列処理のために追加
from datetime import datetime  # タイムスタンプのために追加
import chardet  # エンコード判定用のライブラリ

def analyze_data(data, frac, it, delta):
    """
    与えられたデータに対してLOWESS回帰を行い、トレンドを計算する関数。

    Args:
        data (pd.DataFrame): 処理対象のデータフレーム。'穿孔エネルギー'列が含まれている必要がある。
        frac (float): LOWESSのパラメータ (0 < frac <= 1)。
        it (int): LOWESSのパラメータ (反復回数)。
        delta (float): LOWESSのパラメータ。

    Returns:
        pd.DataFrame: 'Lowess_Trend'列が追加されたデータフレーム。
    """
    lowess = sm.nonparametric.lowess(data['穿孔エネルギー'], data.index, frac=frac, it=it, delta=delta)
    data['Lowess_Trend'] = lowess[:, 1]
    return data

def detect_file_encoding(file_path, num_bytes=10000):
    """
    指定されたファイルのエンコードを判定します。

    Args:
        file_path (str): ファイルのパス
        num_bytes (int): 判定に使用するバイト数（デフォルト: 10000）

    Returns:
        str: 検出されたエンコード
    """
    with open(file_path, 'rb') as f:
        rawdata = f.read(num_bytes)
    result = chardet.detect(rawdata)
    encoding = result['encoding']
    print(f"ファイル {file_path} の検出されたエンコード: {encoding}")
    return encoding

def process_file(file_path, frac, it, delta):
    """
    個々のファイルを処理する関数。並列処理で呼び出される。
    
    ファイル読み込み時に、まずdetect_file_encoding()を使用してエンコードを判定し、
    そのエンコードで読み込みを試み、失敗した場合はutf-16、shift_jisの順に再試行します。

    Args:
        file_path (str): 処理対象のファイルパス。
        frac (float): LOWESSのパラメータ。
        it (int): LOWESSのパラメータ。
        delta (float): LOWESSのパラメータ。

    Returns:
        tuple: (pd.DataFrame, str) 処理結果のデータフレームとファイル名、
               エラー時は (None, None)。
    """
    try:
        # ファイルのエンコードを検出する
        encoding = detect_file_encoding(file_path)

        # 検出されたエンコードでファイルを読み込む
        try:
            data = pd.read_csv(file_path, encoding=encoding, header=1)
        except Exception as e:
            print(f"ファイル {file_path} の読み込みに {encoding} で失敗しました: {e}")
            try:
                data = pd.read_csv(file_path, encoding="utf-16", header=1)
            except UnicodeDecodeError:
                print(f"ファイル {file_path} の読み込みに utf-16 で失敗しました。shift_jisで再試行します。")
                data = pd.read_csv(file_path, encoding="shift_jis", header=1)

        # LOWESS解析を実施（元データにLowess_Trend列を追加）
        result_df = analyze_data(data, frac, it, delta)

        # 元のデータをそのまま保持するために全カラムをコピー
        if '穿孔長' in result_df.columns:
            extracted_data = result_df.copy()
        else:
            print(f"ファイル {file_path} に '穿孔長' 列が見つかりませんでした。スキップします。")
            return None, None

        # ※ ファイル名のカラムは不要のため、追加しない

        # base_nameは統合ファイル作成用に返す
        base_name = os.path.splitext(os.path.basename(file_path))[0]

        return extracted_data, base_name

    except Exception as e:
        print(f"ファイル {file_path} の処理中にエラーが発生しました: {e}")
        return None, None

def main():
    root = tk.Tk()
    root.withdraw()

    # 複数のCSVファイルを選択するダイアログの表示
    file_paths = filedialog.askopenfilenames(title="CSVファイルを選択してください", filetypes=[("CSV files", "*.csv")])
    if not file_paths:
        return

    # パラメータの入力ダイアログ（一度だけ表示）
    frac = simpledialog.askfloat("パラメータ設定", "fracの値を入力してください (0 < frac <= 1):", initialvalue=0.04)
    it = simpledialog.askinteger("パラメータ設定", "itの値を入力してください:", initialvalue=3)
    delta = simpledialog.askfloat("パラメータ設定", "deltaの値を入力してください:", initialvalue=0.0)

    all_data = []               # 全てのデータを格納するリスト
    individual_results = {}     # 個別処理結果を保存する辞書

    # 並列処理の実行
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [executor.submit(process_file, file_path, frac, it, delta) for file_path in file_paths]

        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="ファイル処理中"):
            result, base_name = future.result()
            if result is not None:
                all_data.append(result)
                individual_results[base_name] = result

    # 個別ファイルの保存（元データ全体を含む）
    for base_name, data in individual_results.items():
        output_dir = os.path.dirname(file_paths[0])
        # タイムスタンプを各ファイルの保存名に付与
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file_path = os.path.join(output_dir, f"{base_name}_ana_{timestamp}.csv")
        data.to_csv(output_file_path, index=False, encoding="shift_jis")
        print(f"個別データを {output_file_path} に保存しました。")

    # 全てのデータの統合（従来通り、主要なカラムのみ連結）
    if all_data:
        combined_data = pd.DataFrame()
        for base_name, data in individual_results.items():
            extracted_data = data[['穿孔長', '穿孔エネルギー', 'Lowess_Trend']]
            # 各ファイルの識別子としてbase_nameを列名のプレフィックスに付与
            extracted_data.columns = [f'{base_name}_穿孔長', f'{base_name}_穿孔エネルギー', f'{base_name}_Lowess_Trend']
            if combined_data.empty:
                combined_data = extracted_data
            else:
                combined_data = pd.concat([combined_data, extracted_data], axis=1)

        output_dir = os.path.dirname(file_paths[0])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file_path = os.path.join(output_dir, f"combined_data_{timestamp}.csv")
        combined_data.to_csv(output_file_path, index=False, encoding="shift_jis")
        print(f"統合データを {output_file_path} に保存しました。")
    else:
        print("処理できるファイルがありませんでした。")

if __name__ == "__main__":
    main()
