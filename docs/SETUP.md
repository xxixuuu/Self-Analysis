# LifeMetrics セットアップガイド

このガイドでは、LifeMetricsを初めてセットアップする手順を詳しく説明します。

## システム要件

### 最小要件
- **CPU**: 4コア以上
- **RAM**: 8GB以上 (Ollama使用のため)
- **ストレージ**: 20GB以上の空き容量
- **OS**: Linux, macOS, Windows (WSL2)

### 推奨要件
- **CPU**: 8コア以上
- **RAM**: 16GB以上
- **ストレージ**: SSD 50GB以上
- **GPU**: NVIDIA GPU (Ollama高速化用、オプション)

## 事前準備

### 1. Docker のインストール

#### Linux (Ubuntu/Debian)
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

#### macOS
```bash
brew install --cask docker
```

#### Windows
Docker Desktopをインストール: https://www.docker.com/products/docker-desktop

### 2. Docker Compose のインストール

```bash
# Linux
sudo apt-get update
sudo apt-get install docker-compose-plugin

# macOS (Docker Desktopに含まれています)
# Windows (Docker Desktopに含まれています)
```

### 3. Git のインストール

```bash
# Linux
sudo apt-get install git

# macOS
brew install git

# Windows
# Git for Windowsをインストール: https://git-scm.com/download/win
```

## インストール手順

### Step 1: リポジトリのクローン

```bash
git clone https://github.com/yourusername/lifemetrics.git
cd lifemetrics
```

### Step 2: 環境変数の設定

```bash
# .env.exampleを.envにコピー
cp .env.example .env
```

`.env`ファイルを編集して、以下の値を設定します：

```bash
# 必須: セキュリティキーの生成
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# 必須: データベースパスワード
POSTGRES_PASSWORD=your_secure_password_here

# 必須: Redisパスワード
REDIS_PASSWORD=your_secure_redis_password_here

# 必須: MinIOパスワード
MINIO_ROOT_PASSWORD=your_secure_minio_password_here
```

### Step 3: Docker Composeで起動

```bash
# バックグラウンドで起動
docker-compose up -d

# ログを確認
docker-compose logs -f
```

起動には数分かかる場合があります。すべてのサービスが起動するまで待ちます。

### Step 4: Ollamaモデルのダウンロード

```bash
# llama3.2のダウンロード (推奨)
docker exec -it lifemetrics-ollama ollama pull llama3.2

# mistralのダウンロード (オプション、より軽量)
docker exec -it lifemetrics-ollama ollama pull mistral

# gemma2のダウンロード (オプション)
docker exec -it lifemetrics-ollama ollama pull gemma2
```

モデルのダウンロードには時間がかかります（数GB）。

### Step 5: データベースの初期化

```bash
# データベースマイグレーションの実行
docker exec -it lifemetrics-backend alembic upgrade head
```

### Step 6: 動作確認

以下のURLにアクセスして、各サービスが正常に動作していることを確認します：

- **フロントエンド**: http://localhost:3000
- **バックエンドAPI**: http://localhost:8000
- **API ドキュメント**: http://localhost:8000/api/docs
- **MinIO Console**: http://localhost:9001

## OAuth2 アプリケーションの設定

### GitHub

1. https://github.com/settings/developers にアクセス
2. 「New OAuth App」をクリック
3. 以下を設定:
   - Application name: `LifeMetrics`
   - Homepage URL: `http://localhost:3000`
   - Authorization callback URL: `http://localhost:8000/api/oauth/github/callback`
4. 作成後、Client IDとClient Secretを`.env`に設定:
   ```bash
   GITHUB_CLIENT_ID=your_client_id
   GITHUB_CLIENT_SECRET=your_client_secret
   GITHUB_REDIRECT_URI=http://localhost:8000/api/oauth/github/callback
   ```

### Google (Gmail, Calendar)

1. https://console.cloud.google.com/ にアクセス
2. 新しいプロジェクトを作成
3. 「APIとサービス」→「ライブラリ」で以下を有効化:
   - Gmail API
   - Google Calendar API
4. 「認証情報」→「OAuth 2.0クライアントID」を作成:
   - アプリケーションの種類: Webアプリケーション
   - 承認済みのリダイレクトURI: `http://localhost:8000/api/oauth/google/callback`
5. Client IDとClient Secretを`.env`に設定:
   ```bash
   GOOGLE_CLIENT_ID=your_client_id
   GOOGLE_CLIENT_SECRET=your_client_secret
   GOOGLE_REDIRECT_URI=http://localhost:8000/api/oauth/google/callback
   ```

### Twitter/X

1. https://developer.twitter.com/ にアクセス
2. 「Projects & Apps」→「Create App」
3. OAuth 2.0を有効化
4. Callback URL: `http://localhost:8000/api/oauth/twitter/callback`
5. Client IDとClient Secretを`.env`に設定:
   ```bash
   TWITTER_CLIENT_ID=your_client_id
   TWITTER_CLIENT_SECRET=your_client_secret
   TWITTER_REDIRECT_URI=http://localhost:8000/api/oauth/twitter/callback
   ```

## トラブルシューティング

### Docker Composeが起動しない

```bash
# ログを確認
docker-compose logs

# 特定のサービスのログを確認
docker-compose logs backend
docker-compose logs ollama

# すべてのコンテナを再起動
docker-compose down
docker-compose up -d
```

### Ollamaモデルがダウンロードできない

```bash
# Ollamaコンテナの状態を確認
docker ps | grep ollama

# Ollamaコンテナのログを確認
docker logs lifemetrics-ollama

# ストレージの空き容量を確認
df -h
```

### データベース接続エラー

```bash
# PostgreSQLコンテナの状態を確認
docker exec -it lifemetrics-postgres psql -U lifemetrics_user -d lifemetrics

# データベースを再作成
docker-compose down -v
docker-compose up -d
```

### ポートが既に使用されている

他のアプリケーションが使用しているポートと競合している場合、`.env`ファイルでポートを変更できます：

```bash
FRONTEND_PORT=3001
BACKEND_PORT=8001
POSTGRES_PORT=5433
```

## アンインストール

```bash
# すべてのコンテナとボリュームを削除
docker-compose down -v

# イメージも削除
docker-compose down -v --rmi all

# データディレクトリを削除
rm -rf data/
```

## 次のステップ

セットアップが完了したら：

1. http://localhost:3000 にアクセス
2. アカウントを作成
3. データソースを接続
4. データ収集を開始
5. ダッシュボードで分析結果を確認

詳細は[README.md](../README.md)を参照してください。
