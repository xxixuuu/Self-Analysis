# LifeMetrics アーキテクチャ設計書

## システム概要

LifeMetricsは、プライバシーファーストの自己分析AIダッシュボードです。
個人のデジタルフットプリントをローカルで収集・分析し、Ollamaを使用した
完全プライベートなAI分析を提供します。

## アーキテクチャ原則

1. **Privacy-First**: 全データはローカルストレージのみ
2. **Offline-Capable**: データ収集以外はオフライン動作可能
3. **Modular Design**: コレクター、アナライザー、ビジュアライザーの分離
4. **Security by Default**: エンドツーエンド暗号化、OAuth Token保護
5. **Scalable**: TimescaleDB + DuckDBでスケーラブルな分析

## システム構成図

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  SvelteKit + TypeScript                                   │   │
│  │  ├─ Dashboard (D3.js, Chart.js)                          │   │
│  │  ├─ Data Source Configuration                            │   │
│  │  ├─ Privacy Settings                                     │   │
│  │  └─ Report Generator                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           ↕ REST/WebSocket API                   │
└─────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Backend Layer (FastAPI)                     │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐       │
│  │   API Layer  │  │  Auth Layer  │  │  Security Layer │       │
│  │              │  │              │  │  - Encryption   │       │
│  │  REST API    │  │  OAuth2      │  │  - Token Mgmt   │       │
│  │  WebSocket   │  │  JWT         │  │  - Access Log   │       │
│  └──────────────┘  └──────────────┘  └─────────────────┘       │
│         ↓                  ↓                   ↓                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Core Application Layer                       │   │
│  │                                                            │   │
│  │  ┌─────────────────┐  ┌──────────────────────────────┐  │   │
│  │  │  Data Collectors│  │  Analysis Engine              │  │   │
│  │  │                 │  │                                │  │   │
│  │  │ ├─ GitHub      │  │  ├─ Time Series Analysis      │  │   │
│  │  │ ├─ Twitter     │  │  ├─ Correlation Analysis      │  │   │
│  │  │ ├─ Gmail       │  │  ├─ Clustering (scikit-learn) │  │   │
│  │  │ ├─ Calendar    │  │  ├─ Sentiment (VADER)         │  │   │
│  │  │ ├─ Slack       │  │  ├─ NLP (spaCy)               │  │   │
│  │  │ ├─ Spotify     │  │  └─ Anomaly Detection         │  │   │
│  │  │ └─ Health      │  │                                │  │   │
│  │  └─────────────────┘  └──────────────────────────────┘  │   │
│  │                                                            │   │
│  │  ┌──────────────────────────────────────────────────────┐  │
│  │  │  Ollama Integration (Local LLM)                       │  │
│  │  │                                                        │  │
│  │  │  ├─ Daily Summary Generator                          │  │
│  │  │  ├─ Emotion Analysis                                 │  │
│  │  │  ├─ Topic Extraction                                 │  │
│  │  │  ├─ Productivity Advisor                             │  │
│  │  │  ├─ Natural Language Query                           │  │
│  │  │  └─ Report Generator                                 │  │
│  │  └──────────────────────────────────────────────────────┘  │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Task Queue Layer                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Celery + Redis                                           │   │
│  │  ├─ Scheduled Data Collection (Celery Beat)              │   │
│  │  ├─ Async Analysis Tasks                                 │   │
│  │  └─ Report Generation Jobs                               │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                  │
│                                                                   │
│  ┌───────────────┐  ┌──────────────┐  ┌─────────────────────┐  │
│  │  PostgreSQL   │  │    Redis     │  │      DuckDB         │  │
│  │  + TimescaleDB│  │              │  │   (Analytics OLAP)  │  │
│  │               │  │  - Cache     │  │                     │  │
│  │  - Users      │  │  - Sessions  │  │  - Aggregations     │  │
│  │  - Raw Data   │  │  - Task Q    │  │  - Complex Queries  │  │
│  │  - Metrics    │  │              │  │                     │  │
│  └───────────────┘  └──────────────┘  └─────────────────────┘  │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  MinIO (S3-Compatible Object Storage)                     │  │
│  │  - Attachments, Files, Exports                            │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                    External Services Layer                       │
│  (Data Collection Only - No Data Sent Out)                       │
│                                                                   │
│  GitHub API │ Twitter API │ Gmail API │ Calendar API │ etc...    │
└─────────────────────────────────────────────────────────────────┘
```

## データフロー

### 1. データ収集フロー
```
External API → OAuth2 Auth → Collector → Normalization → PostgreSQL
                                                        → MinIO (files)
                                ↓
                         Celery Beat (Scheduler)
```

### 2. データ分析フロー
```
PostgreSQL → Pandas/Polars → Analysis Engine → Results → Cache (Redis)
                                  ↓                          ↓
                            Ollama (Local LLM)          Frontend API
                                  ↓
                            Insights/Summaries
```

### 3. ダッシュボードフロー
```
User Request → SvelteKit → FastAPI → Cache Check → DB Query
                                          ↓             ↓
                                        Hit          Miss
                                          ↓             ↓
                                     Return       Analyze & Cache
                                                        ↓
                                                     Return
```

## セキュリティレイヤー

### データ暗号化
- **At Rest**: PostgreSQL透過的データ暗号化 (TDE)
- **OAuth Tokens**: AES-256-GCM暗号化
- **Sensitive Fields**: SQLAlchemy encrypted column types
- **Backups**: gpg暗号化

### アクセス制御
```
User → JWT Token → FastAPI Middleware → Permission Check → Resource
                                              ↓
                                         Audit Log
```

### プライバシー保護
- ローカルストレージのみ（外部送信ゼロ）
- Ollamaローカル実行（APIキー不要）
- データ保持期間設定（自動削除）
- GDPR準拠エクスポート機能

## データモデル

### コアエンティティ

```python
User (ユーザー)
├── DataSources (データソース接続情報)
│   ├── GitHub
│   ├── Twitter
│   └── Gmail
├── RawData (生データ)
│   ├── GitHubCommits
│   ├── Tweets
│   └── Emails
├── Metrics (集約メトリクス)
│   ├── DailyProductivity
│   ├── EmotionScores
│   └── ActivitySummary
├── Insights (AI生成インサイト)
│   ├── DailySummary
│   ├── WeeklyReport
│   └── Recommendations
└── Goals (目標・習慣)
    ├── Habits
    └── Progress
```

## 技術スタック詳細

### フロントエンド
- **SvelteKit 2.0**: フレームワーク
- **TypeScript 5.0+**: 型安全性
- **TailwindCSS 4.0**: スタイリング
- **DaisyUI**: UIコンポーネント
- **D3.js v7**: 高度な可視化
- **Chart.js 4.0**: 基本チャート
- **Vite**: ビルドツール

### バックエンド
- **FastAPI 0.110+**: Webフレームワーク
- **Python 3.12**: 言語
- **SQLAlchemy 2.0**: ORM
- **AsyncPG**: 非同期PostgreSQLドライバー
- **Pydantic v2**: バリデーション
- **Celery 5.3**: タスクキュー
- **Redis 7.2**: キャッシュ・ブローカー

### データ処理
- **Pandas 2.1**: データフレーム操作
- **Polars**: 高速データ処理
- **DuckDB**: OLAP分析
- **scikit-learn**: 機械学習
- **spaCy 3.7**: NLP
- **VADER**: 感情分析

### AI/LLM
- **Ollama**: ローカルLLM実行環境
  - llama3.2 (8B): 汎用分析
  - mistral (7B): 高速推論
  - gemma2 (9B): 要約・質問応答

### データベース
- **PostgreSQL 16**: メインDB
- **TimescaleDB**: 時系列データ拡張
- **Redis 7.2**: キャッシュ
- **DuckDB**: 分析用OLAP

### インフラ
- **Docker 24.0+**: コンテナ化
- **Docker Compose**: オーケストレーション
- **Nginx**: リバースプロキシ
- **MinIO**: オブジェクトストレージ

## スケーラビリティ戦略

### データ増加対応
- TimescaleDB自動パーティショニング（月次）
- DuckDB Parquetエクスポート（アーカイブ）
- MinIO階層型ストレージ

### パフォーマンス最適化
- Redis 3層キャッシュ戦略
  1. API Response Cache (1時間)
  2. Query Result Cache (24時間)
  3. ML Model Cache (永続)
- PostgreSQL接続プーリング (AsyncPG)
- Celeryワーカー動的スケーリング

## 開発フェーズ

### Phase 1: 基盤構築 (完了予定: 10時間)
- Docker環境セットアップ
- DB設計・実装
- FastAPI基本構造
- SvelteKit基本構造
- OAuth2認証基盤

### Phase 2: データ収集 (完了予定: 8時間)
- GitHubコレクター
- Twitterコレクター
- Gmailコレクター
- Celery統合

### Phase 3: AI分析 (完了予定: 6時間)
- Ollama統合
- 基本分析エンジン
- 感情分析
- 要約生成

### Phase 4: ダッシュボード (完了予定: 4時間)
- 基本UI
- データ可視化
- リアルタイム更新

### Phase 5: セキュリティ・完成 (完了予定: 2時間)
- 暗号化実装
- GDPR準拠ツール
- ドキュメント作成

## デプロイメント

### ローカル起動
```bash
docker-compose up -d
```

### 環境変数
```bash
# すべて.envファイルで管理
# OAuth認証情報
# 暗号化キー
# データ保持ポリシー
```

### バックアップ戦略
- PostgreSQL: pg_dump (日次)
- MinIO: mc mirror (日次)
- 設定ファイル: Git管理

## モニタリング

- Prometheus: メトリクス収集
- Grafana: 可視化
- アクセスログ: ローカルファイル
- エラートラッキング: ローカルSentry互換

## 次のステップ

1. プロジェクト構造作成
2. Docker Composeファイル作成
3. バックエンド実装開始
4. フロントエンド実装開始
