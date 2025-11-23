"""
ノイズ除去モジュール
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from src.state import AppState
from src.data_processor import DataProcessor
from src.noise_remover import NoiseRemover
from src.ui.common import get_graph_layout_settings

def display_noise_removal():
    """ノイズ除去タブ（元スクリプトの機能を完全再現）"""
    st.header("🔧 ノイズ除去処理 - 穿孔エネルギー値")
    
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
    # Note: Using st.session_state directly for stretched_data as discussed in stretching.py
    has_stretched_data = 'stretched_data' in st.session_state
    
    # 各データタイプ（L/M/R）ごとのデータソース選択
    st.subheader("📊 データソースの選択")
    st.write("各データタイプごとに使用するデータソースを選択してください：")
    
    # 選択されたデータを格納する辞書
    selected_data = {}
    
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
            
            if not has_base and not has_stretched:
                st.warning(f"データなし")
                selected_data[key] = None
            else:
                # 選択オプションを動的に作成
                options = []
                if has_base:
                    options.append("元のデータ")
                if has_stretched:
                    options.append("拡張済みデータ")
                
                # デフォルト値は拡張済みがあれば拡張済み、なければ元のデータ
                default_index = 1 if has_stretched and len(options) > 1 else 0
                
                # データソース選択
                data_source = st.radio(
                    "データソース",
                    options,
                    index=default_index,
                    key=f"noise_source_{key}",
                    label_visibility="collapsed"
                )
                
                # 選択に基づいてデータを設定
                if data_source == "拡張済みデータ":
                    selected_data[key] = st.session_state.stretched_data[key]
                    st.caption("📌 拡張済み")
                else:
                    selected_data[key] = base_data[key]
                    st.caption("📌 元データ")
                
                # データ情報表示
                if selected_data[key] is not None:
                    df_info = selected_data[key]
                    if '穿孔長' in df_info.columns:
                        max_length = df_info['穿孔長'].max()
                        st.caption(f"最大長: {max_length:.1f}m")
                    st.caption(f"行数: {len(df_info):,}")
    
    st.divider()
    
    remover = NoiseRemover()
    
    # 一括処理ボタンを上部に配置
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # 処理可能なデータがあるかチェック
        processable_data = {k: v for k, v in selected_data.items() 
                           if v is not None and not v.empty and '穿孔エネルギー' in v.columns}
        
        if processable_data:
            if st.button("🔧 選択したデータをノイズ除去", type="primary", key="process_all_files", use_container_width=True):
                with st.spinner("データを処理中..."):
                    processed_count = 0
                    processed_data_dict = {}
                    
                    # 選択されたデータで処理
                    for key, df in processable_data.items():
                        # Lowessパラメータはセッションステートから取得（サイドバーで設定されている前提）
                        # app.pyのサイドバー設定がまだ移行されていないため、デフォルト値を使用するか、
                        # ここで設定UIを追加する必要があるかもしれないが、
                        # 元のコードではサイドバーにあるはず。
                        # 今回はapp.pyのリファクタリングでサイドバー設定も考慮する必要がある。
                        # 一旦、st.session_stateから取得するようにする。
                        frac = st.session_state.get('lowess_frac', 0.05)
                        it = st.session_state.get('lowess_it', 3)
                        delta = st.session_state.get('lowess_delta', 0.0)
                        
                        processed_df = remover.apply_lowess(
                            df,
                            target_column='穿孔エネルギー',
                            frac=frac,
                            it=it,
                            delta=delta
                        )
                        # 元のファイル名を使用（存在する場合）
                        if 'lmr_filename_mapping' in st.session_state and key in st.session_state.lmr_filename_mapping:
                            original_filename = st.session_state.lmr_filename_mapping[key]
                            # 処理済みファイル名として保存（元のファイル名を保持）
                            file_name = original_filename.replace('.csv', '_processed.csv') if original_filename.endswith('.csv') else f"{original_filename}_processed"
                        else:
                            # マッピングがない場合は従来の方式
                            file_name = f"{key}_processed"
                        
                        processed_data_dict[file_name] = processed_df
                        
                        # AppStateを使って保存
                        processed_data = AppState.get_processed_data()
                        processed_data[file_name] = processed_df
                        AppState.set_processed_data(processed_data)
                        
                        st.session_state[f'processed_{file_name}'] = processed_df
                        processed_count += 1
                    
                    st.success(f"✅ {processed_count}個のデータのノイズ除去が完了しました！")
                    st.rerun()
        else:
            st.info("処理可能なデータがありません。データを選択してください。")
    
    # 各データのグラフをLMRの順番で表示
    for key in ['L', 'M', 'R']:
        if key in selected_data and selected_data[key] is not None and not selected_data[key].empty:
            df = selected_data[key]
            
            # セクションタイトルとして表示
            st.divider()
            
            # データソース情報を含むタイトル
            source_info = ""
            if key in selected_data:
                # 拡張済みデータかどうか判定
                if has_stretched_data and key in st.session_state.stretched_data and \
                   st.session_state.stretched_data[key] is not None and \
                   df.equals(st.session_state.stretched_data[key]):
                    source_info = " (拡張済みデータ)"
                else:
                    source_info = " (元データ)"
            
            st.markdown(f"### 📄 {key}側データ{source_info}")
            
            # 必須カラムのチェック
            if '穿孔エネルギー' not in df.columns:
                st.warning(f"⚠️ '{key}側' に '穿孔エネルギー' 列が見つかりません")
                st.info("データのカラム: " + ", ".join(df.columns))
                continue
            
            # X軸のカラムを特定
            x_col = '穿孔長' if '穿孔長' in df.columns else ('TD' if 'TD' in df.columns else None)
            
            # 処理済みデータのキー
            # Note: This logic assumes a specific naming convention which might be tricky if multiple files map to same key
            # But following original logic:
            processed_key = f"{key}_processed"
            # Try to find if there is a processed file corresponding to this key
            # If we used filename mapping, we need to reverse it or check values
            processed_df = None
            
            # Check direct key first
            if f'processed_{processed_key}' in st.session_state:
                processed_df = st.session_state[f'processed_{processed_key}']
            else:
                # Check via filename mapping
                if 'lmr_filename_mapping' in st.session_state and key in st.session_state.lmr_filename_mapping:
                    original_filename = st.session_state.lmr_filename_mapping[key]
                    file_name = original_filename.replace('.csv', '_processed.csv') if original_filename.endswith('.csv') else f"{original_filename}_processed"
                    if f'processed_{file_name}' in st.session_state:
                         processed_df = st.session_state[f'processed_{file_name}']
            
            # グラフ表示領域
            # 処理結果がある場合は処理前・処理後を重ねて表示
            if processed_df is not None:
                
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
                            title=f"ノイズ除去結果（{key}側）{source_info} - 全{len(df)}行",
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
                            title=f"ノイズ除去結果（{key}側）{source_info} - 全{len(df)}行",
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
                        title=f"データ（{key}側）{source_info} - 全{len(df)}行"
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
                        title=f"データ（{key}側）{source_info} - 全{len(df)}行"
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
    processed_data = AppState.get_processed_data()
    if processed_data:
        st.divider()
        st.subheader("📥 処理結果のダウンロード")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**個別ファイル**")
            for name in processed_data.keys():
                data = processed_data[name]
                csv = data.to_csv(index=False, encoding='shift_jis')
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"{name}_ana_{timestamp}.csv"
                
                st.download_button(
                    label=f"⬇️ {file_name}",
                    data=csv.encode('shift_jis'),
                    file_name=file_name,
                    mime="text/csv",
                    key=f"download_batch_{name}"
                )
