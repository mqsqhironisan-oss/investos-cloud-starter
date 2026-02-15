# 学習レイヤー（Learning Layer）ガイド

## 概要
学習レイヤーは、過去の実績に基づいてテーマ重みを自動最適化する機能です。

**重要：これは予測AIではありません**
- ❌ 未来の価格を予測するものではない
- ❌ 売買判断を学習に任せない
- ✅ 過去52週のデータから重みを最適化するのみ
- ✅ シャドーモード固定（本番環境には影響しない）

## Champion/Challenger パターン

### Champion（チャンピオン）
- **現在本番稼働中の重み**
- `data/models/champion_weights.json` に保存
- 実際の signals/orders 生成に使用
- 評価を経て手動で更新

### Challenger（チャレンジャー）
- **学習が提案する新しい重み**
- `data/models/challenger_weights.json` に保存
- 週次で自動更新
- 本番環境には影響しない（Shadow Mode）

### 更新フロー
```
1. 週次パイプライン実行
   ↓
2. Championで signals/orders 生成（本番動作）
   ↓
3. Challengerを学習・更新（提案のみ）
   ↓
4. 両方の履歴を out/learn/ に保存
   ↓
5. docs/data/ にコピー（GitHub Pages表示）
   ↓
6. 評価基準を満たしたらChampionを手動更新
```

## 設定（config.yaml）

```yaml
learn:
  enabled: true            # 学習レイヤーの有効化
  mode: shadow             # shadow固定（本番環境には影響しない）
  max_delta: 0.10          # 週次最大変更幅（10%）
  window_weeks: 52         # 評価期間（週）
  bounds:
    min: 0.10              # テーマ重みの下限
    max: 0.50              # テーマ重みの上限
  objective: return_first  # return_first or sharpe
```

### パラメータ説明

#### enabled
- `true`: 学習レイヤー有効
- `false`: 学習レイヤー無効（Championのみ使用）

#### mode
- `shadow`: シャドーモード（固定）
- 本番環境に影響を与えず、提案のみを生成

#### max_delta
- 週次の最大変更幅（0.10 = 10%）
- 急激な変化を防ぐ
- 例: 0.25 → 最大 0.35 または最小 0.15

#### window_weeks
- 過去何週のデータで評価するか
- デフォルト: 52週（1年）

#### bounds
- `min`: テーマ重みの下限（0.10 = 10%）
- `max`: テーマ重みの上限（0.50 = 50%）
- 極端な集中を防ぐ

#### objective
- `return_first`: リターン優先（リスク調整軽め）
  - スコア = リターン - 0.5 × リスク
- `sharpe`: シャープレシオ（リスク調整後リターン）
  - スコア = リターン / リスク

## 学習アルゴリズム

### 1. パフォーマンス計算
各テーマの過去52週のパフォーマンスを計算：
- リターン：年率換算
- リスク：ボラティリティ（標準偏差）

### 2. スコアリング
目的関数に基づいてスコアを計算：
```python
# return_first の場合
score = return - 0.5 * risk

# sharpe の場合
score = return / risk
```

### 3. 重みの計算
スコアを正規化して重みに変換：
```python
weights = normalize(scores)
```

### 4. 制約の適用
- 下限・上限を適用（0.10 - 0.50）
- 変更幅を制限（±10%）
- 合計を1.0に正規化

## 出力ファイル

### out/learn/weights_champion.csv
Champion重みの週次履歴：
```csv
asof,semis,ai_infra,rare_metals,robotics
2026-02-15,0.25,0.25,0.25,0.25
2026-02-22,0.25,0.25,0.25,0.25
...
```

### out/learn/weights_challenger.csv
Challenger重みの週次履歴：
```csv
asof,semis,ai_infra,rare_metals,robotics
2026-02-15,0.192,0.273,0.187,0.347
2026-02-22,0.195,0.280,0.180,0.345
...
```

### data/models/champion_weights.json
現在のChampion重み：
```json
{
  "weights": {
    "semis": 0.25,
    "ai_infra": 0.25,
    "rare_metals": 0.25,
    "robotics": 0.25
  },
  "updated_at": "2026-02-15T00:00:00",
  "metadata": {
    "source": "initial",
    "note": "Equal weight starting point"
  }
}
```

### data/models/challenger_weights.json
最新のChallenger重み：
```json
{
  "weights": {
    "semis": 0.192,
    "ai_infra": 0.273,
    "rare_metals": 0.187,
    "robotics": 0.347
  },
  "updated_at": "2026-02-15T01:48:12.925000",
  "metadata": {
    "source": "optimizer",
    "previous_champion": {...}
  }
}
```

## GitHub Pages 表示

### docs/index.html
Champion と Challenger の重みを比較表示：
- 現在のChampion重み
- Challenger提案
- 変化量（デルタ）
- ビジュアルバー

アクセス方法：
```
https://<your-username>.github.io/<repo-name>/
```

### docs/data/
GitHub Pages用のデータコピー：
- `champion_weights.json`
- `challenger_weights.json`
- `weights_champion.csv`
- `weights_challenger.csv`

## Championの更新方法

Challengerの評価を経て、Championを更新する場合：

### 1. パフォーマンス評価
Challengerの提案が十分な期間（例：4-8週）良好なパフォーマンスを示すか確認：
- リターンがChampionを上回る
- リスクが許容範囲内
- ドローダウンが制御されている

### 2. 手動更新
```bash
# Challengerの内容をChampionにコピー
cp data/models/challenger_weights.json data/models/champion_weights.json

# または、JSONファイルを直接編集
```

### 3. 記録
更新の理由とパフォーマンスを記録：
```json
{
  "weights": {...},
  "updated_at": "2026-03-15T10:00:00",
  "metadata": {
    "source": "promoted_from_challenger",
    "reason": "Outperformed champion for 8 weeks",
    "previous_champion": {...},
    "performance_metrics": {
      "return": 0.15,
      "sharpe": 1.2
    }
  }
}
```

## 運用例

### シナリオ1: 順調な学習
```
週1: Champion=均等, Challenger=均等
週2: Champion=均等, Challenger=半導体↑
週3: Champion=均等, Challenger=半導体↑↑
週4: Champion=均等, Challenger=半導体↑↑（継続）
...
週8: 評価→Championを更新
週9: Champion=半導体↑, Challenger=さらに調整
```

### シナリオ2: 市場環境変化
```
週1: Champion=半導体重視
週2: Challenger=AI重視を提案
週3: Challenger=AI重視を継続
週4: 市場環境確認→AI関連が好調
週5-8: Challengerの提案継続
週8: 評価→Championを更新
```

## トラブルシューティング

### Q: Challengerの変化が小さい
**A:** 以下を調整：
- `max_delta` を増やす（例：0.10 → 0.15）
- `bounds` を広げる（例：min 0.05, max 0.60）

### Q: Challengerが極端な重みを提案
**A:** 以下を調整：
- `bounds` を狭める（例：min 0.15, max 0.40）
- `max_delta` を小さくする（例：0.10 → 0.05）

### Q: 学習が動作しない
**A:** 確認事項：
- `learn.enabled` が `true` か
- `data/models/champion_weights.json` が存在するか
- ログに "Phase 7: Learning Layer" が表示されるか

### Q: Championを元に戻したい
**A:** バックアップから復元：
```bash
# 履歴から復元
# weights_champion.csv から過去の値を取得し、JSONを作成
```

## セキュリティ・制約

### シャドーモード固定
```python
# 学習は提案のみ、本番環境には影響しない
if learn_cfg.get('mode') != 'shadow':
    raise ValueError("Learning mode must be 'shadow'")
```

### 変更幅制限
```python
# 週次で最大±10%まで
delta = new_weight - current_weight
if abs(delta) > max_delta:
    delta = max_delta if delta > 0 else -max_delta
```

### 範囲制限
```python
# 各重みは 0.10 - 0.50 の範囲内
weight = max(min_weight, min(max_weight, weight))
```

## 予測AIとの違い

| 項目 | 学習レイヤー | 予測AI |
|------|------------|--------|
| 目的 | 重みの最適化 | 未来価格の予測 |
| 手法 | 過去実績の分析 | 機械学習/回帰 |
| 出力 | テーマ重み | 予想価格 |
| 影響 | なし（Shadow） | 売買判断 |
| リスク | 低 | 高 |
| 保守性 | 高 | 低 |

## 参考資料

### 実装ファイル
- `src/models/learning.py`: 学習レイヤーの実装
- `tests/test_learning.py`: テストケース
- `docs/index.html`: 可視化ページ

### 関連ドキュメント
- [加速検知](acceleration.md)
- [運用手順](operations.md)
