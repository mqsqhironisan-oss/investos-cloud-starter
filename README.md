# InvestOS Cloud Starter (MetaTrend Rotation)
目的：クラウド上で週次（＋日次更新）でデータ取得→特徴量→テーマ強度→スクリーニング→シグナル生成→CSV出力。
Excelは out/ のCSVをPowerQueryで読み込むだけ（あなたはボタン/更新だけ）。

## 主な機能
- **レジーム判定**: 市場環境を判定し、買って良い週/買うな週を識別（予測ではなく、ルールベース判定）
- **AIチャット**: 現在の状態について質問できるチャット機能（Cloudflare Workers経由）
- **加速検知**: ブレイクアウト・出来高異常・モメンタム加速を検知
- **学習レイヤー**: 過去52週の実績に基づくテーマ重み最適化（シャドーモード）
- **自動更新**: GitHub Actionsで毎週月曜9時に自動実行

## 1) 使い方（最短）
1. このフォルダをクラウド（Render/Railway/Fly.io等）にデプロイ（Dockerfileあり）
2. 環境変数を設定（.env.example参照）
3. /out/signals.csv と /out/orders.csv をExcelが読む

## 2) 重要（日本株の公式開示）
- TDnetの公式APIは有料です。無料で「公式の適時開示」を全自動取得したい場合は、契約が必要になります。
- 当面は「EDINET（有報等）＋企業IRページRSS/PR（提供されている場合）＋価格・出来高」で運用し、
  TDnetは後から拡張する前提にしています。

## 3) エンドポイント
- GET /health
- GET /out/signals.csv
- GET /out/orders.csv
- GET /out/theme_strength.csv
- GET /out/regime.csv (レジーム判定結果)
- POST /run/weekly （手動実行用。通常はスケジューラが動かす）

## 4) レジーム判定（Regime Detection）
市場環境を判定し、リスクが高い週は新規買いを停止します。

### 判定ロジック（ルールベース、予測なし）
- **Trendフィルタ**: SPYが200週移動平均の上/下
- **Volフィルタ**: VIXが閾値（デフォルト25）を超えているか
- **Rateフィルタ**: 10年債金利（TNX）の急変（4週で+0.5%超）
- **FXフィルタ**: USDJPY の急変（4週で±5%超）

スコア合計で判定：
- `+2以上` → **RISK_ON** （通常運用）
- `-2以下` → **RISK_OFF** （新規買い停止、保有継続）
- `それ以外` → **NEUTRAL** （通常運用）

### 設定（config.yaml）
```yaml
regime:
  enabled: true
  threshold_on: 2
  threshold_off: -2
  use_vix: true
  use_tnx: true
  use_usdjpy: true
  window_weeks_ma: 40  # 200日≒40週
  vix_threshold: 25
  rate_shock_threshold: 0.5
  fx_shock_threshold: 5.0
```

### フェイルセーフ
- データ取得失敗時は `NEUTRAL` にフォールバック（処理は継続）
- 個別データソース（VIX/TNX/USDJPY）は無効化可能

## 5) AIチャット機能
GitHub Pages上で動作するチャットインターフェース。現在のレジーム・テーマ強度・シグナル等について質問できます。

### 特徴
- **価格予測禁止**: 将来予測は一切行わない（システムプロンプトで制御）
- **状態説明のみ**: 現在のデータを分かりやすく説明
- **XSS対策**: innerHTML不使用、エスケープ処理

### セットアップ（Cloudflare Workers）
1. Cloudflare Workersで新しいWorkerを作成
2. `docs/cloudflare-worker-example.js` のコードをコピー
3. 環境変数を設定: `OPENAI_API_KEY`
4. Workerをデプロイ
5. フロントエンドの設定（HTML内で指定）:
```html
<script>
  window.INVESTOS_CHAT_API = 'https://your-worker.workers.dev/chat';
</script>
```

### API仕様
- **エンドポイント**: POST /chat
- **リクエスト**: `{ message: string, context: object }`
- **コンテキスト**: regime.csv, theme_strength.csv, signals.csv, orders.csv, weights_champion.csv の最新データ
- **レスポンス**: `{ reply: string }`

## 6) ロジック概要（初期・オーソドックス）
- ETF：S&P500 + TOPIX（比率固定）
- 個別：月5,000円固定。テーマ強度1位の上位銘柄に投入（追加余力があれば同テーマ上位へ）
- 売却：構造破壊（テーマ強度低下＋イベント悪化）/トレンド破壊/全体DD制御
- テーマ：半導体 / AIインフラ / レアメタル / ロボティクス（強度ローテーション）

## 7) Excel側（PowerQuery例）
PowerQueryで以下URLを読み込み：
- https://<あなたのドメイン>/out/signals.csv
- https://<あなたのドメイン>/out/orders.csv

（Mコード例は docs/powerquery_examples.md にあります）

## 重要な注意事項
- **このシステムは価格予測を行いません**
- レジーム判定は現在の市場環境の状態判定のみです
- 加速検知は「現在の状態」を検知するのみです
- 学習レイヤーは過去データに基づく重み最適化のみです
- **投資判断は最終的にご自身で行ってください**

