"""
データ拡張（スケーリング）モジュール
"""
import streamlit as st
import pandas as pd
from src.state import AppState
from src.data_processor import DataProcessor
from src.data_stretcher import DataStretcher
from src.plotly_visualizer import PlotlyVisualizer

def display_data_stretching():
    """データ拡張（スケーリング）処理"""
    st.header("📏 データ拡張（スケーリング）")
    
    raw_data = AppState.get_raw_data()
    
    # データの存在確認
    if not raw_data:
        st.warning("⚠️ データを読み込んでください")
        return
    
    # デバッグ: 利用可能なデータキーを表示
    with st.expander("🔍 利用可能なデータ（デバッグ）", expanded=False):
        st.write("**セッション内のデータキー:**")
        for key in raw_data.keys():
            st.write(f"- {key}")
            if '_extracted' in key.lower():
                st.write(f"  → **抽出データとして検出**")
    
    # DataProcessorを使用してLMR分類
    processor = DataProcessor()
    stretcher = DataStretcher()
    
    # 元データをLMR分類
    base_data = processor.categorize_lmr_data(raw_data)
    
    # 抽出データがあるか確認（_extractedを含むキーを探す）
    extracted_data_keys = [key for key in raw_data.keys() if '_extracted' in key.lower()]
    
    # 拡張済みデータがあるか確認
    stretched_data_state = AppState.get_resampled_data() # Note: Using resampled_data key for stretched data might be confusing, checking original code usage. 
    # Original code used 'stretched_data' in session_state. Let's stick to that key in AppState if possible or add it.
    # AppState doesn't have explicit 'stretched_data' key defined in my previous step, but it has 'resampled_data'.
    # Wait, 'resampled_data' is for processing tab. 'stretched_data' is for stretching tab.
    # I should check AppState definition again. I defined KEY_RESAMPLED_DATA.
    # I should probably add KEY_STRETCHED_DATA to AppState or use st.session_state directly for now if I don't want to modify AppState again immediately.
    # However, to be clean, I should use st.session_state['stretched_data'] if it's not in AppState, or update AppState.
    # Let's check AppState content I wrote.
    # KEY_RESAMPLED_DATA = 'resampled_data'
    # KEY_PROCESSED_DATA = 'processed_data'
    # It seems I missed 'stretched_data' in AppState.
    # I will use st.session_state.get('stretched_data') directly for now to avoid breaking flow, or I can add it to AppState later.
    # Actually, I can just use st.session_state directly for this specific key since it's local to this tab's logic mostly, 
    # but the goal was to use AppState.
    # Let's use st.session_state['stretched_data'] for now to match original logic exactly.
    
    has_stretched_data = 'stretched_data' in st.session_state
    
    # L/M/Rごとにデータソースを選択
    st.subheader("📊 データソースの選択")
    st.write("各データタイプごとに使用するデータソースを選択してください：")
    
    # 選択されたデータを格納する辞書
    current_data = {}
    selected_sources_info = {}  # 選択情報を保存
    
    # L/M/Rそれぞれの選択UI
    cols = st.columns(3)
    
    for idx, key in enumerate(['L', 'M', 'R']):
        with cols[idx]:
            st.write(f"**{key}側データ**")
            
            # そのデータタイプが存在するかチェック
            has_base = key in base_data and base_data[key] is not None and not base_data[key].empty
            has_stretched = has_stretched_data and key in st.session_state.stretched_data and \
                           st.session_state.stretched_data[key] is not None and \
                           not st.session_state.stretched_data[key].empty
            
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
                options = []
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
                    default_option = options[0] if options else None
                
                # データソース選択
                if options:
                    data_source = st.selectbox(
                        "データソース",
                        options,
                        index=options.index(default_option) if default_option in options else 0,
                        key=f"stretch_source_{key}",
                        label_visibility="collapsed"
                    )
                    
                    # 選択に基づいてデータを設定
                    if data_source == "拡張済みデータ":
                        current_data[key] = st.session_state.stretched_data[key]
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
                        depth_col = None
                        for col in ['穿孔長', 'TD', 'x:TD(m)', '深度', 'Depth']:
                            if col in extracted_df.columns:
                                depth_col = col
                                break
                        
                        # 抽出データの元の範囲を保存
                        original_min = None
                        original_max = None
                        if depth_col:
                            original_min = extracted_df[depth_col].min()
                            original_max = extracted_df[depth_col].max()
                            
                            # 穿孔長を0基準に調整（最小値を0にシフト）
                            extracted_df[depth_col] = extracted_df[depth_col] - original_min
                            
                            st.caption(f"📌 抽出: {original_min:.1f}-{original_max:.1f}m")
                            st.caption(f"   → 0-{extracted_df[depth_col].max():.1f}m")
                        else:
                            st.caption(f"📌 抽出データ")
                        
                        # 調整後のデータをLMR分類
                        temp_dict = {ext_key: extracted_df}
                        temp_categorized = processor.categorize_lmr_data(temp_dict)
                        current_data[key] = temp_categorized[key] if key in temp_categorized else None
                        selected_sources_info[key] = f"抽出({ext_key})"
                    
                    # データ情報表示
                    if current_data[key] is not None:
                        df_info = current_data[key]
                        if '穿孔長' in df_info.columns:
                            max_length = df_info['穿孔長'].max()
                            st.caption(f"最大長: {max_length:.1f}m")
                        st.caption(f"行数: {len(df_info):,}")
    
    st.divider()
    
    # 選択情報のサマリーを表示
    if selected_sources_info:
        st.write("⚡ **選択されたデータソース:**")
        source_summary = []
        for key, source in selected_sources_info.items():
            source_summary.append(f"{key}側: {source}")
        st.info(" | ".join(source_summary))
    
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
                    # current_dataを基にして初期化
                    st.session_state.stretched_data = current_data.copy()
                    st.session_state.stretched_data.update(stretched_data)
                
                st.session_state.stretch_applied = True
                
                # 成功メッセージ
                st.success(f"✅ 選択された{len(selected_keys)}個のデータのスケーリングが完了しました")
                
                # サマリー表示
                st.subheader("スケーリング結果")
                stretcher.display_scale_summary(selected_data, stretched_data)
                
                # グラフ表示
                st.subheader("スケーリング前後の比較")
                
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
