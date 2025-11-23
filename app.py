import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
from src.data_loader import DataLoader
from src.state import AppState
from src.ui import styles
from src.ui.overview import display_data_overview
from src.ui.extraction import display_data_extraction
from src.ui.stretching import display_data_stretching
from src.ui.noise import display_noise_removal
from src.ui.processing import display_data_processing
from src.ui.vtk import display_vtk_generation

# Page Config
st.set_page_config(
    page_title="削孔検層データ統合分析システム",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

STEPS = ["データ概要", "データ抽出", "データ拡張", "ノイズ除去", "サンプリング", "VTK生成"]

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
    <div style="text-align: center; padding: 2rem;">
        <h1>⛏️ 削孔検層データ統合分析システム</h1>
        <p style="font-size: 1.2rem; color: #888;">Drilling Logging Data Integrated Analysis System</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        ### 👋 ようこそ
        
        このアプリケーションでは、トンネル工事における削孔検層データの可視化、分析、加工、
        そして3Dモデル化（VTK）を一元的に行うことができます。
        
        ### 🚀 始めるには
        
        左側のサイドバーから **「プロジェクト情報」** を入力し、
        **「データを読み込む」** で開始してください。
        """)
        
    with col2:
        st.info("""
        ### ✨ 主な機能
        
        1. **📊 データ概要**: 基本情報とエネルギー分布
        2. **✂️ データ抽出**: 深度範囲による切り出し
        3. **📏 データ拡張**: 長さ補正（スケーリング）
        4. **🔧 ノイズ除去**: Lowessフィルタリング
        5. **📉 データ加工**: 間引きと補間
        6. **📦 VTK生成**: 3D可視化データ作成
        """)

def render_sidebar():
    """サイドバーのレンダリング"""
    with st.sidebar:
        st.title("⛏️ 分析メニュー")
        
        # 1. プロジェクト情報
        st.subheader("📋 プロジェクト情報")
        with st.container():
            project_date = st.date_input(
                "実施日",
                value=datetime.now(),
                help="出力ファイル名に使用されます"
            )
            AppState.set_project_date(project_date)
            
            survey_point = st.text_input(
                "測点",
                placeholder="例: 250+11",
                help="測点を 主番号+小数部 の形式で入力（例: 250+11）"
            )
            AppState.set_survey_point(survey_point)
        
        # 2. データ入力
        st.subheader("📂 データ入力")
        
        uploaded_files = st.file_uploader(
            "CSVファイルをアップロード",
            type=['csv'],
            accept_multiple_files=True,
            help="Shift-JISまたはUTF-8形式のCSVファイル"
        )

        use_sample = st.checkbox("サンプルデータを使用", value=False)

        with st.expander("⚙️ 読み込み設定", expanded=False):
            header_row = st.selectbox(
                "ヘッダー行",
                options=[0, 1, 2, 3],
                index=1,
                format_func=lambda x: f"{x+1}行目"
            )
            st.session_state[AppState.KEY_HEADER_ROW] = header_row

        # データ読み込み実行
        if uploaded_files or use_sample:
            if st.button("データを読み込む", type="primary", use_container_width=True):
                with st.spinner("データを読み込んでいます..."):
                    raw_data = load_data(uploaded_files, use_sample, header_row)

                    if raw_data:
                        AppState.set_raw_data(raw_data)
                        st.success(f"✅ {len(raw_data)}個のファイルを読み込みました")
                        AppState.set_current_step(0) # 最初のステップへ
                        st.rerun()
                    else:
                        st.error("データの読み込みに失敗しました")

        st.divider()

        # 3. 進捗状況 (Stepper)
        if AppState.is_data_loaded():
            st.subheader("📍 進捗状況")
            current_step = AppState.get_current_step()
            
            for i, step_name in enumerate(STEPS):
                if i == current_step:
                    st.markdown(f"**🔷 {i+1}. {step_name}** 👈")
                elif i < current_step:
                    st.markdown(f"✅ {i+1}. {step_name}")
                else:
                    st.markdown(f"<span style='color: #666'>⚪ {i+1}. {step_name}</span>", unsafe_allow_html=True)

def render_header_navigation():
    """ヘッダーナビゲーションのレンダリング（タイトルの下）"""
    # ナビゲーションエリアの開始マーカー
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    
    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
    current_step = AppState.get_current_step()
    
    with nav_col1:
        if current_step > 0:
            if st.button("⬅️ 戻る", key="nav_back", use_container_width=True):
                AppState.set_current_step(current_step - 1)
                st.rerun()
    
    with nav_col2:
        # スキップボタン削除
        pass
    
    with nav_col3:
        if current_step < len(STEPS) - 1:
            if st.button("次へ ➡️", key="nav_next", type="primary", use_container_width=True):
                AppState.set_current_step(current_step + 1)
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    # ナビゲーションエリアの終了マーカー
    
    st.divider()

def main():
    """メインアプリケーション"""
    # セッション状態の初期化
    AppState.initialize()
    
    # カスタムCSSの読み込み
    styles.load_css()

    # サイドバーレンダリング
    render_sidebar()

    # メインコンテンツ
    if AppState.is_data_loaded():
        current_step = AppState.get_current_step()
        step_name = STEPS[current_step]
        
        # ステップタイトルのマッピング
        STEP_HEADERS = {
            "データ概要": "📊 データ概要",
            "データ抽出": "✂️ データ抽出・部分分析",
            "データ拡張": "📏 データ拡張",
            "ノイズ除去": "🔧 ノイズ除去",
            "サンプリング": "📉 サンプリング",
            "VTK生成": "📦 VTKファイル生成"
        }
        
        # 1. タイトルを表示
        st.header(STEP_HEADERS.get(step_name, step_name))
        
        # 2. ナビゲーション（タイトルの下）
        render_header_navigation()

        # 3. コンテンツ表示
        if step_name == "データ概要":
            display_data_overview()
        elif step_name == "データ抽出":
            display_data_extraction()
        elif step_name == "データ拡張":
            display_data_stretching()
        elif step_name == "ノイズ除去":
            display_noise_removal()
        elif step_name == "サンプリング":
            display_data_processing()
        elif step_name == "VTK生成":
            display_vtk_generation()
            
    else:
        display_welcome()

if __name__ == "__main__":
    main()