#!/usr/bin/env python3

"""VTKファイル名生成のテストスクリプト"""

from src.vtk_converter import VTKConverter

def test_vtk_filename_generation():
    """VTKファイル名生成のテスト"""
    converter = VTKConverter()
    
    # テストケース
    test_cases = [
        ("2025_08_27_07_24_47_L.csv", "Drill-L_ana_25.08.27.vtk"),
        ("2025_08_27_07_24_47_M.csv", "Drill-M_ana_25.08.27.vtk"),
        ("2025_08_27_07_24_47_R.csv", "Drill-R_ana_25.08.27.vtk"),
        ("2025_08_27_07_24_47_L_processed.csv", "Drill-L_ana_25.08.27.vtk"),
        ("L_processed", "Drill-L_ana_00.00.00.vtk"),  # 古い形式（日付情報なし）
    ]
    
    print("=== VTKファイル名生成テスト ===\n")
    
    for input_file, expected_output in test_cases:
        result = converter.generate_vtk_filename(input_file)
        status = "✅" if result == expected_output else "❌"
        print(f"{status} 入力: {input_file}")
        print(f"   期待: {expected_output}")
        print(f"   結果: {result}")
        print()

if __name__ == "__main__":
    test_vtk_filename_generation()