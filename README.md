# InvestOS Cloud Starter (MetaTrend Rotation)
目的：クラウド上で週次（＋日次更新）でデータ取得→特徴量→テーマ強度→スクリーニング→シグナル生成→CSV出力。
Excelは out/ のCSVをPowerQueryで読み込むだけ（あなたはボタン/更新だけ）。

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
- GET /out/predictions.csv （AI株価予想）
- GET /out/recommendations.csv （推奨銘柄）
- POST /run/weekly （手動実行用。通常はスケジューラが動かす）

## 4) ロジック概要（初期・オーソドックス）
- ETF：S&P500 + TOPIX（比率固定）
- 個別：月5,000円固定。テーマ強度1位の上位銘柄に投入（追加余力があれば同テーマ上位へ）
- 売却：構造破壊（テーマ強度低下＋イベント悪化）/トレンド破壊/全体DD制御
- テーマ：半導体 / AIインフラ / レアメタル / ロボティクス（強度ローテーション）

## 5) Excel側（PowerQuery例）
PowerQueryで以下URLを読み込み：
- https://<あなたのドメイン>/out/signals.csv
- https://<あなたのドメイン>/out/orders.csv
- https://<あなたのドメイン>/out/predictions.csv （AI株価予想）
- https://<あなたのドメイン>/out/recommendations.csv （推奨銘柄トップ10）

（Mコード例は docs/powerquery_examples.md にあります）

## 6) AI株価予想機能
- 各銘柄に対して以下を算出：
  - 1週間後、1ヶ月後の予想価格
  - トレンド判定（UP/DOWN/NEUTRAL）
  - 売買シグナル（BUY/SELL/HOLD）
  - 信頼度スコア（0-100）
- テクニカル指標：移動平均（5日/20日）、モメンタム
- テーマ強度と連動：強いテーマの銘柄は予想を上方修正
- predictions.csv：全銘柄の予想結果
- recommendations.csv：信頼度が高いBUY銘柄トップ10
