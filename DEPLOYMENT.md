# Streamlit Cloud デプロイメントガイド

## 🚀 デプロイ手順

### 1. ファイルをGitHubにプッシュ

```bash
git add requirements.txt packages.txt .streamlit/config.toml
git commit -m "Fix Streamlit Cloud deployment: Remove VTK dependency"
git push
```

### 2. Streamlit Cloudで再デプロイ

1. [Streamlit Cloud](https://share.streamlit.io/) にアクセス
2. 「Manage App」をクリック
3. 「Reboot」ボタンをクリック
4. デプロイが完了するまで待機（通常2-5分）

## 📋 現在の設定

### VTKについて

**重要**: VTKは現在 `requirements.txt` でコメントアウトされています。

- **理由**: Streamlit Cloudでは、VTKのシステム依存関係が複雑でインストールに失敗することが多い
- **影響**: VTKファイル生成機能が使用できません（警告メッセージが表示されます）
- **代替案**: 
  - Plotlyによる3D可視化は引き続き使用可能
  - ローカル環境では `pip install vtk` でVTK機能を有効化できます

### ローカル開発でVTKを使用する場合

```bash
pip install vtk>=9.2.6
```

## 🔧 トラブルシューティング

### デプロイが失敗する場合

1. **最小限のrequirements.txtを試す**:
   ```bash
   cp requirements-minimal.txt requirements.txt
   git add requirements.txt
   git commit -m "Use minimal requirements"
   git push
   ```

2. **ログを確認**:
   - Streamlit Cloud → Manage App → Logs
   - エラーメッセージを確認して、問題のあるパッケージを特定

3. **Python バージョンを確認**:
   - `.streamlit/config.toml` でPythonバージョンを指定可能
   - 推奨: Python 3.9 または 3.10

### よくあるエラー

| エラー | 原因 | 解決策 |
|--------|------|--------|
| `Error installing requirements` | パッケージの依存関係の問題 | `requirements-minimal.txt` を使用 |
| `ModuleNotFoundError: No module named 'vtk'` | VTKがインストールされていない | 正常（VTKはオプショナル） |
| メモリ不足 | 大きなファイルの処理 | データサイズを制限 |

## 📦 含まれているファイル

- `requirements.txt`: 本番環境用の依存関係（VTK無効）
- `requirements-minimal.txt`: 最小限の依存関係（緊急時用）
- `packages.txt`: システムレベルの依存関係（現在は空）
- `.streamlit/config.toml`: Streamlit設定

## 🎯 次のステップ

デプロイが成功したら:

1. ✅ アプリが正常に起動することを確認
2. ✅ データアップロード機能をテスト
3. ✅ ノイズ除去・サンプリング機能をテスト
4. ⚠️ VTK生成機能は警告が表示されることを確認（期待される動作）

## 💡 VTKを有効化したい場合

Streamlit Cloud以外のプラットフォーム（Heroku、AWS、GCP等）では、VTKが正常に動作する可能性があります。

または、VTKをWebAssembly版（vtk-js）に置き換えることも検討できます。
