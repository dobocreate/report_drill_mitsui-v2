import os
import tkinter as tk
from tkinter import filedialog
import pandas as pd
import ezdxf

# カスタムダイアログウィンドウを作成して、X軸・Y軸の範囲とスケーリングをまとめて入力させるクラス
class AxisRangeDialog(tk.Toplevel):
    def __init__(self, parent, x_min_init, x_max_init, y_min_init, y_max_init, x_scale_init, y_scale_init, s_interval_init):
        super().__init__(parent)

        self.title("X軸・Y軸の範囲とスケーリング設定")
        
        # ラベルとエントリーフィールド
        tk.Label(self, text="X軸の最小値:").grid(row=0, column=0)
        self.x_min_entry = tk.Entry(self)
        self.x_min_entry.insert(0, str(x_min_init))
        self.x_min_entry.grid(row=0, column=1)
        
        tk.Label(self, text="X軸の最大値:").grid(row=1, column=0)
        self.x_max_entry = tk.Entry(self)
        self.x_max_entry.insert(0, str(x_max_init))
        self.x_max_entry.grid(row=1, column=1)
        
        tk.Label(self, text="Y軸の最小値:").grid(row=2, column=0)
        self.y_min_entry = tk.Entry(self)
        self.y_min_entry.insert(0, str(y_min_init))
        self.y_min_entry.grid(row=2, column=1)
        
        tk.Label(self, text="Y軸の最大値:").grid(row=3, column=0)
        self.y_max_entry = tk.Entry(self)
        self.y_max_entry.insert(0, str(y_max_init))
        self.y_max_entry.grid(row=3, column=1)
        
        # スケーリング値の入力
        tk.Label(self, text="X方向の倍率:").grid(row=4, column=0)
        self.x_scale_entry = tk.Entry(self)
        self.x_scale_entry.insert(0, str(x_scale_init))
        self.x_scale_entry.grid(row=4, column=1)
        
        tk.Label(self, text="Y方向の倍率:").grid(row=5, column=0)
        self.y_scale_entry = tk.Entry(self)
        self.y_scale_entry.insert(0, str(y_scale_init))
        self.y_scale_entry.grid(row=5, column=1)

        tk.Label(self, text="サンプリング間隔:").grid(row=6, column=0)
        self.s_interval_entry = tk.Entry(self)
        self.s_interval_entry.insert(0, str(s_interval_init))
        self.s_interval_entry.grid(row=6, column=1)
        
        # OKボタン
        tk.Button(self, text="OK", command=self.on_ok).grid(row=7, columnspan=2)

        self.result = None

    def on_ok(self):
        # 入力値を取得
        self.result = (
            float(self.x_min_entry.get()),
            float(self.x_max_entry.get()),
            float(self.y_min_entry.get()),
            float(self.y_max_entry.get()),
            float(self.x_scale_entry.get()),  # X方向のスケーリング
            float(self.y_scale_entry.get()),   # Y方向のスケーリング
            float(self.s_interval_entry.get())
        )
        self.destroy()

# ファイル選択ダイアログを表示してCSVファイルを選択する関数
def select_file():
    root = tk.Tk()
    root.withdraw()  # Tkinterのメインウィンドウを非表示にする
    file_path = filedialog.askopenfilename(
        filetypes=[("CSV files", "*.csv")], 
        title="Select a CSV file"
    )
    return file_path

# 軸をプロットする関数
def plot_axis(msp, x_min, x_max, y_min, y_max, x_interval, y_interval, x_scale, y_scale):
    # X軸を描画
    msp.add_line((x_min, 0), (x_max, 0), dxfattribs={'layer': 'X-Axis'})
    
    # X軸の目盛りを線で描画
    for x in range(int(x_min), int(x_max) + 1, int(x_interval)):
        msp.add_line((x, -5 * y_scale), (x, 5 * y_scale), dxfattribs={'layer': 'X-Ticks'})  # 目盛り線の長さもYスケールに基づく

    # Y軸を描画 (X軸の最小値の位置にY軸を描画)
    msp.add_line((x_min, y_min), (x_min, y_max), dxfattribs={'layer': 'Y-Axis'})

    # Y軸の目盛りを線で描画
    for y in range(int(y_min), int(y_max) + 1, int(y_interval)):
        msp.add_line((x_min - 5 * x_scale, y), (x_min + 5 * x_scale, y), dxfattribs={'layer': 'Y-Ticks'})  # 目盛り線の長さもXスケールに基づく

# ダイアログを表示して最小値・最大値を入力させる関数
def get_axis_limits(parent, x_min_init, x_max_init, y_min_init, y_max_init, x_scale_init, y_scale_init, s_interval_init):
    dialog = AxisRangeDialog(parent, x_min_init, x_max_init, y_min_init, y_max_init, x_scale_init, y_scale_init, s_interval_init)
    parent.wait_window(dialog)  # ダイアログが閉じるまで待機
    return dialog.result

# 選択されたCSVファイルからデータを読み込んでDXF形式で保存する関数
def create_dxf_from_csv():
    file_path = select_file()
    
    if file_path:
        # CSVファイルを読み込む
        data = pd.read_csv(file_path, encoding='utf-8')
        
        # NaNの処理: NaNを0に置き換える
        data = data.fillna(0.0)
        
        # 必要な列を取得
        try:
            distance = pd.to_numeric(data['TD'], errors='coerce').fillna(0.0)
            left_shoulder = pd.to_numeric(data['Ene-L'], errors='coerce').fillna(0.0)
            top_section = pd.to_numeric(data['Ene-M'], errors='coerce').fillna(0.0)
            right_shoulder = pd.to_numeric(data['Ene-R'], errors='coerce').fillna(0.0)
        except KeyError as e:
            print(f"エラー: 必要な列がCSVファイルに見つかりませんでした - {e}")
            return

        # 初期値を設定
        x_min_init, x_max_init = distance.min(), distance.max()
        y_min_init, y_max_init = min(left_shoulder.min(), top_section.min(), right_shoulder.min()), max(left_shoulder.max(), top_section.max(), right_shoulder.max())
        
        # ユーザーにX軸・Y軸の範囲とスケーリングを入力させる
        root = tk.Tk()
        root.withdraw()  # Tkinterのメインウィンドウを非表示にする
        axis_limits = get_axis_limits(root, x_min_init, x_max_init, y_min_init, y_max_init=500, x_scale_init=1000, y_scale_init=100, s_interval_init=10)


        if not axis_limits:
            print("軸の範囲入力がキャンセルされました。")
            return
        
        x_min, x_max, y_min, y_max, x_scale, y_scale, s_interval = axis_limits


        # サンプリング間隔
        # s_interval = 10
        sampled_data = data.iloc[::int(s_interval)].reset_index(drop=True)
        
        # サンプリングしたデータを保存
        base, ext = os.path.splitext(file_path)
        sampled_file_path = f"{base}-s{ext}"
        sampled_data.to_csv(sampled_file_path, index=False)
        print(f"サンプリングされたデータが {sampled_file_path} に保存されました。")

        #s_data = pd.read_csv(sampled_file_path, encoding='utf-8')
        s_data = sampled_data
        
        # 必要な列を取得
        try:
            distance = pd.to_numeric(s_data['TD'], errors='coerce').fillna(0.0)
            left_shoulder = pd.to_numeric(s_data['Ene-L'], errors='coerce').fillna(0.0)
            top_section = pd.to_numeric(s_data['Ene-M'], errors='coerce').fillna(0.0)
            right_shoulder = pd.to_numeric(s_data['Ene-R'], errors='coerce').fillna(0.0)
        except KeyError as e:
            print(f"エラー: 必要な列がCSVファイルに見つかりませんでした - {e}")
            return

        
        # DXFファイルの作成
        doc = ezdxf.new(dxfversion='R12')  # DXFバージョンをR12に設定（古いフォーマット）
        msp = doc.modelspace()
        
        # 距離とエネルギー値をプロットする関数（スケーリング適用）
        def plot_dxf(x, y, layer_name):
            if len(x) < 2 or len(y) < 2:
                print(f"エラー: データが不足しています。layer_name={layer_name}")
                return

            for i in range(len(x) - 1):
                # print(i)
                if not pd.isna(x[i]) and not pd.isna(y[i]):
                    # 入力されたスケーリングを使用
                    msp.add_line((x[i] * x_scale, y[i] * y_scale), (x[i+1] * x_scale, y[i+1] * y_scale), dxfattribs={'layer': layer_name})
        
        # 各データをプロット
        plot_dxf(distance, left_shoulder, 'Left Shoulder')
        plot_dxf(distance, top_section, 'Top Section')
        plot_dxf(distance, right_shoulder, 'Right Shoulder')
        
        # 軸をプロット (X軸とY軸)、目盛りもスケーリングに合わせる, x_scale,y_scaleは目盛り線のスケール
        plot_axis(msp, 
                  x_min=x_min * x_scale, x_max=x_max * x_scale, 
                  y_min=y_min * y_scale, y_max=y_max * y_scale, 
                  x_interval=1 * x_scale, y_interval=100 * y_scale, 
                  x_scale=100, y_scale=100)
        
        # DXFファイルとして保存
        output_path = filedialog.asksaveasfilename(
            defaultextension=".dxf", filetypes=[("DXF files", "*.dxf")], title="Save as DXF file"
        )
        if output_path:
            try:
                doc.saveas(output_path)
                print(f"DXFファイルが {output_path} に保存されました。")
            except Exception as e:
                print(f"DXFファイルの保存中にエラーが発生しました: {e}")
        else:
            print("保存がキャンセルされました。")
    else:
        print("ファイルが選択されませんでした。")

# 実行
create_dxf_from_csv()

