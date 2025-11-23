# LifeMetrics テスティングガイド

このガイドでは、LifeMetricsの各機能をテストする方法を説明します。

## 目次

1. [環境のセットアップ](#環境のセットアップ)
2. [ユーザー認証のテスト](#ユーザー認証のテスト)
3. [データソース接続のテスト](#データソース接続のテスト)
4. [データ収集のテスト](#データ収集のテスト)
5. [AI分析のテスト](#ai分析のテスト)
6. [可視化のテスト](#可視化のテスト)
7. [APIエンドポイントのテスト](#apiエンドポイントのテスト)

## 環境のセットアップ

### 1. すべてのサービスが起動していることを確認

```bash
docker-compose ps
```

以下のサービスがすべて`Up`状態であることを確認：
- postgres
- redis
- minio
- ollama
- backend
- celery-worker
- celery-beat
- frontend
- nginx

### 2. ログの確認

```bash
# すべてのログを表示
docker-compose logs -f

# 特定のサービスのログを表示
docker-compose logs -f backend
docker-compose logs -f celery-worker
```

## ユーザー認証のテスト

### 1. ユーザー登録

#### フロントエンド経由

1. ブラウザで http://localhost:3000 にアクセス
2. 「Sign Up」をクリック
3. メールアドレス、ユーザー名、パスワードを入力
4. 登録完了後、自動的にログインされることを確認

#### API経由

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "securepassword123"
  }'
```

期待される応答:
```json
{
  "id": 1,
  "email": "test@example.com",
  "username": "testuser",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00.000Z"
}
```

### 2. ログイン

#### API経由

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123"
  }'
```

期待される応答:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### 3. 認証済みエンドポイントへのアクセス

```bash
# トークンを環境変数に保存
export TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."

# 現在のユーザー情報を取得
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

## データソース接続のテスト

### 1. データソースページへのアクセス

1. ログイン後、http://localhost:3000/sources にアクセス
2. 利用可能なデータソース（GitHub, Twitter, Gmail, Calendar）が表示されることを確認

### 2. GitHub接続のテスト

1. 「GitHub」カードの「接続」ボタンをクリック
2. GitHubの認証ページにリダイレクトされることを確認
3. 認証を承認
4. アプリケーションに戻り、「接続済み」と表示されることを確認

#### API経由での確認

```bash
# データソース一覧を取得
curl -X GET http://localhost:8000/api/data-sources \
  -H "Authorization: Bearer $TOKEN"
```

期待される応答:
```json
[
  {
    "id": 1,
    "source_type": "github",
    "status": "active",
    "last_sync_at": null,
    "sync_error": null,
    "created_at": "2024-01-01T00:00:00.000Z"
  }
]
```

### 3. 手動同期のテスト

1. データソースページで「同期」ボタンをクリック
2. ステータスが「同期中」に変わることを確認
3. 同期完了後、「最終同期」の時刻が更新されることを確認

#### API経由

```bash
# 手動同期をトリガー
curl -X POST http://localhost:8000/api/data-sources/1/sync \
  -H "Authorization: Bearer $TOKEN"
```

## データ収集のテスト

### 1. Celeryワーカーのログ確認

```bash
docker-compose logs -f celery-worker
```

### 2. 手動でタスクを実行

```bash
# Celeryワーカーコンテナに入る
docker exec -it lifemetrics-celery-worker bash

# Pythonシェルを起動
python

# タスクを手動実行
from app.tasks.collection import collect_github_data_for_source
result = collect_github_data_for_source.delay(1)  # data_source_id=1
print(result.get())
```

### 3. 収集されたデータの確認

```bash
# バックエンドコンテナに入る
docker exec -it lifemetrics-backend bash

# Pythonシェルを起動
python

# データを確認
from app.core.database import async_session_maker
from app.db.models import RawData
from sqlalchemy import select
import asyncio

async def check_data():
    async with async_session_maker() as db:
        result = await db.execute(select(RawData).limit(10))
        data = result.scalars().all()
        for item in data:
            print(f"{item.data_type}: {item.timestamp}")

asyncio.run(check_data())
```

## AI分析のテスト

### 1. Ollamaの動作確認

```bash
# Ollamaコンテナに入る
docker exec -it lifemetrics-ollama bash

# モデル一覧を確認
ollama list

# テストクエリを実行
ollama run llama3.2 "Hello, how are you?"
```

### 2. 日次サマリーの生成

#### API経由

```bash
# 今日の日次サマリーを生成
curl -X POST http://localhost:8000/api/insights/generate-daily-summary \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-01-01"
  }'
```

### 3. 自然言語クエリのテスト

```bash
curl -X POST http://localhost:8000/api/insights/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "今週の生産性はどうでしたか？"
  }'
```

### 4. 生成されたインサイトの確認

```bash
curl -X GET http://localhost:8000/api/insights \
  -H "Authorization: Bearer $TOKEN"
```

## 可視化のテスト

### 1. ダッシュボードページ

1. http://localhost:3000/dashboard にアクセス
2. 以下のグラフが表示されることを確認：
   - 生産性トレンド（折れ線グラフ）
   - アクティビティ分布（ドーナツグラフ）
   - 時間別アクティビティ（棒グラフ）

### 2. D3.js可視化のテスト

#### ネットワークグラフ

```svelte
<script>
import NetworkGraph from '$lib/components/charts/NetworkGraph.svelte';

const data = {
  nodes: [
    { id: 'GitHub', group: 'code', value: 10 },
    { id: 'Twitter', group: 'social', value: 5 },
    { id: 'Gmail', group: 'communication', value: 8 }
  ],
  links: [
    { source: 'GitHub', target: 'Twitter', value: 3 },
    { source: 'GitHub', target: 'Gmail', value: 5 }
  ]
};
</script>

<NetworkGraph {data} />
```

#### ヒートマップ

```svelte
<script>
import HeatMap from '$lib/components/charts/HeatMap.svelte';

const data = [];
for (let day = 0; day < 7; day++) {
  for (let hour = 0; hour < 24; hour++) {
    data.push({
      date: `2024-01-0${day + 1}`,
      hour: hour,
      value: Math.random() * 100
    });
  }
}
</script>

<HeatMap {data} />
```

## APIエンドポイントのテスト

### 1. API ドキュメントへのアクセス

ブラウザで http://localhost:8000/api/docs にアクセスし、SwaggerUIが表示されることを確認

### 2. 主要エンドポイントのテスト

#### ダッシュボード統計

```bash
curl -X GET http://localhost:8000/api/dashboard/stats \
  -H "Authorization: Bearer $TOKEN"
```

期待される応答:
```json
{
  "total_activities": 150,
  "total_data_sources": 3,
  "total_insights": 5,
  "active_goals": 2,
  "productivity_score": 75.5,
  "last_sync": "2024-01-01T12:00:00.000Z"
}
```

#### ダッシュボードデータ

```bash
curl -X GET "http://localhost:8000/api/dashboard/data?period=week" \
  -H "Authorization: Bearer $TOKEN"
```

#### 相関分析

```bash
# バックエンドコンテナで実行
docker exec -it lifemetrics-backend python

from app.core.database import async_session_maker
from app.analyzers.correlation_analyzer import analyzer
import asyncio

async def test_correlation():
    async with async_session_maker() as db:
        results = await analyzer.analyze_correlations(
            db=db,
            user_id=1,
            days=30,
            min_correlation=0.3
        )
        print(results)

asyncio.run(test_correlation())
```

#### 感情分析

```bash
# Pythonシェルで
from app.analyzers.sentiment_analyzer import analyzer

text = "Today was a great day! I'm really happy with my progress."
result = analyzer.analyze_text(text)
print(result)
```

## パフォーマンステスト

### 1. 負荷テスト

```bash
# Apache Benchを使用
ab -n 100 -c 10 -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/dashboard/stats
```

### 2. データベースパフォーマンス

```bash
# PostgreSQLコンテナに入る
docker exec -it lifemetrics-postgres psql -U postgres -d lifemetrics

-- クエリパフォーマンスを確認
EXPLAIN ANALYZE SELECT * FROM metrics WHERE user_id = 1 ORDER BY timestamp DESC LIMIT 100;

-- インデックスを確認
\di
```

### 3. Redisキャッシュの確認

```bash
# Redisコンテナに入る
docker exec -it lifemetrics-redis redis-cli -a your_redis_password

# キャッシュキーを確認
KEYS *

# 特定のキーの値を確認
GET oauth_state:abc123
```

## 統合テストスクリプト

完全な統合テストを実行する場合:

```bash
#!/bin/bash

echo "🧪 LifeMetrics 統合テスト開始"

# 1. サービスの起動確認
echo "✅ サービス起動確認..."
docker-compose ps

# 2. ユーザー登録
echo "✅ ユーザー登録テスト..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test-'$(date +%s)'@example.com",
    "username": "testuser-'$(date +%s)'",
    "password": "testpass123"
  }')
echo $RESPONSE

# 3. ログイン
echo "✅ ログインテスト..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }' | jq -r .access_token)

# 4. ダッシュボード統計取得
echo "✅ ダッシュボードテスト..."
curl -s -X GET http://localhost:8000/api/dashboard/stats \
  -H "Authorization: Bearer $TOKEN"

# 5. データソース一覧
echo "✅ データソーステスト..."
curl -s -X GET http://localhost:8000/api/data-sources \
  -H "Authorization: Bearer $TOKEN"

echo "✅ すべてのテスト完了！"
```

## トラブルシューティング

### テストが失敗する場合

1. **認証エラー**
   ```bash
   # トークンの有効期限を確認
   # JWTデコーダー: https://jwt.io/
   ```

2. **データベース接続エラー**
   ```bash
   # PostgreSQLの起動を確認
   docker-compose logs postgres

   # データベースに接続できるか確認
   docker exec -it lifemetrics-postgres psql -U postgres -d lifemetrics
   ```

3. **Ollama応答なし**
   ```bash
   # Ollamaのログを確認
   docker-compose logs ollama

   # モデルがダウンロード済みか確認
   docker exec -it lifemetrics-ollama ollama list
   ```

4. **Celeryタスクが実行されない**
   ```bash
   # Celeryワーカーのログを確認
   docker-compose logs celery-worker

   # Redisに接続できるか確認
   docker exec -it lifemetrics-redis redis-cli -a your_password ping
   ```

## 継続的な監視

本番環境では、以下を定期的に確認することを推奨：

1. **ヘルスチェック**
   ```bash
   curl http://localhost:8000/health
   ```

2. **メトリクス収集**
   - Prometheusを使用したメトリクス収集
   - Grafanaでの可視化

3. **ログ集約**
   - ELKスタックまたはLokiを使用したログ集約

4. **アラート設定**
   - サービスダウン時のアラート
   - エラー率の閾値アラート
   - ディスク容量アラート
