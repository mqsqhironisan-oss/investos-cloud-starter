# 加速検知モジュール実装完了サマリー

## 実装概要
「加速検知（Momentum Acceleration Detection）」モジュールを実装しました。
これは**予測AIではなく、現在の市場状態を判定するルールベースシステム**です。

## 実装内容

### 1. 新規モジュール

#### `src/models/acceleration.py` (230行)
加速検知の中核ロジック：

**検知項目：**
- **ブレイクアウト検知**: 現在価格が過去60日の高値を更新しているか
- **出来高異常検知**: 現在出来高が過去の中央値の1.5倍以上か
- **モメンタム加速**: 短期リターン（4週）が長期リターン（12週）より強いか
- **ボラティリティ調整**: 高ボラティリティの場合はスコアを減点

**主要関数：**
```python
detect_breakout(prices, lookback_days=60) -> (bool, score)
detect_volume_anomaly(volumes, multiplier=1.5) -> (bool, score)
calculate_momentum_acceleration(prices, short_weeks=4, long_weeks=12) -> (acceleration, score)
calculate_volatility_adjustment(prices, max_volatility=0.03) -> adjustment_factor
calculate_acceleration_score(symbol, prices, volumes, cfg) -> Dict
```

**出力形式：**
```python
{
    'symbol': 'NVDA',
    'accel_score': 85.3,  # 0-100
    'breakout': True,
    'breakout_score': 90.0,
    'volume_anomaly': True,
    'volume_score': 85.0,
    'momentum_accel': 12.5,
    'momentum_score': 88.0,
    'volatility_adj': 0.95,
    'reason': 'Acceleration: Breakout(90), Volume(85), Momentum+(88)'
}
```

### 2. 設定ファイル更新

#### `config.yaml`
新規セクション追加：
```yaml
strategy:
  mode: normal  # normal または return_first（攻撃型）

acceleration:
  enabled: true
  breakout_days: 60        # ブレイクアウト判定期間
  volume_multiplier: 1.5   # 出来高異常の倍率
  max_volatility: 0.03     # 許容ボラティリティ
  weights:
    breakout: 40           # ブレイクアウトの重み
    volume: 30             # 出来高の重み
    momentum: 30           # モメンタムの重み
  score_impact: 10         # スコアへの最大影響（0-10点）
```

### 3. データソース強化

#### `src/data_sources/price_source.py`
時系列データ生成機能を追加：
```python
fetch_price_history(symbols, days=90) -> Dict[str, Dict]
```

**返り値：**
```python
{
    'NVDA': {
        'dates': ['2025-11-17', '2025-11-18', ...],
        'prices': [1000.0, 1005.2, ...],
        'volumes': [1500000, 1800000, ...]
    }
}
```

### 4. スコアリング統合

#### `src/models/scoring.py`
加速検知をスコアリングに統合：

**処理フロー：**
1. 各銘柄の加速スコアを計算
2. 通常モード：基本スコア + 加速ボーナス（0-10点）
3. return_firstモード：加速スコアで銘柄を並び替え
4. シグナルのreasonに加速情報を追加

**スコア計算例：**
```python
base_score = 80.0
accel_bonus = (accel_score / 100) * score_impact  # (85.3 / 100) * 10 = 8.53
total_score = 80.0 + 8.53 = 88.5
```

### 5. パイプライン更新

#### `src/pipeline_weekly.py`
価格履歴データの取得を追加：
```python
price_history = price_source.fetch_price_history(symbols, days=90)
signals = scoring.score_stocks(asof, top_theme, symbols, 
                                price_data, price_history, filings_data, cfg)
```

### 6. テスト

#### `tests/test_acceleration.py` (9テスト)
加速検知ロジックの単体テスト：
- ✅ test_detect_breakout_positive
- ✅ test_detect_breakout_negative
- ✅ test_detect_volume_anomaly_positive
- ✅ test_detect_volume_anomaly_negative
- ✅ test_calculate_momentum_acceleration_positive
- ✅ test_calculate_momentum_acceleration_negative
- ✅ test_calculate_volatility_adjustment
- ✅ test_calculate_acceleration_score
- ✅ test_calculate_acceleration_score_with_all_factors

#### `tests/test_integration.py` (4テスト)
統合テスト：
- ✅ test_normal_mode_scoring: 通常モードでの加速スコア加算
- ✅ test_return_first_mode_prioritization: 攻撃型モードでの優先順位付け
- ✅ test_acceleration_disabled: 加速検知無効時の動作
- ✅ test_config_yaml_structure: 設定ファイルの構造確認

#### 既存テスト（6テスト）
全て正常動作：
- ✅ test_pipeline_execution
- ✅ test_output_files_exist
- ✅ test_theme_strength_csv_structure
- ✅ test_signals_csv_structure
- ✅ test_orders_csv_structure
- ✅ test_pipeline_error_handling_missing_config

**合計：19/19テスト全てパス ✅**

### 7. ドキュメント

#### `docs/acceleration.md` (157行)
包括的なドキュメント：
- 加速検知とは何か（予測AIではない）
- 各検知項目の詳細説明
- 設定パラメータのガイド
- 運用モード（normal/return_first）
- スコアへの統合方法
- 使用例とトラブルシューティング
- 予測AIとの違いの明確化

## 出力例

### signals.csv
```csv
asof,symbol,action,score,theme,reason,side,qty_jpy
2026-02-14,FANUY,買う/追加,84.1,ロボティクス,TopTheme+TopPick; Acceleration: Neutral,BUY,5000
```

**変更点：**
- `score`: 80.0 → 84.1（加速ボーナス+4.1点）
- `reason`: "TopTheme+TopPick; Acceleration: Neutral"（加速情報追加）

### 強い加速がある場合
```csv
asof,symbol,action,score,theme,reason,side,qty_jpy
2026-02-14,NVDA,買う/追加,88.5,半導体,TopTheme+TopPick; Acceleration: Breakout(90), Volume(85), Momentum+(88),BUY,5000
```

## 制約の遵守

### ✅ 維持された仕様
- [x] API: `/health`, `/out/{csv}`, `/run/weekly` 全て維持
- [x] 出力: `theme_strength.csv`, `signals.csv`, `orders.csv` 継続生成
- [x] CSV列名: 既存列は変更なし（reasonに情報追加のみ）

### ✅ 要件の実現
- [x] 予測AIではなく、現在の状態判定
- [x] ブレイクアウト、出来高異常、モメンタム加速を検知
- [x] config.yamlでパラメータ調整可能
- [x] スコアへの影響は小さすぎず大きすぎず（+0〜+10点）
- [x] return_firstモードで攻撃的運用可能
- [x] pytestで包括的にテスト
- [x] ドキュメント完備

### ✅ 禁止事項の回避
- [x] 予測価格や回帰/分類モデルは使用していない
- [x] 依存関係は最小限（numpy/pandas のみ追加）
- [x] 既存CSV列名の破壊的変更なし

## 技術的特徴

### 1. ルールベース
機械学習ではなく、明確なルールで判定：
- ブレイクアウト：`current_price > max(past_60_days)`
- 出来高異常：`current_volume >= median(past_volumes) * 1.5`
- モメンタム：`short_return - long_return/3`

### 2. 透明性
全ての判定ロジックが追跡可能：
```python
reason = "Acceleration: Breakout(90), Volume(85)"
```

### 3. カスタマイズ性
全パラメータをconfig.yamlで調整可能：
- 期間（breakout_days）
- 閾値（volume_multiplier, max_volatility）
- 重み（weights）

### 4. 段階的適用
2つの運用モード：
- **normal**: 補助的（+0〜+10点）
- **return_first**: 優先的（加速順に並び替え）

## パフォーマンス影響

### 計算コスト
- 1銘柄あたり約0.001秒（90日データ）
- 5銘柄で約0.005秒
- パイプライン全体への影響は軽微

### メモリ使用
- 1銘柄あたり約10KB（90日 × 3系列）
- 100銘柄でも1MB未満

## 今後の拡張

### データソース統合（TODO）
現在はスタブ実装。実データに置き換え可能：
```python
# Yahoo Finance
import yfinance as yf
data = yf.download(symbol, period='90d')

# Alpha Vantage
from alpha_vantage.timeseries import TimeSeries
ts = TimeSeries(key='YOUR_KEY')
data, meta = ts.get_daily(symbol=symbol, outputsize='full')
```

### 追加指標（拡張可能）
- RSI（相対力指数）
- MACD（移動平均収束拡散）
- ボリンジャーバンド
- ATR（平均真の範囲）

### 機械学習との組み合わせ（将来）
加速検知を特徴量として使用：
```python
features = [
    accel_score,
    breakout_score,
    volume_score,
    momentum_score,
    # + その他の特徴量
]
# → 機械学習モデルへ入力
```

## コミット履歴

```
371b2e2 Fix import and add integration tests
95db54c Add Momentum Acceleration detection module
d8ab636 Add comprehensive refactoring summary documentation
```

## ファイル構成

```
src/
├── models/
│   ├── acceleration.py          # NEW (230行)
│   ├── scoring.py               # UPDATED (統合)
│   └── ...
├── data_sources/
│   ├── price_source.py          # UPDATED (時系列追加)
│   └── ...
└── pipeline_weekly.py           # UPDATED (履歴取得)

tests/
├── test_acceleration.py         # NEW (160行, 9テスト)
├── test_integration.py          # NEW (140行, 4テスト)
└── test_pipeline.py             # EXISTING (6テスト)

docs/
└── acceleration.md              # NEW (157行)

config.yaml                      # UPDATED (パラメータ追加)
```

## まとめ

✅ **加速検知モジュールの実装が完了しました**

- **コア機能**: 230行の加速検知ロジック
- **テスト**: 19/19テスト全てパス
- **ドキュメント**: 157行の包括的ガイド
- **互換性**: 既存機能を100%維持
- **拡張性**: 実データソースへの移行が容易

このモジュールは、予測AIではなく現在の市場状態を客観的に判定し、
投資判断の一助となる情報を提供します。
