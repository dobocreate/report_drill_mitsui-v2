"""
VTK生成モジュール
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
import tempfile
from src.state import AppState
from src.vtk_converter import VTKConverter
from src.survey_point_calculator import SurveyPointCalculator
from src.ui.styles import COLORS, card_container
from src.utils import sort_files_lmr

def display_vtk_generation():
    """VTK生成タブ（LMR座標計算統合版）"""
    # st.header("📦 VTKファイル生成（削孔検層データ）") # Removed as per user request
    
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
    
    # メインレイアウト: 左右1:1
    col_left, col_right = st.columns([1, 1])
    
    # ========== 左側: ファイル選択・設定・実行ボタン ==========
    with col_left:
        # ファイル選択
        with card_container():
            st.subheader("📄 ファイル選択")
            
            # データの優先順位: 間引き後 > ノイズ除去後 > 生データ
            resampled_data = AppState.get_resampled_data()
            processed_data = AppState.get_processed_data()
            raw_data = AppState.get_raw_data()
            
            data_source = {}
            available_files = []
            
            if resampled_data:
                st.info("✅ 間引き処理済みデータを使用します")
                available_files = sort_files_lmr(resampled_data.keys())
                data_source = resampled_data
            elif processed_data:
                st.info("✅ ノイズ除去済みデータを使用します")
                available_files = sort_files_lmr(processed_data.keys())
                data_source = processed_data
            else:
                st.info("ℹ️ 生データを使用します（推奨: ノイズ除去・間引き）")
                available_files = sort_files_lmr(raw_data.keys())
                data_source = raw_data
            
            # チェックボックスでファイル選択（デフォルト全選択）
            st.write("VTK化するファイルを選択:")
            selected_files = []
            
            # 縦に並べてファイル選択
            for file_name in available_files:
                if st.checkbox(file_name, value=True, key=f"vtk_select_{file_name}"):
                    selected_files.append(file_name)
            
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
        
        # 設定
        with card_container():
            st.subheader("⚙️ 設定")
            
            # 距離の計算（サイドバーの測点情報を使用）
            survey_point_str = AppState.get_survey_point()
            distance_from_entrance = 0.0
            
            if survey_point_str:
                try:
                    c_value, e_value = survey_calc.parse_survey_point(survey_point_str)
                    distance_from_entrance = survey_calc.calculate_distance_from_entrance(c_value, e_value)
                    st.success(f"坑口からの距離: **{distance_from_entrance:.1f}m**")
                    st.caption(f"測点: {survey_point_str}")
                except ValueError:
                    st.error("サイドバーの測点形式が不正です")
            else:
                st.warning("サイドバーで測点を入力してください")

            # 詳細設定（固定値・サンプリング）
            with st.expander("🔧 詳細設定（固定値・サンプリング）", expanded=False):
                col_detail_left, col_detail_right = st.columns(2)
                
                with col_detail_left:
                    st.markdown("**座標計算パラメータ**")
                    # 固定値の入力（初期値は現在の固定値）
                    reference_distance = st.number_input("基準距離 (m)", value=967.0, step=1.0)
                    direction_angle = st.number_input("方向角度 (°)", value=65.588, step=0.001, format="%.3f")
                
                with col_detail_right:
                    st.markdown("**Z標高 (m)**")
                    z_l = st.number_input("L側", value=17.3, step=0.1)
                    z_m = st.number_input("M側（天端）", value=21.3, step=0.1)
                    z_r = st.number_input("R側", value=17.3, step=0.1)
                    
                    st.markdown("**サンプリング**")
                    # サンプリング設定
                    sampling_interval = st.number_input(
                        "サンプリング間隔",
                        min_value=1,
                        max_value=100,
                        value=10,
                        help="データ点を間引く間隔（行数）"
                    )
        
        # VTKファイル生成ボタン
        if selected_files and distance_from_entrance > 0:
            if st.button("🚀 VTKファイル生成", type="primary", use_container_width=True):
                with st.spinner("VTKファイルを生成中..."):
                    success_files = []
                    error_files = []
                    generated_files = {}
                    
                    # プロジェクト情報を取得
                    project_date = AppState.get_project_date()
                    date_str = project_date.strftime("%Y%m%d") if project_date else datetime.now().strftime("%Y%m%d")
                    
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
                            
                            # ファイル名生成
                            base_name = file_name.replace('.csv', '')
                            output_vtk_name = f"{date_str}_{base_name}.vtk"
                            output_csv_name = f"{date_str}_{base_name}_3d.csv"
                            
                            output_vtk_path = f"output/{output_vtk_name}"
                            output_csv_path = f"output/{output_csv_name}"
                            
                            # outputフォルダ作成
                            Path("output").mkdir(exist_ok=True)
                            
                            # 変換実行
                            z_elevations = {
                                'L': z_l,
                                'M': z_m,
                                'R': z_r
                            }
                            
                            vtk_path, csv_path = converter.convert_csv_to_vtk(
                                csv_file=temp_csv_path,
                                distance_from_entrance=distance_from_entrance,
                                output_vtk_path=output_vtk_path,
                                output_csv_path=output_csv_path,
                                lmr_type=lmr_type,
                                reference_distance=reference_distance,
                                direction_angle=direction_angle,
                                z_elevations=z_elevations,
                                sampling_interval=int(sampling_interval)
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
                    
                    if error_files:
                        with st.expander("❌ エラーが発生したファイル"):
                            for file_name, error in error_files:
                                st.write(f"- {file_name}: {error}")
        elif selected_files and distance_from_entrance <= 0:
            st.warning("⚠️ 有効な距離を入力してください")
        else:
            st.info("👆 VTK化するファイルを選択してください")
    
    # ========== 右側: 説明文またはダウンロード ==========
    with col_right:
        generated_files = AppState.get_generated_vtk_files()
        
        if generated_files:
            # ダウンロードセクション
            with st.container(border=True):
                st.subheader("📥 ダウンロード")
                
                col_dl1, col_dl2 = st.columns(2)
                
                with col_dl1:
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
                
                with col_dl2:
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
            
            # 3Dプレビューのチェックボックス（右側に配置）
            show_3d_preview = st.checkbox("📊 3D座標プレビュー")
        else:
            # 処理内容の説明
            with card_container():
                st.subheader("📋 処理内容")
                st.markdown("""
                このページでは、削孔検層データをVTK形式に変換します。
                
                **処理の流れ:**
                1. **ファイル選択**: VTK化するファイルをチェックボックスで選択
                2. **設定確認**: 坑口からの距離と詳細パラメータを確認
                3. **VTK生成**: ボタンをクリックして変換を実行
                4. **ダウンロード**: 生成されたVTKファイルと3D座標CSVをダウンロード
                
                **生成されるファイル:**
                - **VTKファイル**: 3D可視化ソフトウェア（ParaView等）で使用
                - **3D座標CSV**: X, Y, Z座標とエネルギー値を含むCSVファイル
                
                **詳細設定:**
                - 座標計算パラメータ（基準距離、方向角度）
                - Z標高（L側、M側、R側）
                - サンプリング間隔（データ点の間引き）
                
                左側の設定を確認し、「🚀 VTKファイル生成」ボタンをクリックしてください。
                """)
            show_3d_preview = False
    
    # 3Dプレビューグラフ（左右カラムの外、下側に配置）
    if generated_files and show_3d_preview:
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

