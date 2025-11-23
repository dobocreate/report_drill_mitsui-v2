"""
データ抽出・部分分析モジュール
"""
import streamlit as st
import plotly.graph_objects as go
from src.state import AppState
from src.ui.common import get_graph_layout_settings
from src.ui.styles import COLORS, card_container
from src.utils import sort_files_lmr
from src.data_extractor import DataExtractor

def display_data_extraction():
    """データ抽出・部分分析タブ"""
    raw_data = AppState.get_raw_data()
    
    if not raw_data:
        st.info("データを読み込んでください")
        return
    
    with card_container():
        # 左右分割レイアウト（左：コントロール、右：グラフ）
        left_col, right_col = st.columns([1, 2], gap="large")
        
        # 左側：データ選択と範囲指定
        with left_col:
            # データ選択（範囲指定の上部に配置）
            st.markdown("##### 📂 対象データの選択")
            selected_file = st.selectbox(
                "抽出対象ファイルを選択",
                sort_files_lmr(raw_data.keys()),
                key="extraction_file_select",
                label_visibility="collapsed"
            )
            
            if not selected_file:
                return
            
            df = raw_data[selected_file]
            extractor = DataExtractor()
            
            # 深度カラムの確認
            depth_col = None
            for col in ['穿孔長', 'TD', 'x:TD(m)', '深度', 'Depth']:
                if col in df.columns:
                    depth_col = col
                    break
            
            if not depth_col:
                st.warning("深度データが見つかりません")
                return
            
            # エネルギーカラムの確認（グラフ表示用）
            energy_col = None
            for col in ['穿孔エネルギー', 'エネルギー', 'Energy', 'Ene-M']:
                if col in df.columns:
                    energy_col = col
                    break
            
            # セッション状態の初期化（ファイルごとに保持）
            session_key_min = f'depth_range_min_{selected_file}'
            session_key_max = f'depth_range_max_{selected_file}'
            
            if session_key_min not in st.session_state:
                st.session_state[session_key_min] = float(df[depth_col].min())
            if session_key_max not in st.session_state:
                st.session_state[session_key_max] = float(df[depth_col].max())
            
            # 現在の範囲を取得
            current_min = st.session_state[session_key_min]
            current_max = st.session_state[session_key_max]
            
            # スペースを空ける
            st.write("")
            st.write("")
            
            # 範囲指定
            st.markdown("##### 🔢 範囲指定")
            
            depth_min = st.number_input(
                "開始深度 (m)",
                value=current_min,
                min_value=float(df[depth_col].min()),
                max_value=float(df[depth_col].max()),
                step=0.1,
                key=f"depth_start_input_{selected_file}"
            )
            
            depth_max = st.number_input(
                "終了深度 (m)",
                value=current_max,
                min_value=float(df[depth_col].min()),
                max_value=float(df[depth_col].max()),
                step=0.1,
                key=f"depth_end_input_{selected_file}"
            )
            
            # 数値入力が変更された場合、current値を即座に更新
            if depth_min != current_min or depth_max != current_max:
                current_min = depth_min
                current_max = depth_max
                # セッション状態も更新
                st.session_state[session_key_min] = depth_min
                st.session_state[session_key_max] = depth_max
            
            st.write("")
            
            # 区切り線
            st.divider()
            
            # 抽出実行ボタン
            if st.button("🔍 データ抽出", key="extract_by_depth", type="primary", use_container_width=True):
                extracted_df = extractor.extract_by_depth_range(
                    df, current_min, current_max, depth_col
                )
                
                # 自動保存用のファイル名を生成
                base_name = selected_file.replace('.csv', '').replace('.CSV', '')
                save_name = f"{base_name}_extracted"
                
                # 自動的にセッションに保存
                raw_data[save_name] = extracted_df.copy()
                AppState.set_raw_data(raw_data)
                
                # 一時保存（結果表示用）
                st.session_state[f'temp_extracted_{selected_file}'] = extracted_df
                st.session_state[f'saved_name_{selected_file}'] = save_name
                
                st.rerun()
        
        # 右側：グラフ表示
        with right_col:
            st.markdown("##### 📊 範囲確認グラフ")
            
            if energy_col:
                fig = go.Figure()
                
                # メインデータをプロット
                fig.add_trace(go.Scatter(
                    x=df[depth_col],
                    y=df[energy_col],
                    mode='lines',
                    name='全データ',
                    line=dict(color=COLORS['text'], width=1),
                    opacity=0.3
                ))
                
                # 選択範囲のデータをハイライト
                mask = (df[depth_col] >= current_min) & \
                       (df[depth_col] <= current_max)
                selected_data = df[mask]
                
                if not selected_data.empty:
                    fig.add_trace(go.Scatter(
                        x=selected_data[depth_col],
                        y=selected_data[energy_col],
                        mode='lines',
                        name='選択範囲',
                        line=dict(color=COLORS['primary'], width=2)
                    ))
                
                # 範囲を示す垂直線
                fig.add_vline(x=current_min, 
                             line_dash="dash", line_color=COLORS['info'], 
                             annotation_text=f"開始: {current_min:.2f}m")
                fig.add_vline(x=current_max, 
                             line_dash="dash", line_color=COLORS['info'],
                             annotation_text=f"終了: {current_max:.2f}m")
                
                # 選択範囲を塗りつぶし
                fig.add_vrect(
                    x0=current_min,
                    x1=current_max,
                    fillcolor=COLORS['primary'],
                    opacity=0.1,
                    layer="below",
                    line_width=0
                )
                
                layout = get_graph_layout_settings()
                layout.update(dict(
                    title=f"{selected_file} - 範囲選択",
                    xaxis_title=f"{depth_col} (m)",
                    yaxis_title=energy_col,
                    height=500,
                    hovermode='x unified',
                    showlegend=True
                ))
                
                depth_min_range = df[depth_col].min()
                depth_max_range = df[depth_col].max()
                depth_margin = (depth_max_range - depth_min_range) * 0.02
                layout['xaxis']['range'] = [depth_min_range - depth_margin, depth_max_range + depth_margin]
                layout['yaxis'].pop('range', None)
                
                fig.update_layout(layout)
                st.plotly_chart(fig, use_container_width=True)
                
                # グラフの下に選択範囲情報を表示
                st.markdown("##### 📏 選択範囲情報")
                
                # データポイント数の計算
                mask = (df[depth_col] >= current_min) & (df[depth_col] <= current_max)
                selected_count = mask.sum()
                total_count = len(df)
                
                # 3列で横並び表示
                info_col1, info_col2, info_col3 = st.columns(3)
                with info_col1:
                    st.metric("範囲の幅", f"{current_max - current_min:.2f} m")
                with info_col2:
                    st.metric("データ点数", f"{selected_count:,} / {total_count:,}")
                with info_col3:
                    st.metric("選択率", f"{(selected_count/total_count*100):.1f}%")
            else:
                st.warning("穿孔エネルギーデータが見つかりません。グラフを表示できません。")
    
    # 抽出結果の表示
    extracted_df = st.session_state.get(f'temp_extracted_{selected_file}')
    saved_name = st.session_state.get(f'saved_name_{selected_file}')
    
    if extracted_df is not None and saved_name:
        with card_container():
            st.success(f"✅ データを抽出し、'{saved_name}' として自動保存しました")
            
            # サマリー情報の表示
            summary = extractor.get_extraction_summary(extracted_df)
            
            st.subheader("📊 抽出結果サマリー")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("元データ行数", summary.get('original_rows', 0))
            with col2:
                st.metric("抽出データ行数", summary.get('extracted_rows', 0))
            with col3:
                extraction_rate = (summary.get('extracted_rows', 0) / 
                                 summary.get('original_rows', 1) * 100)
                st.metric("抽出率", f"{extraction_rate:.1f}%")
            
            if 'depth_range' in summary:
                st.markdown("**深度範囲**")
                depth_info = summary['depth_range']
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("最小深度", f"{depth_info['min']:.2f} m")
                with col2:
                    st.metric("最大深度", f"{depth_info['max']:.2f} m")
                with col3:
                    st.metric("平均深度", f"{depth_info['mean']:.2f} m")
            
            with st.expander("📋 抽出データを表示", expanded=False):
                st.dataframe(extracted_df, use_container_width=True)

