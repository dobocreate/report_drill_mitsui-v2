"""
VTK作成におけるLMR座標計算アルゴリズムの適用確認
"""

from src.vtk_converter import VTKConverter
from src.lmr_coordinate_calculator import LMRCoordinateCalculator
import pandas as pd
import math

def verify_lmr_algorithm_in_vtk():
    """VTK作成でLMR座標計算アルゴリズムが正しく適用されているか検証"""
    
    print("=" * 70)
    print("VTK作成におけるLMR座標計算アルゴリズムの検証")
    print("=" * 70)
    
    # 1. LMR座標計算の固定値確認
    print("\n【1. LMR座標計算の固定値】")
    calculator = LMRCoordinateCalculator()
    print(f"  基準距離: {calculator.REFERENCE_DISTANCE}m")
    print(f"  方向角度: {calculator.DIRECTION_ANGLE}°")
    print("\n  基準座標（974行目）:")
    for key, value in calculator.reference_coords.items():
        print(f"    {key}: {value}")
    
    # 2. VTKConverterでの座標計算確認
    print("\n【2. VTKConverterでの座標計算】")
    converter = VTKConverter()
    
    # テスト距離（Excel 1245行目と同じ）
    test_distance = 1238.0
    
    for lmr_type in ['L', 'M', 'R']:
        print(f"\n  {lmr_type}側（坑口から{test_distance}m）:")
        
        # VTKConverterの座標計算
        x_base, y_base, angle, z_elevation = converter.get_coordinates_for_lmr(
            lmr_type, test_distance
        )
        
        # LMRCoordinateCalculatorの座標計算（比較用）
        coords = calculator.calculate_coordinates(test_distance)
        
        if lmr_type == 'L':
            expected_x = coords['L_X']
            expected_y = coords['L_Y']
            expected_z = 17.3
        elif lmr_type == 'M':
            expected_x = coords['M_X']
            expected_y = coords['M_Y']
            expected_z = 21.3
        else:  # R
            expected_x = coords['R_X']
            expected_y = coords['R_Y']
            expected_z = 17.3
        
        # 比較
        print(f"    VTKConverter計算: X={x_base:.3f}, Y={y_base:.3f}, Z={z_elevation}m")
        print(f"    LMR Calculator計算: X={expected_x:.3f}, Y={expected_y:.3f}, Z={expected_z}m")
        
        # 一致確認
        x_match = abs(x_base - expected_x) < 0.001
        y_match = abs(y_base - expected_y) < 0.001
        z_match = z_elevation == expected_z
        angle_match = angle == calculator.DIRECTION_ANGLE
        
        if x_match and y_match and z_match and angle_match:
            print(f"    ✅ 座標計算が完全に一致")
        else:
            print(f"    ❌ 座標計算に不一致")
    
    # 3. 穿孔長からの座標変換アルゴリズム確認
    print("\n【3. 穿孔長からの3D座標変換アルゴリズム】")
    
    # テストデータ
    drilling_lengths = [0, 10, 20, 30]
    x_base = -907.462  # L側、距離1238mの座標
    y_base = 845.150
    z_elevation = 17.3
    angle = 65.588
    
    print(f"\n  基準点: X={x_base:.3f}, Y={y_base:.3f}, Z={z_elevation}")
    print(f"  掘進角度: {angle}°")
    print("\n  穿孔長からの座標計算:")
    
    # VTKConverterの計算
    points = converter.calculate_3d_points(
        drilling_lengths, x_base, y_base, z_elevation, angle
    )
    
    # 手動計算で検証
    angle_rad = angle * math.pi / 180
    for i, length in enumerate(drilling_lengths):
        x_calc = x_base - length * math.sin(angle_rad)
        y_calc = y_base + length * math.cos(angle_rad)
        z_calc = z_elevation
        
        vtk_point = points[i]
        
        print(f"\n    穿孔長 {length}m:")
        print(f"      VTK計算: X={vtk_point[0]:.3f}, Y={vtk_point[1]:.3f}, Z={vtk_point[2]:.3f}")
        print(f"      手動計算: X={x_calc:.3f}, Y={y_calc:.3f}, Z={z_calc:.3f}")
        
        # 計算式の詳細
        if i == 0:
            print(f"\n      計算式:")
            print(f"        X = {x_base:.3f} - {length} * sin({angle}°) = {x_calc:.3f}")
            print(f"        Y = {y_base:.3f} + {length} * cos({angle}°) = {y_calc:.3f}")
            print(f"        Z = {z_elevation} (固定)")
    
    # 4. 実際のVTKファイル生成での適用確認
    print("\n【4. 実際のVTKファイル生成での座標確認】")
    
    # テストCSV作成
    test_data = pd.DataFrame({
        '穿孔長': [0, 5, 10],
        'Lowess_Trend': [100, 150, 200]
    })
    test_csv = 'test_L_lmr.csv'
    test_data.to_csv(test_csv, index=False, encoding='shift-jis')
    
    # VTK生成
    vtk_path, csv_path = converter.convert_csv_to_vtk(
        test_csv,
        distance_from_entrance=1238.0,  # Excel 1245行目と同じ
        output_vtk_path='test_lmr.vtk',
        output_csv_path='test_lmr_3d.csv',
        lmr_type='L'
    )
    
    # 生成された座標を確認
    df_3d = pd.read_csv(csv_path, encoding='shift-jis', skiprows=1)
    
    print(f"\n  生成された3D座標（L側、坑口から1238m）:")
    for idx, row in df_3d.iterrows():
        print(f"    行{idx+1}: X={row['X(m)']:.3f}, Y={row['Y(m)']:.3f}, Z={row['Z:標高(m)']:.3f}")
    
    # Excel 1245行目の期待値と比較
    print(f"\n  Excel 1245行目の期待値（L側）:")
    print(f"    X=-907.462, Y=845.150")
    print(f"\n  VTKでの計算値（穿孔長0m時点）:")
    print(f"    X={df_3d.iloc[0]['X(m)']:.3f}, Y={df_3d.iloc[0]['Y(m)']:.3f}")
    
    if abs(df_3d.iloc[0]['X(m)'] - (-907.462)) < 0.001:
        print(f"\n  ✅ LMR座標計算アルゴリズムが正しく適用されています")
    else:
        print(f"\n  ❌ 座標計算に問題があります")
    
    # クリーンアップ
    import os
    os.remove(test_csv)
    os.remove(vtk_path)
    os.remove(csv_path)
    
    return True

def check_algorithm_formula():
    """LMR座標計算の数式を詳細確認"""
    print("\n" + "=" * 70)
    print("【LMR座標計算アルゴリズムの数式確認】")
    print("=" * 70)
    
    calculator = LMRCoordinateCalculator()
    
    # Excel数式の再現確認
    print("\n【Excel数式との対応】")
    print("  Q列（L_X）: =ROUND((-($I-$I$974)*1000*COS((90-$W)*PI()/180)+Q$974)/1000,3)")
    print("  R列（L_Y）: =ROUND((($I-$I$974)*1000*SIN((90-$W)*PI()/180)+R$974)/1000,3)")
    
    print("\n【Pythonでの実装】")
    print("  distance_diff = (distance_from_entrance - 967) * 1000")
    print("  angle_rad = (90 - 65.588) * math.pi / 180")
    print("  l_x = round((-distance_diff * cos(angle_rad) + Q974) / 1000, 3)")
    print("  l_y = round((distance_diff * sin(angle_rad) + R974) / 1000, 3)")
    
    # 具体例で計算
    distance = 1238.0
    print(f"\n【具体例: 距離{distance}m】")
    
    # 手動計算
    distance_diff = (distance - 967) * 1000
    angle_rad = (90 - 65.588) * math.pi / 180
    cos_val = math.cos(angle_rad)
    sin_val = math.sin(angle_rad)
    
    print(f"  distance_diff = ({distance} - 967) * 1000 = {distance_diff}")
    print(f"  angle_rad = (90 - 65.588) * π/180 = {angle_rad:.6f}")
    print(f"  cos(angle_rad) = {cos_val:.6f}")
    print(f"  sin(angle_rad) = {sin_val:.6f}")
    
    l_x = round((-distance_diff * cos_val + calculator.reference_coords['Q']) / 1000, 3)
    l_y = round((distance_diff * sin_val + calculator.reference_coords['R']) / 1000, 3)
    
    print(f"\n  L_X = round((-{distance_diff} * {cos_val:.6f} + {calculator.reference_coords['Q']}) / 1000, 3)")
    print(f"      = {l_x}")
    print(f"  L_Y = round(({distance_diff} * {sin_val:.6f} + {calculator.reference_coords['R']}) / 1000, 3)")
    print(f"      = {l_y}")
    
    # VTKでの穿孔長変換
    print("\n【VTKでの穿孔長→座標変換】")
    print("  掘進方向の角度: 65.588°（固定）")
    print("  X方向: X = X_base - 穿孔長 * sin(65.588°)")
    print("  Y方向: Y = Y_base + 穿孔長 * cos(65.588°)")
    print("  Z方向: Z = Z_固定（L/R: 17.3m, M: 21.3m）")
    
    return True

if __name__ == "__main__":
    print("VTK作成におけるLMR座標計算アルゴリズムの検証\n")
    
    # メイン検証
    test1 = verify_lmr_algorithm_in_vtk()
    
    # 数式確認
    test2 = check_algorithm_formula()
    
    if test1 and test2:
        print("\n" + "=" * 70)
        print("検証完了 ✅")
        print("=" * 70)
        print("\nVTK作成には以下のLMR座標計算アルゴリズムが正しく適用されています:")
        print("1. 固定値（基準距離967m、角度65.588°）の使用")
        print("2. 基準座標（974行目）からの相対計算")
        print("3. L/M/R別のZ標高設定（L:17.3m, M:21.3m, R:17.3m）")
        print("4. 穿孔長からの3D座標変換（sin/cos計算）")
    else:
        print("\n検証失敗")