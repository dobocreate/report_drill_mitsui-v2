"""
アプリケーションの状態管理（ViewModel）
Streamlitのsession_stateを型安全に管理するためのクラスを提供します。
"""

import streamlit as st
from typing import Any, Dict, Optional, List
import pandas as pd
from pathlib import Path

class AppState:
    """アプリケーションのグローバル状態を管理するViewModelクラス"""
    
    # キー定数
    KEY_DATA_LOADED = 'data_loaded'
    KEY_RAW_DATA = 'raw_data'
    KEY_PROCESSED_DATA = 'processed_data'
    KEY_RESAMPLED_DATA = 'resampled_data'
    KEY_STRETCHED_DATA = 'stretched_data'
    KEY_VTK_DATA = 'vtk_data'
    KEY_GENERATED_VTK_FILES = 'generated_vtk_files'
    KEY_HEADER_ROW = 'header_row_value'
    KEY_SAVE_FOLDER = 'save_folder'
    KEY_CURRENT_STEP = 'current_step'
    KEY_PROJECT_DATE = 'project_date'
    KEY_SURVEY_POINT = 'survey_point'
    
    @staticmethod
    def initialize():
        """セッション状態の初期化"""
        if AppState.KEY_DATA_LOADED not in st.session_state:
            st.session_state[AppState.KEY_DATA_LOADED] = False
        if AppState.KEY_PROCESSED_DATA not in st.session_state:
            st.session_state[AppState.KEY_PROCESSED_DATA] = {}
        if AppState.KEY_RESAMPLED_DATA not in st.session_state:
            st.session_state[AppState.KEY_RESAMPLED_DATA] = {}
        if AppState.KEY_STRETCHED_DATA not in st.session_state:
            st.session_state[AppState.KEY_STRETCHED_DATA] = {}
        if AppState.KEY_VTK_DATA not in st.session_state:
            st.session_state[AppState.KEY_VTK_DATA] = None
        if AppState.KEY_HEADER_ROW not in st.session_state:
            st.session_state[AppState.KEY_HEADER_ROW] = 1  # デフォルト: 2行目
        if AppState.KEY_CURRENT_STEP not in st.session_state:
            st.session_state[AppState.KEY_CURRENT_STEP] = 0
            
    @staticmethod
    def get_raw_data() -> Dict[str, pd.DataFrame]:
        """読み込み済み生データを取得"""
        return st.session_state.get(AppState.KEY_RAW_DATA, {})
        
    @staticmethod
    def set_raw_data(data: Dict[str, pd.DataFrame]):
        """生データを設定"""
        st.session_state[AppState.KEY_RAW_DATA] = data
        st.session_state[AppState.KEY_DATA_LOADED] = True
        
    @staticmethod
    def get_stretched_data() -> Dict[str, pd.DataFrame]:
        """拡張済みデータを取得"""
        return st.session_state.get(AppState.KEY_STRETCHED_DATA, {})

    @staticmethod
    def set_stretched_data(data: Dict[str, pd.DataFrame]):
        """拡張済みデータを設定"""
        st.session_state[AppState.KEY_STRETCHED_DATA] = data

    @staticmethod
    def get_processed_data() -> Dict[str, pd.DataFrame]:
        """加工済みデータを取得"""
        return st.session_state.get(AppState.KEY_PROCESSED_DATA, {})
        
    @staticmethod
    def set_processed_data(data: Dict[str, pd.DataFrame]):
        """加工済みデータを設定"""
        st.session_state[AppState.KEY_PROCESSED_DATA] = data
        
    @staticmethod
    def get_resampled_data() -> Dict[str, pd.DataFrame]:
        """リサンプリング済みデータを取得"""
        return st.session_state.get(AppState.KEY_RESAMPLED_DATA, {})
        
    @staticmethod
    def set_resampled_data(data: Dict[str, pd.DataFrame]):
        """リサンプリング済みデータを設定"""
        st.session_state[AppState.KEY_RESAMPLED_DATA] = data

    @staticmethod
    def get_generated_vtk_files() -> Dict[str, Dict[str, str]]:
        """生成されたVTKファイル情報を取得"""
        return st.session_state.get(AppState.KEY_GENERATED_VTK_FILES, {})

    @staticmethod
    def set_generated_vtk_files(files: Dict[str, Dict[str, str]]):
        """生成されたVTKファイル情報を設定"""
        st.session_state[AppState.KEY_GENERATED_VTK_FILES] = files
        
    @staticmethod
    def is_data_loaded() -> bool:
        """データが読み込まれているか確認"""
        return st.session_state.get(AppState.KEY_DATA_LOADED, False)

    @staticmethod
    def get_current_step() -> int:
        """現在のステップインデックスを取得"""
        return st.session_state.get(AppState.KEY_CURRENT_STEP, 0)

    @staticmethod
    def set_current_step(step: int):
        """現在のステップインデックスを設定"""
        st.session_state[AppState.KEY_CURRENT_STEP] = step

    @staticmethod
    def get_project_date():
        """実施日を取得"""
        return st.session_state.get(AppState.KEY_PROJECT_DATE)

    @staticmethod
    def set_project_date(date):
        """実施日を設定"""
        st.session_state[AppState.KEY_PROJECT_DATE] = date

    @staticmethod
    def get_survey_point() -> str:
        """測点を取得"""
        return st.session_state.get(AppState.KEY_SURVEY_POINT, "")

    @staticmethod
    def set_survey_point(point: str):
        """測点を設定"""
        st.session_state[AppState.KEY_SURVEY_POINT] = point
