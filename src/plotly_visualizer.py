"""
Plotlyによる美しいインタラクティブグラフ作成モジュール
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple


class PlotlyVisualizer:
    """Plotlyグラフ作成クラス"""
    
    def __init__(self):
        self.default_colorscale = 'Viridis'
        self.default_marker_size = 5
        self.default_line_width = 2
        
        # カラーテーマ
        self.color_palette = px.colors.qualitative.Set2
        
    def create_3d_trajectory(
        self,
        data_dict: Dict[str, pd.DataFrame],
        file_names: List[str],
        show_energy: bool = True,
        colorscale: str = None
    ) -> go.Figure:
        """3D軌跡グラフの作成
        
        Args:
            data_dict: ファイル名とデータフレームの辞書
            file_names: 表示するファイル名のリスト
            show_energy: エネルギー値を色で表示するか
            colorscale: カラースケール
            
        Returns:
            Plotly Figure オブジェクト
        """
        
        colorscale = colorscale or self.default_colorscale
        fig = go.Figure()
        
        for i, file_name in enumerate(file_names):
            if file_name not in data_dict:
                continue
            
            df = data_dict[file_name]
            
            # 座標データの取得
            x, y, z = self._extract_coordinates(df)
            
            if show_energy:
                # エネルギー値を色として使用
                energy = self._extract_energy(df)
                
                fig.add_trace(go.Scatter3d(
                    x=x,
                    y=y,
                    z=z,
                    mode='markers+lines',
                    name=file_name,
                    marker=dict(
                        size=self.default_marker_size,
                        color=energy,
                        colorscale=colorscale,
                        showscale=i == 0,  # 最初のトレースのみカラーバー表示
                        colorbar=dict(
                            title="エネルギー",
                            thickness=20,
                            len=0.7,
                            x=1.02
                        ),
                        line=dict(width=0)
                    ),
                    line=dict(
                        color=self.color_palette[i % len(self.color_palette)],
                        width=self.default_line_width
                    ),
                    text=[f"深度: {z_val:.1f}m<br>エネルギー: {e:.1f}" 
                          for z_val, e in zip(z, energy)],
                    hovertemplate="%{text}<extra>%{fullData.name}</extra>"
                ))
            else:
                # 単色表示
                fig.add_trace(go.Scatter3d(
                    x=x,
                    y=y,
                    z=z,
                    mode='markers+lines',
                    name=file_name,
                    marker=dict(
                        size=self.default_marker_size,
                        color=self.color_palette[i % len(self.color_palette)]
                    ),
                    line=dict(
                        color=self.color_palette[i % len(self.color_palette)],
                        width=self.default_line_width
                    )
                ))
        
        # レイアウト設定
        fig.update_layout(
            title="削孔軌跡 3D表示",
            scene=dict(
                xaxis_title="X座標 (m)",
                yaxis_title="Y座標 (m)",
                zaxis_title="Z座標 (m)",
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                ),
                aspectmode='data'
            ),
            height=700,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        return fig
    
    def create_depth_energy_plot(
        self,
        data_dict: Dict[str, pd.DataFrame],
        file_names: List[str]
    ) -> go.Figure:
        """深度-エネルギープロット
        
        Args:
            data_dict: ファイル名とデータフレームの辞書
            file_names: 表示するファイル名のリスト
            
        Returns:
            Plotly Figure オブジェクト
        """
        
        fig = go.Figure()
        
        for i, file_name in enumerate(file_names):
            if file_name not in data_dict:
                continue
            
            df = data_dict[file_name]
            
            # 深度とエネルギーデータの取得
            depth = self._extract_depth(df)
            
            # Ene-L, Ene-M, Ene-Rがある場合は3つのラインを表示
            if all(col in df.columns for col in ['Ene-L', 'Ene-M', 'Ene-R']):
                # 左肩
                fig.add_trace(go.Scatter(
                    x=depth,
                    y=df['Ene-L'],
                    mode='lines',
                    name=f"{file_name} - 左",
                    line=dict(
                        color=self.color_palette[i * 3 % len(self.color_palette)],
                        width=self.default_line_width
                    )
                ))
                
                # 中央
                fig.add_trace(go.Scatter(
                    x=depth,
                    y=df['Ene-M'],
                    mode='lines',
                    name=f"{file_name} - 中央",
                    line=dict(
                        color=self.color_palette[(i * 3 + 1) % len(self.color_palette)],
                        width=self.default_line_width,
                        dash='solid'
                    )
                ))
                
                # 右肩
                fig.add_trace(go.Scatter(
                    x=depth,
                    y=df['Ene-R'],
                    mode='lines',
                    name=f"{file_name} - 右",
                    line=dict(
                        color=self.color_palette[(i * 3 + 2) % len(self.color_palette)],
                        width=self.default_line_width,
                        dash='dash'
                    )
                ))
            else:
                # 単一エネルギー値
                energy = self._extract_energy(df)
                fig.add_trace(go.Scatter(
                    x=depth,
                    y=energy,
                    mode='lines',
                    name=file_name,
                    line=dict(
                        color=self.color_palette[i % len(self.color_palette)],
                        width=self.default_line_width
                    )
                ))
        
        # レイアウト設定
        fig.update_layout(
            title="深度-エネルギー特性",
            xaxis_title="深度 (m)",
            yaxis_title="エネルギー値",
            height=600,
            hovermode='x unified',
            showlegend=True
        )
        
        # グリッド表示
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
        
        return fig
    
    def create_energy_distribution(
        self,
        data_dict: Dict[str, pd.DataFrame],
        file_names: List[str]
    ) -> go.Figure:
        """エネルギー分布のヒストグラムと箱ひげ図
        
        Args:
            data_dict: ファイル名とデータフレームの辞書
            file_names: 表示するファイル名のリスト
            
        Returns:
            Plotly Figure オブジェクト
        """
        
        # サブプロットの作成
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('エネルギー分布 (ヒストグラム)', 'エネルギー分布 (箱ひげ図)'),
            vertical_spacing=0.15,
            row_heights=[0.6, 0.4]
        )
        
        all_energy_data = []
        all_labels = []
        
        for i, file_name in enumerate(file_names):
            if file_name not in data_dict:
                continue
            
            df = data_dict[file_name]
            energy = self._extract_energy(df)
            
            # NaN値を除去
            energy_clean = energy[~np.isnan(energy)]
            
            # ヒストグラム
            fig.add_trace(
                go.Histogram(
                    x=energy_clean,
                    name=file_name,
                    opacity=0.7,
                    marker_color=self.color_palette[i % len(self.color_palette)]
                ),
                row=1, col=1
            )
            
            # 箱ひげ図用データ
            all_energy_data.extend(energy_clean)
            all_labels.extend([file_name] * len(energy_clean))
        
        # 箱ひげ図
        if all_energy_data:
            df_box = pd.DataFrame({
                'エネルギー': all_energy_data,
                'ファイル': all_labels
            })
            
            for i, file_name in enumerate(file_names):
                df_file = df_box[df_box['ファイル'] == file_name]
                if not df_file.empty:
                    fig.add_trace(
                        go.Box(
                            y=df_file['エネルギー'],
                            name=file_name,
                            marker_color=self.color_palette[i % len(self.color_palette)]
                        ),
                        row=2, col=1
                    )
        
        # レイアウト設定
        fig.update_xaxes(title_text="エネルギー値", row=1, col=1)
        fig.update_yaxes(title_text="頻度", row=1, col=1)
        fig.update_yaxes(title_text="エネルギー値", row=2, col=1)
        
        fig.update_layout(
            height=700,
            showlegend=True,
            title_text="エネルギー値の統計分布"
        )
        
        return fig
    
    def create_correlation_matrix(
        self,
        df: pd.DataFrame
    ) -> go.Figure:
        """相関行列のヒートマップ
        
        Args:
            df: データフレーム
            
        Returns:
            Plotly Figure オブジェクト
        """
        
        # 数値カラムのみ選択
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) < 2:
            # 相関を計算できない場合
            fig = go.Figure()
            fig.add_annotation(
                text="相関行列を作成するための数値データが不足しています",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False
            )
            return fig
        
        # 相関行列の計算
        corr_matrix = df[numeric_cols].corr()
        
        # ヒートマップの作成
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu',
            zmid=0,
            text=corr_matrix.values.round(2),
            texttemplate="%{text}",
            textfont={"size": 10},
            colorbar=dict(
                title="相関係数",
                thickness=20,
                len=0.7
            )
        ))
        
        # レイアウト設定
        fig.update_layout(
            title="パラメータ相関行列",
            height=600,
            width=700,
            xaxis=dict(tickangle=-45),
            yaxis=dict(autorange='reversed')
        )
        
        return fig
    
    def _extract_coordinates(
        self,
        df: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """データフレームから座標を抽出"""
        
        # X座標
        x_cols = ['X', 'X(m)', 'x', 'x:TD(m)']
        x_col = next((col for col in x_cols if col in df.columns), None)
        x = df[x_col].values if x_col else np.zeros(len(df))
        
        # Y座標
        y_cols = ['Y', 'Y(m)', 'y', 'y:CL差(m)']
        y_col = next((col for col in y_cols if col in df.columns), None)
        y = df[y_col].values if y_col else np.zeros(len(df))
        
        # Z座標
        z_cols = ['Z', 'Z(m)', 'z', 'Z:標高(m)', 'z:SL差(m)', 'Z_SL']
        z_col = next((col for col in z_cols if col in df.columns), None)
        if z_col:
            z = df[z_col].values
        elif 'TD' in df.columns:
            z = -df['TD'].values  # 深度を負の値として使用
        else:
            z = np.zeros(len(df))
        
        return x, y, z
    
    def _extract_depth(self, df: pd.DataFrame) -> np.ndarray:
        """深度データを抽出"""
        depth_cols = ['TD', 'Depth', '深度', 'x:TD(m)']
        depth_col = next((col for col in depth_cols if col in df.columns), None)
        
        if depth_col:
            return df[depth_col].values
        else:
            return np.arange(len(df))
    
    def _extract_energy(self, df: pd.DataFrame) -> np.ndarray:
        """エネルギーデータを抽出"""
        energy_cols = ['穿孔エネルギー', 'エネルギー', 'Energy', 'Ene-M']
        energy_col = next((col for col in energy_cols if col in df.columns), None)
        
        if energy_col:
            return df[energy_col].values
        elif all(col in df.columns for col in ['Ene-L', 'Ene-M', 'Ene-R']):
            # 3つの平均を計算
            return df[['Ene-L', 'Ene-M', 'Ene-R']].mean(axis=1).values
        else:
            return np.zeros(len(df))