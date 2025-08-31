# 削孔検層データ処理システム

トンネル工事における削孔検層データ（穿孔エネルギー値）の可視化・解析システムです。
L側（左）、M側（中央/天端）、R側（右）の3方向の削孔データを処理し、3D座標への変換やVTKファイル生成を行います。

## 主な機能

### 1. データ可視化
- 複数CSVファイルの一括読み込み
- L/M/R別のグラフ表示
- インタラクティブなPlotlyグラフ

### 2. ノイズ除去
- LOWESS（局所重み付き回帰）によるスムージング
- スパイクノイズの自動除去
- 処理前後の比較表示

### 3. VTKファイル生成
- 削孔データを3D座標に変換
- ParaView対応のVTKファイル出力
- LMR座標計算の自動化

### 4. 座標計算機能
- 測点から坑口からの距離を自動計算
- トンネル座標系での3D位置算出
- 固定パラメータの設定ファイル管理

## インストール

### 必要要件
- Python 3.8以上
- 仮想環境の使用を推奨

### セットアップ
```bash
# リポジトリのクローン
git clone https://github.com/dobocreate/report_drill_mitsui.git
cd report_drill_mitsui

# 仮想環境の作成と有効化
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存パッケージのインストール
pip install -r requirements.txt
```

## 使用方法

### アプリケーションの起動
```bash
python -m streamlit run app.py
```

ブラウザが自動的に開き、`http://localhost:8501`でアプリケーションが表示されます。

### 基本的な使用手順

1. **データ読み込み**
   - `data/`フォルダにCSVファイルを配置
   - ファイル名に`L`、`M`、`R`を含めることで自動識別

2. **ノイズ除去**
   - 「ノイズ除去」タブでパラメータ調整
   - Window幅とPolynomial次数を設定
   - 「ノイズ除去実行」ボタンをクリック

3. **VTKファイル生成**
   - 「VTK生成」タブで坑口からの距離を入力
   - 測点（例：250+11）または距離（m）を指定
   - 生成されたVTKファイルをダウンロード

## 設定ファイル

`config/fixed_parameters.yaml`で以下の固定値を管理：

```yaml
lmr_coordinates:
  reference_distance: 967      # 基準距離（m）
  direction_angle: 65.588      # 掘進方向角度（度）
  reference_coordinates:       # 基準座標（測地座標系）
    L:
      X: -660689.7596
      Y: 733147.0996
    M:
      X: -658622.871
      Y: 737699.9102
    R:
      X: -656556.8108
      Y: 742253.072

z_elevations:
  L: 17.3  # L側のZ標高（m）
  M: 21.3  # M側（天端）のZ標高（m）
  R: 17.3  # R側のZ標高（m）

survey_point:
  reference_point:
    C: 255  # 基準測点（主番号）
    E: 4    # 基準測点（小数部）
```

設定を変更した場合は、アプリケーションを再起動してください。

## データ形式

### 入力CSVファイル
以下の列を含むCSV形式（Shift-JIS エンコーディング）：
- `穿孔長`: 削孔の深さ（m）
- `穿孔エネルギー`: エネルギー値
- `Lowess_Trend`: スムージング後の値（オプション）

### 出力ファイル
- **VTKファイル**: ParaView等で3D表示可能
- **3D座標CSV**: X, Y, Z座標とエネルギー値

## プロジェクト構造

```
report_drill_mitsui/
├── app.py                    # メインアプリケーション
├── config/
│   └── fixed_parameters.yaml # 固定パラメータ設定
├── src/
│   ├── config_loader.py      # 設定ファイル読み込み
│   ├── data_loader.py        # データ読み込み
│   ├── data_processor.py     # データ処理
│   ├── lmr_coordinate_calculator.py  # LMR座標計算
│   ├── noise_remover.py      # ノイズ除去
│   ├── plotly_visualizer.py  # グラフ表示
│   ├── survey_point_calculator.py    # 測点計算
│   └── vtk_converter.py      # VTK変換
├── data/                     # 入力データフォルダ
├── output/                   # 出力ファイルフォルダ
└── requirements.txt          # 依存パッケージ

```

## トラブルシューティング

### VTKライブラリのエラー
```bash
# VTKライブラリのインストール
pip install vtk
```

### メモリ不足エラー
大量のデータを処理する場合は、サンプリング間隔を調整してください。

### 文字コードエラー
CSVファイルはShift-JISエンコーディングで保存してください。

## ライセンス

このプロジェクトは内部使用を目的としています。

## 開発者

- 開発: dobocreate
- 連絡先: [GitHub Issues](https://github.com/dobocreate/report_drill_mitsui/issues)

## 更新履歴

- 2024-08-31: 初版リリース
  - VTK生成機能実装
  - 測点から距離の自動計算機能追加
  - 設定ファイル管理システム実装