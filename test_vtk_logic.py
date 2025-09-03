#!/usr/bin/env python3

"""VTKファイル名生成ロジックのテスト（依存関係なし）"""

def generate_vtk_filename(csv_file: str) -> str:
    """VTKファイル名生成のロジック確認用"""
    import os
    
    base = os.path.basename(csv_file)
    name, _ = os.path.splitext(base)
    
    # デバッグ用: ファイル名を出力
    print(f"[DEBUG] Input csv_file: {csv_file}")
    print(f"[DEBUG] Base name: {base}")
    print(f"[DEBUG] Name without extension: {name}")
    
    # LMRタイプを簡易検出
    lmr_type = "X"
    if '_L' in name.upper():
        lmr_type = "L"
    elif '_M' in name.upper():
        lmr_type = "M"
    elif '_R' in name.upper():
        lmr_type = "R"
    
    # 日付文字列を生成
    date_str = "00.00.00"
    
    # アンダースコアで分割
    parts = name.split('_')
    print(f"[DEBUG] Parts after split: {parts}")
    
    # YYYY_MM_DD_HH_MM_SS_L 形式を想定
    if len(parts) >= 3:
        try:
            # 最初の3つの要素が年月日
            year = parts[0]
            month = parts[1]
            day = parts[2]
            
            print(f"[DEBUG] Year: {year}, Month: {month}, Day: {day}")
            
            # 数値として妥当かチェック
            if (len(year) == 4 and year.isdigit() and 
                month.isdigit() and day.isdigit() and
                1 <= int(month) <= 12 and 1 <= int(day) <= 31):
                # YY.MM.DD形式に変換
                date_str = f"{year[-2:]}.{month.zfill(2)}.{day.zfill(2)}"
                print(f"[DEBUG] Date string generated: {date_str}")
            else:
                print(f"[DEBUG] Date validation failed")
        except Exception as e:
            print(f"[DEBUG] Exception in date parsing: {e}")
    else:
        print(f"[DEBUG] Not enough parts: {len(parts)} < 3")
    
    result = f"Drill-{lmr_type}_ana_{date_str}.vtk"
    print(f"[DEBUG] Final VTK filename: {result}")
    return result

def test_vtk_filename_generation():
    """VTKファイル名生成のテスト"""
    
    # テストケース
    test_cases = [
        ("2025_08_27_07_24_47_L.csv", "Drill-L_ana_25.08.27.vtk"),
        ("2025_08_27_07_24_47_M.csv", "Drill-M_ana_25.08.27.vtk"),
        ("2025_08_27_07_24_47_R.csv", "Drill-R_ana_25.08.27.vtk"),
        ("2025_08_27_07_24_47_L_processed.csv", "Drill-L_ana_25.08.27.vtk"),
        ("L_processed", "Drill-L_ana_00.00.00.vtk"),  # 古い形式（日付情報なし）
    ]
    
    print("=== VTKファイル名生成ロジックテスト ===\n")
    
    for input_file, expected_output in test_cases:
        print(f"\n--- テスト: {input_file} ---")
        result = generate_vtk_filename(input_file)
        status = "✅ OK" if result == expected_output else "❌ NG"
        print(f"\n{status}")
        print(f"期待値: {expected_output}")
        print(f"実際値: {result}")
        print("-" * 40)

if __name__ == "__main__":
    test_vtk_filename_generation()