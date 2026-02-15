# 学習レイヤー実装完了サマリー

## 実装概要
テーマ重みを過去実績に基づいて自動最適化する学習レイヤーを実装しました。
**予測AIではなく、重みの最適化のみを行います。**

## Before / After 比較

### Before（実装前）
```python
# 固定された重み
theme_weights = {
    "semis": 0.25,
    "ai_infra": 0.25,
    "rare_metals": 0.25,
    "robotics": 0.25
}

# 変更方法：手動でconfig.yamlを編集
```

**課題:**
- 重みの調整が手動
- 市場環境変化への対応が遅い
- 最適な重みの判断が困難

### After（実装後）
```python
# Champion（本番稼働中）
champion_weights = {
    "semis": 0.25,
    "ai_infra": 0.25,
    "rare_metals": 0.25,
    "robotics": 0.25
}

# Challenger（学習提案）
challenger_weights = {
    "semis": 0.192,      # -5.8%
    "ai_infra": 0.273,   # +2.3%
    "rare_metals": 0.187,# -6.3%
    "robotics": 0.347    # +9.7%
}

# 評価を経て、Championを手動更新
```

**改善:**
- 週次で自動的に最適化提案
- 過去52週の実績を反映
- Champion/Challeneger で比較可能

## 実装の詳細

### 1. Champion / Challenger パターン

#### Champion（チャンピオン）
- **役割**: 本番稼働中の重み
- **保存先**: `data/models/champion_weights.json`
- **使用箇所**: signals/orders 生成
- **更新**: 評価を経て手動

#### Challenger（チャレンジャー）
- **役割**: 学習が提案する重み
- **保存先**: `data/models/challenger_weights.json`
- **使用箇所**: なし（シャドーモード）
- **更新**: 週次で自動

### 2. 学習アルゴリズム

```
┌─────────────────────────────────────────┐
│ Step 1: 過去52週のパフォーマンス計算 │
│ - 各テーマの代表銘柄バスケット       │
│ - リターン、リスク（ボラティリティ）  │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ Step 2: スコアリング                   │
│ - return_first: return - 0.5 * risk    │
│ - sharpe: return / risk                 │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ Step 3: 重み計算                       │
│ - スコアを正規化して重みに変換         │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ Step 4: 制約の適用                     │
│ - 下限: 0.10, 上限: 0.50              │
│ - 変更幅: ±10%以内                     │
│ - 合計: 1.0                             │
└─────────────────────────────────────────┘
```

### 3. 制約とセーフガード

#### 変更幅制限
```python
max_delta = 0.10  # 週次で最大±10%

# 例
current = 0.25
new = 0.40  # +15% → 制限適用
limited = 0.35  # 0.25 + 0.10
```

#### 範囲制限
```python
min_weight = 0.10  # 10%
max_weight = 0.50  # 50%

# 極端な集中を防ぐ
```

#### 正規化
```python
# 常に合計を1.0に
total = sum(weights.values())
normalized = {k: v/total for k, v in weights.items()}
```

### 4. シャドーモード

```python
# 学習は提案のみ、本番には影響しない

# Phase 6: 本番動作（Championを使用）
signals = generate_signals(champion_weights)
orders = generate_orders(signals)

# Phase 7: 学習動作（提案のみ）
challenger_weights = optimize_weights(...)
save_as_proposal(challenger_weights)  # 保存のみ
```

## 出力ファイル

### 1. JSON（重みデータ）

**data/models/champion_weights.json**
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

**data/models/challenger_weights.json**
```json
{
  "weights": {
    "semis": 0.192,
    "ai_infra": 0.273,
    "rare_metals": 0.187,
    "robotics": 0.347
  },
  "updated_at": "2026-02-15T01:48:12",
  "metadata": {
    "source": "optimizer",
    "previous_champion": {...}
  }
}
```

### 2. CSV（週次履歴）

**out/learn/weights_champion.csv**
```csv
asof,semis,ai_infra,rare_metals,robotics
2026-02-15,0.25,0.25,0.25,0.25
2026-02-22,0.25,0.25,0.25,0.25
...
```

**out/learn/weights_challenger.csv**
```csv
asof,semis,ai_infra,rare_metals,robotics
2026-02-15,0.192,0.273,0.187,0.347
2026-02-22,0.195,0.280,0.180,0.345
...
```

### 3. 可視化（GitHub Pages）

**docs/index.html**
- Champion vs Challenger 比較表
- 変化量の可視化
- 最終更新時刻

アクセス方法:
```
https://<username>.github.io/<repo>/
```

## 運用フロー

### 週次パイプライン実行

```
┌──────────────────────────────────────┐
│ Phase 1-6: 通常の投資プロセス      │
│ - データ収集                        │
│ - テーマ強度計算                    │
│ - スクリーニング                    │
│ - スコアリング                      │
│ - リスク管理                        │
│ - 注文生成                          │
│                                      │
│ ★ Championで signals/orders 生成  │
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│ Phase 7: 学習レイヤー（シャドー）  │
│ - Champion読み込み                  │
│ - Challenger最適化                  │
│ - 履歴保存                          │
│ - GitHub Pagesにコピー              │
│                                      │
│ ★ 本番環境には影響しない           │
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│ 人間による評価                      │
│ - パフォーマンス確認                │
│ - リスク確認                        │
│ - 4-8週の実績確認                   │
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│ Championの手動更新（必要時のみ）  │
│ - challenger → champion にコピー   │
│ - 更新理由を記録                    │
└──────────────────────────────────────┘
```

### Championの更新判断基準

1. **パフォーマンス**: Championを上回る
2. **安定性**: 急激な変動がない
3. **期間**: 4-8週の継続的な実績
4. **リスク**: ドローダウンが制御範囲内

## テスト結果

### 新規テスト（8個）
```
test_normalize_weights                     ✅ 正規化テスト
test_enforce_bounds                        ✅ 範囲制限テスト
test_limit_change                          ✅ 変更幅制限テスト
test_save_and_load_weights                 ✅ 保存・読み込みテスト
test_optimize_weights                      ✅ 最適化テスト
test_save_weights_history                  ✅ 履歴保存テスト
test_challenger_update                     ✅ Challenger更新テスト
test_pipeline_integration_with_learning    ✅ 統合テスト
```

### 全テスト結果
```
tests/test_learning.py:      8/8 passed ✅
tests/test_acceleration.py:  9/9 passed ✅
tests/test_integration.py:   4/4 passed ✅
tests/test_pipeline.py:      6/6 passed ✅
=========================================
Total: 27/27 tests passing ✅
```

## パイプライン実行ログ

```
2026-02-15 01:48:12 - INFO - === Weekly Pipeline Started ===
...
2026-02-15 01:48:12 - INFO - Phase 7: Learning Layer (Shadow Mode)
2026-02-15 01:48:12 - INFO - Loaded weights from .../champion_weights.json
2026-02-15 01:48:12 - INFO - Optimizing weights with return_first objective over 52 weeks
2026-02-15 01:48:12 - INFO - Optimized weights: {
    'semis': 0.192,
    'ai_infra': 0.273,
    'rare_metals': 0.187,
    'robotics': 0.347
}
2026-02-15 01:48:12 - INFO - Saved weights to .../challenger_weights.json
2026-02-15 01:48:12 - INFO - Saved champion history to .../weights_champion.csv
2026-02-15 01:48:12 - INFO - Saved challenger history to .../weights_challenger.csv
2026-02-15 01:48:12 - INFO - Copied ... to docs/data/
2026-02-15 01:48:12 - INFO - Learning completed: Champion={...}, Challenger={...}
2026-02-15 01:48:12 - INFO - === Weekly Pipeline Completed ===
```

## 制約の遵守

### ✅ 実装された制約

**1. シャドーモード固定**
```python
mode = cfg['learn']['mode']
assert mode == 'shadow', "Learning mode must be shadow"
```

**2. 変更幅制限（±10%）**
```python
max_delta = 0.10
delta = new - current
if abs(delta) > max_delta:
    delta = max_delta if delta > 0 else -max_delta
```

**3. 範囲制限（0.10-0.50）**
```python
weight = max(0.10, min(0.50, weight))
```

**4. 正規化（合計1.0）**
```python
total = sum(weights.values())
normalized = {k: v/total for k, v in weights.items()}
```

### ❌ 禁止事項の回避

**価格予測なし**
- ✅ 過去実績の分析のみ
- ❌ 未来価格の回帰/分類なし

**売買判断の上書きなし**
- ✅ シャドーモード固定
- ❌ 学習が本番判断を変更しない

**過剰な依存なし**
- ✅ numpy/pandas のみ使用
- ❌ 重い機械学習ライブラリなし

## ファイル構成

```
investos-cloud-starter/
├── src/
│   └── models/
│       └── learning.py          # NEW (340 lines)
├── data/
│   └── models/
│       ├── champion_weights.json   # NEW
│       └── challenger_weights.json # NEW
├── out/
│   └── learn/
│       ├── weights_champion.csv    # NEW
│       └── weights_challenger.csv  # NEW
├── docs/
│   ├── index.html               # NEW (218 lines)
│   ├── learning.md              # NEW (194 lines)
│   └── data/                    # NEW (GitHub Pages用)
│       ├── champion_weights.json
│       ├── challenger_weights.json
│       ├── weights_champion.csv
│       └── weights_challenger.csv
├── tests/
│   └── test_learning.py         # NEW (170 lines)
└── config.yaml                  # UPDATED (learn section追加)
```

## まとめ

### 実装完了 ✅
- 学習レイヤー（340行）
- Champion/Challenger パターン
- シャドーモード運用
- 週次自動最適化
- GitHub Pages 可視化
- 包括的テスト（8個）
- 詳細ドキュメント

### 制約遵守 ✅
- 予測AIなし
- シャドーモード固定
- 変更幅制限（±10%）
- 範囲制限（0.10-0.50）
- 正規化（合計1.0）
- 既存機能維持
- 全テストパス（27/27）

### 運用準備 ✅
- 週次で自動実行
- GitHub Pagesで可視化
- 手動でChampion更新
- 長期運用に対応

**学習レイヤーの実装が完了しました！** 🎉
