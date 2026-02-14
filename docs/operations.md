# 運用手順

## 概要
このドキュメントでは、InvestOS Cloud Starterの日常運用手順を説明します。

## ローカル環境での実行

### 1. 環境構築
```bash
# 依存関係のインストール
pip install -r requirements.txt

# 環境変数の設定（.env.exampleを参考に.envを作成）
cp .env.example .env
# .envファイルを編集して必要な設定を行う
```

### 2. 週次パイプラインの実行
```bash
# 手動実行
python src/pipeline_weekly.py

# 出力確認
ls -la out/
head out/signals.csv
head out/orders.csv
head out/theme_strength.csv
```

### 3. APIサーバーの起動
```bash
# サーバー起動
uvicorn src.app:app --host 0.0.0.0 --port 8000

# 動作確認
curl http://localhost:8000/health
curl http://localhost:8000/out/signals.csv
curl http://localhost:8000/out/orders.csv
curl http://localhost:8000/out/theme_strength.csv

# 手動でパイプライン実行
curl -X POST http://localhost:8000/run/weekly
```

## クラウド環境での運用

### スケジューラ設定
週次で自動実行するには、クラウドプロバイダーのスケジューラを使用：

#### Render.com
Cron Jobsを使用：
```yaml
services:
  - type: web
    name: investos-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn src.app:app --host 0.0.0.0 --port $PORT
    
  - type: cron
    name: weekly-pipeline
    env: python
    schedule: "0 9 * * 1"  # 毎週月曜9:00 UTC
    buildCommand: pip install -r requirements.txt
    startCommand: python src/pipeline_weekly.py
```

#### Railway
Railway Cronを使用：
```
# railway.toml
[build]
  builder = "DOCKERFILE"

[deploy]
  startCommand = "uvicorn src.app:app --host 0.0.0.0 --port $PORT"

[[schedules]]
  cron = "0 9 * * 1"
  command = "python src/pipeline_weekly.py"
```

#### Fly.io
Fly Machines APIまたは外部cronサービス（GitHub Actions等）を使用

## モニタリング

### ログの確認
```bash
# パイプライン実行ログ
python src/pipeline_weekly.py 2>&1 | tee pipeline.log

# APIサーバーログ
uvicorn src.app:app --log-level info
```

### エラー処理
- パイプラインがエラーで停止した場合、ログを確認
- スタックトレースから原因を特定
- データソースの問題（API制限等）は、再実行で解決する場合が多い

## データバックアップ

### CSVファイルのバックアップ
```bash
# 日付付きバックアップ
DATE=$(date +%Y%m%d)
cp -r out/ backups/out_$DATE/
```

### クラウドストレージへの保存
- S3 / Google Cloud Storage / Azure Blob Storage等に定期バックアップ
- versioning機能を有効化して履歴管理

## トラブルシューティング

### よくある問題

#### 1. CSVが生成されない
```bash
# ディレクトリ権限を確認
ls -la out/

# 手動で作成
mkdir -p out/

# パイプライン再実行
python src/pipeline_weekly.py
```

#### 2. APIエンドポイントが404を返す
```bash
# ファイルの存在確認
ls -la out/*.csv

# パイプラインが実行されていない場合は実行
python src/pipeline_weekly.py
```

#### 3. メモリ不足
- データ量が増えた場合、インスタンスサイズを拡大
- pandas処理を最適化（chunk処理等）

## パフォーマンス最適化

### 1. データソースのキャッシュ
```python
# 価格データを一時保存して再利用
# data_sources/price_source.py に実装予定
```

### 2. 並列処理
```python
# 複数テーマの処理を並列化
# concurrent.futures を使用
```

### 3. インクリメンタル更新
```python
# 全データを毎回取得せず、差分更新
# 前回実行時刻を記録して、その後のデータのみ取得
```

## セキュリティ

### 環境変数管理
- `.env`ファイルはGitにコミットしない
- クラウド環境では、各プロバイダーのSecret管理機能を使用

### API キー
- データソースのAPIキーは環境変数で管理
- 定期的にローテーション

### アクセス制限
- APIエンドポイントに認証を追加（将来実装）
- IPホワイトリスト設定

## 拡張ガイド

### 新しいデータソースの追加
1. `src/data_sources/` に新しいモジュールを追加
2. `pipeline_weekly.py` でインポートして使用
3. テストを `tests/` に追加

### 新しいモデルの追加
1. `src/models/` に新しいモジュールを追加
2. 既存のスコアリングロジックに統合
3. `config.yaml` に必要な設定を追加

### カスタムエクスポート形式
1. `src/exporters/` に新しいエクスポーターを追加
2. JSON、Parquet等、CSV以外の形式にも対応可能
