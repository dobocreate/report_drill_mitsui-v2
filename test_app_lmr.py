"""
Streamlit app.pyのLMR座標計算部分のテスト
"""

from src.lmr_coordinate_calculator import LMRCoordinateCalculator

def test_app_lmr_calculation():
    """app.pyのLMR座標計算ロジックをテスト"""
    
    # app.pyと同じ初期化
    calculator = LMRCoordinateCalculator()
    
    # テストケース: 距離1238m（Excelの1245行目と同じ）
    distance = 1238.0
    
    # app.pyと同じ計算方法（修正後）
    # reference_distanceを指定しない（デフォルト値967を使用）
    result = calculator.calculate_coordinates(
        distance_from_entrance=distance
    )
    
    print("=" * 60)
    print("Streamlit app.py LMR座標計算テスト")
    print("=" * 60)
    print(f"\n入力距離: {distance}m")
    print(f"\n使用される固定値:")
    print(f"  基準距離: {calculator.REFERENCE_DISTANCE}m")
    print(f"  方向角度: {calculator.DIRECTION_ANGLE}°")
    
    print(f"\n計算結果:")
    print(f"  L側: X={result['L_X']:.3f}, Y={result['L_Y']:.3f}")
    print(f"  M側: X={result['M_X']:.3f}, Y={result['M_Y']:.3f}")
    print(f"  R側: X={result['R_X']:.3f}, Y={result['R_Y']:.3f}")
    
    # 期待値との比較
    expected_L_X = -907.462
    diff = abs(result['L_X'] - expected_L_X)
    
    print(f"\n検証結果:")
    if diff < 0.001:
        print(f"  ✅ L_X期待値と一致: {expected_L_X}")
        print(f"  統合版（app.py）のLMR座標計算は正常に動作しています！")
        return True
    else:
        print(f"  ❌ L_X期待値と不一致")
        print(f"     期待値: {expected_L_X}")
        print(f"     計算値: {result['L_X']}")
        print(f"     差: {diff:.6f}")
        return False

if __name__ == "__main__":
    success = test_app_lmr_calculation()
    
    if success:
        print("\n" + "=" * 60)
        print("統合版のテスト成功")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("統合版のテスト失敗 - app.pyの確認が必要です")
        print("=" * 60)
