"""
ノイズ除去モジュール
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from src.state import AppState
from src.data_processor import DataProcessor
from src.noise_remover import NoiseRemover
from src.ui.common import get_graph_layout_settings
from src.ui.styles import COLORS, card_container

def display_noise_removal():
    """ノイズ除去タブ"""
    
    raw_data = AppState.get_raw_data()
    
    # データの存在確認
    if not raw_data:
        st.warning("⚠️ データを読み込んでください")
        return
    
    # DataProcessorを使用してLMR分類
    processor = DataProcessor()
    base_data, filename_mapping = processor.categorize_lmr_data(raw_data, return_filenames=True)
    
    # ファイル名マッピングをセッションステートに保存
    st.session_state.lmr_filename_mapping = filename_mapping
    
    # 拡張済みデータの存在確認
    has_stretched_data = 'stretched_data' in st.session_state
    
    # 抽出データの存在確認
    extracted_data_keys = [key for key in raw_data.keys() if '_extracted' in key.lower()]
    
    # メインレイアウト: 左（設定）と右（グラフ）
    left_col, right_col = st.columns([1, 2], gap="large")
    
    # --- 左カラム: 設定 ---
    with left_col:
        with card_container():
            st.subheader("⚙️ ノイズ除去設定")
            st.caption("Lowessフィルタパラメータ")
            
            frac = st.slider("平滑化係数 (frac)", 0.01, 0.5, 0.05, 0.01, help="値が大きいほど滑らかになります")
            it = st.slider("反復回数 (it)", 0, 10, 3, 1, help="外れ値の影響を減らす回数")
            delta = st.number_input("Delta", 0.0, 10.0, 0.0, 0.1, help="計算高速化のためのパラメータ")
            
            # セッションステートに保存
            st.session_state['lowess_frac'] = frac
            st.session_state['lowess_it'] = it
            st.session_state['lowess_delta'] = delta
            
            st.divider()
            
            if st.button("🔄 ノイズ除去実行", type="primary", use_container_width=True):
                with st.spinner("ノイズ除去処理中..."):
                    # 処理実行ロジック
                    remover = NoiseRemover()
                    processed_count = 0
                    
                    for key in ['L', 'M', 'R']:
                        # データソースの決定（表示用と同じロジック）
                        current_df = None
                        if has_stretched_data and key in st.session_state.stretched_data and \
                           st.session_state.stretched_data[key] is not None:
                            current_df = st.session_state.stretched_data[key]
                        elif key in base_data and base_data[key] is not None:
                            current_df = base_data[key]
                        
                        if current_df is not None and '穿孔エネルギー' in current_df.columns:
                            # 処理実行
                            processed_df = remover.apply_lowess(
                                current_df,
                                target_column='穿孔エネルギー',
                                frac=frac,
                                it=it,
                                delta=delta
                            )
                            
                            # 保存
                            original_filename = filename_mapping.get(key)
                            if original_filename:
                                current_processed = AppState.get_processed_data().copy()
                                current_processed[original_filename] = processed_df
                                AppState.set_processed_data(current_processed)
                                processed_count += 1
                    
                    if processed_count > 0:
                        st.success(f"✅ {processed_count}件のデータを処理しました")
                        st.rerun()
                    else:
                        st.warning("処理対象のデータがありません")

    # --- 右カラム: グラフ表示 ---
    with right_col:
        st.subheader("📊 処理結果確認")
        
        # 処理済みデータを取得
        processed_data_map = AppState.get_processed_data()
        
        # 処理済みデータがない場合のみ説明を表示
        if not processed_data_map:
            st.info("👈 設定を行い、「ノイズ除去実行」ボタンを押すと処理結果が重ねて表示されます")
        
        # L/M/Rのデータを順次処理して表示（縦に並べる）
        for key in ['L', 'M', 'R']:
            # データソースの自動選択ロジック
            current_df = None
            source_label = "なし"
            
            if has_stretched_data and key in st.session_state.stretched_data and \
               st.session_state.stretched_data[key] is not None:
                current_df = st.session_state.stretched_data[key]
                source_label = "拡張済みデータ"
            elif key in base_data and base_data[key] is not None:
                current_df = base_data[key]
                source_label = "元データ"
            
            if current_df is None:
                continue
            
            with card_container():
                col_header, col_info = st.columns([2, 1])
                with col_header:
                    st.markdown(f"**{key}側データ**")
                with col_info:
                    st.caption(f"ソース: {source_label}")
                
                # 処理済みデータを取得
                processed_df = None
                original_filename = filename_mapping.get(key)
                if original_filename and original_filename in processed_data_map:
                    processed_df = processed_data_map[original_filename]
                
                # グラフ表示（処理前データは常に表示）
                fig = go.Figure()
                
                # X軸の決定
                x_col = '穿孔長' if '穿孔長' in current_df.columns else \
                        'x:TD(m)' if 'x:TD(m)' in current_df.columns else None
                        
                if x_col:
                    # 元データ（白）
                    fig.add_trace(go.Scatter(
                        x=current_df[x_col],
                        y=current_df['穿孔エネルギー'],
                        mode='lines',
                        name='処理前',
                        line=dict(color='white', width=1),
                        opacity=0.5
                    ))
                    
                    # 処理後データ（青） - 存在する場合のみ追加
                    if processed_df is not None:
                        fig.add_trace(go.Scatter(
                            x=processed_df[x_col],
                            y=processed_df['Lowess_Trend'],
                            mode='lines',
                            name='処理後',
                            line=dict(color=COLORS['primary'], width=2)
                        ))
                    
                    layout = get_graph_layout_settings()
                    layout.update(dict(
                        title=f"{key}側 - ノイズ除去結果",
                        xaxis_title="深度 (m)",
                        yaxis_title="穿孔エネルギー",
                        height=350,
                        margin=dict(l=40, r=20, t=40, b=40),
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        )
                    ))
                    fig.update_layout(layout)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("深度列が見つかりません")

    # ダウンロードセクション（処理済みデータがある場合）
    processed_data = AppState.get_processed_data()
    if processed_data:
        with st.container(border=True):
            st.subheader("📥 処理結果のダウンロード")
            
            # プロジェクト情報を取得
            project_date = AppState.get_project_date()
            date_str = project_date.strftime("%Y%m%d") if project_date else datetime.now().strftime("%Y%m%d")
            
            cols = st.columns(len(processed_data))
            for i, (name, df) in enumerate(processed_data.items()):
                with cols[i % 3]:
                    # ファイル名生成: 実施日_元のファイル名_ana.csv
                    # 元のファイル名から拡張子を除く
                    base_name = name.replace('.csv', '')
                    # もし元のファイル名に日付が入っている場合は重複するかもしれないが、
                    # 要件「各出力ファイルの名称に使用する日付は、実施日を使用してください」に従う
                    
                    file_name = f"{date_str}_{base_name}_ana.csv"
                    
                    csv = df.to_csv(index=False, encoding='shift_jis')
                    st.download_button(
                        label=f"⬇️ {file_name}",
                        data=csv.encode('shift_jis'),
                        file_name=file_name,
                        mime="text/csv",
                        key=f"download_processed_{name}"
                    )
