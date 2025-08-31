"""
LMR座標計算の簡易スタンドアロン版
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.lmr_coordinate_calculator import LMRCoordinateCalculator

st.set_page_config(
    page_title="LMR座標計算システム",
    page_icon="🎯",
    layout="wide"
)

def main():
    st.title("🎯 LMR穿孔データ座標計算システム")
    
    # 固定値の表示
    with st.sidebar:
        st.header("📌 固定値")
        st.info("""
        **基準点（974行目）:**
        - 基準距離: 967m
        - 方向角度: 65.588°
        
        **基準座標:**
        - L側X: -660,689.760
        - L側Y: 733,147.100
        - M側X: -658,622.871
        - M側Y: 737,699.910
        - R側X: -656,556.811
        - R側Y: 742,253.072
        """)
    
    # 計算機の初期化
    calculator = LMRCoordinateCalculator()
    
    # メインエリア
    st.header("📊 座標計算")
    
    # 単一距離の計算
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("距離入力")
        
        # 距離入力
        distance = st.number_input(
            "トンネル坑口からの距離 (m)",
            min_value=0.0,
            value=1238.0,
            step=1.0,
            format="%.1f",
            help="測点の距離を入力してください"
        )
        
        # 計算ボタン
        if st.button("🔢 座標計算", type="primary", use_container_width=True):
            # 座標計算（固定値を使用）
            result = calculator.calculate_coordinates(
                distance_from_entrance=distance
            )
            
            # 結果を保存
            st.session_state.last_result = result
            st.session_state.last_distance = distance
    
    with col2:
        st.subheader("計算結果")
        
        if 'last_result' in st.session_state:
            result = st.session_state.last_result
            distance = st.session_state.last_distance
            
            # 結果を見やすく表示
            result_data = {
                '座標': ['L側', 'M側', 'R側'],
                'X座標': [result['L_X'], result['M_X'], result['R_X']],
                'Y座標': [result['L_Y'], result['M_Y'], result['R_Y']]
            }
            result_df = pd.DataFrame(result_data)
            
            st.success(f"✅ 距離 {distance}m の座標を計算しました")
            st.dataframe(result_df, use_container_width=True)
            
            # ダウンロードボタン
            csv = result_df.to_csv(index=False, encoding='shift_jis')
            st.download_button(
                label="📥 CSVダウンロード",
                data=csv.encode('shift_jis'),
                file_name=f"lmr_coordinates_{int(distance)}m.csv",
                mime="text/csv"
            )
    
    st.divider()
    
    # 複数距離の一括計算
    st.header("📋 複数距離の一括計算")
    
    col3, col4 = st.columns([1, 2])
    
    with col3:
        st.subheader("距離リスト入力")
        
        # テキストエリアで複数距離を入力
        distances_text = st.text_area(
            "距離を改行区切りで入力",
            value="1000\n1100\n1200\n1238\n1300",
            height=150,
            help="複数の距離を改行で区切って入力してください"
        )
        
        if st.button("🔢 一括計算", type="primary", use_container_width=True, key="batch_calc"):
            try:
                # 距離をパース
                distances = [float(d.strip()) for d in distances_text.split('\n') if d.strip()]
                
                # 一括計算
                results = []
                for dist in distances:
                    result = calculator.calculate_coordinates(distance_from_entrance=dist)
                    results.append({
                        '距離(m)': dist,
                        'L側X': result['L_X'],
                        'L側Y': result['L_Y'],
                        'M側X': result['M_X'],
                        'M側Y': result['M_Y'],
                        'R側X': result['R_X'],
                        'R側Y': result['R_Y']
                    })
                
                batch_df = pd.DataFrame(results)
                st.session_state.batch_results = batch_df
                st.success(f"✅ {len(distances)}点の座標を計算しました")
                
            except ValueError as e:
                st.error("❌ 距離の入力形式が正しくありません")
    
    with col4:
        st.subheader("一括計算結果")
        
        if 'batch_results' in st.session_state:
            batch_df = st.session_state.batch_results
            
            # 結果表示
            st.dataframe(batch_df, use_container_width=True, height=300)
            
            # ダウンロードボタン
            csv = batch_df.to_csv(index=False, encoding='shift_jis')
            st.download_button(
                label="📥 一括計算結果をダウンロード",
                data=csv.encode('shift_jis'),
                file_name="lmr_coordinates_batch.csv",
                mime="text/csv",
                key="download_batch"
            )
            
            # グラフ表示
            if st.checkbox("📊 グラフ表示"):
                fig = go.Figure()
                
                # L, M, R各点をプロット
                fig.add_trace(go.Scatter(
                    x=batch_df['L側X'],
                    y=batch_df['L側Y'],
                    mode='markers+lines',
                    name='L側',
                    marker=dict(size=8, color='blue')
                ))
                
                fig.add_trace(go.Scatter(
                    x=batch_df['M側X'],
                    y=batch_df['M側Y'],
                    mode='markers+lines',
                    name='M側',
                    marker=dict(size=8, color='green')
                ))
                
                fig.add_trace(go.Scatter(
                    x=batch_df['R側X'],
                    y=batch_df['R側Y'],
                    mode='markers+lines',
                    name='R側',
                    marker=dict(size=8, color='red')
                ))
                
                # 距離ラベルを追加
                for _, row in batch_df.iterrows():
                    fig.add_annotation(
                        x=row['M側X'],
                        y=row['M側Y'],
                        text=f"{row['距離(m)']:.0f}m",
                        showarrow=False,
                        font=dict(size=10)
                    )
                
                fig.update_layout(
                    title="LMR座標プロット",
                    xaxis_title="X座標",
                    yaxis_title="Y座標",
                    height=500,
                    hovermode='closest'
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    # テスト検証セクション
    with st.expander("🧪 計算検証（1238m地点）"):
        test_distance = 1238.0
        test_result = calculator.calculate_coordinates(distance_from_entrance=test_distance)
        
        expected = {
            'L_X': -907.462,
            'L_Y': 845.15,
            'M_X': -905.395,
            'M_Y': 849.703,
            'R_X': -903.329,
            'R_Y': 854.256
        }
        
        comparison_data = []
        for key in ['L_X', 'L_Y', 'M_X', 'M_Y', 'R_X', 'R_Y']:
            comparison_data.append({
                '項目': key,
                '計算値': test_result[key],
                '期待値': expected[key],
                '差': abs(test_result[key] - expected[key])
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df)
        
        # 検証結果
        max_diff = comparison_df['差'].max()
        if max_diff < 0.001:
            st.success("✅ 計算結果が期待値と一致しています")
        else:
            st.warning(f"⚠️ 最大誤差: {max_diff:.6f}")

if __name__ == "__main__":
    main()