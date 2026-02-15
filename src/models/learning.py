"""
学習レイヤー（Learning Layer）
テーマ重みの自動調整

注意：これは「予測モデル」ではなく、過去の実績に基づく「重み最適化」です。
- 売買判断は学習に任せない
- 学習はテーマ重みの微調整のみ
- シャドーモード固定（本番環境には影響しない）

Champion/Challenger パターン:
- Champion: 本番で使用中の重み（data/models/champion_weights.json）
- Challenger: 学習が提案する新しい重み（data/models/challenger_weights.json）
- Challengerは週次で更新されるが、Championは評価を経てのみ更新
"""
import logging
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple
import datetime as dt

logger = logging.getLogger(__name__)

# テーマ名（日本語）から内部キーへのマッピング
THEME_MAP = {
    "半導体": "semis",
    "AIインフラ": "ai_infra",
    "レアメタル": "rare_metals",
    "ロボティクス": "robotics"
}

THEME_MAP_REVERSE = {v: k for k, v in THEME_MAP.items()}

def get_default_weights() -> Dict[str, float]:
    """デフォルトのテーマ重み（均等配分）"""
    return {
        "semis": 0.25,
        "ai_infra": 0.25,
        "rare_metals": 0.25,
        "robotics": 0.25
    }

def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """重みを正規化して合計を1.0にする"""
    total = sum(weights.values())
    if total == 0:
        return get_default_weights()
    return {k: v / total for k, v in weights.items()}

def enforce_bounds(weights: Dict[str, float], min_weight: float = 0.10, max_weight: float = 0.50) -> Dict[str, float]:
    """
    重みに上限・下限を適用
    
    Args:
        weights: テーマ重み
        min_weight: 最小重み
        max_weight: 最大重み
    
    Returns:
        制約を満たす重み（正規化済み）
    """
    bounded = {}
    for theme, weight in weights.items():
        bounded[theme] = max(min_weight, min(max_weight, weight))
    
    # 正規化して合計を1.0に（ただし範囲は守る）
    total = sum(bounded.values())
    if total == 0:
        return get_default_weights()
    
    # 正規化
    normalized = {k: v / total for k, v in bounded.items()}
    
    # 正規化後に再度境界チェック（正規化で境界を超えた場合の調整）
    needs_adjustment = any(v < min_weight or v > max_weight for v in normalized.values())
    if needs_adjustment:
        # 境界を超える場合は、繰り返し調整
        for _ in range(10):  # 最大10回の調整試行
            adjusted = {}
            for theme, weight in normalized.items():
                adjusted[theme] = max(min_weight, min(max_weight, weight))
            
            # 再正規化
            total = sum(adjusted.values())
            normalized = {k: v / total for k, v in adjusted.items()}
            
            # すべてが範囲内か確認
            if all(min_weight <= v <= max_weight for v in normalized.values()):
                break
    
    return normalized

def limit_change(current_weights: Dict[str, float], new_weights: Dict[str, float], max_delta: float = 0.10) -> Dict[str, float]:
    """
    重みの変更幅を制限（週次で最大±10%）
    
    Args:
        current_weights: 現在の重み
        new_weights: 新しい重み
        max_delta: 最大変更幅（0.10 = 10%）
    
    Returns:
        変更制限を適用した重み（正規化済み）
    """
    limited = {}
    for theme in current_weights.keys():
        current = current_weights[theme]
        new = new_weights.get(theme, current)
        
        # 変更幅を制限
        delta = new - current
        if abs(delta) > max_delta:
            delta = max_delta if delta > 0 else -max_delta
        
        limited[theme] = current + delta
    
    # 正規化（ただし変更幅を再度チェック）
    normalized = normalize_weights(limited)
    
    # 正規化で変更幅が大きくなった場合、再調整
    for _ in range(5):  # 最大5回の調整試行
        max_actual_delta = max(abs(normalized[theme] - current_weights[theme]) for theme in current_weights.keys())
        if max_actual_delta <= max_delta + 1e-6:
            break
        
        # 変更幅が大きすぎる場合、現在値に近づける
        adjusted = {}
        for theme in current_weights.keys():
            current = current_weights[theme]
            proposed = normalized[theme]
            delta = proposed - current
            if abs(delta) > max_delta:
                delta = max_delta * 0.9 if delta > 0 else -max_delta * 0.9  # 少し余裕を持たせる
            adjusted[theme] = current + delta
        
        normalized = normalize_weights(adjusted)
    
    return normalized

def load_weights(filepath: Path) -> Dict[str, float]:
    """
    重みファイルを読み込み
    
    Args:
        filepath: JSONファイルのパス
    
    Returns:
        テーマ重み辞書
    """
    if not filepath.exists():
        logger.info(f"Weights file not found: {filepath}, using defaults")
        return get_default_weights()
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        weights = data.get('weights', {})
        logger.info(f"Loaded weights from {filepath}: {weights}")
        return weights
    except Exception as e:
        logger.error(f"Failed to load weights from {filepath}: {e}")
        return get_default_weights()

def save_weights(filepath: Path, weights: Dict[str, float], metadata: Dict = None):
    """
    重みをJSONファイルに保存
    
    Args:
        filepath: JSONファイルのパス
        weights: テーマ重み
        metadata: 追加メタデータ
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        'weights': weights,
        'updated_at': dt.datetime.now().isoformat(),
        'metadata': metadata or {}
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved weights to {filepath}")

def calculate_theme_performance(theme: str, price_history: Dict, weeks: int = 52) -> Tuple[float, float]:
    """
    テーマの過去パフォーマンスを計算
    
    Args:
        theme: テーマ名（内部キー）
        price_history: 価格履歴データ
        weeks: 評価期間（週）
    
    Returns:
        (return, risk) - リターンとリスク
    
    TODO: 実際のデータソース統合
    - 各テーマの代表銘柄バスケットを定義
    - 実際の価格データから計算
    """
    # スタブ実装：ランダムなパフォーマンス生成
    # 実運用では実際の価格データから計算
    np.random.seed(hash(theme) % (2**32))
    
    # リターン: -10% 〜 +30%
    annual_return = np.random.uniform(-0.10, 0.30)
    
    # リスク（ボラティリティ）: 10% 〜 40%
    annual_volatility = np.random.uniform(0.10, 0.40)
    
    return annual_return, annual_volatility

def optimize_weights(
    themes: list,
    price_history: Dict,
    current_weights: Dict[str, float],
    cfg: Dict
) -> Dict[str, float]:
    """
    過去実績に基づいて重みを最適化
    
    Args:
        themes: テーマリスト
        price_history: 価格履歴データ
        current_weights: 現在の重み
        cfg: 学習設定
    
    Returns:
        最適化された重み
    
    最適化アルゴリズム:
    1. 各テーマの過去52週のリターン/リスクを計算
    2. 目的関数: リターン最大化 + DDペナルティ（軽め）
    3. 制約: 重み合計=1.0, 各重み 0.10-0.50
    4. 変更幅制限: 週次で±10%まで
    """
    learn_cfg = cfg.get('learn', {})
    window_weeks = learn_cfg.get('window_weeks', 52)
    bounds = learn_cfg.get('bounds', {'min': 0.10, 'max': 0.50})
    max_delta = learn_cfg.get('max_delta', 0.10)
    objective = learn_cfg.get('objective', 'return_first')
    
    logger.info(f"Optimizing weights with {objective} objective over {window_weeks} weeks")
    
    # 各テーマのパフォーマンスを計算
    theme_stats = {}
    for theme_key in current_weights.keys():
        theme_return, theme_risk = calculate_theme_performance(theme_key, price_history, window_weeks)
        theme_stats[theme_key] = {
            'return': theme_return,
            'risk': theme_risk
        }
        logger.debug(f"{theme_key}: return={theme_return:.2%}, risk={theme_risk:.2%}")
    
    # 目的関数に基づいて重みを計算
    if objective == 'return_first':
        # リターン重視（リスク調整は軽め）
        scores = {}
        for theme_key, stats in theme_stats.items():
            # スコア = リターン - 0.5 * リスク
            scores[theme_key] = stats['return'] - 0.5 * stats['risk']
    else:
        # シャープレシオ（リスク調整後リターン）
        scores = {}
        for theme_key, stats in theme_stats.items():
            if stats['risk'] > 0:
                scores[theme_key] = stats['return'] / stats['risk']
            else:
                scores[theme_key] = stats['return']
    
    # スコアを正規化して重みに変換（ソフトマックス的）
    # ただし、負のスコアは最小重みに
    min_score = min(scores.values())
    if min_score < 0:
        # 全て正にシフト
        scores = {k: v - min_score + 0.1 for k, v in scores.items()}
    
    # 正規化
    new_weights = normalize_weights(scores)
    
    # 制約を適用
    new_weights = enforce_bounds(new_weights, bounds['min'], bounds['max'])
    
    # 変更幅を制限
    new_weights = limit_change(current_weights, new_weights, max_delta)
    
    logger.info(f"Optimized weights: {new_weights}")
    
    return new_weights

def update_challenger(
    base_dir: Path,
    themes: list,
    price_history: Dict,
    cfg: Dict
) -> Dict[str, float]:
    """
    Challenger重みを更新
    
    Args:
        base_dir: ベースディレクトリ
        themes: テーマリスト
        price_history: 価格履歴
        cfg: 設定
    
    Returns:
        新しいChallenger重み
    """
    models_dir = base_dir / "data" / "models"
    champion_file = models_dir / "champion_weights.json"
    challenger_file = models_dir / "challenger_weights.json"
    
    # 現在のChampion重みを読み込み
    champion_weights = load_weights(champion_file)
    
    # 新しい重みを最適化
    new_weights = optimize_weights(themes, price_history, champion_weights, cfg)
    
    # Challenger重みとして保存
    save_weights(challenger_file, new_weights, {
        'source': 'optimizer',
        'previous_champion': champion_weights
    })
    
    return new_weights

def save_weights_history(
    out_dir: Path,
    asof: dt.date,
    champion_weights: Dict[str, float],
    challenger_weights: Dict[str, float]
):
    """
    重みの履歴をCSVに保存
    
    Args:
        out_dir: 出力ディレクトリ（out/learn/）
        asof: 日付
        champion_weights: Champion重み
        challenger_weights: Challenger重み
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Champion履歴
    champion_file = out_dir / "weights_champion.csv"
    champion_row = {'asof': asof.isoformat()}
    champion_row.update(champion_weights)
    
    champion_df = pd.DataFrame([champion_row])
    if champion_file.exists():
        existing = pd.read_csv(champion_file)
        champion_df = pd.concat([existing, champion_df], ignore_index=True)
    
    champion_df.to_csv(champion_file, index=False)
    logger.info(f"Saved champion history to {champion_file}")
    
    # Challenger履歴
    challenger_file = out_dir / "weights_challenger.csv"
    challenger_row = {'asof': asof.isoformat()}
    challenger_row.update(challenger_weights)
    
    challenger_df = pd.DataFrame([challenger_row])
    if challenger_file.exists():
        existing = pd.read_csv(challenger_file)
        challenger_df = pd.concat([existing, challenger_df], ignore_index=True)
    
    challenger_df.to_csv(challenger_file, index=False)
    logger.info(f"Saved challenger history to {challenger_file}")

def copy_to_docs(base_dir: Path):
    """
    最新の重みをdocs/data/にコピー（GitHub Pages用）
    
    Args:
        base_dir: ベースディレクトリ
    """
    import shutil
    
    learn_dir = base_dir / "out" / "learn"
    docs_data_dir = base_dir / "docs" / "data"
    docs_data_dir.mkdir(parents=True, exist_ok=True)
    
    # CSV履歴をコピー
    for filename in ["weights_champion.csv", "weights_challenger.csv"]:
        src = learn_dir / filename
        if src.exists():
            dst = docs_data_dir / filename
            shutil.copy2(src, dst)
            logger.info(f"Copied {filename} to docs/data/")
    
    # JSONもコピー
    models_dir = base_dir / "data" / "models"
    for filename in ["champion_weights.json", "challenger_weights.json"]:
        src = models_dir / filename
        if src.exists():
            dst = docs_data_dir / filename
            shutil.copy2(src, dst)
            logger.info(f"Copied {filename} to docs/data/")
