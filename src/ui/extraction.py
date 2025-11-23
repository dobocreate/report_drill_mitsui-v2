"""
データ抽出・部分分析モジュール
"""
import streamlit as st
import plotly.graph_objects as go
from src.state import AppState
from src.ui.common import get_graph_layout_settings
from src.utils import sort_files_lmr
from src.data_extractor import DataExtractor

def display_data_extraction():
    """データ抽出・部分分析タブ"""
    st.header("✂️ データ抽出・部分分析")
    
    raw_data = AppState.get_raw_data()
    
    if not raw_data:
        st.info("データを読み込んでください")
        return
    
    # データ選択
    selected_file = st.selectbox(
        "抽出対象ファイルを選択",
        sort_files_lmr(raw_data.keys()),
        key="extraction_file_select"
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
    
    st.subheader("🎯 穿孔長（深度）範囲による抽出")
    
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
    
    # 左右分割レイアウト（左：コントロール、右：グラフ）
    left_col, right_col = st.columns([1, 3])
    
    # 左側：数値入力とコントロール
    with left_col:
        st.write("**🔢 数値で範囲を指定**")
        
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
        
        # 抽出実行ボタン
        if st.button("🔍 選択範囲でデータを抽出", key="extract_by_depth", type="primary", use_container_width=True):
            extracted_df = extractor.extract_by_depth_range(
                df, current_min, current_max, depth_col
            )
            # セッション状態に一時的に保存
            st.session_state[f'temp_extracted_{selected_file}'] = extracted_df
        
        # 範囲情報の表示
        st.divider()
        st.write("**📏 選択範囲情報**")
        
        # データポイント数の計算
        mask = (df[depth_col] >= current_min) & (df[depth_col] <= current_max)
        selected_count = mask.sum()
        total_count = len(df)
        
        # メトリクス表示（CSSで高さ調整）
        st.metric("範囲の幅", f"{current_max - current_min:.2f} m")
        st.metric("データ点数", f"{selected_count:,} / {total_count:,}")
        st.metric("選択率", f"{(selected_count/total_count*100):.1f}%")
    
    # 右側：グラフ表示
    with right_col:
        st.write("**📊 グラフで範囲を確認**")
        
        if energy_col:
            # Plotlyでインタラクティブグラフを作成（穿孔長をX軸、穿孔エネルギーをY軸）
            fig = go.Figure()
            
            # メインデータをプロット
            fig.add_trace(go.Scatter(
                x=df[depth_col],
                y=df[energy_col],
                mode='lines',
                name='全データ',
                line=dict(color='lightgray', width=1)
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
                    line=dict(color='red', width=2)
                ))
            
            # 範囲を示す垂直線（X軸上の穿孔長範囲）
            fig.add_vline(x=current_min, 
                         line_dash="dash", line_color="blue", 
                         annotation_text=f"開始: {current_min:.2f}m")
            fig.add_vline(x=current_max, 
                         line_dash="dash", line_color="blue",
                         annotation_text=f"終了: {current_max:.2f}m")
            
            # 選択範囲を薄い青で塗りつぶし
            fig.add_vrect(
                x0=current_min,
                x1=current_max,
                fillcolor="lightblue",
                opacity=0.2,
                layer="below",
                line_width=0
            )
            
            # レイアウト設定（標準的なグラフレイアウトを使用）
            layout = get_graph_layout_settings()
            layout.update(dict(
                title=f"{selected_file} - 範囲選択",
                xaxis_title=f"{depth_col} (m)",
                yaxis_title=energy_col,
                height=700,
                hovermode='x unified',
                showlegend=True
            ))
            # X軸の範囲を深度データの全範囲に設定（少し余裕を持たせる）
            depth_min_range = df[depth_col].min()
            depth_max_range = df[depth_col].max()
            depth_margin = (depth_max_range - depth_min_range) * 0.02  # 2%の余白
            layout['xaxis']['range'] = [depth_min_range - depth_margin, depth_max_range + depth_margin]
            # Y軸の範囲を自動調整
            layout['yaxis'].pop('range', None)
            
            fig.update_layout(layout)
            
            # グラフ表示
            st.plotly_chart(fig, use_container_width=True)
        else:
            # エネルギーデータがない場合
            st.warning("穿孔エネルギーデータが見つかりません。グラフを表示できません。")
    
    # 抽出結果の表示（セッション状態から取得）
    extracted_df = st.session_state.get(f'temp_extracted_{selected_file}')
    if extracted_df is not None:
        st.success(f"✅ データを抽出しました")
        
        # サマリー情報の表示
        summary = extractor.get_extraction_summary(extracted_df)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("元データ行数", summary.get('original_rows', 0))
        with col2:
            st.metric("抽出データ行数", summary.get('extracted_rows', 0))
        with col3:
            extraction_rate = (summary.get('extracted_rows', 0) / 
                             summary.get('original_rows', 1) * 100)
            st.metric("抽出率", f"{extraction_rate:.1f}%")
        
        # 深度範囲の情報
        if 'depth_range' in summary:
            st.write("**深度範囲:**")
            depth_info = summary['depth_range']
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("最小深度", f"{depth_info['min']:.2f} m")
            with col2:
                st.metric("最大深度", f"{depth_info['max']:.2f} m")
            with col3:
                st.metric("平均深度", f"{depth_info['mean']:.2f} m")
        
        # エネルギー統計
        if 'energy_stats' in summary:
            st.write("**エネルギー統計:**")
            energy_info = summary['energy_stats']
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("最小", f"{energy_info['min']:.2f}")
            with col2:
                st.metric("最大", f"{energy_info['max']:.2f}")
            with col3:
                st.metric("平均", f"{energy_info['mean']:.2f}")
            with col4:
                st.metric("標準偏差", f"{energy_info['std']:.2f}")
        
        # データ表示
        with st.expander("📋 抽出データを表示", expanded=True):
            st.dataframe(extracted_df)
        
        # データ保存
        st.write("**💾 抽出データの保存**")
        col1, col2 = st.columns(2)
        
        with col1:
            # セッションステートに保存
            default_name = f"{selected_file.replace('.csv', '')}_extracted"
            save_name = st.text_input(
                "保存名",
                value=default_name,
                key="save_extracted_name",
                help="抽出データとして保存されます。'_extracted'を含む名前にしてください。"
            )
            
            if st.button("セッションに保存", key="save_to_session"):
                # _extractedが含まれていない場合は追加
                if '_extracted' not in save_name.lower():
                    save_name = f"{save_name}_extracted"
                
                # AppStateを使って保存
                raw_data[save_name] = extracted_df.copy()
                AppState.set_raw_data(raw_data)
                
                st.success(f"✅ '{save_name}'として保存しました")
                
                # 保存されたデータの情報を表示
                st.info(f"保存されたデータ: {len(extracted_df)}行, 範囲: {extracted_df[depth_col].min():.1f}m - {extracted_df[depth_col].max():.1f}m")
                
                # 一時データをクリア
                if f'temp_extracted_{selected_file}' in st.session_state:
                    del st.session_state[f'temp_extracted_{selected_file}']
                
                st.rerun()
        
        with col2:
            # CSVダウンロード
            csv = extracted_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="CSVダウンロード",
                data=csv,
                file_name=f"{selected_file}_extracted.csv",
                mime="text/csv",
                key="download_extracted"
            )
        
        # グラフ表示
        st.write("**📊 データ可視化**")
        
        # 深度カラムとエネルギーカラムの検出
        depth_col = None
        energy_col = None
        
        for col in ['穿孔長', 'TD', 'x:TD(m)', '深度', 'Depth']:
            if col in extracted_df.columns:
                depth_col = col
                break
        
        for col in ['穿孔エネルギー', 'エネルギー', 'Energy', 'Ene-M']:
            if col in extracted_df.columns:
                energy_col = col
                break
        
        if depth_col and energy_col:
            # Plotlyで比較グラフを作成（X軸：穿孔長、Y軸：穿孔エネルギー）
            fig = go.Figure()
            
            # 元データ（薄いグレー）
            fig.add_trace(go.Scatter(
                x=df[depth_col],
                y=df[energy_col],
                mode='lines',
                name='元データ',
                line=dict(color='lightgray', width=1),
                opacity=0.5
            ))
            
            # 抽出データ（赤）
            fig.add_trace(go.Scatter(
                x=extracted_df[depth_col],
                y=extracted_df[energy_col],
                mode='lines',
                name='抽出データ',
                line=dict(color='red', width=2)
            ))
            
            # 抽出範囲を示す垂直線と塗りつぶし
            fig.add_vline(x=current_min, 
                         line_dash="dash", line_color="blue", opacity=0.5)
            fig.add_vline(x=current_max, 
                         line_dash="dash", line_color="blue", opacity=0.5)
            
            fig.add_vrect(
                x0=current_min,
                x1=current_max,
                fillcolor="lightblue",
                opacity=0.1,
                layer="below",
                line_width=0
            )
            
            # レイアウト設定（標準的なグラフレイアウトを使用）
            layout = get_graph_layout_settings()
            layout.update(dict(
                title=f"抽出結果の比較 - {selected_file}",
                xaxis_title=f"{depth_col} (m)",
                yaxis_title=energy_col,
                height=500,
                hovermode='x unified',
                showlegend=True
            ))
            # X軸の範囲を深度データの全範囲に設定（少し余裕を持たせる）
            depth_min = df[depth_col].min()
            depth_max = df[depth_col].max()
            depth_margin = (depth_max - depth_min) * 0.02  # 2%の余白
            layout['xaxis']['range'] = [depth_min - depth_margin, depth_max + depth_margin]
            # Y軸の範囲を自動調整
            layout['yaxis'].pop('range', None)
            
            fig.update_layout(layout)
            st.plotly_chart(fig, use_container_width=True)
