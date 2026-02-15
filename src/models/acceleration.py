"""
加速検知モジュール（Momentum Acceleration Detection）

注意：これは「予測AI」ではなく「現在の状態判定」です。
未来の価格を予測するのではなく、現在の加速状態を検知します。

検知項目：
1. ブレイクアウト：直近N日高値更新
2. 出来高異常：過去N日の中央値/平均のx倍
3. モメンタム加速：12週リターンと4週リターンの差
4. ボラティリティ調整：高ボラは減点
"""
import logging
import numpy as np
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

def detect_breakout(prices: List[float], lookback_days: int = 60) -> Tuple[bool, float]:
    """
    ブレイクアウト検知：直近の終値が過去N日の高値を更新しているか
    
    Args:
        prices: 価格時系列（古い順）
        lookback_days: 参照期間
    
    Returns:
        (breakout判定, スコア0-100)
    """
    if len(prices) < lookback_days + 1:
        return False, 0.0
    
    current_price = prices[-1]
    historical_high = max(prices[-lookback_days-1:-1])
    
    # 現在価格が過去最高値を更新しているか
    is_breakout = current_price > historical_high
    
    # スコア：更新率に応じて0-100
    if is_breakout:
        pct_above = ((current_price / historical_high) - 1) * 100
        score = min(100.0, 50.0 + pct_above * 10)  # 基準50点 + 更新率で加点
    else:
        # 高値に近いほど点数を付ける（最高値の95%以上なら一定点数）
        ratio = current_price / historical_high
        if ratio >= 0.95:
            score = 40.0
        elif ratio >= 0.90:
            score = 20.0
        else:
            score = 0.0
    
    return is_breakout, score

def detect_volume_anomaly(volumes: List[int], multiplier: float = 1.5) -> Tuple[bool, float]:
    """
    出来高異常検知：現在の出来高が過去の中央値のx倍以上か
    
    Args:
        volumes: 出来高時系列（古い順）
        multiplier: 異常判定の倍率
    
    Returns:
        (異常判定, スコア0-100)
    """
    if len(volumes) < 20:
        return False, 0.0
    
    current_volume = volumes[-1]
    historical_median = np.median(volumes[:-1])
    
    if historical_median == 0:
        return False, 0.0
    
    volume_ratio = current_volume / historical_median
    is_anomaly = volume_ratio >= multiplier
    
    # スコア：倍率に応じて0-100
    if volume_ratio >= 2.0:
        score = 100.0
    elif volume_ratio >= multiplier:
        # multiplier(1.5)〜2.0の範囲を50-100点にマップ
        score = 50.0 + (volume_ratio - multiplier) / (2.0 - multiplier) * 50.0
    else:
        # multiplier未満は倍率に応じて0-50点
        score = (volume_ratio / multiplier) * 50.0
    
    return is_anomaly, min(100.0, score)

def calculate_momentum_acceleration(prices: List[float], short_weeks: int = 4, long_weeks: int = 12) -> Tuple[float, float]:
    """
    モメンタム加速計算：長期リターンと短期リターンの差
    
    Args:
        prices: 価格時系列（週次または日次、古い順）
        short_weeks: 短期期間（週）
        long_weeks: 長期期間（週）
    
    Returns:
        (加速度, スコア0-100)
    
    注意：日次データの場合は weeks * 5 で日数換算
    """
    # 簡易的に週 = 5営業日として換算
    short_days = short_weeks * 5
    long_days = long_weeks * 5
    
    if len(prices) < long_days + 1:
        return 0.0, 0.0
    
    current_price = prices[-1]
    
    # 短期リターン（4週前比）
    if len(prices) >= short_days + 1:
        short_return = (current_price / prices[-short_days-1] - 1) * 100
    else:
        short_return = 0.0
    
    # 長期リターン（12週前比）
    if len(prices) >= long_days + 1:
        long_return = (current_price / prices[-long_days-1] - 1) * 100
    else:
        long_return = 0.0
    
    # 加速度 = 短期が長期より強い上昇をしているか
    acceleration = short_return - (long_return / 3)  # 長期を正規化
    
    # スコア：加速度に応じて0-100
    # プラス加速（短期＞長期）は高得点、マイナス加速は低得点
    if acceleration > 10:
        score = 100.0
    elif acceleration > 5:
        score = 75.0 + (acceleration - 5) / 5 * 25.0
    elif acceleration > 0:
        score = 50.0 + (acceleration / 5) * 25.0
    elif acceleration > -5:
        score = 25.0 + ((acceleration + 5) / 5) * 25.0
    else:
        score = 0.0
    
    return acceleration, min(100.0, max(0.0, score))

def calculate_volatility_adjustment(prices: List[float], max_volatility: float = 0.03) -> float:
    """
    ボラティリティ調整：高ボラは減点
    
    Args:
        prices: 価格時系列
        max_volatility: 許容ボラティリティ（日次標準偏差の閾値）
    
    Returns:
        調整係数（0.5-1.0）高ボラほど低い値
    """
    if len(prices) < 20:
        return 1.0
    
    # 日次リターンの標準偏差を計算
    returns = []
    for i in range(1, len(prices)):
        ret = (prices[i] / prices[i-1]) - 1
        returns.append(ret)
    
    volatility = np.std(returns) if len(returns) > 0 else 0.0
    
    # ボラティリティが高いほど減点（0.5〜1.0の範囲）
    if volatility <= max_volatility:
        return 1.0
    elif volatility >= max_volatility * 3:
        return 0.5
    else:
        # 線形補間
        return 1.0 - (volatility - max_volatility) / (max_volatility * 2) * 0.5

def calculate_acceleration_score(
    symbol: str,
    prices: List[float],
    volumes: List[int],
    cfg: dict
) -> Dict:
    """
    加速スコアを計算
    
    Args:
        symbol: 銘柄コード
        prices: 価格時系列（古い順、最低60日推奨）
        volumes: 出来高時系列
        cfg: 設定（acceleration パラメータ）
    
    Returns:
        {
            'symbol': str,
            'accel_score': float (0-100),
            'breakout': bool,
            'breakout_score': float,
            'volume_anomaly': bool,
            'volume_score': float,
            'momentum_accel': float,
            'momentum_score': float,
            'volatility_adj': float,
            'reason': str
        }
    """
    # 設定から加速検知パラメータを取得
    accel_cfg = cfg.get('acceleration', {})
    breakout_days = accel_cfg.get('breakout_days', 60)
    volume_multiplier = accel_cfg.get('volume_multiplier', 1.5)
    max_volatility = accel_cfg.get('max_volatility', 0.03)
    
    # 各要素のスコア計算
    breakout, breakout_score = detect_breakout(prices, breakout_days)
    volume_anomaly, volume_score = detect_volume_anomaly(volumes, volume_multiplier)
    momentum_accel, momentum_score = calculate_momentum_acceleration(prices)
    volatility_adj = calculate_volatility_adjustment(prices, max_volatility)
    
    # 重み付け平均でaccel_scoreを算出
    weights = accel_cfg.get('weights', {'breakout': 40, 'volume': 30, 'momentum': 30})
    total_weight = weights['breakout'] + weights['volume'] + weights['momentum']
    
    accel_score = (
        breakout_score * weights['breakout'] +
        volume_score * weights['volume'] +
        momentum_score * weights['momentum']
    ) / total_weight
    
    # ボラティリティ調整を適用
    accel_score *= volatility_adj
    
    # 理由文字列を生成
    reason_parts = []
    if breakout:
        reason_parts.append(f"Breakout({int(breakout_score)})")
    if volume_anomaly:
        reason_parts.append(f"Volume({int(volume_score)})")
    if momentum_accel > 5:
        reason_parts.append(f"Momentum+({int(momentum_score)})")
    elif momentum_accel < -5:
        reason_parts.append(f"Momentum-({int(momentum_score)})")
    
    if volatility_adj < 0.9:
        reason_parts.append(f"HighVol(x{volatility_adj:.2f})")
    
    reason = "Acceleration: " + ", ".join(reason_parts) if reason_parts else "Acceleration: Neutral"
    
    logger.debug(f"{symbol}: accel_score={accel_score:.1f}, reason={reason}")
    
    return {
        'symbol': symbol,
        'accel_score': round(accel_score, 1),
        'breakout': breakout,
        'breakout_score': round(breakout_score, 1),
        'volume_anomaly': volume_anomaly,
        'volume_score': round(volume_score, 1),
        'momentum_accel': round(momentum_accel, 2),
        'momentum_score': round(momentum_score, 1),
        'volatility_adj': round(volatility_adj, 2),
        'reason': reason
    }
