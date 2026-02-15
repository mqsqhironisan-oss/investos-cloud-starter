# Renderへのデプロイ手順

## 概要
Render.comは、Gitリポジトリから直接デプロイできるクラウドプラットフォームです。
無料枠でも十分に動作します。

## 前提条件
- GitHubアカウント
- Renderアカウント（https://render.com）
- このリポジトリがGitHubにプッシュされていること

## デプロイ手順

### 1. Renderアカウント作成
1. https://render.com にアクセス
2. Sign Upからアカウント作成
3. GitHubアカウントで認証

### 2. 新しいWebサービスの作成

#### 2-1. リポジトリ接続
1. Renderダッシュボードで「New +」→「Web Service」をクリック
2. GitHubリポジトリを選択
3. このリポジトリ（investos-cloud-starter）を選択

#### 2-2. サービス設定
以下の設定を入力：

```
Name: investos-cloud-starter
Environment: Python 3
Region: Oregon (US West) または Singapore（日本から近い）
Branch: main

Build Command:
pip install -r requirements.txt

Start Command:
uvicorn src.app:app --host 0.0.0.0 --port $PORT
```

#### 2-3. プラン選択
- **Free**: 開発・テスト用（十分）
- **Starter**: 本番運用（$7/月〜）

### 3. 環境変数の設定
RenderダッシュボードのEnvironmentセクションで以下を設定：

```
STOCK_MONTHLY_JPY=5000
EXTRA_CASH_JPY=0
# 必要に応じて他の環境変数を追加
```

### 4. デプロイ実行
「Create Web Service」をクリックすると自動的にデプロイが開始されます。

### 5. 動作確認
デプロイ完了後、URLが発行されます（例: `https://investos-cloud-starter.onrender.com`）

```bash
# Health check
curl https://your-app.onrender.com/health

# CSV取得
curl https://your-app.onrender.com/out/signals.csv
curl https://your-app.onrender.com/out/orders.csv
curl https://your-app.onrender.com/out/theme_strength.csv
```

## 週次パイプラインのスケジュール設定

Renderで週次パイプラインを自動実行するには、Cron Jobsを使用します。

### Cron Jobの作成
1. Renderダッシュボードで「New +」→「Cron Job」をクリック
2. 同じリポジトリを選択
3. 以下の設定を入力：

```
Name: weekly-pipeline
Environment: Python 3
Build Command:
pip install -r requirements.txt

Command:
python src/pipeline_weekly.py

Schedule: 0 9 * * 1
（毎週月曜日 9:00 UTC = 日本時間 18:00）
```

### スケジュール書式
Cron形式：`分 時 日 月 曜日`

例：
- `0 9 * * 1`: 毎週月曜9:00 UTC
- `0 10 * * 5`: 毎週金曜10:00 UTC
- `0 0 * * *`: 毎日0:00 UTC

## Renderの無料枠制限
- **Web Service**: 750時間/月（1サービス）、リクエストがない場合はスリープ
- **Cron Jobs**: 無料で利用可能
- **データベース**: PostgreSQL 90日間無料、その後有料

注意：
- 無料プランのWebサービスは、15分間アクセスがないとスリープします
- 最初のアクセス時に起動に30秒程度かかる場合があります

## トラブルシューティング

### デプロイエラー
```bash
# ログを確認
# RenderダッシュボードのLogsタブを確認
```

### 環境変数が反映されない
- Renderダッシュボードで環境変数を確認
- サービスを再デプロイ

### スリープからの復帰が遅い
- Starter プラン（$7/月）にアップグレードするとスリープしなくなります
- または、外部モニタリングサービス（UptimeRobot等）で定期的にアクセス

## カスタムドメイン設定
Renderでは無料でカスタムドメインを設定可能：

1. ダッシュボードの「Settings」→「Custom Domain」
2. ドメイン名を入力（例：investos.yourdomain.com）
3. DNSレコードを設定（CNAMEレコード）

## セキュリティ設定

### HTTPS
Renderは自動的にHTTPSを有効化（Let's Encrypt）

### アクセス制限
必要に応じて：
- Basic認証を追加
- API キー認証を実装
- IP ホワイトリスト設定

## コスト管理
- 無料枠で開始
- 必要に応じてStarter（$7/月）にアップグレード
- 複数サービスを運用する場合、Teamプラン検討

## バックアップ
Renderはビルド成果物を保持しますが、生成されたCSVファイルは：
- 外部ストレージ（S3等）に保存
- または、Githubに定期的にコミット（GitHub Actions使用）

## 参考リンク
- Render公式ドキュメント: https://render.com/docs
- Python デプロイガイド: https://render.com/docs/deploy-fastapi
- Cron Jobs: https://render.com/docs/cronjobs
