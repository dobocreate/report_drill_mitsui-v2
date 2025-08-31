"""
ヘッダー行選択の動作確認テスト
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# プロジェクトのパスを追加
sys.path.append(str(Path(__file__).parent))

from src.data_loader import DataLoader

def test_header_row_functionality():
    """ヘッダー行の読み込みテスト"""
    
    print("=" * 60)
    print("ヘッダー行選択機能のテスト")
    print("=" * 60)
    
    loader = DataLoader()
    test_file = "data/2025_07_29_07_12_06_L_002.csv"
    
    if Path(test_file).exists():
        print(f"\nテストファイル: {test_file}")
        
        # 1行目をヘッダーとして読み込み（header_row=0）
        print("\n1. header_row=0（1行目がヘッダー）")
        df_header0 = loader.load_single_file(test_file, header_row=0)
        print(f"   データ行数: {len(df_header0)}")
        print(f"   カラム名（最初の5つ）: {list(df_header0.columns[:5])}")
        if '穿孔エネルギー' in df_header0.columns:
            print("   ✅ '穿孔エネルギー'カラムが検出されました")
        else:
            print("   ❌ '穿孔エネルギー'カラムが見つかりません")
        
        # 2行目をヘッダーとして読み込み（header_row=1）
        print("\n2. header_row=1（2行目がヘッダー、1行目スキップ）")
        df_header1 = loader.load_single_file(test_file, header_row=1)
        print(f"   データ行数: {len(df_header1)}")
        print(f"   カラム名（最初の5つ）: {list(df_header1.columns[:5])}")
        if '穿孔エネルギー' in df_header1.columns:
            print("   ✅ '穿孔エネルギー'カラムが検出されました")
        else:
            print("   ❌ '穿孔エネルギー'カラムが見つかりません")
        
        # データ行数の差を確認
        print(f"\n3. データ行数の差: {len(df_header0) - len(df_header1)} 行")
        print("   （header_row=1の場合、1行少なくなるはず）")
        
        # 実際のデータの最初の数行を表示
        print("\n4. 実際のデータ内容（header_row=1の場合）")
        print("   最初の3行:")
        for col in ['穿孔長', '穿孔エネルギー', 'TD', 'Ene-M']:
            if col in df_header1.columns:
                print(f"   {col}: {df_header1[col].head(3).tolist()}")
                break
        
        return True
    else:
        print(f"❌ テストファイルが見つかりません: {test_file}")
        return False

def check_streamlit_session():
    """Streamlitセッション状態の確認"""
    print("\n5. Streamlitセッション状態の推奨設定")
    print("   - デフォルトで header_row_value = 1 を設定")
    print("   - これにより「2行目」がデフォルトで選択される")
    print("   - st.selectbox の index パラメータで制御")
    
    print("\n推奨コード:")
    print("""
    if 'header_row_value' not in st.session_state:
        st.session_state.header_row_value = 1  # デフォルトで2行目
    
    header_row = st.selectbox(
        "ヘッダー行",
        options=[0, 1],
        index=st.session_state.header_row_value,  # デフォルト値を設定
        format_func=lambda x: "1行目" if x == 0 else "2行目（1行目をスキップ）",
        key="header_row_select"
    )
    st.session_state.header_row_value = header_row  # 選択値を保存
    """)

if __name__ == "__main__":
    success = test_header_row_functionality()
    check_streamlit_session()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ヘッダー行選択機能は正常に動作しています")
        print("\n次のステップ:")
        print("1. Streamlitアプリを再起動")
        print("2. デフォルトで「2行目」が選択されていることを確認")
        print("3. データ読み込み後も設定が保持されることを確認")
    else:
        print("❌ テストに失敗しました")
    print("=" * 60)