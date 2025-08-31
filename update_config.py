#!/usr/bin/env python3
"""
固定パラメータ設定ファイルの更新ツール
コマンドラインから簡単に設定値を変更できます
"""

import yaml
import argparse
from pathlib import Path
import sys

def load_config(config_path='config/fixed_parameters.yaml'):
    """設定ファイルを読み込む"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_config(config, config_path='config/fixed_parameters.yaml'):
    """設定ファイルを保存"""
    # 既存ファイルのバックアップ
    backup_path = Path(config_path).with_suffix('.yaml.bak')
    if Path(config_path).exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            backup_content = f.read()
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(backup_content)
        print(f"バックアップを作成: {backup_path}")
    
    # 新しい設定を保存
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    print(f"設定を更新: {config_path}")

def update_value(config, path, value):
    """ネストした辞書の値を更新"""
    keys = path.split('.')
    current = config
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    # 型を自動判定
    try:
        # 数値の場合
        if '.' in str(value):
            value = float(value)
        else:
            value = int(value)
    except ValueError:
        # 文字列のまま
        pass
    
    current[keys[-1]] = value
    return config

def show_current_values(config):
    """現在の設定値を表示"""
    print("\n現在の設定値:")
    print("="*60)
    
    print("\n【LMR座標計算パラメータ】")
    lmr = config['lmr_coordinates']
    print(f"  基準距離: {lmr['reference_distance']}m")
    print(f"  方向角度: {lmr['direction_angle']}°")
    
    print("\n【基準座標】")
    for side in ['L', 'M', 'R']:
        coords = lmr['reference_coordinates'][side]
        print(f"  {side}側: X={coords['X']}, Y={coords['Y']}")
    
    print("\n【Z標高】")
    z_elev = config['z_elevations']
    for side in ['L', 'M', 'R']:
        print(f"  {side}側: {z_elev[side]}m")
    
    print("\n【測点計算パラメータ】")
    survey = config['survey_point']
    ref = survey['reference_point']
    print(f"  基準測点: {ref['C']}+{ref['E']}")
    print(f"  変換係数: {survey['conversion_factor']}")

def main():
    parser = argparse.ArgumentParser(description='固定パラメータ設定を更新')
    parser.add_argument('--show', action='store_true', help='現在の設定を表示')
    parser.add_argument('--set', nargs=2, metavar=('PATH', 'VALUE'), 
                       help='設定値を更新 (例: --set lmr_coordinates.reference_distance 968)')
    parser.add_argument('--config', default='config/fixed_parameters.yaml', 
                       help='設定ファイルのパス')
    
    args = parser.parse_args()
    
    # 設定を読み込む
    config = load_config(args.config)
    
    if args.show or (not args.set):
        # 現在の値を表示
        show_current_values(config)
    
    if args.set:
        # 値を更新
        path, value = args.set
        print(f"\n更新: {path} = {value}")
        config = update_value(config, path, value)
        save_config(config, args.config)
        
        # 更新後の値を表示
        print("\n更新後:")
        show_current_values(config)

if __name__ == '__main__':
    main()