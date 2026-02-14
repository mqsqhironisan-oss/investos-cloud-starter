# 加速検知（Momentum Acceleration Detection）

## 概要
加速検知モジュールは、銘柄の**現在の勢い**を測定するための機能です。

**重要：これは「予測AI」ではありません**
- ❌ 未来の価格を予測するものではない
- ✅ 現在の市場状態（加速・減速）を判定するルールベースシステム
- ✅ 過去データから現在の勢いを客観的に測定

## 検知項目

### 1. ブレイクアウト検知（Breakout Detection）
**定義：** 現在の終値が過去N日（デフォルト60日）の高値を更新しているか

**判定ロジック：**
```python
current_price > max(past_60_days_prices)
```

**スコアリング：**
- ブレイクアウト達成：50点〜100点（更新率に応じて）
- 高値に近い（95%以上）：40点
- 高値に近い（90%以上）：20点
- その他：0点

**意味：**
新高値更新は、強い買い圧力と上昇トレンドの継続を示唆します。

### 2. 出来高異常検知（Volume Anomaly Detection）
**定義：** 現在の出来高が過去の中央値のx倍（デフォルト1.5倍）以上

**判定ロジック：**
```python
current_volume >= median(past_volumes) * 1.5
```

**スコアリング：**
- 2倍以上：100点
- 1.5〜2倍：50〜100点（線形補間）
- 1.5倍未満：0〜50点（比率に応じて）

**意味：**
異常な出来高増加は、市場参加者の関心の高まりを示し、価格変動の前兆となることがあります。

### 3. モメンタム加速（Momentum Acceleration）
**定義：** 短期リターンが長期リターンより強いか

**判定ロジック：**
```python
short_return (4週) - long_return (12週) / 3
```

**スコアリング：**
- 加速度 > 10%：100点
- 加速度 5〜10%：75〜100点
- 加速度 0〜5%：50〜75点
- 加速度 -5〜0%：25〜50点
- 加速度 < -5%：0点

**意味：**
短期的な上昇が長期トレンドより強い場合、モメンタムが加速していることを示します。

### 4. ボラティリティ調整（Volatility Adjustment）
**定義：** 高ボラティリティの銘柄はスコアを減点

**調整係数：**
```python
volatility <= max_volatility (0.03):  係数 1.0
volatility >= max_volatility * 3:     係数 0.5
その他:                                線形補間
```

**意味：**
高ボラティリティはリスクが高いため、加速スコアを調整します。

## 総合加速スコア

### 計算式
```
accel_score = (
    breakout_score * weight_breakout +
    volume_score * weight_volume +
    momentum_score * weight_momentum
) / total_weight * volatility_adjustment
```

### デフォルトの重み
- ブレイクアウト：40%
- 出来高：30%
- モメンタム：30%

### スコア範囲
- 0〜100点
- 70点以上：強い加速
- 50〜70点：中程度の加速
- 30〜50点：弱い加速
- 30点未満：加速なし/減速

## 設定パラメータ（config.yaml）

```yaml
acceleration:
  enabled: true                # 加速検知の有効化
  breakout_days: 60            # ブレイクアウト判定期間（日）
  volume_multiplier: 1.5       # 出来高異常の倍率
  max_volatility: 0.03         # 許容ボラティリティ（日次標準偏差）
  weights:
    breakout: 40               # ブレイクアウトの重み（%）
    volume: 30                 # 出来高の重み（%）
    momentum: 30               # モメンタムの重み（%）
  score_impact: 10             # スコアへの最大影響（0-10点）

strategy:
  mode: normal                 # normal または return_first
```

### パラメータ調整ガイド

#### breakout_days
- **短期（20-30日）**: より敏感に反応、短期トレーディング向け
- **中期（60日）**: バランス型（推奨）
- **長期（120日）**: 長期トレンド重視

#### volume_multiplier
- **低感度（1.3-1.5）**: 頻繁に異常検知、誤検知リスク高
- **標準（1.5-2.0）**: バランス型（推奨）
- **高感度（2.0-3.0）**: 明確な異常のみ検知

#### weights
用途に応じて調整：
- **トレンドフォロー重視**: breakout 50, volume 20, momentum 30
- **出来高重視**: breakout 30, volume 50, momentum 20
- **バランス型**: breakout 40, volume 30, momentum 30（推奨）

## 運用モード

### normal モード（デフォルト）
- 加速スコアは補助的な役割
- 総合スコアに0-10点を加算
- テーマや他の要素とバランスを取る

### return_first モード（攻撃型）
```yaml
strategy:
  mode: return_first
```
- 加速スコアを最優先
- 同一テーマ内で加速スコアが高い銘柄を選択
- リターン重視、リスク許容度高い運用向け

## スコアへの統合

### 総合スコアの計算
```python
base_score = 80.0  # 基本スコア
accel_bonus = (accel_score / 100) * score_impact  # 0-10点
total_score = base_score + accel_bonus  # 80-90点
```

### signals.csvへの反映
```csv
asof,symbol,action,score,theme,reason,side,qty_jpy
2026-02-14,NVDA,買う/追加,87.5,半導体,TopTheme+TopPick; Acceleration: Breakout(85), Volume(70),BUY,5000
```

## 使用例

### 例1：強いブレイクアウト
```
銘柄: NVDA
現在価格: 1100円
60日高値: 1000円
出来高: 通常の2.5倍
→ accel_score: 85点
→ reason: "Acceleration: Breakout(90), Volume(95)"
```

### 例2：加速なし
```
銘柄: XYZ
現在価格: 900円（60日高値: 1000円）
出来高: 通常レベル
→ accel_score: 15点
→ reason: "Acceleration: Neutral"
```

### 例3：高ボラティリティ
```
銘柄: VOL
強い加速シグナル（accel_score: 80）
ただしボラティリティ高い（volatility_adj: 0.6）
→ 最終スコア: 80 * 0.6 = 48点
→ reason: "Acceleration: Breakout(75), HighVol(x0.60)"
```

## 予測AIとの違い

| 項目 | 加速検知 | 予測AI |
|------|---------|--------|
| 目的 | 現在の状態を判定 | 未来の価格を予測 |
| 手法 | ルールベース | 機械学習/統計モデル |
| 入力 | 過去の価格・出来高 | 多様なデータ |
| 出力 | 加速スコア（0-100） | 予想価格 |
| リスク | 低（単純なルール） | 高（モデル依存） |
| 保守性 | 高（理解しやすい） | 低（ブラックボックス） |

## トラブルシューティング

### Q: 加速スコアが常に低い
**A:** パラメータを調整してください
- `breakout_days`を短くする（60→30）
- `volume_multiplier`を下げる（1.5→1.3）
- `max_volatility`を上げる（0.03→0.05）

### Q: 誤検知が多い
**A:** パラメータを厳格にしてください
- `breakout_days`を長くする（60→120）
- `volume_multiplier`を上げる（1.5→2.0）
- ボラティリティ調整を強化

### Q: return_firstモードでリスクが高い
**A:** normalモードに戻すか、`score_impact`を下げてください
```yaml
strategy:
  mode: normal
acceleration:
  score_impact: 5  # 10から5に削減
```

## データ要件

### 最低限必要なデータ
- 価格時系列：60日以上（日次終値）
- 出来高時系列：60日以上（日次）

### 推奨データ
- 価格時系列：90日以上
- 出来高時系列：90日以上
- 更新頻度：日次

### データソース（TODO）
現在はスタブ実装。実運用では以下を統合：
- Yahoo Finance API
- Alpha Vantage
- その他価格データプロバイダー

## 参考資料

### 実装ファイル
- `src/models/acceleration.py`: 加速検知の実装
- `src/models/scoring.py`: スコアリングへの統合
- `tests/test_acceleration.py`: テストケース

### 関連ドキュメント
- [運用手順](operations.md)
- [Renderデプロイ](deploy_render.md)
