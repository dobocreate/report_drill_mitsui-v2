"""
削孔検層データ統合分析アプリケーション
Streamlit + Plotly による対話的可視化とVTK生成
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import numpy as np
from datetime import datetime
import io
import base64

# カスタムモジュール
from src.data_loader import DataLoader
from src.noise_remover import NoiseRemover
from src.vtk_generator import VTKGenerator
from src.plotly_visualizer import PlotlyVisualizer
from src.data_processor import DataProcessor
from src.vtk_converter import VTKConverter

# ページ設定
st.set_page_config(
    page_title="削孔検層データ分析システム",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSSスタイル
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
    .measurement-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# セッション状態の初期化
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = {}  # 空の辞書として初期化
if 'vtk_data' not in st.session_state:
    st.session_state.vtk_data = None

def main():
    """メインアプリケーション"""
    
    # ヘッダー
    st.title("⛏️ 削孔検層データ統合分析システム")
    st.markdown("**三井掘削レポート** - データ可視化・ノイズ除去・VTK生成")
    
    # サイドバー
    with st.sidebar:
        st.header("📁 データ読み込み")
        
        # ファイルアップロード
        uploaded_files = st.file_uploader(
            "CSVファイルを選択",
            type=['csv'],
            accept_multiple_files=True,
            help="複数のCSVファイルを同時に読み込めます"
        )
        
        # サンプルデータ使用オプション
        use_sample = st.checkbox("サンプルデータを使用", value=False)
        
        # ヘッダー行設定
        # デフォルト値をセッション状態に保存
        if 'header_row_value' not in st.session_state:
            st.session_state.header_row_value = 1  # デフォルトで"2行目"を選択
        
        header_row = st.selectbox(
            "ヘッダー行",
            options=[0, 1],
            index=st.session_state.header_row_value,
            format_func=lambda x: "1行目" if x == 0 else "2行目（1行目をスキップ）",
            help="データの開始行を指定します。穿孔エネルギーデータは通常2行目から開始します。",
            key="header_row_select"
        )
        st.session_state.header_row_value = header_row
        
        # 保存先フォルダ設定
        st.divider()
        st.header("💾 保存設定")
        save_folder = st.text_input(
            "保存先フォルダ",
            value="output",
            help="処理結果の保存先フォルダを指定します"
        )
        if st.button("📁 フォルダ作成"):
            Path(save_folder).mkdir(exist_ok=True)
            st.session_state.save_folder = save_folder
            st.success(f"フォルダ '{save_folder}' を作成/確認しました")
        
        if use_sample or uploaded_files:
            if st.button("📊 データ読み込み", type="primary"):
                load_data(uploaded_files, use_sample, header_row)
        
        st.divider()
        
        # 処理オプション
        if st.session_state.data_loaded:
            st.header("⚙️ 処理設定")
            
            # ノイズ除去設定
            with st.expander("🔧 ノイズ除去設定", expanded=False):
                st.slider("LOWESS Frac", 0.01, 0.5, 0.04, key="lowess_frac",
                         help="データの何割を使用するか（デフォルト: 0.04 = 4%）")
                st.slider("反復回数", 1, 10, 3, key="lowess_it",
                         help="LOWESS処理の反復回数")
                st.number_input("Delta", 0.0, 10.0, 0.0, key="lowess_delta",
                               help="距離パラメータ（通常は0.0）")
                st.checkbox("並列処理を使用", value=True, key="use_parallel",
                           help="複数ファイルを並列で処理します")
            
            # VTK生成設定
            with st.expander("📦 VTK設定", expanded=False):
                st.selectbox("座標系", ["測地系", "ローカル座標"], key="coord_system")
                st.checkbox("エネルギー値を含める", value=True, key="include_energy")
                st.number_input("サンプリング間隔", 1, 100, 10, key="sampling_interval")
            
            # グラフ設定
            with st.expander("📈 グラフ設定", expanded=False):
                st.selectbox("カラーマップ", ["Viridis", "Plasma", "Inferno", "Turbo"], key="colormap")
                st.slider("マーカーサイズ", 1, 20, 5, key="marker_size")
                st.checkbox("グリッド表示", value=True, key="show_grid")
    
    # メインコンテンツ
    if st.session_state.data_loaded:
        display_main_content()
    else:
        display_welcome()

def load_data(uploaded_files, use_sample, header_row=0):
    """データ読み込み処理
    
    Args:
        uploaded_files: アップロードされたファイル
        use_sample: サンプルデータを使用するか
        header_row: ヘッダー行番号（0: 1行目、1: 2行目をヘッダーとする）
    """
    try:
        loader = DataLoader()
        
        if use_sample:
            # サンプルデータのパス
            sample_dir = Path("data")
            sample_files = list(sample_dir.glob("*.csv"))[:3]
            data_dict = loader.load_multiple_files([str(f) for f in sample_files], header_row=header_row)
        else:
            # アップロードファイルの処理
            data_dict = {}
            for file in uploaded_files:
                df = loader.load_from_stream(file, header_row=header_row)
                data_dict[file.name] = df
        
        st.session_state.raw_data = data_dict
        st.session_state.data_loaded = True
        st.success(f"✅ {len(data_dict)}個のファイルを読み込みました")
        
    except Exception as e:
        st.error(f"❌ データ読み込みエラー: {str(e)}")

def get_graph_layout_settings():
    """共通のグラフレイアウト設定を返す"""
    return dict(
        xaxis=dict(
            range=[0, 45],  # X軸の範囲を0-45mに固定
            showgrid=True,
            gridwidth=1,
            gridcolor='LightGray',
            showline=True,
            linewidth=1,  # 枠線を細く
            linecolor='LightGray',  # 枠線の色を補助線と同じに
            mirror=True,
            tickfont=dict(size=14),  # X軸の数値フォントサイズを大きく
            title=dict(font=dict(size=16))  # X軸タイトルのフォントサイズ
        ),
        yaxis=dict(
            range=[0, 1000],  # Y軸の範囲を0-1000に設定
            showgrid=True,
            gridwidth=1,
            gridcolor='LightGray',
            showline=True,
            linewidth=1,  # 枠線を細く
            linecolor='LightGray',  # 枠線の色を補助線と同じに
            mirror=True,
            tickfont=dict(size=14),  # Y軸の数値フォントサイズを大きく
            title=dict(font=dict(size=16))  # Y軸タイトルのフォントサイズ
        ),
        plot_bgcolor='white',
        font=dict(size=14),  # 全体のフォントサイズ
        title_font=dict(size=18)  # タイトルのフォントサイズ
    )

def display_welcome():
    """ウェルカム画面表示"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("""
        ### 👋 ようこそ！
        
        このアプリケーションは削孔検層データの統合分析を行います。
        
        **主な機能:**
        - 📊 データの可視化と統計分析
        - 🔧 LOWESS法によるノイズ除去
        - ✂️ データの間引き・補間処理
        - 📦 VTKファイル生成（LMR座標自動計算）
        - 📈 美しいPlotlyグラフ
        
        **開始方法:**
        1. 左サイドバーからCSVファイルをアップロード
        2. またはサンプルデータを使用
        3. データ読み込みボタンをクリック
        """)

def display_main_content():
    """メインコンテンツ表示"""
    # タブ作成（データ拡張タブを追加）
    tab_names = ["📊 データ概要", "📏 データ拡張", "🔧 ノイズ除去"]
    
    if st.session_state.get('processed_data'):
        tab_names.append("✂️ データ加工")
    else:
        tab_names.append("✂️ データ加工 (要ノイズ除去)")
    
    # VTK生成タブのみ追加（測点管理とLMR座標計算は削除）
    tab_names.append("📦 VTK生成")
    
    tabs = st.tabs(tab_names)
    tab1, tab2, tab3 = tabs[0], tabs[1], tabs[2]
    tab4 = tabs[3] if len(tabs) > 3 else None
    tab5 = tabs[4] if len(tabs) > 4 else None
    
    with tab1:
        display_data_overview()
    
    with tab2:
        display_data_stretching()
    
    with tab3:
        display_noise_removal()
    
    with tab4:
        display_data_processing()
    
    with tab5:
        display_vtk_generation()

def display_data_overview():
    """データ概要タブ"""
    st.header("📊 データ概要")
    
    # データ選択（LMRの順番）
    selected_file = st.selectbox(
        "ファイルを選択",
        sort_files_lmr(st.session_state.raw_data.keys())
    )
    
    if selected_file:
        df = st.session_state.raw_data[selected_file]
        
        # 重要カラムの特定
        length_col = None
        if '穿孔長' in df.columns:
            length_col = '穿孔長'
        elif 'TD' in df.columns:
            length_col = 'TD'
        elif 'x:TD(m)' in df.columns:
            length_col = 'x:TD(m)'
        
        energy_col = None
        if '穿孔エネルギー' in df.columns:
            energy_col = '穿孔エネルギー'
        elif 'Ene-M' in df.columns:
            energy_col = 'Ene-M'
        
        # 基本統計（穿孔長と穿孔エネルギーのみ）
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("データ行数", f"{len(df):,}")
        with col2:
            if length_col:
                st.metric("最大穿孔長", f"{df[length_col].max():.1f} m")
            else:
                st.metric("穿孔長カラム", "未検出")
        with col3:
            if energy_col:
                st.metric("平均エネルギー", f"{df[energy_col].mean():.1f}")
            else:
                st.metric("エネルギーカラム", "未検出")
        with col4:
            if energy_col:
                st.metric("最大エネルギー", f"{df[energy_col].max():.1f}")
        
        # 必要なカラムのみ表示
        display_cols = []
        if length_col:
            display_cols.append(length_col)
        if energy_col:
            display_cols.append(energy_col)
        
        # その他の関連カラムも追加（座標関連は除外）
        for col in df.columns:
            if col not in display_cols and col not in ['X', 'Y', 'Z', 'X(m)', 'Y(m)', 'Z:標高(m)', 'z:SL差(m)']:
                if 'シーケンス' in col or '時' in col or '分' in col or '秒' in col:
                    continue  # タイムスタンプ関連も除外
                if len(display_cols) < 10:  # 最大10カラムまで表示
                    display_cols.append(col)
        
        # データプレビュー
        st.subheader("データプレビュー（穿孔長・穿孔エネルギー中心）")
        if display_cols:
            st.dataframe(
                df[display_cols].head(100),
                height=400
            )
        else:
            st.warning("表示可能なカラムがありません")
        
        # 統計情報（穿孔長と穿孔エネルギーのみ）
        if length_col or energy_col:
            with st.expander("📊 統計情報", expanded=False):
                stats_cols = []
                if length_col:
                    stats_cols.append(length_col)
                if energy_col:
                    stats_cols.append(energy_col)
                st.dataframe(df[stats_cols].describe())

def sort_files_lmr(file_list):
    """ファイルをL-M-Rの順番にソート"""
    def get_lmr_order(filename):
        if '_L_' in filename or filename.endswith('_L.csv'):
            return 0  # L files first
        elif '_M_' in filename or filename.endswith('_M.csv'):
            return 1  # M files second
        elif '_R_' in filename or filename.endswith('_R.csv'):
            return 2  # R files third
        else:
            return 3  # Other files last
    
    return sorted(file_list, key=lambda x: (get_lmr_order(x), x))

def display_data_stretching():
    """データ拡張（スケーリング）処理"""
    st.header("📏 データ拡張（スケーリング）")
    
    # データの存在確認
    if 'raw_data' not in st.session_state or not st.session_state.raw_data:
        st.warning("⚠️ データを読み込んでください")
        return
    
    # DataProcessorを使用してLMR分類
    processor = DataProcessor()
    base_data = processor.categorize_lmr_data(st.session_state.raw_data)
    
    # データストレッチャーのインポート
    from src.data_stretcher import DataStretcher
    stretcher = DataStretcher()
    
    # 使用するデータの選択
    data_source = st.radio(
        "使用するデータ",
        ["元のデータ", "拡張済みデータ（存在する場合）"],
        key="stretch_data_source"
    )
    
    # データソースの決定
    if data_source == "拡張済みデータ（存在する場合）" and 'stretched_data' in st.session_state:
        current_data = st.session_state.stretched_data
        st.info("📌 拡張済みデータを使用しています")
    else:
        current_data = base_data
        if data_source == "拡張済みデータ（存在する場合）":
            st.info("📌 拡張済みデータが存在しないため、元のデータを使用しています")
    
    # 現在のデータ情報を表示
    st.subheader("現在のデータ情報")
    current_info = []
    for key in ['L', 'M', 'R']:
        if key in current_data and current_data[key] is not None and not current_data[key].empty:
            info = stretcher.get_scale_info(current_data[key])
            current_info.append({
                'データ': f'{key}側',
                '最大長 (m)': f"{info['current_max_length']:.2f}",
                '最小長 (m)': f"{info['current_min_length']:.2f}",
                'データ点数': info['data_points']
            })
    
    if current_info:
        st.table(pd.DataFrame(current_info))
    
    # スケーリング設定
    st.subheader("スケーリング設定")
    
    # 処理対象のデータを選択
    st.write("**処理対象のデータを選択**")
    available_keys = []
    for key in ['L', 'M', 'R']:
        if key in current_data and current_data[key] is not None and not current_data[key].empty:
            available_keys.append(key)
    
    selected_keys = []
    cols = st.columns(len(available_keys))
    for idx, key in enumerate(available_keys):
        with cols[idx]:
            if st.checkbox(f"{key}側", value=True, key=f"select_{key}"):
                selected_keys.append(key)
    
    if not selected_keys:
        st.warning("⚠️ 少なくとも1つのデータを選択してください")
        return
    
    st.divider()
    
    # 目標長の設定方法を選択
    st.write("**目標長の設定**")
    
    # 一括設定モード
    unified_mode = st.checkbox("すべて同じ目標長にする", value=False, key="unified_stretch")
    
    target_lengths = {}
    
    if unified_mode:
        # 一括設定
        target_length_all = st.number_input(
            "共通の目標長さ (m)",
            min_value=1.0,
            max_value=100.0,
            value=50.0,
            step=0.5,
            key="target_length_all"
        )
        target_lengths = {key: target_length_all for key in selected_keys}
        
        # 設定内容の確認表示
        st.info(f"すべてのデータを {target_length_all:.1f}m に拡張します")
    else:
        # 個別設定
        st.write("**各データの目標長を個別に設定**")
        
        # 選択されたデータの数に応じてカラム数を調整
        cols = st.columns(len(selected_keys) if len(selected_keys) <= 3 else 3)
        
        for idx, key in enumerate(selected_keys):
            col_idx = idx % len(cols)
            with cols[col_idx]:
                if key in current_data and current_data[key] is not None and not current_data[key].empty:
                    current_max = current_data[key]['穿孔長'].max()
                    current_min = current_data[key]['穿孔長'].min()
                    
                    st.write(f"**{key}側**")
                    st.caption(f"現在: {current_min:.1f}〜{current_max:.1f}m")
                    
                    target_lengths[key] = st.number_input(
                        f"目標長さ (m)",
                        min_value=1.0,
                        max_value=100.0,
                        value=min(current_max * 1.5, 50.0),
                        step=0.5,
                        key=f"target_length_{key}",
                        label_visibility="collapsed"
                    )
                    
                    # 拡張率を表示
                    scale_factor = target_lengths[key] / current_max
                    if scale_factor > 1:
                        st.caption(f"↑ {scale_factor:.2f}倍に拡張")
                    elif scale_factor < 1:
                        st.caption(f"↓ {scale_factor:.2f}倍に縮小")
                    else:
                        st.caption("→ 変更なし")
    
    # スケーリング実行
    if st.button("🔄 スケーリング実行", type="primary", key="execute_stretching"):
        with st.spinner("スケーリング処理中..."):
            try:
                # 選択されたデータのみを処理
                selected_data = {key: current_data[key] for key in selected_keys if key in current_data}
                
                # スケーリング実行
                stretched_data = stretcher.stretch_multiple_data(selected_data, target_lengths)
                
                # 既存の拡張済みデータがある場合はマージ
                if 'stretched_data' in st.session_state:
                    # 既存データを保持し、新しい処理結果で更新
                    merged_data = st.session_state.stretched_data.copy()
                    merged_data.update(stretched_data)
                    st.session_state.stretched_data = merged_data
                else:
                    # 元データをコピーして、処理したデータのみ更新
                    st.session_state.stretched_data = base_data.copy()
                    st.session_state.stretched_data.update(stretched_data)
                
                st.session_state.stretch_applied = True
                
                # 成功メッセージ
                st.success(f"✅ 選択された{len(selected_keys)}個のデータのスケーリングが完了しました")
                
                # サマリー表示
                st.subheader("スケーリング結果")
                stretcher.display_scale_summary(selected_data, stretched_data)
                
                # グラフ表示
                st.subheader("スケーリング前後の比較")
                
                from src.plotly_visualizer import PlotlyVisualizer
                visualizer = PlotlyVisualizer()
                
                # 選択されたデータのみグラフ表示
                for key in selected_keys:
                    if key in selected_data and selected_data[key] is not None and not selected_data[key].empty:
                        if key in stretched_data and stretched_data[key] is not None:
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**{key}側 - 元のデータ**")
                                fig_original = visualizer.create_line_plot(
                                    current_data[key],
                                    title=f"{key}側 - 元のデータ",
                                    x_col='穿孔長',
                                    y_col='穿孔エネルギー',
                                    height=400
                                )
                                st.plotly_chart(fig_original, use_container_width=True)
                            
                            with col2:
                                st.write(f"**{key}側 - スケーリング後**")
                                fig_stretched = visualizer.create_line_plot(
                                    stretched_data[key],
                                    title=f"{key}側 - スケーリング後",
                                    x_col='穿孔長',
                                    y_col='穿孔エネルギー',
                                    height=400
                                )
                                st.plotly_chart(fig_stretched, use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ エラーが発生しました: {str(e)}")
                import traceback
                st.error(traceback.format_exc())
    
    # 拡張済みデータが存在する場合、リセットオプションを表示
    if 'stretched_data' in st.session_state:
        st.divider()
        st.subheader("リセットオプション")
        
        if st.button("🔄 すべての拡張データをリセット", key="reset_all"):
            del st.session_state.stretched_data
            if 'stretch_applied' in st.session_state:
                del st.session_state.stretch_applied
            st.success("✅ すべての拡張データをリセットしました")
            st.rerun()

def display_noise_removal():
    """ノイズ除去タブ（元スクリプトの機能を完全再現）"""
    st.header("🔧 ノイズ除去処理 - 穿孔エネルギー値")
    
    remover = NoiseRemover()
    
    # 一括処理ボタンを上部に配置
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔧 すべてのファイルを一括でノイズ除去", type="primary", key="process_all_files", use_container_width=True):
            with st.spinner("すべてのファイルを処理中..."):
                processed_count = 0
                # LMRの順番で処理
                for file_name in sort_files_lmr(st.session_state.raw_data.keys()):
                    df = st.session_state.raw_data[file_name]
                    if '穿孔エネルギー' in df.columns:
                        processed_df = remover.apply_lowess(
                            df,
                            target_column='穿孔エネルギー',
                            frac=st.session_state.lowess_frac,
                            it=st.session_state.lowess_it,
                            delta=st.session_state.lowess_delta
                        )
                        st.session_state.processed_data[file_name] = processed_df
                        st.session_state[f'processed_{file_name}'] = processed_df
                        processed_count += 1
                st.success(f"✅ {processed_count}個のファイルのノイズ除去が完了しました！")
                st.rerun()
    
    # 各ファイルのグラフをLMRの順番で表示
    for selected_file in sort_files_lmr(st.session_state.raw_data.keys()):
        df = st.session_state.raw_data[selected_file]
        
        # ファイル名をセクションタイトルとして表示
        st.divider()
        st.markdown(f"### 📄 {selected_file}")
        
        # 必須カラムのチェック
        if '穿孔エネルギー' not in df.columns:
            st.warning(f"⚠️ '{selected_file}' に '穿孔エネルギー' 列が見つかりません")
            st.info("データのカラム: " + ", ".join(df.columns))
            continue
        
        # X軸のカラムを特定
        x_col = '穿孔長' if '穿孔長' in df.columns else ('TD' if 'TD' in df.columns else None)
        
        # グラフ表示領域
        # 処理結果がある場合は処理前・処理後を重ねて表示
        if f'processed_{selected_file}' in st.session_state:
            processed_df = st.session_state[f'processed_{selected_file}']
            
            if 'Lowess_Trend' in processed_df.columns:
                # 処理前と処理後を重ねたグラフを作成
                fig = go.Figure()
                
                if x_col:
                    # X軸タイトルを設定
                    x_axis_title = '穿孔長(m)' if x_col == '穿孔長' else x_col
                    
                    # 処理前データ（青いライン）
                    fig.add_trace(go.Scatter(
                        x=df[x_col],
                        y=df['穿孔エネルギー'],
                        mode='lines',
                        name='処理前',
                        line=dict(color='blue', width=2),
                        opacity=0.7
                    ))
                    
                    # 処理後データ（赤いライン、上に表示）
                    fig.add_trace(go.Scatter(
                        x=processed_df[x_col],
                        y=processed_df['Lowess_Trend'],
                        mode='lines',
                        name='処理後',
                        line=dict(color='red', width=2)
                    ))
                    
                    # 共通のレイアウト設定を取得
                    layout = get_graph_layout_settings()
                    layout.update(dict(
                        title=f"ノイズ除去結果（{selected_file}） - 全{len(df)}行",
                        xaxis_title=x_axis_title,
                        yaxis_title='穿孔エネルギー',
                        hovermode='x unified',
                        height=600,
                        showlegend=True,
                        autosize=True,
                        margin=dict(l=80, r=80, t=100, b=80)
                    ))
                    fig.update_layout(layout)
                else:
                    # X軸がない場合はインデックスを使用
                    fig.add_trace(go.Scatter(
                        y=df['穿孔エネルギー'],
                        mode='lines',
                        name='処理前',
                        line=dict(color='blue', width=2),
                        opacity=0.7
                    ))
                    
                    fig.add_trace(go.Scatter(
                        y=processed_df['Lowess_Trend'],
                        mode='lines',
                        name='処理後',
                        line=dict(color='red', width=2)
                    ))
                    
                    # 共通のレイアウト設定を取得
                    layout = get_graph_layout_settings()
                    layout.update(dict(
                        title=f"ノイズ除去結果（{selected_file}） - 全{len(df)}行",
                        xaxis_title='データポイント',
                        yaxis_title='穿孔エネルギー',
                        hovermode='x unified',
                        height=600,
                        showlegend=True,
                        autosize=True,
                        margin=dict(l=80, r=80, t=100, b=80)
                    ))
                    fig.update_layout(layout)
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            # 処理前データのみ表示
            if x_col:
                # X軸タイトルを設定
                x_axis_title = '穿孔長(m)' if x_col == '穿孔長' else x_col
                
                fig = px.line(
                    df,
                    x=x_col,
                    y='穿孔エネルギー',
                    title=f"元データ（{selected_file}） - 全{len(df)}行"
                )
                fig.update_traces(line=dict(color='blue', width=2))
                # 共通のレイアウト設定を取得して適用
                layout = get_graph_layout_settings()
                layout.update(dict(
                    xaxis_title=x_axis_title,
                    height=600,
                    autosize=True,
                    margin=dict(l=80, r=80, t=100, b=80)
                ))
                fig.update_layout(layout)
            else:
                fig = px.line(
                    y=df['穿孔エネルギー'],
                    title=f"元データ（{selected_file}） - 全{len(df)}行"
                )
                fig.update_traces(line=dict(color='blue', width=2))
                # 共通のレイアウト設定を取得して適用
                layout = get_graph_layout_settings()
                layout.update(dict(
                    height=600,
                    autosize=True,
                    margin=dict(l=80, r=80, t=100, b=80)
                ))
                fig.update_layout(layout)
            
            st.plotly_chart(fig, use_container_width=True)
    
    # ファイル保存セクション（処理済みデータがある場合）
    if st.session_state.get('processed_data'):
        st.divider()
        st.subheader("📥 処理結果のダウンロード")
        
        # 結合ファイルを生成（複数ファイルの場合）
        if len(st.session_state.processed_data) > 1:
            with st.spinner("結合ファイルを生成中..."):
                # process_multiple_filesメソッドを使用して結合
                _, combined_data = remover.process_multiple_files(
                    st.session_state.processed_data,
                    frac=st.session_state.lowess_frac,
                    it=st.session_state.lowess_it,
                    delta=st.session_state.lowess_delta,
                    use_parallel=False  # 既に処理済みなので並列化不要
                )
                st.session_state.combined_data = combined_data
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**個別ファイル**")
            for name in sort_files_lmr(st.session_state.processed_data.keys()):
                data = st.session_state.processed_data[name]
                csv = data.to_csv(index=False, encoding='shift_jis')
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"{name.replace('.csv', '')}_ana_{timestamp}.csv"
                
                st.download_button(
                    label=f"⬇️ {file_name}",
                    data=csv.encode('shift_jis'),
                    file_name=file_name,
                    mime="text/csv",
                    key=f"download_batch_{name}"
                )
        
        with col2:
            if st.session_state.get('combined_data') is not None and not st.session_state.combined_data.empty:
                st.write("**統合ファイル**")
                csv = st.session_state.combined_data.to_csv(index=False, encoding='shift_jis')
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                combined_file_name = f"combined_data_{timestamp}.csv"
                
                st.download_button(
                    label=f"⬇️ {combined_file_name}",
                    data=csv.encode('shift_jis'),
                    file_name=combined_file_name,
                    mime="text/csv",
                    key="download_combined"
                )

def display_data_processing():
    """データ加工タブ（間引き・補間処理）"""
    st.header("✂️ データ加工 - 間引き・補間処理")
    
    processor = DataProcessor()
    
    # 処理対象データの確認
    if not st.session_state.get('processed_data'):
        st.info("ℹ️ データ加工を行うには、まず「ノイズ除去」タブでデータを処理してください")
        st.stop()
        return
    
    # 処理設定
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("📏 間引き設定")
        
        # 間隔設定
        interval = st.number_input(
            "サンプリング間隔 (m)",
            min_value=0.01,
            max_value=1.0,
            value=0.02,
            step=0.01,
            format="%.2f",
            help="データを間引く間隔を指定します。デフォルトは0.02m（2cm）刻みです。"
        )
        
        st.info(f"""
        **処理内容:**
        - {interval:.2f}m 刻みでデータを再サンプリング
        - 該当位置にデータがない場合は線形補間
        - ノイズ除去後のデータ（Lowess_Trend）を処理
        """)
        
        # 処理実行ボタン
        if st.button("🔧 データ間引き実行", type="primary", key="process_resample", use_container_width=True):
            with st.spinner("データを間引き処理中..."):
                resampled_data = {}
                error_files = []
                
                for filename in sort_files_lmr(st.session_state.processed_data.keys()):
                    df = st.session_state.processed_data[filename]
                    try:
                        # リサンプリング処理
                        resampled_df = processor.resample_data(
                            df,
                            interval=interval,
                            target_columns=None  # 自動選択
                        )
                        resampled_data[filename] = resampled_df
                    except Exception as e:
                        error_files.append((filename, str(e)))
                
                # セッションに保存
                if resampled_data:
                    st.session_state.resampled_data = resampled_data
                    st.success(f"✅ {len(resampled_data)}個のファイルの間引き処理が完了しました！")
                    
                    # エラーがあれば表示
                    if error_files:
                        with st.expander("⚠️ 処理できなかったファイル"):
                            for filename, error in error_files:
                                st.write(f"- {filename}: {error}")
                else:
                    st.error("データの間引き処理に失敗しました")
    
    st.divider()
    
    # 処理結果の表示
    if st.session_state.get('resampled_data'):
        st.subheader("📊 間引き処理結果")
        
        # ファイルごとの結果表示（LMRの順番）
        for filename in sort_files_lmr(st.session_state.resampled_data.keys()):
            df = st.session_state.resampled_data[filename]
            st.divider()
            st.markdown(f"### 📄 {filename}")
            
            # 統計情報
            col1, col2, col3, col4 = st.columns(4)
            
            # 深度カラムを特定
            depth_col = processor._find_depth_column(df)
            
            with col1:
                original_count = len(st.session_state.processed_data[filename])
                st.metric("元データ行数", f"{original_count:,}")
            
            with col2:
                resampled_count = len(df)
                st.metric("間引き後行数", f"{resampled_count:,}")
            
            with col3:
                reduction_rate = (1 - resampled_count / original_count) * 100
                st.metric("削減率", f"{reduction_rate:.1f}%")
            
            with col4:
                if depth_col and depth_col in df.columns:
                    depth_range = f"{df[depth_col].min():.2f} - {df[depth_col].max():.2f}"
                    st.metric("深度範囲 (m)", depth_range)
            
            # グラフ表示（処理前後の比較）
            if depth_col and 'Lowess_Trend' in df.columns:
                fig = go.Figure()
                
                # 元データ（処理済み）
                original_df = st.session_state.processed_data[filename]
                if depth_col in original_df.columns and 'Lowess_Trend' in original_df.columns:
                    fig.add_trace(go.Scatter(
                        x=original_df[depth_col],
                        y=original_df['Lowess_Trend'],
                        mode='lines',
                        name='ノイズ除去後',
                        line=dict(color='blue', width=1),
                        opacity=0.5
                    ))
                
                # 間引き後データ
                fig.add_trace(go.Scatter(
                    x=df[depth_col],
                    y=df['Lowess_Trend'],
                    mode='markers+lines',
                    name=f'間引き後 ({interval:.2f}m刻み)',
                    line=dict(color='red', width=2),
                    marker=dict(size=3, color='red')
                ))
                
                # X軸タイトルを設定
                x_axis_title = '穿孔長(m)' if depth_col == '穿孔長' else depth_col
                
                # 共通のレイアウト設定を取得
                layout = get_graph_layout_settings()
                layout.update(dict(
                    title=f"間引き処理結果（{filename}）",
                    xaxis_title=x_axis_title,
                    yaxis_title='穿孔エネルギー',
                    hovermode='x unified',
                    height=500,
                    showlegend=True
                ))
                fig.update_layout(layout)
                
                st.plotly_chart(fig, use_container_width=True)
            
            # データプレビュー
            with st.expander("📋 データプレビュー（最初の50行）"):
                display_cols = [col for col in df.columns if col in [depth_col, 'Lowess_Trend', '穿孔エネルギー']]
                if display_cols:
                    st.dataframe(df[display_cols].head(50), height=300)
        
        # ダウンロードセクション
        st.divider()
        st.subheader("📥 間引きデータのダウンロード")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**個別ファイル**")
            for filename in sort_files_lmr(st.session_state.resampled_data.keys()):
                df = st.session_state.resampled_data[filename]
                csv = df.to_csv(index=False, encoding='shift_jis')
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                interval_str = f"{int(interval*100):02d}cm"  # 0.02 -> 02cm
                file_name = f"{filename.replace('.csv', '')}_resampled_{interval_str}_{timestamp}.csv"
                
                st.download_button(
                    label=f"⬇️ {file_name}",
                    data=csv.encode('shift_jis'),
                    file_name=file_name,
                    mime="text/csv",
                    key=f"download_resampled_{filename}"
                )
        
        with col2:
            # 全ファイルを結合したデータ（ノイズ除去と同じ横結合形式）
            if len(st.session_state.resampled_data) > 1:
                st.write("**結合ファイル**")
                
                # 横結合処理（ノイズ除去と同じ形式）
                combined_df = pd.DataFrame()
                
                for filename in sort_files_lmr(st.session_state.resampled_data.keys()):
                    df = st.session_state.resampled_data[filename]
                    # 深度カラムを特定
                    depth_col = processor._find_depth_column(df)
                    
                    # 必要なカラムのみ抽出
                    required_cols = []
                    if depth_col:
                        required_cols.append(depth_col)
                    if 'Lowess_Trend' in df.columns:
                        required_cols.append('Lowess_Trend')
                    if '穿孔エネルギー' in df.columns:
                        required_cols.append('穿孔エネルギー')
                    
                    if required_cols:
                        extracted_data = df[required_cols].copy()
                        
                        # カラム名にファイル名を付与
                        base_name = filename.replace('.csv', '')
                        extracted_data.columns = [f'{base_name}_{col}' for col in extracted_data.columns]
                        
                        # 横方向に結合
                        if combined_df.empty:
                            combined_df = extracted_data
                        else:
                            combined_df = pd.concat([combined_df, extracted_data], axis=1)
                
                csv = combined_df.to_csv(index=False, encoding='shift_jis')
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                interval_str = f"{int(interval*100):02d}cm"
                combined_file_name = f"combined_resampled_{interval_str}_{timestamp}.csv"
                
                st.download_button(
                    label=f"⬇️ {combined_file_name}",
                    data=csv.encode('shift_jis'),
                    file_name=combined_file_name,
                    mime="text/csv",
                    key="download_combined_resampled"
                )

def display_vtk_generation():
    """VTK生成タブ（LMR座標計算統合版）"""
    st.header("📦 VTKファイル生成（削孔検層データ）")
    
    # VTK converter初期化
    if 'vtk_converter' not in st.session_state:
        st.session_state.vtk_converter = VTKConverter()
    
    converter = st.session_state.vtk_converter
    
    # 測点計算機の初期化
    from src.survey_point_calculator import SurveyPointCalculator
    survey_calc = SurveyPointCalculator()
    
    # VTKライブラリの確認
    try:
        import vtk
        vtk_available = True
    except ImportError:
        vtk_available = False
        st.warning("⚠️ VTKライブラリがインストールされていません。VTKファイル生成機能が制限されます。")
        st.info("インストール方法: `pip install vtk`")
    
    # ファイル選択エリア
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📄 ファイル選択")
        
        # 処理済みデータがある場合はそれを優先
        if st.session_state.get('processed_data'):
            st.info("✅ ノイズ除去済みデータを使用します")
            available_files = sort_files_lmr(st.session_state.processed_data.keys())
            data_source = st.session_state.processed_data
        else:
            st.info("ℹ️ 生データを使用します（ノイズ除去推奨）")
            available_files = sort_files_lmr(st.session_state.raw_data.keys())
            data_source = st.session_state.raw_data
        
        selected_files = st.multiselect(
            "VTK化するファイルを選択",
            available_files,
            key="vtk_file_select_new",
            help="L, M, Rのファイルを選択してください"
        )
        
        # LMRタイプの自動検出結果表示
        if selected_files:
            detected_types = []
            for file in selected_files:
                lmr_type = converter.detect_lmr_type(file)
                if lmr_type:
                    detected_types.append(f"{file} → **{lmr_type}側**")
                else:
                    detected_types.append(f"{file} → ❌ タイプ検出失敗")
            
            with st.expander("🔍 LMRタイプ検出結果"):
                for detection in detected_types:
                    st.write(detection)
    
    with col2:
        st.subheader("⚙️ 座標設定")
        
        # 距離入力方法の選択
        distance_input_method = st.radio(
            "距離の入力方法",
            ["直接入力", "測点から計算"],
            help="坑口からの距離を入力する方法を選択"
        )
        
        if distance_input_method == "直接入力":
            # 坑口からの距離入力
            distance_from_entrance = st.number_input(
                "トンネル坑口からの距離 (m)",
                min_value=0.0,
                value=1000.0,
                step=1.0,
                help="測点のトンネル坑口からの距離を入力"
            )
        else:
            # 測点から計算
            st.write("**測点入力（例: 250+11）**")
            survey_point_str = st.text_input(
                "測点",
                value="250+11",
                help="測点を 主番号+小数部 の形式で入力"
            )
            
            try:
                c_value, e_value = survey_calc.parse_survey_point(survey_point_str)
                distance_from_entrance = survey_calc.calculate_distance_from_entrance(c_value, e_value)
                st.success(f"計算された距離: **{distance_from_entrance:.1f}m**")
                
                # 計算詳細
                with st.expander("📊 計算詳細"):
                    st.write(f"測点: {survey_calc.format_survey_point(c_value, e_value)}")
                    st.write(f"測点数値: {c_value}×20 + {e_value} = {survey_calc.calculate_survey_point_value(c_value, e_value)}")
                    st.write(f"基準測点: 255+4 (= {survey_calc.reference_value})")
                    st.write(f"坑口からの距離: {survey_calc.reference_value} - {survey_calc.calculate_survey_point_value(c_value, e_value)} = {distance_from_entrance:.1f}m")
            except ValueError as e:
                st.error(f"測点の形式が不正です: {e}")
                distance_from_entrance = 0.0
        
        # 固定値の表示
        with st.expander("📐 使用される固定値", expanded=False):
            st.write("**座標計算パラメータ:**")
            st.write(f"- 基準距離: 967m")
            st.write(f"- 方向角度: 65.588°")
            st.write("**Z標高:**")
            st.write("- L側: 17.3m")
            st.write("- M側（天端）: 21.3m")
            st.write("- R側: 17.3m")
        
        # サンプリング設定
        sampling_interval = st.number_input(
            "サンプリング間隔",
            min_value=1,
            max_value=100,
            value=10,
            help="データ点を間引く間隔（行数）"
        )
    
    st.divider()
    
    # 処理実行エリア
    if selected_files and distance_from_entrance > 0:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🚀 VTKファイル生成", type="primary", use_container_width=True):
                with st.spinner("VTKファイルを生成中..."):
                    success_files = []
                    error_files = []
                    generated_files = {}
                    
                    for file_name in selected_files:
                        try:
                            # LMRタイプの検出
                            lmr_type = converter.detect_lmr_type(file_name)
                            if not lmr_type:
                                error_files.append((file_name, "L/M/Rタイプを検出できません"))
                                continue
                            
                            # データの取得
                            df = data_source[file_name]
                            
                            # CSVファイルを一時保存（VTKConverterが読み込むため）
                            import tempfile
                            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='shift-jis') as tmp:
                                df.to_csv(tmp, index=False)
                                temp_csv_path = tmp.name
                            
                            # VTK変換実行
                            output_vtk_name = converter.generate_vtk_filename(file_name)
                            output_vtk_path = f"output/{output_vtk_name}"
                            output_csv_path = f"output/{file_name.replace('.csv', '_3d.csv')}"
                            
                            # outputフォルダ作成
                            Path("output").mkdir(exist_ok=True)
                            
                            # 変換実行
                            vtk_path, csv_path = converter.convert_csv_to_vtk(
                                csv_file=temp_csv_path,
                                distance_from_entrance=distance_from_entrance,
                                output_vtk_path=output_vtk_path,
                                output_csv_path=output_csv_path,
                                lmr_type=lmr_type
                            )
                            
                            # 一時ファイル削除
                            Path(temp_csv_path).unlink()
                            
                            # 成功リストに追加
                            success_files.append(file_name)
                            generated_files[file_name] = {
                                'vtk': vtk_path,
                                'csv': csv_path,
                                'lmr_type': lmr_type
                            }
                            
                        except Exception as e:
                            error_files.append((file_name, str(e)))
                    
                    # 結果表示
                    if success_files:
                        st.success(f"✅ {len(success_files)}個のVTKファイルを生成しました")
                        st.session_state.generated_vtk_files = generated_files
                        
                        # 生成ファイル情報
                        with st.expander("📁 生成されたファイル"):
                            for file_name, info in generated_files.items():
                                st.write(f"**{file_name}**")
                                st.write(f"- LMRタイプ: {info['lmr_type']}側")
                                st.write(f"- VTK: {info['vtk']}")
                                st.write(f"- CSV: {info['csv']}")
                    
                    if error_files:
                        with st.expander("❌ エラーが発生したファイル"):
                            for file_name, error in error_files:
                                st.write(f"- {file_name}: {error}")
        
        # ダウンロードセクション
        if st.session_state.get('generated_vtk_files'):
            st.divider()
            st.subheader("📥 ダウンロード")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**VTKファイル**")
                for file_name, info in st.session_state.generated_vtk_files.items():
                    vtk_path = info['vtk']
                    if Path(vtk_path).exists():
                        with open(vtk_path, 'rb') as f:
                            vtk_content = f.read()
                        
                        st.download_button(
                            label=f"⬇️ {Path(vtk_path).name}",
                            data=vtk_content,
                            file_name=Path(vtk_path).name,
                            mime="application/vtk",
                            key=f"download_vtk_{file_name}"
                        )
            
            with col2:
                st.write("**3D座標CSV**")
                for file_name, info in st.session_state.generated_vtk_files.items():
                    csv_path = info['csv']
                    if Path(csv_path).exists():
                        with open(csv_path, 'r', encoding='shift-jis') as f:
                            csv_content = f.read()
                        
                        st.download_button(
                            label=f"⬇️ {Path(csv_path).name}",
                            data=csv_content.encode('shift-jis'),
                            file_name=Path(csv_path).name,
                            mime="text/csv",
                            key=f"download_csv_{file_name}"
                        )
        
        # 3Dプレビュー（座標のみ）
        if st.checkbox("📊 3D座標プレビュー"):
            if st.session_state.get('generated_vtk_files'):
                fig = go.Figure()
                
                for file_name, info in st.session_state.generated_vtk_files.items():
                    csv_path = info['csv']
                    if Path(csv_path).exists():
                        # CSVから座標を読み込む
                        preview_df = pd.read_csv(csv_path, encoding='shift-jis', skiprows=1)
                        if all(col in preview_df.columns for col in ['X(m)', 'Y(m)', 'Z:標高(m)']):
                            fig.add_trace(go.Scatter3d(
                                x=preview_df['X(m)'],
                                y=preview_df['Y(m)'],
                                z=preview_df['Z:標高(m)'],
                                mode='lines+markers',
                                name=f"{info['lmr_type']}側",
                                marker=dict(size=2),
                                line=dict(width=3)
                            ))
                
                fig.update_layout(
                    scene=dict(
                        xaxis_title='X (m)',
                        yaxis_title='Y (m)',
                        zaxis_title='Z:標高 (m)',
                        aspectmode='data'
                    ),
                    height=600,
                    title=f"削孔検層3D軌跡（坑口から{distance_from_entrance}m）"
                )
                st.plotly_chart(fig, use_container_width=True)
    elif selected_files and distance_from_entrance <= 0:
        st.warning("⚠️ 有効な距離を入力してください")
    else:
        st.info("👆 VTK化するファイルを選択してください")
if __name__ == "__main__":
    main()