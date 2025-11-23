# .env ファイル設定ガイド

このガイドでは、`.env`ファイルの設定方法を詳しく説明します。

## 基本セットアップ

### Step 1: .envファイルの作成

```bash
cd /path/to/Self-Analysis
cp .env.example .env
```

### Step 2: 必須項目の設定

以下の項目は**必ず変更**してください。

## 🔐 セキュリティキーの生成（必須）

### SECRET_KEY の生成

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

出力例: `xPq8K2gH9mN5vL7wR3jT6yU4eF1bC0aD2fG8hJ5kM9n`

この値を`.env`の`SECRET_KEY`に設定:
```bash
SECRET_KEY=xPq8K2gH9mN5vL7wR3jT6yU4eF1bC0aD2fG8hJ5kM9n
```

### ENCRYPTION_KEY の生成

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

出力例: `zH9fK3mN8pQ5wE2tY7uI4oP1aS6dF0gJ3kL9xC8vB2n=`

この値を`.env`の`ENCRYPTION_KEY`に設定:
```bash
ENCRYPTION_KEY=zH9fK3mN8pQ5wE2tY7uI4oP1aS6dF0gJ3kL9xC8vB2n=
```

### JWT_SECRET_KEY の生成

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

出力例: `aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2uV3wX4yZ5`

この値を`.env`の`JWT_SECRET_KEY`に設定:
```bash
JWT_SECRET_KEY=aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2uV3wX4yZ5
```

## 🔒 パスワードの設定（必須）

強力なパスワードを設定してください。以下のコマンドで生成できます：

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(16))"
```

### PostgreSQL パスワード

```bash
POSTGRES_PASSWORD=your-generated-password-here
```

例:
```bash
POSTGRES_PASSWORD=K8mN2pQ9wE5tY7uI3oP
```

### Redis パスワード

```bash
REDIS_PASSWORD=your-generated-password-here
```

例:
```bash
REDIS_PASSWORD=L9xC4vB6nM8kJ3fG1hD
```

### MinIO パスワード

```bash
MINIO_ROOT_PASSWORD=your-generated-password-here
```

例:
```bash
MINIO_ROOT_PASSWORD=P2qR5sT8uV3wX7yZ1aB
```

## 🔗 OAuth2 設定（データソース接続用）

データソースを接続したい場合のみ設定が必要です。

### GitHub OAuth2（オプション）

GitHubからコミット、PR、Issueなどを収集する場合:

**1. OAuth Appの作成**
- https://github.com/settings/developers にアクセス
- 「New OAuth App」をクリック
- 以下を入力:
  - **Application name**: `LifeMetrics`
  - **Homepage URL**: `http://localhost:3000`
  - **Authorization callback URL**: `http://localhost:8000/api/oauth/github/callback`
- 「Register application」をクリック

**2. Client IDとSecretを取得**
- 作成されたアプリのページに表示されるClient IDをコピー
- 「Generate a new client secret」をクリックしてSecretを生成

**3. .envに設定**
```bash
GITHUB_CLIENT_ID=Iv1.a1b2c3d4e5f6g7h8
GITHUB_CLIENT_SECRET=1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0
GITHUB_REDIRECT_URI=http://localhost:8000/api/oauth/github/callback
```

### Google OAuth2（Gmail, Calendar用）（オプション）

GmailやGoogle Calendarを接続する場合:

**1. Google Cloud Projectの作成**
- https://console.cloud.google.com/ にアクセス
- 新しいプロジェクトを作成（例: "LifeMetrics"）

**2. APIの有効化**
- 「APIとサービス」→「ライブラリ」
- 以下のAPIを検索して有効化:
  - **Gmail API**
  - **Google Calendar API**

**3. OAuth同意画面の設定**
- 「APIとサービス」→「OAuth同意画面」
- User Type: 「外部」を選択
- アプリ名、サポートメールを入力
- スコープは後で自動的に追加されます

**4. 認証情報の作成**
- 「APIとサービス」→「認証情報」
- 「認証情報を作成」→「OAuth 2.0 クライアントID」
- アプリケーションの種類: **Webアプリケーション**
- 名前: `LifeMetrics`
- 承認済みのリダイレクトURI:
  ```
  http://localhost:8000/api/oauth/google/callback
  ```
- 「作成」をクリック

**5. Client IDとSecretを取得**
- ダイアログに表示されるClient IDとClient Secretをコピー

**6. .envに設定**
```bash
GOOGLE_CLIENT_ID=123456789012-abc3def4ghi5jkl6mno7pqr8stu9vwx0.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-aBcDeFgHiJkLmNoPqRsTuVwXyZ
GOOGLE_REDIRECT_URI=http://localhost:8000/api/oauth/google/callback
```

### Twitter/X OAuth2（オプション）

Twitter/Xからツイートやいいねを収集する場合:

**1. Developer Portalへアクセス**
- https://developer.twitter.com/en/portal/dashboard にアクセス
- Twitter Developer アカウントが必要（申請が必要な場合があります）

**2. Appの作成**
- 「Projects & Apps」→「Overview」
- 「+ Create App」をクリック
- App名を入力（例: "LifeMetrics"）

**3. OAuth 2.0の設定**
- 作成したAppの「Settings」タブへ
- 「User authentication settings」→「Set up」
- App permissions: **Read**
- Type of App: **Web App**
- Callback URI / Redirect URL:
  ```
  http://localhost:8000/api/oauth/twitter/callback
  ```
- Website URL: `http://localhost:3000`
- 「Save」をクリック

**4. Client IDとSecretを取得**
- 設定完了後に表示されるClient IDとClient Secretをコピー
- ⚠️ Client Secretは一度しか表示されないので必ず保存！

**5. .envに設定**
```bash
TWITTER_CLIENT_ID=aBcDeFgHiJkLmNoPqRsTuVwXyZ123456
TWITTER_CLIENT_SECRET=1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7
TWITTER_REDIRECT_URI=http://localhost:8000/api/oauth/twitter/callback
```

## ⚙️ その他の設定（オプション）

### Ollamaモデルの設定

使用するLLMモデルを指定:

```bash
OLLAMA_MODEL=llama3.2  # または mistral, gemma2
```

利用可能なモデル:
- `llama3.2` - バランスの取れたモデル（推奨、約2GB）
- `mistral` - より軽量なモデル（約4GB）
- `gemma2` - Googleのモデル（約5GB）

### データ収集の設定

```bash
# 自動収集の間隔（分）
COLLECTION_INTERVAL_MINUTES=60

# データ保持期間（日）
DATA_RETENTION_DAYS=365

# 自動収集の有効化
ENABLE_AUTO_COLLECTION=true
```

### ログレベル

```bash
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

開発中は`DEBUG`、本番では`INFO`または`WARNING`を推奨。

### CORS設定

フロントエンドのURLが異なる場合は変更:

```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

## 📝 最小限の設定例

すぐに試したい場合の最小設定（OAuth2なし）:

```bash
# セキュリティ（必須）
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# パスワード（必須）
POSTGRES_PASSWORD=your-secure-postgres-password
REDIS_PASSWORD=your-secure-redis-password
MINIO_ROOT_PASSWORD=your-secure-minio-password

# その他はデフォルト値のままでOK
```

この設定でDockerを起動し、後でOAuth2を追加できます。

## 🔄 設定変更後の反映

.envファイルを変更した後は、Dockerコンテナを再起動:

```bash
docker-compose down
docker-compose up -d
```

## 🛡️ セキュリティのベストプラクティス

1. **絶対に.envをGitにコミットしない**
   - `.gitignore`に`.env`が含まれていることを確認

2. **強力なパスワードを使用**
   - 最低16文字以上
   - 英数字+記号を組み合わせる

3. **本番環境では必ず変更**
   - `DEBUG=false`に設定
   - `APP_ENV=production`に設定
   - すべてのパスワードを本番用に変更

4. **定期的なローテーション**
   - 重要なキーは3-6ヶ月ごとに更新

## ❓ トラブルシューティング

### キー生成でエラーが出る

Pythonがインストールされていない場合:

```bash
# Ubuntu/Debian
sudo apt-get install python3

# macOS
brew install python3
```

または、オンラインツールを使用:
- https://www.uuidgenerator.net/ (SECRET_KEYとJWT_SECRET_KEY用)

### OAuth2で認証エラー

1. リダイレクトURIが正確に一致しているか確認
   - スペースや改行が入っていないか
   - HTTPとHTTPSの違い
   - ポート番号が正しいか

2. Client Secretをコピーミスしていないか確認

3. Docker再起動を実行
   ```bash
   docker-compose restart backend
   ```

### Dockerが起動しない

1. .envファイルの文法エラーを確認
   - `=`の前後にスペースを入れない
   - 値にスペースが含まれる場合は`"`で囲む

2. ログを確認
   ```bash
   docker-compose logs backend
   ```

## 📚 参考リンク

- [GitHub OAuth Apps](https://docs.github.com/en/developers/apps/building-oauth-apps)
- [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- [Twitter OAuth 2.0](https://developer.twitter.com/en/docs/authentication/oauth-2-0)
