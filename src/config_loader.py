"""
設定ファイル読み込みモジュール
YAMLファイルから固定パラメータを読み込む
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any

class ConfigLoader:
    """設定ファイル読み込みクラス"""
    
    def __init__(self, config_path: str = None):
        """
        初期化
        
        Args:
            config_path: 設定ファイルのパス（省略時はデフォルトパス）
        """
        if config_path is None:
            # デフォルトパスを設定
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / "config" / "fixed_parameters.yaml"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        YAMLファイルから設定を読み込む
        
        Returns:
            設定辞書
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def get_lmr_parameters(self) -> Dict[str, Any]:
        """
        LMR座標計算パラメータを取得
        
        Returns:
            LMR座標計算パラメータの辞書
        """
        return self.config.get('lmr_coordinates', {})
    
    def get_z_elevations(self) -> Dict[str, float]:
        """
        Z標高設定を取得
        
        Returns:
            Z標高の辞書
        """
        return self.config.get('z_elevations', {})
    
    def get_survey_point_parameters(self) -> Dict[str, Any]:
        """
        測点計算パラメータを取得
        
        Returns:
            測点計算パラメータの辞書
        """
        return self.config.get('survey_point', {})
    
    def get_reference_distance(self) -> float:
        """基準距離を取得"""
        return self.config['lmr_coordinates']['reference_distance']
    
    def get_direction_angle(self) -> float:
        """掘進方向角度を取得"""
        return self.config['lmr_coordinates']['direction_angle']
    
    def get_reference_coordinates(self) -> Dict[str, Dict[str, float]]:
        """基準座標を取得"""
        return self.config['lmr_coordinates']['reference_coordinates']
    
    def reload(self):
        """設定を再読み込み"""
        self.config = self._load_config()
    
    def save_config(self, new_config: Dict[str, Any]):
        """
        設定をファイルに保存
        
        Args:
            new_config: 新しい設定辞書
        """
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(new_config, f, default_flow_style=False, allow_unicode=True)
        
        # 設定を再読み込み
        self.reload()
    
    def update_parameter(self, path: str, value: Any):
        """
        特定のパラメータを更新
        
        Args:
            path: パラメータのパス（例: "lmr_coordinates.reference_distance"）
            value: 新しい値
        """
        keys = path.split('.')
        config = self.config
        
        # ネストした辞書を辿る
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # 値を更新
        config[keys[-1]] = value
        
        # ファイルに保存
        self.save_config(self.config)