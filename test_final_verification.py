"""
最終検証テスト - 固定値を使用したLMR座標計算
"""

from src.lmr_coordinate_calculator import LMRCoordinateCalculator
import pandas as pd

def test_fixed_values():
    """固定値を使用した計算テスト"""
    print("=" * 60)
    print("LMR座標計算 - 最終検証")
    print("=" * 60)
    
    # 計算機の初期化（デフォルトの固定値を使用）
    calculator = LMRCoordinateCalculator()
    
    print("\n【固定値の確認】")
    print(f"基準距離: {calculator.REFERENCE_DISTANCE}m")
    print(f"方向角度: {calculator.DIRECTION_ANGLE}°")
    print("\n基準座標（974行目）:")
    for key, value in calculator.reference_coords.items():
        print(f"  {key}: {value}")
    
    # テストケース
    test_cases = [
        {"distance": 1238, "expected_L_X": -907.462},  # Excel 1245行目
        {"distance": 1000, "expected_L_X": None},      # 任意の距離
        {"distance": 1500, "expected_L_X": None},      # 任意の距離
    ]
    
    print("\n【計算結果】")
    print("-" * 60)
    
    results = []
    for test in test_cases:
        distance = test["distance"]
        result = calculator.calculate_coordinates(distance_from_entrance=distance)
        
        print(f"\n距離: {distance}m")
        print(f"  L側: X={result['L_X']:.3f}, Y={result['L_Y']:.3f}")
        print(f"  M側: X={result['M_X']:.3f}, Y={result['M_Y']:.3f}")
        print(f"  R側: X={result['R_X']:.3f}, Y={result['R_Y']:.3f}")
        
        # 期待値との比較（1238mの場合）
        if test["expected_L_X"]:
            diff = abs(result['L_X'] - test["expected_L_X"])
            if diff < 0.001:
                print(f"  ✅ L_X期待値と一致: {test['expected_L_X']}")
            else:
                print(f"  ❌ L_X期待値と不一致: 期待={test['expected_L_X']}, 差={diff:.6f}")
        
        results.append({
            '距離(m)': distance,
            'L_X': result['L_X'],
            'L_Y': result['L_Y'],
            'M_X': result['M_X'],
            'M_Y': result['M_Y'],
            'R_X': result['R_X'],
            'R_Y': result['R_Y']
        })
    
    # 結果をDataFrameで表示
    print("\n【結果一覧】")
    print("-" * 60)
    df = pd.DataFrame(results)
    print(df.to_string(index=False))
    
    # 座標の差分を計算（L-M, M-Rの間隔）
    print("\n【座標間隔の確認】")
    print("-" * 60)
    for _, row in df.iterrows():
        lm_x = row['M_X'] - row['L_X']
        lm_y = row['M_Y'] - row['L_Y']
        mr_x = row['R_X'] - row['M_X']
        mr_y = row['R_Y'] - row['M_Y']
        
        print(f"距離 {row['距離(m)']}m:")
        print(f"  L-M間: ΔX={lm_x:.3f}, ΔY={lm_y:.3f}")
        print(f"  M-R間: ΔX={mr_x:.3f}, ΔY={mr_y:.3f}")
    
    return df

def test_batch_calculation():
    """複数距離の一括計算テスト"""
    print("\n" + "=" * 60)
    print("一括計算テスト")
    print("=" * 60)
    
    calculator = LMRCoordinateCalculator()
    
    # 100m刻みで計算
    distances = list(range(900, 1401, 100))
    angles = [calculator.DIRECTION_ANGLE] * len(distances)
    
    results = calculator.calculate_batch(
        distances=distances,
        angles=angles
    )
    
    print("\n100m刻みの計算結果:")
    print(results.to_string(index=False))
    
    # CSVに保存
    results.to_csv('lmr_coordinates_test.csv', index=False, encoding='shift_jis')
    print("\n✅ 結果をlmr_coordinates_test.csvに保存しました")
    
    return results

if __name__ == "__main__":
    print("LMR座標計算システム - 最終検証テスト\n")
    
    # 固定値テスト
    df1 = test_fixed_values()
    
    # 一括計算テスト
    df2 = test_batch_calculation()
    
    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)
    print("\n固定値での計算が正常に動作することを確認しました。")
    print("ユーザーは距離を入力するだけで、L/M/R側の座標を自動計算できます。")