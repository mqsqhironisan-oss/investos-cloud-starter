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

（Mコード例は docs/powerquery_examples.md にあります）
