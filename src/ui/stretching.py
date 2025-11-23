"""
データ拡張（スケーリング）モジュール
"""
import streamlit as st
import pandas as pd
from src.state import AppState
from src.data_processor import DataProcessor
from src.data_stretcher import DataStretcher
from src.plotly_visualizer import PlotlyVisualizer
from src.ui.styles import COLORS, card_container

def display_data_stretching():
    """データ拡張（スケーリング）処理"""
    # タイトルはapp.pyで表示されるため削除
    
    raw_data = AppState.get_raw_data()
    
    # データの存在確認
    if not raw_data:
        st.warning("⚠️ データを読み込んでください")
        return
    
    # DataProcessorを使用してLMR分類
    processor = DataProcessor()
    stretcher = DataStretcher()
    
    # 元データをLMR分類
    base_data = processor.categorize_lmr_data(raw_data)
    
    # 抽出データがあるか確認（_extracted または _stretched を含むキーを探す）
    extracted_data_keys = [key for key in raw_data.keys() if '_extracted' in key.lower() or '_stretched' in key.lower()]
    
    # 拡張済みデータがあるか確認
    stretched_data_state = AppState.get_stretched_data()
    has_stretched_data = bool(stretched_data_state)
    
    # L/M/Rごとにデータソースを選択
    with card_container():
        st.subheader("📊 データソースの選択")
        st.write("各データタイプごとに使用するデータソースを選択してください：")
        
        # 選択されたデータを格納する辞書
        current_data = {}
        selected_sources_info = {}  # 選択情報を保存
        target_lengths = {} # 目標長さを保存
        depth_cols = {} # 深度カラム名を保存
        
        # L/M/Rそれぞれの選択UI
        cols = st.columns(3)
        
        for idx, key in enumerate(['L', 'M', 'R']):
            with cols[idx]:
                st.markdown(f"**{key}側データ**")
                
                # そのデータタイプが存在するかチェック
                has_base = key in base_data and base_data[key] is not None and not base_data[key].empty
                has_stretched = has_stretched_data and key in stretched_data_state and \
                               stretched_data_state[key] is not None and \
                               not stretched_data_state[key].empty
                
                # 抽出データで該当するLMRタイプを探す
                available_extracted = []
                for ext_key in extracted_data_keys:
                    # 抽出データをLMR分類
                    temp_dict = {ext_key: raw_data[ext_key]}
                    temp_categorized = processor.categorize_lmr_data(temp_dict)
                    if key in temp_categorized and temp_categorized[key] is not None and not temp_categorized[key].empty:
                        available_extracted.append(ext_key)
                
                if not has_base and not has_stretched and not available_extracted:
                    st.warning(f"データなし")
                    current_data[key] = None
                else:
                    # 選択オプションを動的に作成
                    options = ["データ拡張を行わない"] # デフォルトオプション
                    if has_base:
                        options.append("元のデータ")
                    if available_extracted:
                        for ext_key in available_extracted:
                            options.append(f"抽出: {ext_key}")
                    if has_stretched:
                        options.append("拡張済みデータ")
                    
                    # デフォルト値は拡張済みがあれば拡張済み、なければ元のデータ
                    if has_stretched:
                        default_option = "拡張済みデータ"
                    elif has_base:
                        default_option = "元のデータ"
                    else:
                        default_option = options[1] if len(options) > 1 else options[0]
                    
                    # データソース選択
                    if len(options) > 1: # データがある場合のみ選択可能
                        data_source = st.selectbox(
                            "データソース",
                            options,
                            index=options.index(default_option) if default_option in options else 0,
                            key=f"stretch_source_{key}",
                            label_visibility="collapsed"
                        )
                        
                        if data_source == "データ拡張を行わない":
                            current_data[key] = None
                            st.caption("📌 拡張なし")
                        else:
                            # 選択に基づいてデータを設定
                            if data_source == "拡張済みデータ":
                                current_data[key] = stretched_data_state[key]
                                st.caption("📌 拡張済み")
                                selected_sources_info[key] = "拡張済み"
                            elif data_source == "元のデータ":
                                current_data[key] = base_data[key]
                                st.caption("📌 元データ")
                                selected_sources_info[key] = "元データ"
                            elif data_source.startswith("抽出:"):
                                # 抽出データの場合
                                ext_key = data_source.replace("抽出: ", "")
                                extracted_df = raw_data[ext_key].copy()
                                
                                # 深度カラムを特定
                                depth_col = processor._find_depth_column(extracted_df)
                                
                                # 抽出データの元の範囲を保存
                                original_min = None
                                original_max = None
                                if depth_col:
                                    original_min = extracted_df[depth_col].min()
                                    original_max = extracted_df[depth_col].max()
                                    
                                    # 穿孔長を0基準に調整（最小値を0にシフト）
                                    extracted_df[depth_col] = extracted_df[depth_col] - original_min
                                    
                                    length = original_max - original_min
                                    st.caption(f"📌 抽出: {original_min:.2f}-{original_max:.2f}m (長さ: {length:.2f}m)")
                                else:
                                    st.caption(f"📌 抽出データ")
                                
                                # 調整後のデータをLMR分類
                                temp_dict = {ext_key: extracted_df}
                                temp_categorized = processor.categorize_lmr_data(temp_dict)
                                current_data[key] = temp_categorized[key] if key in temp_categorized else None
                                selected_sources_info[key] = f"抽出({ext_key})"
                            
                            # 目標長さの入力
                            if current_data[key] is not None:
                                depth_col = processor._find_depth_column(current_data[key])
                                if depth_col:
                                    depth_cols[key] = depth_col # 深度カラム名を保存
                                    current_max = float(current_data[key][depth_col].max())
                                    
                                    # データソースによってキーを一意にする（ウィジェットの状態更新のため）
                                    # data_source文字列にはファイル名などが含まれるため、これをキーの一部にする
                                    widget_key = f"target_len_{key}_{hash(data_source)}"
                                    
                                    target_lengths[key] = st.number_input(
                                        f"目標長さ (m)",
                                        min_value=0.1, # 0.1m以上
                                        max_value=500.0, # 上限を広げる
                                        value=current_max, # 初期値を現在の長さに設定
                                        step=0.5,
                                        key=widget_key
                                    )
                                    # 拡張率表示
                                    scale = target_lengths[key] / current_max if current_max > 0 else 1.0
                                    st.caption(f"現在: {current_max:.1f}m → {scale:.2f}倍")

    
    # 選択情報のサマリーを表示
    if selected_sources_info:
        st.info("⚡ **選択されたデータソース:** " + " | ".join([f"{key}側: {source}" for key, source in selected_sources_info.items()]))
    
    # スケーリング実行
    if st.button("🔄 スケーリング実行", type="primary", key="execute_stretching", use_container_width=True):
        with st.spinner("スケーリング処理中..."):
            try:
                # 選択されたデータのみを処理
                selected_keys = [k for k, v in current_data.items() if v is not None]
                
                if not selected_keys:
                    st.warning("処理対象のデータが選択されていません。")
                else:
                    selected_data = {key: current_data[key] for key in selected_keys}
                    
                    # スケーリング実行 (depth_colsを渡す)
                    stretched_data = stretcher.stretch_multiple_data(selected_data, target_lengths, depth_cols=depth_cols)
                    
                    # 既存の拡張済みデータがある場合はマージ
                    merged_data = stretched_data_state.copy()
                    merged_data.update(stretched_data)
                    AppState.set_stretched_data(merged_data)
                    
                    # 拡張データをraw_dataにも保存
                    for key, df in stretched_data.items():
                        if df is not None:
                            save_name = f"stretched_{key}"
                            raw_data[save_name] = df.copy()
                    AppState.set_raw_data(raw_data)
                    
                    st.session_state.stretch_applied = True
                    
                    st.success(f"✅ 選択された{len(selected_keys)}個のデータのスケーリングが完了しました")
                    st.info("ℹ️ 拡張されたデータは新しいデータソースとして保存されました。")
                    
                    # グラフ表示
                    with card_container():
                        # サブタイトル削除
                        # st.subheader("スケーリング前後の比較")
                        
                        visualizer = PlotlyVisualizer()
                        
                        # 選択されたデータのみグラフ表示
                        for key in selected_keys:
                            if key in selected_data and selected_data[key] is not None and not selected_data[key].empty:
                                if key in stretched_data and stretched_data[key] is not None:
                                    col1, col2 = st.columns(2)
                                    
                                    depth_col = depth_cols.get(key)
                                    
                                    with col1:
                                        if depth_col:
                                            fig_original = visualizer.create_line_plot(
                                                current_data[key],
                                                title=f"{key}側 - 元のデータ",
                                                x_col=depth_col,
                                                y_col='穿孔エネルギー',
                                                height=400
                                            )
                                            st.plotly_chart(fig_original, use_container_width=True)
                                    
                                    with col2:
                                        # スケーリング後のデータも同じdepth_col名を持っているはず
                                        if depth_col:
                                            fig_stretched = visualizer.create_line_plot(
                                                stretched_data[key],
                                                title=f"{key}側 - スケーリング後",
                                                x_col=depth_col,
                                                y_col='穿孔エネルギー',
                                                height=400
                                            )
                                            st.plotly_chart(fig_stretched, use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ エラーが発生しました: {str(e)}")
                import traceback
                st.error(traceback.format_exc())
    
    # 拡張済みデータが存在する場合、リセットオプションを表示
    if AppState.get_stretched_data():
        st.divider()
        with card_container():
            st.subheader("リセットオプション")
            
            if st.button("🔄 すべての拡張データをリセット", key="reset_all"):
                AppState.set_stretched_data({})
                if 'stretch_applied' in st.session_state:
                    del st.session_state.stretch_applied
                st.success("✅ すべての拡張データをリセットしました")
                st.rerun()
