"""
VTK生成モジュール
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import tempfile
from src.state import AppState
from src.vtk_converter import VTKConverter
from src.survey_point_calculator import SurveyPointCalculator
from src.utils import sort_files_lmr

def display_vtk_generation():
    """VTK生成タブ（LMR座標計算統合版）"""
    st.header("📦 VTKファイル生成（削孔検層データ）")
    
    # VTK converter初期化
    if 'vtk_converter' not in st.session_state:
        st.session_state.vtk_converter = VTKConverter()
    
    converter = st.session_state.vtk_converter
    
    # 測点計算機の初期化
    survey_calc = SurveyPointCalculator()
    
    # VTKライブラリの確認
    try:
        import vtk
        vtk_available = True
    except ImportError:
        vtk_available = False
        st.warning("⚠️ VTKライブラリがインストールされていません。VTKファイル生成機能が制限されます。")
        st.info("インストール方法: `pip install vtk`")
    
    # ファイル選択エリア
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📄 ファイル選択")
        
        # 処理済みデータがある場合はそれを優先
        processed_data = AppState.get_processed_data()
        raw_data = AppState.get_raw_data()
        
        if processed_data:
            st.info("✅ ノイズ除去済みデータを使用します")
            available_files = sort_files_lmr(processed_data.keys())
            data_source = processed_data
        else:
            st.info("ℹ️ 生データを使用します（ノイズ除去推奨）")
            available_files = sort_files_lmr(raw_data.keys())
            data_source = raw_data
        
        selected_files = st.multiselect(
            "VTK化するファイルを選択",
            available_files,
            key="vtk_file_select_new",
            help="L, M, Rのファイルを選択してください"
        )
        
        # LMRタイプの自動検出結果表示
        if selected_files:
            detected_types = []
            for file in selected_files:
                lmr_type = converter.detect_lmr_type(file)
                if lmr_type:
                    detected_types.append(f"{file} → **{lmr_type}側**")
                else:
                    detected_types.append(f"{file} → ❌ タイプ検出失敗")
            
            with st.expander("🔍 LMRタイプ検出結果"):
                for detection in detected_types:
                    st.write(detection)
    
    with col2:
        st.subheader("⚙️ 座標設定")
        
        # 距離入力方法の選択
        distance_input_method = st.radio(
            "距離の入力方法",
            ["直接入力", "測点から計算"],
            help="坑口からの距離を入力する方法を選択"
        )
        
        if distance_input_method == "直接入力":
            # 坑口からの距離入力
            distance_from_entrance = st.number_input(
                "トンネル坑口からの距離 (m)",
                min_value=0.0,
                value=1000.0,
                step=1.0,
                help="測点のトンネル坑口からの距離を入力"
            )
        else:
            # 測点から計算
            st.write("**測点入力（例: 250+11）**")
            survey_point_str = st.text_input(
                "測点",
                value="250+11",
                help="測点を 主番号+小数部 の形式で入力"
            )
            
            try:
                c_value, e_value = survey_calc.parse_survey_point(survey_point_str)
                distance_from_entrance = survey_calc.calculate_distance_from_entrance(c_value, e_value)
                st.success(f"計算された距離: **{distance_from_entrance:.1f}m**")
                
                # 計算詳細
                with st.expander("📊 計算詳細"):
                    st.write(f"測点: {survey_calc.format_survey_point(c_value, e_value)}")
                    st.write(f"測点数値: {c_value}×20 + {e_value} = {survey_calc.calculate_survey_point_value(c_value, e_value)}")
                    st.write(f"基準測点: 255+4 (= {survey_calc.reference_value})")
                    st.write(f"坑口からの距離: {survey_calc.reference_value} - {survey_calc.calculate_survey_point_value(c_value, e_value)} = {distance_from_entrance:.1f}m")
            except ValueError as e:
                st.error(f"測点の形式が不正です: {e}")
                distance_from_entrance = 0.0
        
        # 固定値の表示
        with st.expander("📐 使用される固定値", expanded=False):
            st.write("**座標計算パラメータ:**")
            st.write(f"- 基準距離: 967m")
            st.write(f"- 方向角度: 65.588°")
            st.write("**Z標高:**")
            st.write("- L側: 17.3m")
            st.write("- M側（天端）: 21.3m")
            st.write("- R側: 17.3m")
        
        # サンプリング設定
        sampling_interval = st.number_input(
            "サンプリング間隔",
            min_value=1,
            max_value=100,
            value=10,
            help="データ点を間引く間隔（行数）"
        )
    
    st.divider()
    
    # 処理実行エリア
    if selected_files and distance_from_entrance > 0:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🚀 VTKファイル生成", type="primary", use_container_width=True):
                with st.spinner("VTKファイルを生成中..."):
                    success_files = []
                    error_files = []
                    generated_files = {}
                    
                    for file_name in selected_files:
                        try:
                            # LMRタイプの検出
                            lmr_type = converter.detect_lmr_type(file_name)
                            if not lmr_type:
                                error_files.append((file_name, "L/M/Rタイプを検出できません"))
                                continue
                            
                            # データの取得
                            df = data_source[file_name]
                            
                            # CSVファイルを一時保存（VTKConverterが読み込むため）
                            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='shift-jis') as tmp:
                                df.to_csv(tmp, index=False)
                                temp_csv_path = tmp.name
                            
                            # VTK変換実行
                            output_vtk_name = converter.generate_vtk_filename(file_name)
                            output_vtk_path = f"output/{output_vtk_name}"
                            output_csv_path = f"output/{file_name.replace('.csv', '_3d.csv')}"
                            
                            # outputフォルダ作成
                            Path("output").mkdir(exist_ok=True)
                            
                            # 変換実行
                            vtk_path, csv_path = converter.convert_csv_to_vtk(
                                csv_file=temp_csv_path,
                                distance_from_entrance=distance_from_entrance,
                                output_vtk_path=output_vtk_path,
                                output_csv_path=output_csv_path,
                                lmr_type=lmr_type
                            )
                            
                            # 一時ファイル削除
                            Path(temp_csv_path).unlink()
                            
                            # 成功リストに追加
                            success_files.append(file_name)
                            generated_files[file_name] = {
                                'vtk': vtk_path,
                                'csv': csv_path,
                                'lmr_type': lmr_type
                            }
                            
                        except Exception as e:
                            error_files.append((file_name, str(e)))
                    
                    # 結果表示
                    if success_files:
                        st.success(f"✅ {len(success_files)}個のVTKファイルを生成しました")
                        AppState.set_generated_vtk_files(generated_files)
                        
                        # 生成ファイル情報
                        with st.expander("📁 生成されたファイル"):
                            for file_name, info in generated_files.items():
                                st.write(f"**{file_name}**")
                                st.write(f"- LMRタイプ: {info['lmr_type']}側")
                                st.write(f"- VTK: {info['vtk']}")
                                st.write(f"- CSV: {info['csv']}")
                    
                    if error_files:
                        with st.expander("❌ エラーが発生したファイル"):
                            for file_name, error in error_files:
                                st.write(f"- {file_name}: {error}")
        
        # ダウンロードセクション
        generated_files = AppState.get_generated_vtk_files()
        if generated_files:
            st.divider()
            st.subheader("📥 ダウンロード")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**VTKファイル**")
                for file_name, info in generated_files.items():
                    vtk_path = info['vtk']
                    if Path(vtk_path).exists():
                        with open(vtk_path, 'rb') as f:
                            vtk_content = f.read()
                        
                        st.download_button(
                            label=f"⬇️ {Path(vtk_path).name}",
                            data=vtk_content,
                            file_name=Path(vtk_path).name,
                            mime="application/vtk",
                            key=f"download_vtk_{file_name}"
                        )
            
            with col2:
                st.write("**3D座標CSV**")
                for file_name, info in generated_files.items():
                    csv_path = info['csv']
                    if Path(csv_path).exists():
                        with open(csv_path, 'r', encoding='shift-jis') as f:
                            csv_content = f.read()
                        
                        st.download_button(
                            label=f"⬇️ {Path(csv_path).name}",
                            data=csv_content.encode('shift-jis'),
                            file_name=Path(csv_path).name,
                            mime="text/csv",
                            key=f"download_csv_{file_name}"
                        )
        
        # 3Dプレビュー（座標のみ）
        if st.checkbox("📊 3D座標プレビュー"):
            if generated_files:
                fig = go.Figure()
                
                for file_name, info in generated_files.items():
                    csv_path = info['csv']
                    if Path(csv_path).exists():
                        # CSVから座標を読み込む
                        preview_df = pd.read_csv(csv_path, encoding='shift-jis', skiprows=1)
                        if all(col in preview_df.columns for col in ['X(m)', 'Y(m)', 'Z:標高(m)']):
                            fig.add_trace(go.Scatter3d(
                                x=preview_df['X(m)'],
                                y=preview_df['Y(m)'],
                                z=preview_df['Z:標高(m)'],
                                mode='lines+markers',
                                name=f"{info['lmr_type']}側",
                                marker=dict(size=2),
                                line=dict(width=3)
                            ))
                
                fig.update_layout(
                    scene=dict(
                        xaxis_title='X (m)',
                        yaxis_title='Y (m)',
                        zaxis_title='Z:標高 (m)',
                        aspectmode='data'
                    ),
                    height=600,
                    title=f"削孔検層3D軌跡（坑口から{distance_from_entrance}m）"
                )
                st.plotly_chart(fig, use_container_width=True)
    elif selected_files and distance_from_entrance <= 0:
        st.warning("⚠️ 有効な距離を入力してください")
    else:
        st.info("👆 VTK化するファイルを選択してください")
