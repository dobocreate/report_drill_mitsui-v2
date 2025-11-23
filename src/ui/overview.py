"""データ概要表示モジュール"""
import streamlit as st
import plotly.graph_objects as go
from src.state import AppState
from src.ui.common import get_graph_layout_settings
from src.ui.styles import COLORS, card_container
from src.utils import sort_files_lmr


def display_data_overview():
    """データ概要タブ - エネルギー分布のみ表示"""
    raw_data = AppState.get_raw_data()
    if not raw_data:
        st.info("データが読み込まれていません")
        return

    for file_name in sort_files_lmr(raw_data.keys()):
        df = raw_data[file_name]
        length_col = next((c for c in ["穿孔長", "TD", "x:TD(m)"] if c in df.columns), None)
        energy_col = next((c for c in ["穿孔エネルギー", "Ene-M"] if c in df.columns), None)
        if not (length_col and energy_col):
            continue
        with card_container():
            # Subheader removed to avoid duplicate title
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df[length_col],
                    y=df[energy_col],
                    mode="lines",
                    name="穿孔エネルギー",
                    line=dict(color=COLORS["primary"], width=1.5),
                )
            )
            layout = get_graph_layout_settings()
            layout["title"] = {
                "text": f"{file_name} - 穿孔エネルギー",
                "font": {"size": 16}
            }
            layout["xaxis"]["title"] = "穿孔長 (m)"
            layout["yaxis"]["title"] = "穿孔エネルギー (kJ)"
            fig.update_layout(layout)
            st.plotly_chart(fig, use_container_width=True)
