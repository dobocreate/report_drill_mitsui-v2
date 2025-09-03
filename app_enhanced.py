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
    """VTKファイル生成と可視化"""
    st.header("📦 VTKファイル生成と可視化")
    
    # データ確認
    if 'raw_data' not in st.session_state or not st.session_state.raw_data:
        st.warning("⚠️ データを読み込んでください")
        return
    
    # DataProcessorを使用してLMR分類
    processor = DataProcessor()
    base_data = processor.categorize_lmr_data(st.session_state.raw_data)
    
    # データソースの選択
    data_source = st.radio(
        "使用するデータ",
        ["元のデータ", "拡張済みデータ（存在する場合）", "ノイズ除去済みデータ（存在する場合）"],
        key="vtk_data_source"
    )
    
    # データソースの決定
    if data_source == "拡張済みデータ（存在する場合）" and 'stretched_data' in st.session_state:
        current_data = st.session_state.stretched_data
        st.info("📌 拡張済みデータを使用しています")
    elif data_source == "ノイズ除去済みデータ（存在する場合）" and st.session_state.get('processed_data'):
        # ノイズ除去済みデータがある場合
        current_data = {}
        for name, df in st.session_state.processed_data.items():
            # L, M, Rに対応するキーを抽出
            if 'L_processed' in name:
                current_data['L'] = df
            elif 'M_processed' in name:
                current_data['M'] = df
            elif 'R_processed' in name:
                current_data['R'] = df
        if not current_data:
            current_data = base_data
            st.info("📌 ノイズ除去済みデータが見つからないため、元のデータを使用しています")
        else:
            st.info("📌 ノイズ除去済みデータを使用しています")
    else:
        current_data = base_data
        if data_source != "元のデータ":
            st.info("📌 指定されたデータが存在しないため、元のデータを使用しています")
    
    # VTK生成オプション
    st.subheader("🔧 VTK生成設定")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        point_size = st.slider("ポイントサイズ", 1, 20, 5)
        line_width = st.slider("ライン幅", 1, 10, 2)
    
    with col2:
        color_mode = st.selectbox(
            "カラーモード",
            ["エネルギー値", "深度", "単色"],
            index=0
        )
        
        color_map = st.selectbox(
            "カラーマップ",
            ["viridis", "plasma", "inferno", "magma", "cividis", "turbo", "rainbow"],
            index=0
        )
    
    with col3:
        show_points = st.checkbox("ポイント表示", value=True)
        show_lines = st.checkbox("ライン表示", value=True)
        show_scalars = st.checkbox("スカラー値表示", value=True)
    
    # 可視化タブの追加
    viz_tab1, viz_tab2, viz_tab3 = st.tabs(["📊 プレビュー", "💾 VTK生成", "🎨 高度な可視化"])
    
    with viz_tab1:
        st.subheader("3Dプレビュー")
        
        # matplotlib による簡易プレビュー
        if st.button("🔄 プレビューを生成", key="generate_preview"):
            with st.spinner("プレビュー生成中..."):
                try:
                    from src.vtk_simple_renderer import VTKSimpleRenderer
                    import matplotlib.pyplot as plt
                    import tempfile
                    
                    # 一時的なVTKファイルを生成
                    generator = VTKGenerator()
                    converter = VTKConverter()
                    
                    # データの統合
                    combined_df = pd.DataFrame()
                    for key in ['L', 'M', 'R']:
                        if key in current_data and current_data[key] is not None:
                            df = current_data[key].copy()
                            # プレフィックスを追加
                            df['データ種別'] = key
                            combined_df = pd.concat([combined_df, df], ignore_index=True)
                    
                    if not combined_df.empty:
                        # VTKデータ作成
                        with tempfile.NamedTemporaryFile(suffix='.vtk', delete=False) as tmp_file:
                            vtk_path = tmp_file.name
                            
                            # 座標データの準備
                            if 'X' in combined_df.columns and 'Y' in combined_df.columns and 'Z' in combined_df.columns:
                                points = combined_df[['X', 'Y', 'Z']].values
                            else:
                                # 座標計算が必要な場合
                                st.warning("座標データが不足しています。デフォルトの座標を使用します。")
                                points = np.column_stack([
                                    np.zeros(len(combined_df)),
                                    np.zeros(len(combined_df)),
                                    -combined_df['穿孔長'].values if '穿孔長' in combined_df.columns else np.arange(len(combined_df))
                                ])
                            
                            # エネルギー値の取得
                            scalars = None
                            if color_mode == "エネルギー値" and '穿孔エネルギー' in combined_df.columns:
                                scalars = combined_df['穿孔エネルギー'].values
                            elif color_mode == "深度" and '穿孔長' in combined_df.columns:
                                scalars = combined_df['穿孔長'].values
                            
                            # VTKファイル生成
                            converter.create_vtk_polydata(
                                points=points,
                                scalars=scalars,
                                scalar_name='Energy' if color_mode == "エネルギー値" else 'Depth',
                                output_path=vtk_path
                            )
                            
                            # レンダリング
                            renderer = VTKSimpleRenderer()
                            if renderer.parse_vtk_file(vtk_path):
                                fig = renderer.render_to_figure(
                                    title="削孔軌跡 3D プレビュー",
                                    colormap=color_map,
                                    show_colorbar=show_scalars
                                )
                                st.pyplot(fig)
                                
                                # データサマリー表示
                                summary = renderer.get_data_summary()
                                with st.expander("📊 データサマリー"):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.metric("ポイント数", summary['num_points'])
                                        st.metric("ライン数", summary['num_lines'])
                                    with col2:
                                        if summary['bounds']:
                                            st.write("**座標範囲:**")
                                            st.write(f"X: {summary['bounds']['x_min']:.2f} ~ {summary['bounds']['x_max']:.2f}")
                                            st.write(f"Y: {summary['bounds']['y_min']:.2f} ~ {summary['bounds']['y_max']:.2f}")
                                            st.write(f"Z: {summary['bounds']['z_min']:.2f} ~ {summary['bounds']['z_max']:.2f}")
                            else:
                                st.error("VTKファイルの解析に失敗しました")
                            
                            # 一時ファイルを削除
                            import os
                            os.unlink(vtk_path)
                            
                    else:
                        st.warning("表示するデータがありません")
                        
                except Exception as e:
                    st.error(f"プレビュー生成エラー: {str(e)}")
                    import traceback
                    st.error(traceback.format_exc())
    
    with viz_tab2:
        st.subheader("VTKファイル生成")
        
        # VTK生成
        if st.button("🎯 VTKファイル生成", type="primary", key="generate_vtk"):
            with st.spinner("VTKファイル生成中..."):
                try:
                    generator = VTKGenerator()
                    converter = VTKConverter()
                    
                    generated_files = []
                    
                    # 各データ（L/M/R）ごとにVTKファイル生成
                    for key in ['L', 'M', 'R']:
                        if key in current_data and current_data[key] is not None:
                            df = current_data[key]
                            
                            # 座標データの準備
                            if 'X' in df.columns and 'Y' in df.columns and 'Z' in df.columns:
                                points = df[['X', 'Y', 'Z']].values
                            else:
                                # デフォルト座標
                                points = np.column_stack([
                                    np.zeros(len(df)),
                                    np.zeros(len(df)),
                                    -df['穿孔長'].values if '穿孔長' in df.columns else np.arange(len(df))
                                ])
                            
                            # スカラーデータ
                            scalars = None
                            scalar_name = 'Value'
                            
                            if color_mode == "エネルギー値":
                                if 'Lowess_Trend' in df.columns:
                                    scalars = df['Lowess_Trend'].values
                                    scalar_name = 'Energy_Smoothed'
                                elif '穿孔エネルギー' in df.columns:
                                    scalars = df['穿孔エネルギー'].values
                                    scalar_name = 'Energy'
                            elif color_mode == "深度" and '穿孔長' in df.columns:
                                scalars = df['穿孔長'].values
                                scalar_name = 'Depth'
                            
                            # VTKファイル生成
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            vtk_filename = f"trajectory_{key}_{timestamp}.vtk"
                            
                            vtk_content = converter.create_vtk_polydata(
                                points=points,
                                scalars=scalars,
                                scalar_name=scalar_name,
                                output_path=None  # メモリ上で生成
                            )
                            
                            if vtk_content:
                                generated_files.append((vtk_filename, vtk_content, key))
                    
                    # ダウンロードセクション
                    if generated_files:
                        st.success(f"✅ {len(generated_files)}個のVTKファイルを生成しました")
                        
                        st.subheader("📥 ダウンロード")
                        
                        for filename, content, key in generated_files:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.download_button(
                                    label=f"⬇️ {filename}",
                                    data=content,
                                    file_name=filename,
                                    mime="application/octet-stream",
                                    key=f"download_vtk_{key}_{timestamp}"
                                )
                            with col2:
                                st.write(f"{key}側データ")
                        
                        # 統合VTKファイルも生成
                        if len(generated_files) > 1:
                            st.divider()
                            if st.button("🔗 統合VTKファイル生成", key="generate_combined_vtk"):
                                # すべてのデータを統合
                                combined_df = pd.DataFrame()
                                for key in ['L', 'M', 'R']:
                                    if key in current_data and current_data[key] is not None:
                                        df = current_data[key].copy()
                                        df['データ種別'] = key
                                        combined_df = pd.concat([combined_df, df], ignore_index=True)
                                
                                # 統合VTK生成
                                if 'X' in combined_df.columns and 'Y' in combined_df.columns and 'Z' in combined_df.columns:
                                    points = combined_df[['X', 'Y', 'Z']].values
                                else:
                                    points = np.column_stack([
                                        np.zeros(len(combined_df)),
                                        np.zeros(len(combined_df)),
                                        -combined_df['穿孔長'].values if '穿孔長' in combined_df.columns else np.arange(len(combined_df))
                                    ])
                                
                                scalars = None
                                if color_mode == "エネルギー値" and '穿孔エネルギー' in combined_df.columns:
                                    scalars = combined_df['穿孔エネルギー'].values
                                elif color_mode == "深度" and '穿孔長' in combined_df.columns:
                                    scalars = combined_df['穿孔長'].values
                                
                                combined_vtk = converter.create_vtk_polydata(
                                    points=points,
                                    scalars=scalars,
                                    scalar_name='Combined_Data',
                                    output_path=None
                                )
                                
                                combined_filename = f"trajectory_combined_{timestamp}.vtk"
                                st.download_button(
                                    label=f"⬇️ {combined_filename} (統合データ)",
                                    data=combined_vtk,
                                    file_name=combined_filename,
                                    mime="application/octet-stream",
                                    key=f"download_vtk_combined_{timestamp}"
                                )
                    else:
                        st.warning("生成可能なデータがありません")
                        
                except Exception as e:
                    st.error(f"エラー: {str(e)}")
                    import traceback
                    st.error(traceback.format_exc())
    
    with viz_tab3:
        st.subheader("🎨 高度な可視化オプション")
        
        st.info("ParaViewやVTKを使用した高度な可視化機能")
        
        # レンダラー選択
        renderer_type = st.selectbox(
            "レンダラータイプ",
            ["Simple (matplotlib)", "VTK (要インストール)", "ParaView (要インストール)"],
            index=0,
            help="WSL環境では'Simple'を推奨"
        )
        
        if renderer_type == "VTK (要インストール)":
            st.warning("""
            ⚠️ VTKレンダラーの使用には以下が必要です：
            - VTKライブラリのインストール (`pip install vtk`)
            - X11サーバー（WSLの場合）
            - OpenGL対応
            """)
            
            if st.button("VTKレンダラーでプレビュー", key="vtk_preview"):
                st.info("VTKレンダラーは環境依存のため、エラーが発生する可能性があります")
                
        elif renderer_type == "ParaView (要インストール)":
            st.warning("""
            ⚠️ ParaViewレンダラーの使用には以下が必要です：
            - ParaViewのインストール
            - pvpythonへのパス設定
            """)
            
            paraview_path = st.text_input(
                "ParaViewインストールパス",
                placeholder="/usr/local/bin/paraview",
                help="ParaViewのインストールディレクトリを指定"
            )
            
            if st.button("ParaViewでレンダリング", key="paraview_preview"):
                if paraview_path:
                    st.info("ParaViewレンダリング機能は実装準備中です")
                else:
                    st.error("ParaViewのパスを指定してください")
        
        # エクスポートオプション
        st.divider()
        st.subheader("📤 エクスポートオプション")
        
        export_format = st.selectbox(
            "エクスポート形式",
            ["VTK", "PLY", "STL", "OBJ"],
            index=0
        )
        
        if export_format != "VTK":
            st.info(f"{export_format}形式へのエクスポート機能は実装準備中です")

if __name__ == "__main__":
    main()