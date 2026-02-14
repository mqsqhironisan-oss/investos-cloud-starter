"""
加速検知モジュールのテスト
"""
import pytest
from src.models import acceleration
import numpy as np

def test_detect_breakout_positive():
    """ブレイクアウトが正しく検知されることを確認"""
    # 過去60日は100前後、最新が110（ブレイクアウト）
    prices = [100.0] * 60 + [110.0]
    
    is_breakout, score = acceleration.detect_breakout(prices, lookback_days=60)
    
    assert is_breakout == True, "Should detect breakout"
    assert score > 50.0, "Breakout should have high score"

def test_detect_breakout_negative():
    """ブレイクアウトしていない場合を確認"""
    # 最新が過去最高値より低い
    prices = [100.0] * 30 + [105.0] + [100.0] * 29 + [103.0]
    
    is_breakout, score = acceleration.detect_breakout(prices, lookback_days=60)
    
    assert is_breakout == False, "Should not detect breakout"
    assert score < 50.0, "Non-breakout should have lower score"

def test_detect_volume_anomaly_positive():
    """出来高異常が正しく検知されることを確認"""
    # 通常は100万、最新が200万（2倍）
    volumes = [1000000] * 60 + [2000000]
    
    is_anomaly, score = acceleration.detect_volume_anomaly(volumes, multiplier=1.5)
    
    assert is_anomaly == True, "Should detect volume anomaly"
    assert score > 50.0, "Volume anomaly should have high score"

def test_detect_volume_anomaly_negative():
    """出来高異常がない場合を確認"""
    # 全て同じ出来高
    volumes = [1000000] * 61
    
    is_anomaly, score = acceleration.detect_volume_anomaly(volumes, multiplier=1.5)
    
    assert is_anomaly == False, "Should not detect volume anomaly"
    assert score < 50.0, "Normal volume should have lower score"

def test_calculate_momentum_acceleration_positive():
    """正のモメンタム加速が検知されることを確認"""
    # 最近急上昇（短期リターン > 長期リターン）
    prices = []
    for i in range(60):
        prices.append(100.0 + i * 0.5)  # 緩やかな上昇
    for i in range(20):
        prices.append(prices[-1] + 2.0)  # 急上昇
    
    acceleration_val, score = acceleration.calculate_momentum_acceleration(prices)
    
    assert acceleration_val > 0, "Should have positive acceleration"
    assert score > 50.0, "Positive acceleration should have high score"

def test_calculate_momentum_acceleration_negative():
    """負のモメンタム加速（減速）が検知されることを確認"""
    # 最近減速
    prices = []
    for i in range(60):
        prices.append(100.0 + i * 2.0)  # 急上昇
    for i in range(20):
        prices.append(prices[-1] + 0.1)  # 減速
    
    acceleration_val, score = acceleration.calculate_momentum_acceleration(prices)
    
    assert score < 75.0, "Deceleration should have lower score"

def test_calculate_volatility_adjustment():
    """ボラティリティ調整が正しく動作することを確認"""
    # 低ボラティリティ（安定）
    stable_prices = [100.0 + i * 0.1 for i in range(60)]
    adj_stable = acceleration.calculate_volatility_adjustment(stable_prices, max_volatility=0.03)
    
    # 高ボラティリティ（不安定）
    volatile_prices = [100.0]
    for i in range(59):
        change = np.random.uniform(-5, 5)
        volatile_prices.append(volatile_prices[-1] * (1 + change / 100))
    adj_volatile = acceleration.calculate_volatility_adjustment(volatile_prices, max_volatility=0.03)
    
    assert adj_stable >= adj_volatile, "Stable prices should have higher adjustment factor"
    assert 0.5 <= adj_volatile <= 1.0, "Adjustment should be in valid range"

def test_calculate_acceleration_score():
    """総合的な加速スコアが計算されることを確認"""
    # ブレイクアウト + 高出来高のシナリオ
    prices = [100.0] * 60 + [105.0, 107.0, 110.0]
    volumes = [1000000] * 60 + [1500000, 1800000, 2000000]
    
    cfg = {
        'acceleration': {
            'breakout_days': 60,
            'volume_multiplier': 1.5,
            'max_volatility': 0.03,
            'weights': {'breakout': 40, 'volume': 30, 'momentum': 30}
        }
    }
    
    result = acceleration.calculate_acceleration_score('TEST', prices, volumes, cfg)
    
    assert 'accel_score' in result
    assert 0 <= result['accel_score'] <= 100
    assert 'reason' in result
    assert 'Acceleration:' in result['reason']
    assert result['symbol'] == 'TEST'

def test_calculate_acceleration_score_with_all_factors():
    """全ての要素が揃った場合の高スコアを確認"""
    # 全ての条件を満たすシナリオ：ブレイクアウト + 高出来高 + 加速
    prices = [100.0] * 50
    # 中期的な上昇
    for i in range(30):
        prices.append(prices[-1] * 1.005)
    # 直近の急上昇（ブレイクアウト）
    for i in range(10):
        prices.append(prices[-1] * 1.02)
    
    # 出来高も急増
    volumes = [1000000] * 80 + [2500000] * 10
    
    cfg = {
        'acceleration': {
            'breakout_days': 60,
            'volume_multiplier': 1.5,
            'max_volatility': 0.05,
            'weights': {'breakout': 40, 'volume': 30, 'momentum': 30}
        }
    }
    
    result = acceleration.calculate_acceleration_score('HOT_STOCK', prices, volumes, cfg)
    
    assert result['accel_score'] > 50.0, "Should have high acceleration score"
    assert result['breakout'] == True
    assert result['volume_anomaly'] == True
    assert 'Breakout' in result['reason']
    assert 'Volume' in result['reason']
