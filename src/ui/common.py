"""
共通UIコンポーネント
"""
import streamlit as st
import plotly.graph_objects as go

def get_graph_layout_settings():
    """共通のグラフレイアウト設定を返す"""
    return dict(
        xaxis=dict(
            range=[0, 45],  # X軸の範囲を0-45mに固定
            showgrid=True,
            gridwidth=1,
            gridcolor='LightGray',
            showline=True,
            linewidth=1,  # 枠線を細く
            linecolor='LightGray',  # 枠線の色を補助線と同じに
            mirror=True,
            tickfont=dict(size=14),  # X軸の数値フォントサイズを大きく
            title=dict(font=dict(size=16))  # X軸タイトルのフォントサイズ
        ),
        yaxis=dict(
            range=[0, 1000],  # Y軸の範囲を0-1000に設定
            showgrid=True,
            gridwidth=1,
            gridcolor='LightGray',
            showline=True,
            linewidth=1,  # 枠線を細く
            linecolor='LightGray',  # 枠線の色を補助線と同じに
            mirror=True,
            tickfont=dict(size=14),  # Y軸の数値フォントサイズを大きく
            title=dict(font=dict(size=16))  # Y軸タイトルのフォントサイズ
        ),
        plot_bgcolor='white',
        font=dict(size=14),  # 全体のフォントサイズ
        title_font=dict(size=18)  # タイトルのフォントサイズ
    )
