"""
ノイズ除去機能の詳細テスト
元のスクリプトと同じ処理が行われているか確認
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# プロジェクトのパスを追加
sys.path.append(str(Path(__file__).parent))

from src.data_loader import DataLoader
from src.noise_remover import NoiseRemover
from datetime import datetime

def test_noise_removal_functionality():
    """ノイズ除去機能の詳細テスト"""
    
    print("=" * 60)
    print("ノイズ除去機能の詳細テスト")
    print("=" * 60)
    
    # 1. テストデータの準備
    test_files = [
        "data/2025_07_29_07_12_06_L_002.csv",
        "data/2025_07_29_07_12_06_M_001.csv",
        "data/2025_07_29_07_12_06_R_002.csv"
    ]
    
    # DataLoaderとNoiseRemoverのインスタンス作成
    loader = DataLoader()
    remover = NoiseRemover()
    
    # 2. パラメータの確認
    print("\n1. LOWESS パラメータの確認")
    print(f"   - default_frac: {remover.default_frac}")
    print(f"   - default_it: {remover.default_it}")
    print(f"   - default_delta: {remover.default_delta}")
    
    if remover.default_frac == 0.04:
        print("   ✅ fracパラメータが元スクリプトと一致 (0.04)")
    else:
        print(f"   ❌ fracパラメータが異なる: {remover.default_frac} (期待値: 0.04)")
    
    # 3. 単一ファイルの処理テスト
    print("\n2. 単一ファイル処理のテスト")
    test_file = test_files[0]
    
    if Path(test_file).exists():
        print(f"   テストファイル: {test_file}")
        
        # ヘッダー行を1に設定（2行目からデータ）
        df = loader.load_single_file(test_file, header_row=1)
        print(f"   ✅ ファイル読み込み成功: {len(df)}行")
        print(f"   カラム: {', '.join(df.columns[:5])}...")
        
        # エネルギー関連カラムの確認
        energy_col = remover._find_energy_column(df)
        if energy_col:
            print(f"   ✅ エネルギーカラムを検出: {energy_col}")
            
            # ノイズ除去処理
            result_df = remover.apply_lowess(df, frac=0.04)
            
            # 結果の確認
            smoothed_col = f"{energy_col}_smoothed"
            if smoothed_col in result_df.columns and energy_col in df.columns:
                # 変化の確認
                original_values = df[energy_col].dropna()
                smoothed_values = result_df[smoothed_col].dropna()
                
                if len(original_values) > 0 and len(smoothed_values) > 0:
                    diff = np.abs(original_values.values[:len(smoothed_values)] - smoothed_values.values).mean()
                    print(f"   ✅ {energy_col}: 平均差分 = {diff:.4f}")
        else:
            print("   ⚠️ エネルギーカラムが見つかりません")
    else:
        print(f"   ❌ テストファイルが見つかりません: {test_file}")
    
    # 4. 複数ファイルの並列処理テスト
    print("\n3. 複数ファイル並列処理のテスト")
    
    existing_files = [f for f in test_files if Path(f).exists()]
    
    if existing_files:
        print(f"   処理対象ファイル数: {len(existing_files)}")
        
        # 複数ファイルを読み込み
        data_dict = {}
        for file in existing_files:
            df = loader.load_single_file(file, header_row=1)
            data_dict[Path(file).name] = df
            print(f"   ✅ {Path(file).name}: {len(df)}行")
        
        # 並列処理
        print("\n   並列処理を実行中...")
        individual_results, combined_data = remover.process_multiple_files(
            data_dict, 
            frac=0.04, 
            use_parallel=True
        )
        
        # 結果の確認
        print(f"   ✅ 処理完了: {len(individual_results)}個のファイル")
        
        # 個別ファイルの結果確認
        for filename, df in individual_results.items():
            print(f"   - {filename}: {len(df)}行")
        
        # 結合ファイルの確認
        if combined_data is not None:
            print(f"   ✅ 結合ファイル: {len(combined_data)}行")
            
            # ファイル名カラムの確認
            if 'ファイル名' in combined_data.columns:
                unique_files = combined_data['ファイル名'].unique()
                print(f"   ✅ ファイル名カラムあり: {len(unique_files)}ファイル")
        else:
            print("   ⚠️ 結合ファイルが作成されませんでした")
    else:
        print("   ❌ 処理可能なファイルが見つかりません")
    
    # 5. 出力ファイル名の形式確認
    print("\n4. 出力ファイル名形式の確認")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 個別ファイル名の形式
    test_name = "test_file.csv"
    expected_individual = f"{Path(test_name).stem}_ana_{timestamp}.csv"
    print(f"   個別ファイル名形式: {expected_individual}")
    
    # 結合ファイル名の形式
    expected_combined = f"combined_data_{timestamp}.csv"
    print(f"   結合ファイル名形式: {expected_combined}")
    
    print("\n" + "=" * 60)
    print("詳細テスト完了")
    print("=" * 60)
    
    return True

def test_sample_data():
    """サンプルデータの動作確認"""
    print("\n5. サンプルデータの動作確認")
    
    sample_dir = Path("sample_data")
    if sample_dir.exists():
        sample_files = list(sample_dir.glob("*.csv"))
        if sample_files:
            print(f"   ✅ サンプルデータが存在: {len(sample_files)}ファイル")
            for f in sample_files[:3]:
                print(f"   - {f.name}")
        else:
            print("   ⚠️ サンプルデータディレクトリは存在するがCSVファイルがありません")
    else:
        print("   ℹ️ サンプルデータディレクトリが存在しません")

if __name__ == "__main__":
    # 詳細機能テスト
    success = test_noise_removal_functionality()
    
    # サンプルデータテスト
    test_sample_data()
    
    # 推奨事項
    print("\n" + "=" * 60)
    print("推奨事項")
    print("=" * 60)
    print("1. ブラウザで http://localhost:8502 にアクセス")
    print("2. サイドバーの「サンプルデータを使用」をチェック")
    print("3. ヘッダー行を「2行目」に設定")
    print("4. 「データ読み込み」をクリック")
    print("5. 「ノイズ除去」タブで「複数ファイル一括処理」を選択")
    print("6. 「一括ノイズ除去実行」をクリック")
    print("7. 個別ファイルと結合ファイルのダウンロードボタンが表示されることを確認")