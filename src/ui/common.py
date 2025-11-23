"""
共通UIコンポーネント
"""
import streamlit as st
import plotly.graph_objects as go
from src.ui.styles import COLORS

def get_graph_layout_settings():
    """共通のグラフレイアウト設定を返す"""
    return dict(
        xaxis=dict(
            range=[0, 45],  # X軸の範囲を0-45mに固定
            showgrid=True,
            gridwidth=1,
            gridcolor=COLORS['border'],
            showline=True,
            linewidth=1,
            linecolor=COLORS['border'],
            mirror=True,
            tickfont=dict(size=12, color=COLORS['text']),
            title=dict(font=dict(size=14, color=COLORS['text']))
        ),
        yaxis=dict(
            range=[0, 1000],  # Y軸の範囲を0-1000に設定
            showgrid=True,
            gridwidth=1,
            gridcolor=COLORS['border'],
            showline=True,
            linewidth=1,
            linecolor=COLORS['border'],
            mirror=True,
            tickfont=dict(size=12, color=COLORS['text']),
            title=dict(font=dict(size=14, color=COLORS['text']))
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(size=12, color=COLORS['text']),
        title_font=dict(size=16, color=COLORS['text']),
        margin=dict(l=50, r=20, t=40, b=40)
    )
