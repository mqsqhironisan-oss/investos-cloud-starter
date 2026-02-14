# AI株価予想機能の説明

## 概要
このシステムは、AIベースの株価予想機能を提供します。
テクニカル分析とテーマ分析を組み合わせて、各銘柄の将来価格と投資シグナルを生成します。

## 予想の仕組み

### 1. データ分析
- **移動平均**: 5日移動平均（MA5）と20日移動平均（MA20）を計算
- **トレンド判定**: 現在価格とMA5、MA20の位置関係からトレンドを判定
  - UP（上昇）: 現在価格 > MA5 > MA20
  - DOWN（下降）: 現在価格 < MA5 < MA20
  - NEUTRAL（中立）: その他
- **モメンタム**: 直近5日間の価格変化率を計算

### 2. 価格予想
トレンドとモメンタムに基づいて予想価格を算出:
- **上昇トレンド**: 1週間で+2-5%、1ヶ月で+5-15%
- **下降トレンド**: 1週間で-2-5%、1ヶ月で-5-15%
- **中立**: 1週間で±1%、1ヶ月で±3%

### 3. テーマ連動
強いテーマ（半導体、AIインフラ等）に属する銘柄は予想を上方修正:
- 予想価格を+2-5%調整
- 信頼度を+5ポイント上昇

### 4. 投資シグナル
- **BUY**: 上昇トレンド、購入推奨
- **SELL**: 下降トレンド、売却推奨
- **HOLD**: 中立トレンド、保持推奨

## 出力ファイル

### predictions.csv
全銘柄の予想結果を含む。信頼度が高い順にソート。

| カラム | 説明 | 例 |
|--------|------|-----|
| asof | 予想日 | 2026-02-14 |
| symbol | 銘柄コード | NVDA, 9984 |
| theme | テーマ | 半導体, AIインフラ |
| current_price | 現在価格 | 3794.78 |
| predicted_1w | 1週間後の予想価格 | 4058.04 |
| predicted_1m | 1ヶ月後の予想価格 | 4277.22 |
| trend | トレンド | UP, DOWN, NEUTRAL |
| signal | 投資シグナル | BUY, SELL, HOLD |
| confidence | 信頼度 (0-100) | 88.1 |
| ma5 | 5日移動平均 | 3740.22 |
| ma20 | 20日移動平均 | 3680.61 |
| momentum | モメンタム (%) | 4.34 |
| reason | 予想理由 | 上昇トレンド継続... |

### recommendations.csv
BUYシグナルで信頼度が高い銘柄トップ10。
フォーマットはpredictions.csvと同じ。

## API エンドポイント

### GET /out/predictions.csv
全銘柄の予想結果を取得

```bash
curl https://your-domain.com/out/predictions.csv
```

### GET /out/recommendations.csv
推奨銘柄トップ10を取得

```bash
curl https://your-domain.com/out/recommendations.csv
```

### POST /run/weekly
週次パイプラインを手動実行（予想を再生成）

```bash
curl -X POST https://your-domain.com/run/weekly
```

## Excel / Google スプレッドシートでの利用

### Power Query (Excel)
```m
let
    Source = Csv.Document(
        Web.Contents("https://your-domain.com/out/predictions.csv"),
        [Delimiter=",", Columns=13, Encoding=65001, QuoteStyle=QuoteStyle.None]
    ),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedType = Table.TransformColumnTypes(Headers,{
        {"asof", type date},
        {"symbol", type text},
        {"current_price", type number},
        {"predicted_1w", type number},
        {"predicted_1m", type number},
        {"confidence", type number}
    })
in
    ChangedType
```

### Google Sheets
```
=IMPORTDATA("https://your-domain.com/out/predictions.csv")
```

## 注意事項
- この予想は過去データに基づく統計的な分析です
- 実際の投資判断は、複数の情報源を組み合わせて行ってください
- 突発的なニュースやイベントは予測に含まれません
- 予想の信頼度が高くても、必ず利益が出るとは限りません
- 最終的な投資判断は自己責任で行ってください

## 今後の拡張
- 実際の価格データ取得（Yahoo Finance API等）
- より高度なAIモデル（LSTM, Transformerなど）
- ニュース・IRデータの自然言語処理
- バックテスト機能
- アラート機能（信頼度が高い予想が出た時に通知）
