# 利用可能なMCPサーバー一覧

## 現在の環境で有効なMCPサーバー

### 1. Codesign MCP
- **状態**: ✅ 有効
- **機能**: コード署名機能
- **利用可能なツール**: `mcp__codesign__sign_file`

---

## 公式リファレンスMCPサーバー

Model Context Protocol運営グループが管理する公式サーバー:

### 1. Everything
- **機能**: プロンプト、リソース、ツールを含むリファレンス/テストサーバー

### 2. Fetch
- **機能**: Webコンテンツの取得と変換（LLM効率的な利用向け）

### 3. Filesystem
- **機能**: 設定可能なアクセス制御による安全なファイル操作

### 4. Git
- **機能**: Gitリポジトリの読み取り、検索、操作ツール

### 5. Memory
- **機能**: ナレッジグラフベースの永続的メモリシステム

### 6. Sequential Thinking
- **機能**: 思考シーケンスによる動的・反射的問題解決

### 7. Time
- **機能**: 時刻・タイムゾーン変換機能

---

## カテゴリ別コミュニティMCPサーバー

### 開発・バージョン管理

#### GitHub MCP Server
- リポジトリ管理
- コミット、ブランチ、プルリクエスト、Issue管理

#### GitLab MCP Server
- CI/CDパイプライン監視
- マージリクエスト管理
- コードレビュー

---

### データベース・データ管理

#### PostgreSQL MCP Server
- 自然言語でのデータベースクエリ

#### ClickHouse MCP Server
- ClickHouseデータベースサーバーへのクエリ

#### Pinecone MCP Server
- ベクトルデータベースアクセス

#### Excel MCP Server
- Excelファイルの作成、読み取り、変更

---

### クラウド・生産性ツール

#### Google Drive MCP Server
- クラウドドキュメントの検索、要約、整理

#### Slack MCP Server
- チームコミュニケーションと通知の自動化

#### Notion MCP Server
- Notion統合による生産性向上

#### Airtable MCP Server
- Airtableデータベースへの読み書きアクセス

#### Zapier MCP Server
- 数千のアプリとClaudeを接続

---

### API・ドキュメント

#### Apidog MCP Server
- OpenAPI/Swaggerサポート
- リアルタイムAPIドキュメント

#### Stripe MCP Server
- Stripe API統合（関数呼び出し対応）

#### Sentry MCP Server
- エラートラッキングとパフォーマンス監視

#### Context7
- ソースリポジトリから直接リアルタイムドキュメントを取得

---

### デザイン・コード生成

#### Figma MCP Server
- デザインからコードへのワークフロー
- アクセシビリティツリーを通じたFigmaデザインへの構造化アクセス

---

### 自動化・スクリプト

#### Desktop Commander
- ターミナルコマンド実行
- アプリケーション起動
- ファイル操作の自動化

#### Puppeteer MCP Server
- Web自動インタラクション

#### Browser-use MCP Server
- Webブラウザ制御
- 自動インタラクションとデータ抽出

#### Rube MCP Server
- 500以上のビジネス・生産性アプリケーションへのアクセス

---

### インフラストラクチャ

#### Oracle Cloud Infrastructure (OCI) MCP Server
- OCIリソースとのインタラクション

#### GCP MCP Server
- Google Cloud Platform統合（コミュニティメンテナンス）

---

## MCPサーバーの管理コマンド

```bash
# 新しいMCPサーバーを追加
claude mcp add [name] --scope user

# インストール済みMCPサーバーを一覧表示
claude mcp list

# MCPサーバーを削除
claude mcp remove [name]

# サーバー接続をテスト
claude mcp get [name]
```

**注**: 現在の環境では `ENABLE_MCP_CLI=false` のため、CLIコマンドは使用できません。

---

## MCPサーバーの検索

最新の利用可能なMCPサーバーの完全なリストは以下で確認できます:

- **MCP Registry** - 公式レジストリ (registry.modelcontextprotocol.io)
- **Community Directories** - mcp.so, claudemcp.com, mcpcat.io（キュレーションコレクション）
- **GitHub Repository** - github.com/modelcontextprotocol/servers（リファレンス実装）
- **Smithery.ai** - MCPサーバーのコミュニティリポジトリ

---

## 市場の成長

MCPエコシステムは急速に拡大しており、サーバーダウンロード数は2024年11月の10万未満から2025年4月には800万に成長し、利用可能なツールと統合の強い採用と成長を示しています。

---

*最終更新: 2025年12月*
