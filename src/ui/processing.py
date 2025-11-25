"""
データ加工（間引き・補間）モジュール
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from src.state import AppState
from src.data_processor import DataProcessor
from src.ui.common import get_graph_layout_settings
from src.ui.styles import COLORS, card_container
from src.utils import sort_files_lmr

def display_data_processing():
    """データ加工タブ（間引き・補間処理）"""
    # st.header("✂️ データ加工 - 間引き・補間処理") # Removed as per user request
    
    processor = DataProcessor()
    
    # 処理対象データの確認
    processed_data = AppState.get_processed_data()
    if not processed_data:
        st.warning("⚠️ データ加工を行うには、まず「ノイズ除去」タブでデータを処理してください")
        return
    
    # 処理設定
    with card_container():
        st.subheader("📏 サンプリング設定")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
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
            
            st.divider()
            
            # 処理実行ボタン
            process_clicked = st.button("🔧 データ間引き実行", type="primary", key="process_resample", use_container_width=True)
        
        with col2:
            # 処理済みデータがある場合はダウンロードボタンを表示
            resampled_data = AppState.get_resampled_data()
            if resampled_data:
                with st.container(border=True):
                    st.subheader("📥 サンプリングデータのダウンロード")
                    
                    # プロジェクト情報を取得
                    project_date = AppState.get_project_date()
                    date_str = project_date.strftime("%Y%m%d") if project_date else datetime.now().strftime("%Y%m%d")
                    
                    dl_col1, dl_col2 = st.columns(2)
                    
                    with dl_col1:
                        st.write("**個別ファイル**")
                        for filename in sort_files_lmr(resampled_data.keys()):
                            df = resampled_data[filename]
                            csv = df.to_csv(index=False, encoding='shift_jis')
                            
                            interval_str = f"{int(interval*100):02d}cm"  # 0.02 -> 02cm
                            # 元のファイル名から拡張子を除く
                            base_name = filename.replace('.csv', '')
                            file_name = f"{date_str}_{base_name}_resampled_{interval_str}.csv"
                            
                            st.download_button(
                                label=f"⬇️ {file_name}",
                                data=csv.encode('shift_jis'),
                                file_name=file_name,
                                mime="text/csv",
                                key=f"download_resampled_{filename}"
                            )
                    
                    with dl_col2:
                        # 全ファイルを結合したデータ（ノイズ除去と同じ横結合形式）
                        if len(resampled_data) > 1:
                            st.write("**結合ファイル**")
                            
                            # 横結合処理（ノイズ除去と同じ形式）
                            combined_df = pd.DataFrame()
                            
                            for filename in sort_files_lmr(resampled_data.keys()):
                                df = resampled_data[filename]
                                # 深度カラムを特定
                                depth_col = processor._find_depth_column(df)
                                
                                # 必要なカラムのみ抽出（順序：穿孔長、穿孔エネルギー、Lowess_Trend）
                                required_cols = []
                                if depth_col:
                                    required_cols.append(depth_col)
                                if '穿孔エネルギー' in df.columns:
                                    required_cols.append('穿孔エネルギー')
                                if 'Lowess_Trend' in df.columns:
                                    required_cols.append('Lowess_Trend')
                                
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
                            interval_str = f"{int(interval*100):02d}cm"
                            combined_file_name = f"{date_str}_combined_resampled_{interval_str}.csv"
                            
                            st.download_button(
                                label=f"⬇️ {combined_file_name}",
                                data=csv.encode('shift_jis'),
                                file_name=combined_file_name,
                                mime="text/csv",
                                key="download_combined_resampled"
                            )
            else:
                with st.container(border=True, height=200):
                    st.markdown(f"""
                    **処理内容:**
                    - {interval:.2f}m 刻みでデータを再サンプリング
                    - 該当位置にデータがない場合は線形補間
                    - ノイズ除去後のデータ（Lowess_Trend）を処理
                    """)
        
        # 処理実行
        if process_clicked:
            with st.spinner("データを間引き処理中..."):
                resampled_data = {}
                error_files = []
                
                for filename in sort_files_lmr(processed_data.keys()):
                    df = processed_data[filename]
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
                    AppState.set_resampled_data(resampled_data)
                    st.success(f"✅ {len(resampled_data)}個のファイルの間引き処理が完了しました！")
                    st.rerun()
                    
                    # エラーがあれば表示
                    if error_files:
                        with st.expander("⚠️ 処理できなかったファイル"):
                            for filename, error in error_files:
                                st.write(f"- {filename}: {error}")
                else:
                    st.error("データの間引き処理に失敗しました")
    
    # 処理結果の表示
    resampled_data = AppState.get_resampled_data()
    original_data_source = AppState.get_raw_data()
    
    if resampled_data:
        st.subheader("📊 サンプリング結果")
        
        # ファイルごとの結果表示（LMRの順番）
        for filename in sort_files_lmr(resampled_data.keys()):
            df = resampled_data[filename]
            
            with card_container():
                st.markdown(f"### 📄 {filename}")
                
                # レイアウト: 左側に統計情報、右側にグラフ
                col_stats, col_graph = st.columns([1, 2])
                
                # 深度カラムを特定
                depth_col = processor._find_depth_column(df)
                
                with col_stats:
                    # st.markdown("#### 📊 統計情報") # Removed as per user request
                    original_count = len(processed_data[filename])
                    st.metric("元データ行数", f"{original_count:,}")
                    
                    resampled_count = len(df)
                    st.metric("間引き後行数", f"{resampled_count:,}")
                    
                    reduction_rate = (1 - resampled_count / original_count) * 100
                    st.metric("削減率", f"{reduction_rate:.1f}%")
                    
                    if depth_col and depth_col in df.columns:
                        depth_range = f"{df[depth_col].min():.2f} - {df[depth_col].max():.2f}"
                        st.metric("深度範囲 (m)", depth_range)

                with col_graph:
                    # グラフ表示（処理前後の比較）
                    if depth_col:
                        fig = go.Figure()
                        
                        # 1. オリジナルデータ（穿孔エネルギー）
                        if original_data_source and filename in original_data_source:
                            raw_df = original_data_source[filename]
                            if depth_col in raw_df.columns and '穿孔エネルギー' in raw_df.columns:
                                fig.add_trace(go.Scatter(
                                    x=raw_df[depth_col],
                                    y=raw_df['穿孔エネルギー'],
                                    mode='lines',
                                    name='オリジナル',
                                    line=dict(color='rgba(128, 128, 128, 0.5)', width=1),
                                    hoverinfo='skip'
                                ))

                        # 2. 間引き前（ノイズ除去後）
                        before_resample_df = processed_data[filename]
                        if depth_col in before_resample_df.columns and 'Lowess_Trend' in before_resample_df.columns:
                            fig.add_trace(go.Scatter(
                                x=before_resample_df[depth_col],
                                y=before_resample_df['Lowess_Trend'],
                                mode='lines',
                                name='間引き前',
                                line=dict(color='rgba(255, 255, 255, 0.8)', width=1.5),
                            ))
                        
                        # 3. 間引き後データ
                        if 'Lowess_Trend' in df.columns:
                            fig.add_trace(go.Scatter(
                                x=df[depth_col],
                                y=df['Lowess_Trend'],
                                mode='markers+lines',
                                name=f'間引き後 ({interval:.2f}m刻み)',
                                line=dict(color=COLORS['primary'], width=2),
                                marker=dict(size=3, color=COLORS['primary'])
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
                            height=400,
                            showlegend=True
                        ))
                        fig.update_layout(layout)
                        
                        st.plotly_chart(fig, use_container_width=True)
