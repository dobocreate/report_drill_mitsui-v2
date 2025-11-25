"""
測点から坑口からの距離を計算するモジュール
トンネル進行表の計算式を実装
"""

class SurveyPointCalculator:
    """測点から坑口からの距離を計算するクラス"""
    
    # 基準測点（トンネル進行表.xlsx 5行目の値）
    REFERENCE_POINT_C = 255  # C5の値
    REFERENCE_POINT_E = 4    # E5の値
    
    def __init__(self, config_path=None):
        """
        初期化
        
        Args:
            config_path: 設定ファイルのパス（省略時はデフォルト）
        """
        # 設定ファイルから値を読み込む
        try:
            from .config_loader import ConfigLoader
            loader = ConfigLoader(config_path)
            
            # 測点計算パラメータを取得
            survey_params = loader.get_survey_point_parameters()
            ref_point = survey_params['reference_point']
            
            self.REFERENCE_POINT_C = ref_point['C']
            self.REFERENCE_POINT_E = ref_point['E']
            self.CONVERSION_FACTOR = survey_params['conversion_factor']
            
        except (ImportError, FileNotFoundError):
            # 設定ファイルが読めない場合はデフォルト値を使用
            self.REFERENCE_POINT_C = 255
            self.REFERENCE_POINT_E = 4
            self.CONVERSION_FACTOR = 20
        
        # 基準測点の数値を計算
        self.reference_value = self.REFERENCE_POINT_C * self.CONVERSION_FACTOR + self.REFERENCE_POINT_E
        
    def calculate_survey_point_value(self, c_value: float, e_value: float) -> float:
        """
        測点の数値を計算
        
        Args:
            c_value: C列の値（測点の主番号）
            e_value: E列の値（測点の小数部）
            
        Returns:
            測点の数値
        """
        return c_value * self.CONVERSION_FACTOR + e_value
    
    def calculate_distance_from_entrance(self, c_value: float, e_value: float) -> float:
        """
        測点から坑口からの距離を計算
        
        計算式: 坑口からの距離 = 基準測点 - 現在測点
        
        Args:
            c_value: C列の値（測点の主番号）
            e_value: E列の値（測点の小数部）
            
        Returns:
            坑口からの距離（m）
        """
        current_point_value = self.calculate_survey_point_value(c_value, e_value)
        distance = self.reference_value - current_point_value
        return distance
    
    def format_survey_point(self, c_value: float, e_value: float) -> str:
        """
        測点を文字列形式でフォーマット
        
        Args:
            c_value: C列の値
            e_value: E列の値
            
        Returns:
            フォーマットされた測点文字列（例: \"254+19.4\"）
        """
        if e_value == 0:
            return f"{int(c_value)}+0"
        elif e_value == int(e_value):
            return f"{int(c_value)}+{int(e_value)}"
        else:
            return f"{int(c_value)}+{e_value}"
    
    def parse_survey_point(self, survey_point_str: str) -> tuple:
        """
        測点文字列をC値とE値に分解
        
        Args:
            survey_point_str: 測点文字列（例: \"254+19.4\"）
            
        Returns:
            (c_value, e_value)のタプル
            
        Raises:
            ValueError: 不正な測点形式の場合
        """
        if '+' not in survey_point_str:
            raise ValueError(f"不正な測点形式: {survey_point_str}")
        
        parts = survey_point_str.split('+')
        if len(parts) != 2:
            raise ValueError(f"不正な測点形式: {survey_point_str}")
        
        try:
            c_value = float(parts[0])
            e_value = float(parts[1])
            return c_value, e_value
        except ValueError:
            raise ValueError(f"測点の数値変換に失敗: {survey_point_str}")