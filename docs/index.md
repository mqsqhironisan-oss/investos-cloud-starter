# InvestOS Cloud Starter – Worker版概要

## 目的
- Cloudflare Worker 1本で UI (`/`) と API (`/api/analyze`, `/api/health`) を提供。
- 入力: ティッカー（例: `7203.T`、`AAPL`）
- 処理: 市場データ生成 → ファクター算出 → スコア合算 → BUY/WATCH/PASS 判定 → AIで根拠文章生成
- 出力: JSON & UI。価格予測は行わず、計算済み事実のみを説明する。

## エンドポイント
- `GET /` : 投資家向けUI。結論→根拠→内訳→生データの順で表示。
- `GET /api/analyze?ticker=7203.T` : スコアリング結果のJSONを返却。`skip_ai=1`でAI呼び出し省略。
- `GET /api/health` : APIキー有無・キャッシュ種別を返却。

### レスポンス例
```json
{
  "ticker": "7203.T",
  "asof": "2026-02-15T14:12:00Z",
  "action": "WATCH",
  "score_total": 73,
  "score_breakdown": {
    "trend": 18,
    "breakout": 20,
    "volume": 12,
    "volatility_risk": -5,
    "liquidity": 8,
    "event_risk": -2,
    "theme_fit": 22
  },
  "evidence": {
    "breakout_60d": true,
    "volume_multiple": 1.7,
    "atr_percent": 2.8,
    "max_drawdown_90d": -9.4
  },
  "rationale_ai": "投資家向けの根拠文章",
  "disclaimer": "投資判断は自己責任…"
}
```

## ファイル構成（worker/）
- `src/index.ts` : ルーティング `/` `/api/analyze` `/api/health`
- `src/ui/app.html|css|js` : UI（結論→根拠→内訳→生データ）
- `src/domain/score.ts` : スコア集計 & 判定
- `src/domain/factors/*` : 各ファクター計算
- `src/infra/marketData.ts` : 市場データ取得スタブ（将来API差し替え想定）
- `src/infra/cache.ts` : KV or インメモリキャッシュ
- `src/infra/validators.ts` : tickerバリデーション
- `src/ai/rationale.ts` : OpenAI Responses API呼び出し（キー未設定時はフォールバック文言）
- `src/ai/prompts.ts` : システムプロンプト & 出力フォーマット
- `src/config/weights.ts` : Champion/Challengerウェイト
- `src/config/universe.ts` : テーマ分類ヘルパ
- `wrangler.toml` : Worker設定（HTML/CSS/JSをText扱いでバンドル）

## セキュリティ・課金観点
- `OPENAI_API_KEY` をSecretで設定（未設定時はフォールバック文章を返す）
- `skip_ai=1` で呼び出し抑制可能
- `cache.ts` で同一ティッカーをTTL付きキャッシュ（デフォルト: メモリ）
- OpenAIエラー時はAPIのエラーメッセージを返却し、UIで明示表示

## デプロイ
1. Cloudflareで Worker を作成し、`wrangler.toml` の `name` を合わせる
2. `OPENAI_API_KEY` を `wrangler secret put` で登録
3. （任意）KVを作成し、`wrangler.toml` の `kv_namespaces` を設定
4. `npm install && npm run deploy`
