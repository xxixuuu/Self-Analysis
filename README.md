# LifeMetrics - プライバシーファースト自己分析AIダッシュボード

<div align="center">

**個人のデジタルフットプリントを統合し、ローカルLLMで分析する完全プライベートなライフログシステム**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Privacy: Local](https://img.shields.io/badge/Privacy-100%25%20Local-green.svg)](/)
[![GDPR: Compliant](https://img.shields.io/badge/GDPR-Compliant-success.svg)](/)

</div>

## 特徴

### 🔒 プライバシーファースト
- **100%ローカルストレージ**: すべてのデータはあなたのマシンに保存
- **外部送信ゼロ**: Ollama使用により、データは一切外部に送信されません
- **完全な管理権**: あなたのデータはあなたのもの
- **GDPR準拠**: データエクスポート・削除機能完備

### 🤖 ローカルAI分析
- **Ollama統合**: llama3.2, mistral, gemma2などのモデルを使用
- **日次サマリー自動生成**: その日の活動を要約
- **感情分析**: ツイート/メールのトーン分析
- **トピック抽出**: 何について考えているかを自動抽出
- **生産性アドバイス**: パーソナライズされた改善提案
- **自然言語クエリ**: 「先週最も生産的だった日は?」などの質問に回答

### 📊 多様なデータソース
- ✅ GitHub (コミット、PR、Issue、スター)
- ✅ Twitter/X (ツイート、いいね、リツイート)
- ✅ Gmail (送受信、ラベル、アーカイブ)
- ✅ Google Calendar (イベント、予定)
- ✅ Slack (メッセージ、リアクション)
- ✅ Spotify (再生履歴、プレイリスト)
- ✅ Fitbit/Apple Health (歩数、睡眠、心拍)
- ✅ 銀行取引 (支出分析)
- ✅ RSS (ブログ購読記録)
- ✅ Toggl/RescueTime (時間追跡)

### 📈 高度な分析機能
- 時系列分析とトレンド検出
- 相関分析 (睡眠時間 vs 生産性など)
- クラスタリング (行動パターンの自動分類)
- 予測モデル (明日の生産性予測)
- 異常検知 (いつもと違う行動パターン)
- ネットワーク分析 (人間関係の可視化)

### 🎨 リッチなビジュアライゼーション
- インタラクティブグラフ (D3.js + Chart.js)
- ヒートマップ (時間帯別活動)
- ネットワークグラフ (人間関係)
- ワードクラウド (頻出単語)
- サンキーダイアグラム (時間配分)
- カスタムレポートビルダー

## 技術スタック

### フロントエンド
- **SvelteKit** + TypeScript
- **TailwindCSS** + DaisyUI
- **D3.js** + Chart.js
- **Vite**

### バックエンド
- **FastAPI** (Python 3.12+)
- **Pandas** + Polars
- **SQLAlchemy** + AsyncPG
- **Ollama** (ローカルLLM)
- **Celery** (データ収集ジョブ)

### データベース
- **PostgreSQL 16** + TimescaleDB
- **Redis** (キャッシュ)
- **DuckDB** (分析用OLAP)
- **MinIO** (S3互換ストレージ)

### 機械学習
- **scikit-learn** (クラスタリング、予測)
- **spaCy** (NLP処理)
- **VADER** (感情分析)
- **transformers** (ローカルモデル)

## クイックスタート

### 前提条件
- Docker & Docker Compose
- Git
- 8GB以上のRAM (Ollama用)

### インストール

1. **リポジトリのクローン**
```bash
git clone https://github.com/yourusername/lifemetrics.git
cd lifemetrics
```

2. **環境変数の設定**
```bash
cp .env.example .env
# .envファイルを編集して必要な設定を行う
```

3. **シークレットキーの生成**
```bash
# Python環境で実行
python -c "import secrets; print(secrets.token_urlsafe(32))"
# 出力された値を.envのSECRET_KEYに設定

# 暗号化キーの生成
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# 出力された値を.envのENCRYPTION_KEYに設定
```

4. **Docker Composeで起動**
```bash
docker-compose up -d
```

5. **Ollamaモデルのダウンロード**
```bash
docker exec -it lifemetrics-ollama ollama pull llama3.2
docker exec -it lifemetrics-ollama ollama pull mistral
```

6. **アクセス**
- フロントエンド: http://localhost:3000
- バックエンドAPI: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- MinIO Console: http://localhost:9001

## データソースの接続

### 1. GitHub

1. [GitHub OAuth App](https://github.com/settings/developers)を作成
2. Callback URL: `http://localhost:3000/auth/github/callback`
3. Client IDとSecretを`.env`に設定
4. ダッシュボードから「Connect GitHub」をクリック

### 2. Google (Gmail, Calendar)

1. [Google Cloud Console](https://console.cloud.google.com/)でプロジェクト作成
2. Gmail API, Calendar APIを有効化
3. OAuth 2.0 認証情報を作成
4. Callback URL: `http://localhost:3000/auth/google/callback`
5. Client IDとSecretを`.env`に設定

### 3. Twitter/X

1. [Twitter Developer Portal](https://developer.twitter.com/)でアプリ作成
2. OAuth 2.0を有効化
3. Callback URL: `http://localhost:3000/auth/twitter/callback`
4. Client IDとSecretを`.env`に設定

詳細は[docs/API_SETUP.md](docs/API_SETUP.md)を参照してください。

## 使い方

### 日次サマリーの生成

```python
# バックエンドで自動実行されます
# 手動でトリガーする場合:
curl -X POST http://localhost:8000/api/insights/daily-summary
```

### 自然言語クエリ

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "先週最も生産的だった日は?"}'
```

### データのエクスポート (GDPR準拠)

```bash
# すべてのデータをエクスポート
curl -X GET http://localhost:8000/api/export/all \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o my_data.json
```

## アーキテクチャ

詳細なアーキテクチャ情報は[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)を参照してください。

```
┌─────────────────────────────────────────────────────────┐
│                  Frontend (SvelteKit)                    │
│                     ↓ REST API ↓                         │
│                  Backend (FastAPI)                       │
│    ┌──────────────┬──────────────┬──────────────┐       │
│    │  Collectors  │  Analyzers   │   Ollama     │       │
│    └──────────────┴──────────────┴──────────────┘       │
│                     ↓ Data ↓                             │
│    ┌──────────────┬──────────────┬──────────────┐       │
│    │ PostgreSQL   │    Redis     │    MinIO     │       │
│    └──────────────┴──────────────┴──────────────┘       │
└─────────────────────────────────────────────────────────┘
```

## セキュリティ

### データ暗号化
- **At Rest**: PostgreSQL透過的データ暗号化
- **OAuth Tokens**: AES-256-GCM暗号化
- **Backups**: gpg暗号化

### プライバシー保護
- ローカルストレージのみ
- Ollamaローカル実行
- データ保持期間設定
- 自動削除機能

## 開発

### 開発環境のセットアップ

```bash
# バックエンド
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# フロントエンド
cd frontend
npm install
npm run dev
```

### テスト

```bash
# バックエンド
pytest backend/tests

# フロントエンド
npm test
```

## ロードマップ

- [x] 基本アーキテクチャ
- [x] Docker環境
- [x] FastAPI基盤
- [x] SvelteKit基盤
- [x] PostgreSQL + TimescaleDB
- [x] Ollama統合
- [x] GitHubコレクター
- [ ] Twitter/Gmailコレクター
- [ ] データ可視化 (D3.js)
- [ ] リアルタイム分析
- [ ] モバイル対応
- [ ] 多言語対応

## コントリビューション

プライバシーファーストの原則を守りながら、コントリビューションを歓迎します。

1. Fork it
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## ライセンス

MIT License

## 免責事項

このプロジェクトは個人利用を目的としています。各APIの利用規約を遵守してください。

## 謝辞

- [Ollama](https://ollama.ai/) - ローカルLLM実行環境
- [FastAPI](https://fastapi.tiangolo.com/) - 高速なPython Webフレームワーク
- [SvelteKit](https://kit.svelte.dev/) - モダンなWebフレームワーク
- [TimescaleDB](https://www.timescale.com/) - 時系列データベース

---

<div align="center">

**あなたのデータ、あなたの管理、あなたのプライバシー**

Made with ❤️ for privacy-conscious individuals

</div>
