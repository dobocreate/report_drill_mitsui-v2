"""
削孔検層データ統合分析アプリケーション
Streamlit + Plotly による対話的可視化とVTK生成
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from src.data_loader import DataLoader
from src.state import AppState
from src.ui.overview import display_data_overview
from src.ui.extraction import display_data_extraction
from src.ui.stretching import display_data_stretching
from src.ui.noise import display_noise_removal
from src.ui.processing import display_data_processing
from src.ui.vtk import display_vtk_generation

# ページ設定
st.set_page_config(
    page_title="削孔検層データ統合分析システム",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff;
        border-bottom: 2px solid #ff4b4b;
    }
    .stMetric {
        background-color: #f8f9fa;
        padding: 0.5rem 0.75rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .stMetric label {
        font-size: 0.875rem;
    }
    .stMetric [data-testid="stMetricValue"] {
        font-size: 1.25rem;
    }
</style>
""", unsafe_allow_html=True)

def load_data(uploaded_files, use_sample, header_row=1):
    """データ読み込み処理"""
    loader = DataLoader()
    
    if use_sample:
        # サンプルデータの読み込み (L, M, R)
        sample_files = [
            "data/2025_11_17_12_33_57_L.csv",
            "data/2025_11_17_12_33_57_M.csv",
            "data/2025_11_17_12_33_57_R.csv"
        ]
        
        data_dict = {}
        for file_path in sample_files:
            path = Path(file_path)
            if path.exists():
                try:
                    df = loader.load_single_file(path, header_row=header_row)
                    data_dict[path.name] = df
                except Exception as e:
                    st.error(f"サンプルファイル {path.name} の読み込みに失敗: {str(e)}")
            else:
                st.warning(f"サンプルファイルが見つかりません: {file_path}")
        
        return data_dict
    
    if uploaded_files:
        try:
            # 複数ファイルを一括読み込み
            data_dict = {}
            for uploaded_file in uploaded_files:
                df = loader.load_from_stream(uploaded_file, header_row=header_row)
                data_dict[uploaded_file.name] = df
            return data_dict
        except Exception as e:
            st.error(f"データ読み込みエラー: {str(e)}")
            return {}
            
    return {}

def display_welcome():
    """ウェルカム画面表示"""
    st.markdown("""
    ## 👋 ようこそ！
    
    **削孔検層データ統合分析システム**へようこそ。
    このアプリケーションでは、トンネル工事における削孔検層データの可視化、分析、加工、そして3Dモデル化（VTK）を一元的に行うことができます。
    
    ### 🚀 始めるには
    
    左側のサイドバーから **「CSVファイルをアップロード」** またはサンプルデータを使用してください。
    
    ### ✨ 主な機能
    
    1. **📊 データ概要**: データの基本情報とエネルギー分布を確認
    2. **✂️ データ抽出**: 深度範囲によるデータの切り出し
    3. **📏 データ拡張**: データの長さを補正（スケーリング）
    4. **🔧 ノイズ除去**: Lowessフィルタによるスムージング処理
    5. **📉 データ加工**: データの間引きと補間
    6. **📦 VTK生成**: 3D可視化用のVTKファイル生成
    """)
    
    st.info("👈 サイドバーからデータをアップロードして開始してください")

def display_main_content():
    """メインコンテンツ表示"""
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 データ概要",
        "✂️ データ抽出",
        "📏 データ拡張",
        "🔧 ノイズ除去",
        "📉 データ加工",
        "📦 VTK生成"
    ])
    
    with tab1:
        display_data_overview()
        
    with tab2:
        display_data_extraction()
        
    with tab3:
        display_data_stretching()
        
    with tab4:
        display_noise_removal()
        
    with tab5:
        display_data_processing()
        
    with tab6:
        display_vtk_generation()

def main():
    """メインアプリケーション"""
    # セッション状態の初期化
    AppState.initialize()
    
    st.title("⛏️ 削孔検層データ統合分析システム")
    st.caption("Drilling Logging Data Integrated Analysis System")
    
    # サイドバー設定
    with st.sidebar:
        st.header("📂 データ入力")
        
        # ファイルアップロード
        uploaded_files = st.file_uploader(
            "CSVファイルをアップロード",
            type=['csv'],
            accept_multiple_files=True,
            help="Shift-JISまたはUTF-8形式のCSVファイル"
        )
        
        # サンプルデータ使用オプション
        use_sample = st.checkbox("サンプルデータを使用", value=False)
        
        st.divider()
        
        # 読み込み設定
        with st.expander("⚙️ 読み込み設定", expanded=False):
            header_row = st.selectbox(
                "ヘッダー行",
                options=[0, 1, 2, 3],
                index=1,  # デフォルトは2行目（インデックス1）
                format_func=lambda x: f"{x+1}行目",
                help="カラム名が記載されている行を指定します"
            )
            # AppStateに保存
            st.session_state[AppState.KEY_HEADER_ROW] = header_row
        
        # データ読み込み実行
        if uploaded_files or use_sample:
            if st.button("データを読み込む", type="primary", use_container_width=True):
                with st.spinner("データを読み込んでいます..."):
                    raw_data = load_data(uploaded_files, use_sample, header_row)
                    
                    if raw_data:
                        AppState.set_raw_data(raw_data)
                        st.success(f"✅ {len(raw_data)}個のファイルを読み込みました")
                        st.rerun()
                    else:
                        st.error("データの読み込みに失敗しました")
        
        st.divider()
        
        # 共通設定
        if AppState.is_data_loaded():
            st.header("🛠️ 共通設定")
            
            # 保存フォルダ設定
            save_folder = st.text_input(
                "保存フォルダ",
                value="output",
                help="生成されたファイルの保存先フォルダ"
            )
            st.session_state[AppState.KEY_SAVE_FOLDER] = save_folder
            
            # ノイズ除去パラメータ（サイドバーで共通設定）
            st.subheader("ノイズ除去パラメータ")
            st.session_state.lowess_frac = st.slider(
                "平滑化係数 (frac)", 
                0.01, 0.5, 0.05, 0.01,
                help="値が大きいほど滑らかになります"
            )
            st.session_state.lowess_it = st.slider(
                "反復回数 (it)", 
                1, 10, 3, 1,
                help="外れ値の影響を除去する回数"
            )
            st.session_state.lowess_delta = st.number_input(
                "Delta (高速化)", 
                0.0, 10.0, 0.0, 0.1,
                help="0より大きい値を設定すると計算が高速化されます"
            )

    # メインコンテンツの表示切り替え
    if AppState.is_data_loaded():
        display_main_content()
    else:
        display_welcome()

if __name__ == "__main__":
    main()