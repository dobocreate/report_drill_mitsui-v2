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
from src.utils import sort_files_lmr

def display_data_processing():
    """データ加工タブ（間引き・補間処理）"""
    st.header("✂️ データ加工 - 間引き・補間処理")
    
    processor = DataProcessor()
    
    # 処理対象データの確認
    processed_data = AppState.get_processed_data()
    if not processed_data:
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
                    
                    # エラーがあれば表示
                    if error_files:
                        with st.expander("⚠️ 処理できなかったファイル"):
                            for filename, error in error_files:
                                st.write(f"- {filename}: {error}")
                else:
                    st.error("データの間引き処理に失敗しました")
    
    st.divider()
    
    # 処理結果の表示
    resampled_data = AppState.get_resampled_data()
    if resampled_data:
        st.subheader("📊 間引き処理結果")
        
        # ファイルごとの結果表示（LMRの順番）
        for filename in sort_files_lmr(resampled_data.keys()):
            df = resampled_data[filename]
            st.divider()
            st.markdown(f"### 📄 {filename}")
            
            # 統計情報
            col1, col2, col3, col4 = st.columns(4)
            
            # 深度カラムを特定
            depth_col = processor._find_depth_column(df)
            
            with col1:
                original_count = len(processed_data[filename])
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
                original_df = processed_data[filename]
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
            for filename in sort_files_lmr(resampled_data.keys()):
                df = resampled_data[filename]
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
