import csv
import os
import math  # 追加
import datetime  # タイムスタンプ用モジュール
import tkinter as tk
from tkinter import filedialog, simpledialog  # simpledialogのインポート
import vtk

def generate_vtk_filename(csv_file):
    base = os.path.basename(csv_file)
    name, _ = os.path.splitext(base)
    parts = name.split('_')
    # CSVファイル名中のL,M,Rを取得
    letter = None
    for part in parts:
        if part in ['L', 'M', 'R']:
            letter = part
            break
    if not letter:
        letter = "X"  # 見つからなかった場合のデフォルト
    # 最初の3要素: 年, 月, 日（例: 2025, 03, 20）から "25.03.20" を作成
    if len(parts) >= 3:
        year = parts[0]
        month = parts[1]
        day = parts[2]
        date_str = f"{year[-2:]}.{month}.{day}"
    else:
        date_str = "00.00.00"
    return f"Drill-{letter}_ana_{date_str}.vtk"

def select_csv_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[('CSV Files', '*.csv')])
    if file_path:
        # インポートしたファイル名をターミナルに表示
        print(f"選択されたCSVファイル: {file_path}")
        save_vtk_file(file_path)

def save_computed_csv(original_csv_file, points, energy_values):
    # タイムスタンプを生成
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dir_name = os.path.dirname(original_csv_file)
    base = os.path.basename(original_csv_file)
    name, ext = os.path.splitext(base)
    new_csv_filename = os.path.join(dir_name, f"{name}_{timestamp}.csv")

    with open(new_csv_filename, "w", newline="", encoding="shift-jis") as f:
        writer = csv.writer(f)
        # ヘッダーは確認用にX(m), Y(m), Z:標高(m)と穿孔エネルギーを出力
        writer.writerow(["X(m)", "Y(m)", "Z:標高(m)", "穿孔エネルギー"])
        for (pt, energy) in zip(points, energy_values):
            x, y, z = pt
            writer.writerow([x, y, z, energy])
    print(f'Computed CSV file "{new_csv_filename}" has been created.')

def save_vtk_file(csv_file):
    points = []
    energy_values = []

    with open(csv_file, 'r', newline='', encoding='shift-jis') as file:
        reader = csv.reader(file)
        header = next(reader)  # Read the second row (header)
        # 「穿孔長」と「Lowess_Trend」の列を取得
        f2_index = header.index('穿孔長')
        energy_index = header.index('Lowess_Trend')

        # ユーザーに定数値の入力を求める
        root = tk.Tk()
        root.withdraw()
        x_base = simpledialog.askfloat("X座標入力", "基準となるX座標を入力してください", initialvalue=-656.557)
        if x_base is None:
            print("X座標が入力されなかったため、処理を中断します。")
            return

        y_base = simpledialog.askfloat("Y座標入力", "基準となるY座標を入力してください", initialvalue=742.253)
        if y_base is None:
            print("Y座標が入力されなかったため、処理を中断します。")
            return

        angle = simpledialog.askfloat("角度入力", "角度(度)を入力してください", initialvalue=65.588)
        if angle is None:
            print("角度が入力されなかったため、処理を中断します。")
            return

        z_fixed = simpledialog.askfloat("Z値入力", "Z:標高(m) の値を入力してください", initialvalue=0.0)
        if z_fixed is None:
            print("Z値が入力されなかったため、処理を中断します。")
            return

        for row in reader:
            f2 = float(row[f2_index])
            # X(m) = 基準X座標 - F2 * sin(角度 * π/180)
            x = x_base - f2 * math.sin(angle * math.pi / 180)
            # Y(m) = 基準Y座標 + F2 * cos(角度 * π/180)
            y = y_base + f2 * math.cos(angle * math.pi / 180)
            z = z_fixed  # ユーザーが指定した固定値
            energy = float(row[energy_index])
            points.append((x, y, z))
            energy_values.append(energy)

    if len(points) < 2:
        print('Not enough data points to create lines.')
        return

    # 計算結果を反映したCSVファイルを保存（タイムスタンプ付き）
    save_computed_csv(csv_file, points, energy_values)

    filename_default = generate_vtk_filename(csv_file)
    save_path = filedialog.asksaveasfilename(initialfile=filename_default,
                                             defaultextension='.vtk',
                                             filetypes=[('VTK Files', '*.vtk')])
    if save_path:
        create_vtk_file(save_path, points, energy_values)

def create_vtk_file(save_path, points, energy_values):
    vtk_points = vtk.vtkPoints()
    for point in points:
        vtk_points.InsertNextPoint(point)

    lines = vtk.vtkCellArray()
    line = vtk.vtkPolyLine()
    line.GetPointIds().SetNumberOfIds(len(points))
    for i in range(len(points)):
        line.GetPointIds().SetId(i, i)
    lines.InsertNextCell(line)

    poly_data = vtk.vtkPolyData()
    poly_data.SetPoints(vtk_points)
    poly_data.SetLines(lines)

    energy_array = vtk.vtkDoubleArray()
    energy_array.SetName("Energy")
    for energy in energy_values:
        energy_array.InsertNextValue(energy)
    poly_data.GetPointData().AddArray(energy_array)

    writer = vtk.vtkPolyDataWriter()
    writer.SetFileName(save_path)
    writer.SetInputData(poly_data)
    writer.Write()

    print(f'VTK file "{save_path}" has been created.')

# ファイルを選択するためのウィンドウを表示し、CSVファイルからVTKファイルを作成します
select_csv_file()
