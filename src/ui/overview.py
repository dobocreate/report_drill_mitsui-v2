"""
データ概要表示モジュール
"""
import streamlit as st
import plotly.graph_objects as go
from src.state import AppState
from src.ui.common import get_graph_layout_settings
from src.utils import sort_files_lmr

def display_data_overview():
    """データ概要タブ"""
    st.header("📊 データ概要")
    
    raw_data = AppState.get_raw_data()
    
    # データ選択（LMRの順番）
    selected_file = st.selectbox(
        "ファイルを選択",
        sort_files_lmr(raw_data.keys())
    )
    
    if selected_file:
        df = raw_data[selected_file]
        
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
        
        # 基本情報表示
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("データ点数", f"{len(df):,} 行")
        with col2:
            st.metric("カラム数", f"{len(df.columns)} 列")
        with col3:
            if length_col:
                max_depth = df[length_col].max()
                st.metric("最大深度", f"{max_depth:.2f} m")
        
        # グラフ表示
        if length_col and energy_col:
            st.subheader("📈 穿孔エネルギー分布")
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df[length_col],
                y=df[energy_col],
                mode='lines',
                name='穿孔エネルギー',
                line=dict(color='#1f77b4', width=1)
            ))
            
            layout = get_graph_layout_settings()
            layout['title'] = f"{selected_file} - 穿孔エネルギー"
            layout['xaxis']['title'] = "穿孔長 (m)"
            layout['yaxis']['title'] = "穿孔エネルギー (kJ)"
            
            fig.update_layout(layout)
            st.plotly_chart(fig, use_container_width=True)
        
        # データプレビュー
        with st.expander("📋 データプレビュー", expanded=False):
            st.dataframe(df.head(100))
