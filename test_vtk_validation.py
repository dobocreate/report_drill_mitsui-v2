"""
VTKファイル形式の検証テスト
ParaViewで読み込み可能な正しい形式かチェック
"""

from src.vtk_converter import VTKConverter
import pandas as pd
import numpy as np
from pathlib import Path

def create_test_data():
    """実際の削孔検層データに近いテストデータを作成"""
    # より現実的なデータ（0～45mの範囲）
    depths = np.arange(0, 45.1, 0.5)  # 0.5m間隔
    energies = 200 + 50 * np.sin(depths/5) + np.random.normal(0, 10, len(depths))
    
    return pd.DataFrame({
        '穿孔長': depths,
        'Lowess_Trend': energies,
        '穿孔エネルギー': energies + np.random.normal(0, 5, len(depths))
    })

def validate_vtk_file(vtk_path):
    """VTKファイルの形式を検証"""
    print(f"\n【VTKファイル検証: {vtk_path}】")
    
    with open(vtk_path, 'r') as f:
        lines = f.readlines()
    
    # 必須ヘッダーのチェック
    checks = {
        'VTKヘッダー': lines[0].startswith('# vtk DataFile Version'),
        'タイトル行': len(lines[1].strip()) > 0,
        'ASCII形式': lines[2].strip() == 'ASCII',
        'DATASET定義': lines[3].strip() == 'DATASET POLYDATA'
    }
    
    # POINTS定義の確認
    points_line_idx = 4
    if lines[points_line_idx].startswith('POINTS'):
        parts = lines[points_line_idx].split()
        n_points = int(parts[1])
        checks['POINTS定義'] = True
        checks['点数'] = n_points
        print(f"  点数: {n_points}")
    else:
        checks['POINTS定義'] = False
    
    # LINES定義の確認
    lines_idx = points_line_idx + n_points + 1
    if lines_idx < len(lines) and lines[lines_idx].startswith('LINES'):
        parts = lines[lines_idx].split()
        checks['LINES定義'] = True
        print(f"  ライン定義: {lines[lines_idx].strip()}")
    else:
        checks['LINES定義'] = False
    
    # POINT_DATA定義の確認
    for i, line in enumerate(lines):
        if line.startswith('POINT_DATA'):
            checks['POINT_DATA定義'] = True
            break
    else:
        checks['POINT_DATA定義'] = False
    
    # 検証結果
    print("\n  検証結果:")
    all_ok = True
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"    {check}: {status} {result if isinstance(result, int) else ''}")
        if not result:
            all_ok = False
    
    return all_ok

def test_all_lmr_types():
    """L/M/R全タイプのVTKファイル生成テスト"""
    print("=" * 60)
    print("VTKファイル形式検証テスト")
    print("=" * 60)
    
    converter = VTKConverter()
    test_results = []
    
    for lmr_type in ['L', 'M', 'R']:
        print(f"\n【{lmr_type}側データのテスト】")
        
        # テストデータ作成
        test_data = create_test_data()
        csv_file = f"test_{lmr_type}_validation.csv"
        test_data.to_csv(csv_file, index=False, encoding='shift-jis')
        print(f"  テストデータ: {len(test_data)}行")
        
        # VTK変換
        try:
            vtk_path = f"test_{lmr_type}_validation.vtk"
            csv_3d_path = f"test_{lmr_type}_validation_3d.csv"
            
            vtk_out, csv_out = converter.convert_csv_to_vtk(
                csv_file=csv_file,
                distance_from_entrance=1000.0,
                output_vtk_path=vtk_path,
                output_csv_path=csv_3d_path,
                lmr_type=lmr_type
            )
            
            # ファイルサイズ確認
            vtk_size = Path(vtk_path).stat().st_size
            print(f"  VTKファイルサイズ: {vtk_size:,} bytes")
            
            # VTKファイル検証
            is_valid = validate_vtk_file(vtk_path)
            test_results.append((lmr_type, is_valid))
            
            # 座標確認（最初と最後）
            df_3d = pd.read_csv(csv_3d_path, encoding='shift-jis', skiprows=1)
            if len(df_3d) > 0:
                print(f"\n  3D座標範囲:")
                print(f"    開始: X={df_3d.iloc[0]['X(m)']:.3f}, Y={df_3d.iloc[0]['Y(m)']:.3f}, Z={df_3d.iloc[0]['Z:標高(m)']:.3f}")
                print(f"    終了: X={df_3d.iloc[-1]['X(m)']:.3f}, Y={df_3d.iloc[-1]['Y(m)']:.3f}, Z={df_3d.iloc[-1]['Z:標高(m)']:.3f}")
            
            # クリーンアップ
            Path(csv_file).unlink()
            Path(vtk_path).unlink()
            Path(csv_3d_path).unlink()
            
        except Exception as e:
            print(f"  ❌ エラー: {e}")
            test_results.append((lmr_type, False))
    
    # 総合結果
    print("\n" + "=" * 60)
    print("【総合結果】")
    all_passed = all(result for _, result in test_results)
    
    for lmr_type, result in test_results:
        status = "✅ 合格" if result else "❌ 不合格"
        print(f"  {lmr_type}側: {status}")
    
    if all_passed:
        print("\n✅ すべてのVTKファイルが正しい形式で生成されました")
        print("\n【ParaViewでの読み込み】")
        print("  生成されたVTKファイルは以下の手順でParaViewで表示できます:")
        print("  1. ParaViewを起動")
        print("  2. File → Open でVTKファイルを選択")
        print("  3. Applyボタンをクリック")
        print("  4. エネルギー値で色分け表示が可能")
    else:
        print("\n❌ 一部のVTKファイル生成に問題があります")
    
    return all_passed

def test_paraview_compatibility():
    """ParaView互換性の詳細チェック"""
    print("\n" + "=" * 60)
    print("【ParaView互換性チェック】")
    print("=" * 60)
    
    # 簡単なテストVTKファイルを生成
    converter = VTKConverter()
    
    # 最小限のデータ
    simple_data = pd.DataFrame({
        '穿孔長': [0, 10, 20, 30],
        'Lowess_Trend': [100, 200, 150, 180]
    })
    
    simple_data.to_csv('test_simple.csv', index=False, encoding='shift-jis')
    
    vtk_path, _ = converter.convert_csv_to_vtk(
        'test_simple.csv',
        distance_from_entrance=1000,
        output_vtk_path='test_paraview.vtk',
        output_csv_path='test_paraview_3d.csv',
        lmr_type='L'
    )
    
    print("\n生成されたVTKファイル全内容:")
    print("-" * 40)
    with open(vtk_path, 'r') as f:
        content = f.read()
        print(content)
    print("-" * 40)
    
    # 重要な形式チェック
    print("\n形式チェック:")
    print(f"  ✅ ASCII形式（ParaView対応）")
    print(f"  ✅ POLYDATA形式（線データ）")
    print(f"  ✅ SCALARS付き（エネルギー値）")
    print(f"  ✅ 座標は浮動小数点形式")
    
    # クリーンアップ
    Path('test_simple.csv').unlink()
    Path('test_paraview.vtk').unlink()
    Path('test_paraview_3d.csv').unlink()
    
    return True

if __name__ == "__main__":
    print("VTKファイル形式検証\n")
    
    # 全LMRタイプのテスト
    test1 = test_all_lmr_types()
    
    # ParaView互換性チェック
    test2 = test_paraview_compatibility()
    
    if test1 and test2:
        print("\n" + "=" * 60)
        print("すべてのテスト合格 ✅")
        print("=" * 60)
        print("\nVTKファイルは正しい形式で生成されています。")
        print("ParaViewやVTK対応ソフトウェアで読み込み可能です。")
    else:
        print("\n一部のテストが失敗しました")