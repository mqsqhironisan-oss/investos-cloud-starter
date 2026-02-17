# スコアリング設計（0〜100）

## ファクターとウェイト
- Championウェイト（`src/config/weights.ts`）  
  - trend: 18 / breakout: 20 / volume: 12 / volatility_risk: 14 / liquidity: 10 / event_risk: 6 / theme_fit: 20  
- Challengerウェイトも同ファイルに用意。必要に応じて切替。

各ファクターは -1〜+1 の正規化値を返し、ウェイトを乗算して合算する。合計は 0〜100 にクランプ。

## 判定ロジック
- 80〜100: BUY（ただし ATR%≦6 かつ 90日DD>-20% のとき）
- 60〜79: WATCH
- 0〜59: PASS

## ファクター概要
- **trend**: 60日価格変化率を20%幅でスケール。上昇はプラス、下降はマイナス。
- **breakout**: 終値/60日高値。高値更新で最大プラス、95%下回りでマイナス。
- **volume**: 直近出来高 ÷ 60日中央値。1xを基準に、3xで最大プラス。
- **volatility_risk**: ATR%と90日最大DDから減点。ATR 6% + DD20%で上限減点。
- **liquidity**: 推定売買代金の対数でスケール。薄いと減点。
- **event_risk**: ATR/Drawdownをトリガーにマイナス寄与。
- **theme_fit**: テーマ推定（`config/universe.ts`）に基づき加点。汎用は小加点、テーマ一致は大きめ加点。

## 出力フィールド
- `score_total` : 合計スコア（0〜100）
- `score_breakdown` : 各ファクターの寄与度（ウェイト×正規化）
- `action` : BUY / WATCH / PASS
- `evidence` : ブレイクアウト判定、出来高倍率、ATR%、最大DD など主要指標

## キャリブレーションの目安
- 上昇基調＋ブレイクアウト＋出来高増加 → 60点台後半〜80点
- リスクが高い（ATR>6% or DD<-20%） → BUYを抑制し、WATCH/PASSへ
- 流動性不足・イベントリスクが顕在 → 減点で60点未満へ
