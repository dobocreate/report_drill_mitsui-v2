def display_noise_removal():
    """ノイズ除去タブ（元スクリプトの機能を完全再現）"""
    st.header("🔧 ノイズ除去処理 - 穿孔エネルギー値")
    
    if 'data' not in st.session_state or not st.session_state.data:
        st.warning("⚠️ データを読み込んでください")
        return
    
    # 使用するデータの選択
    data_source = st.radio(
        "使用するデータ",
        ["元のデータ", "拡張済みデータ（存在する場合）"],
        key="noise_data_source"
    )
    
    # データソースの決定
    if data_source == "拡張済みデータ（存在する場合）" and 'stretched_data' in st.session_state:
        current_data = st.session_state.stretched_data
        st.info("📌 拡張済みデータを使用しています")
    else:
        current_data = st.session_state.data
        if data_source == "拡張済みデータ（存在する場合）":
            st.info("📌 拡張済みデータが存在しないため、元のデータを使用しています")
    
    remover = NoiseRemover()
    
    # 一括処理ボタンを上部に配置
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔧 すべてのファイルを一括でノイズ除去", type="primary", key="process_all_files", use_container_width=True):
            with st.spinner("すべてのファイルを処理中..."):
                processed_count = 0
                processed_data_dict = {}
                
                # LMRデータで処理
                for key in ['L', 'M', 'R']:
                    if key in current_data and current_data[key] is not None and not current_data[key].empty:
                        df = current_data[key]
                        if '穿孔エネルギー' in df.columns:
                            processed_df = remover.apply_lowess(
                                df,
                                target_column='穿孔エネルギー',
                                frac=st.session_state.lowess_frac,
                                it=st.session_state.lowess_it,
                                delta=st.session_state.lowess_delta
                            )
                            # キーをファイル名形式に変換して保存
                            file_name = f"{key}_processed"
                            processed_data_dict[file_name] = processed_df
                            st.session_state.processed_data[file_name] = processed_df
                            st.session_state[f'processed_{file_name}'] = processed_df
                            processed_count += 1
                
                st.success(f"✅ {processed_count}個のデータのノイズ除去が完了しました！")
                st.rerun()
    
    # 各データのグラフをLMRの順番で表示
    for key in ['L', 'M', 'R']:
        if key in current_data and current_data[key] is not None and not current_data[key].empty:
            df = current_data[key]
            
            # セクションタイトルとして表示
            st.divider()
            st.markdown(f"### 📄 {key}側データ")
            
            # 必須カラムのチェック
            if '穿孔エネルギー' not in df.columns:
                st.warning(f"⚠️ '{key}側' に '穿孔エネルギー' 列が見つかりません")
                st.info("データのカラム: " + ", ".join(df.columns))
                continue
            
            # X軸のカラムを特定
            x_col = '穿孔長' if '穿孔長' in df.columns else ('TD' if 'TD' in df.columns else None)
            
            # 処理済みデータのキー
            processed_key = f"{key}_processed"
            
            # グラフ表示領域
            # 処理結果がある場合は処理前・処理後を重ねて表示
            if f'processed_{processed_key}' in st.session_state:
                processed_df = st.session_state[f'processed_{processed_key}']
                
                if 'Lowess_Trend' in processed_df.columns:
                    # 処理前と処理後を重ねたグラフを作成
                    fig = go.Figure()
                    
                    if x_col:
                        # X軸タイトルを設定
                        x_axis_title = '穿孔長(m)' if x_col == '穿孔長' else x_col
                        
                        # 処理前データ（青いライン）
                        fig.add_trace(go.Scatter(
                            x=df[x_col],
                            y=df['穿孔エネルギー'],
                            mode='lines',
                            name='処理前',
                            line=dict(color='blue', width=2),
                            opacity=0.7
                        ))
                        
                        # 処理後データ（赤いライン、上に表示）
                        fig.add_trace(go.Scatter(
                            x=processed_df[x_col],
                            y=processed_df['Lowess_Trend'],
                            mode='lines',
                            name='処理後',
                            line=dict(color='red', width=2)
                        ))
                        
                        # 共通のレイアウト設定を取得
                        layout = get_graph_layout_settings()
                        layout.update(dict(
                            title=f"ノイズ除去結果（{key}側） - 全{len(df)}行",
                            xaxis_title=x_axis_title,
                            yaxis_title='穿孔エネルギー',
                            hovermode='x unified',
                            height=600,
                            showlegend=True,
                            autosize=True,
                            margin=dict(l=80, r=80, t=100, b=80)
                        ))
                        fig.update_layout(layout)
                    else:
                        # X軸がない場合はインデックスを使用
                        fig.add_trace(go.Scatter(
                            y=df['穿孔エネルギー'],
                            mode='lines',
                            name='処理前',
                            line=dict(color='blue', width=2),
                            opacity=0.7
                        ))
                        
                        fig.add_trace(go.Scatter(
                            y=processed_df['Lowess_Trend'],
                            mode='lines',
                            name='処理後',
                            line=dict(color='red', width=2)
                        ))
                        
                        # 共通のレイアウト設定を取得
                        layout = get_graph_layout_settings()
                        layout.update(dict(
                            title=f"ノイズ除去結果（{key}側） - 全{len(df)}行",
                            xaxis_title='データポイント',
                            yaxis_title='穿孔エネルギー',
                            hovermode='x unified',
                            height=600,
                            showlegend=True,
                            autosize=True,
                            margin=dict(l=80, r=80, t=100, b=80)
                        ))
                        fig.update_layout(layout)
                    
                    st.plotly_chart(fig, use_container_width=True)
            else:
                # 処理前データのみ表示
                if x_col:
                    # X軸タイトルを設定
                    x_axis_title = '穿孔長(m)' if x_col == '穿孔長' else x_col
                    
                    fig = px.line(
                        df,
                        x=x_col,
                        y='穿孔エネルギー',
                        title=f"元データ（{key}側） - 全{len(df)}行"
                    )
                    fig.update_traces(line=dict(color='blue', width=2))
                    # 共通のレイアウト設定を取得して適用
                    layout = get_graph_layout_settings()
                    layout.update(dict(
                        xaxis_title=x_axis_title,
                        height=600,
                        autosize=True,
                        margin=dict(l=80, r=80, t=100, b=80)
                    ))
                    fig.update_layout(layout)
                else:
                    fig = px.line(
                        y=df['穿孔エネルギー'],
                        title=f"元データ（{key}側） - 全{len(df)}行"
                    )
                    fig.update_traces(line=dict(color='blue', width=2))
                    # 共通のレイアウト設定を取得して適用
                    layout = get_graph_layout_settings()
                    layout.update(dict(
                        height=600,
                        autosize=True,
                        margin=dict(l=80, r=80, t=100, b=80)
                    ))
                    fig.update_layout(layout)
                
                st.plotly_chart(fig, use_container_width=True)
    
    # ファイル保存セクション（処理済みデータがある場合）
    if st.session_state.get('processed_data'):
        st.divider()
        st.subheader("📥 処理結果のダウンロード")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**個別ファイル**")
            for name in st.session_state.processed_data.keys():
                data = st.session_state.processed_data[name]
                csv = data.to_csv(index=False, encoding='shift_jis')
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"{name}_ana_{timestamp}.csv"
                
                st.download_button(
                    label=f"⬇️ {file_name}",
                    data=csv.encode('shift_jis'),
                    file_name=file_name,
                    mime="text/csv",
                    key=f"download_batch_{name}"
                )