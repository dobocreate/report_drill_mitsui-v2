"""
LMR座標計算機能のテストスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.lmr_coordinate_calculator import LMRCoordinateCalculator
import pandas as pd

def test_calculation_with_excel_values():
    """Excelの実際の値を使用して計算をテスト"""
    print("=" * 50)
    print("LMR座標計算テスト")
    print("=" * 50)
    
    # 974行目の基準座標（Excelから読み取った値を仮定）
    reference_coords = {
        'Q': -1000.0,  # 仮の値
        'R': 800.0,     # 仮の値
        'S': -998.0,    # 仮の値
        'T': 804.5,     # 仮の値
        'U': -996.0,    # 仮の値
        'V': 809.0      # 仮の値
    }
    
    # 計算機を初期化
    calculator = LMRCoordinateCalculator(reference_coords=reference_coords)
    
    # 1245行目のテストケース
    print("\n[テストケース] 1245行目の座標計算")
    print("-" * 30)
    
    # I1245の値とW1245の値
    distance = 271.0  # トンネル坑口からの距離
    angle = 65.588    # 向き（角度）
    ref_distance = 200.0  # I974の値（仮）
    
    # 座標計算
    result = calculator.calculate_coordinates(
        distance_from_entrance=distance,
        direction_angle=angle,
        reference_distance=ref_distance
    )
    
    print(f"入力値:")
    print(f"  距離 (I列): {distance} m")
    print(f"  角度 (W列): {angle}°")
    print(f"  基準距離: {ref_distance} m")
    
    print(f"\n計算結果:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    # 期待値との比較
    expected = {
        'L_X': -907.462,
        'L_Y': 845.15,
        'M_X': -905.395,
        'M_Y': 849.703,
        'R_X': -903.329,
        'R_Y': 854.256
    }
    
    print(f"\n期待値（Excel 1245行目）:")
    for key in ['L_X', 'L_Y', 'M_X', 'M_Y', 'R_X', 'R_Y']:
        print(f"  {key}: {expected[key]}")
    
    # 検証
    is_valid = calculator.validate_calculation(expected, result)
    print(f"\n検証結果: {'✅ 一致' if is_valid else '❌ 不一致'}")
    
    return is_valid

def test_batch_calculation():
    """複数測点の一括計算テスト"""
    print("\n" + "=" * 50)
    print("複数測点の一括計算テスト")
    print("=" * 50)
    
    # 仮の基準座標
    calculator = LMRCoordinateCalculator()
    calculator.reference_coords = {
        'Q': -1000.0, 'R': 800.0,
        'S': -998.0, 'T': 804.5,
        'U': -996.0, 'V': 809.0
    }
    
    # テストデータ
    distances = [250.0, 260.0, 270.0, 280.0, 290.0]
    angles = [65.588] * 5  # 同じ角度を使用
    
    # 一括計算
    results = calculator.calculate_batch(
        distances=distances,
        angles=angles,
        reference_distance=200.0
    )
    
    print("\n計算結果:")
    print(results.to_string())
    
    return results

def test_excel_loading():
    """Excelファイルからの読み込みテスト"""
    print("\n" + "=" * 50)
    print("Excelファイル読み込みテスト")
    print("=" * 50)
    
    excel_path = "data/江川トンネル進行表.xlsx"
    
    if os.path.exists(excel_path):
        try:
            calculator = LMRCoordinateCalculator(reference_point=974)
            calculator.load_reference_from_excel(excel_path)
            
            print(f"✅ Excelファイルから基準座標を読み込みました")
            print(f"基準座標（974行目）:")
            for key, value in calculator.reference_coords.items():
                print(f"  {key}: {value}")
            
            # 実際の値で計算
            print("\n実際の値で1245行目を計算:")
            
            # Excelから実際のI974とI1245の値を読み取る必要がある
            import openpyxl
            wb = openpyxl.load_workbook(excel_path, data_only=True)
            sheet = wb.active
            
            i_974 = sheet['I974'].value or 0
            i_1245 = sheet['I1245'].value or 271.0
            w_1245 = sheet['W1245'].value or 65.588
            
            wb.close()
            
            result = calculator.calculate_coordinates(
                distance_from_entrance=i_1245,
                direction_angle=w_1245,
                reference_distance=i_974
            )
            
            print(f"  I974: {i_974}")
            print(f"  I1245: {i_1245}")
            print(f"  W1245: {w_1245}")
            print(f"\n計算結果:")
            for key, value in result.items():
                print(f"  {key}: {value}")
            
            # 期待値と比較
            expected = {
                'L_X': -907.462,
                'L_Y': 845.15,
                'M_X': -905.395,
                'M_Y': 849.703,
                'R_X': -903.329,
                'R_Y': 854.256
            }
            
            print(f"\n期待値との差:")
            for key in ['L_X', 'L_Y', 'M_X', 'M_Y', 'R_X', 'R_Y']:
                diff = abs(result[key] - expected[key])
                status = "✅" if diff < 0.001 else "❌"
                print(f"  {key}: {diff:.6f} {status}")
            
            return True
            
        except Exception as e:
            print(f"❌ エラー: {str(e)}")
            return False
    else:
        print(f"⚠️ Excelファイルが見つかりません: {excel_path}")
        return False

if __name__ == "__main__":
    # テスト実行
    print("LMR座標計算機能のテストを開始します...\n")
    
    # 1. 基本計算テスト
    test_calculation_with_excel_values()
    
    # 2. 一括計算テスト
    test_batch_calculation()
    
    # 3. Excel読み込みテスト
    test_excel_loading()
    
    print("\n" + "=" * 50)
    print("テスト完了")
    print("=" * 50)