"""
Regime detection logic
Determines RISK_ON / RISK_OFF / NEUTRAL state based on:
- Trend filter (SPY vs 200MA)
- Volatility filter (VIX threshold)
- Rate filter (TNX shock)
- FX filter (USDJPY shock)
"""

import logging
from enum import Enum
from typing import Dict, Tuple
import pandas as pd

logger = logging.getLogger(__name__)

class RegimeState(Enum):
    """Regime states"""
    RISK_ON = "RISK_ON"
    RISK_OFF = "RISK_OFF"
    NEUTRAL = "NEUTRAL"

def fetch_market_data(cfg: Dict) -> Dict[str, pd.DataFrame]:
    """
    Fetch market data for regime detection
    Returns dict with 'spy', 'vix', 'tnx', 'usdjpy' keys (each may be None if fetch fails)
    """
    import yfinance as yf
    
    data = {}
    symbols = {
        'spy': 'SPY',
        'vix': '^VIX',
        'tnx': '^TNX',
        'usdjpy': 'JPY=X'
    }
    
    # Determine lookback period (need enough for MA calculation)
    ma_weeks = cfg.get('regime', {}).get('window_weeks_ma', 40)
    # Weekly data, so get 1.5x to ensure we have enough
    lookback_days = int(ma_weeks * 7 * 1.5)
    
    for key, symbol in symbols.items():
        # Check if this data source is enabled
        use_key = f'use_{key}' if key != 'spy' else None
        if use_key and not cfg.get('regime', {}).get(use_key, True):
            logger.info(f"Skipping {symbol} (disabled in config)")
            data[key] = None
            continue
        
        try:
            logger.info(f"Fetching {symbol} for regime detection")
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=f"{lookback_days}d", interval="1d")
            
            if hist.empty:
                logger.warning(f"No data returned for {symbol}")
                data[key] = None
            else:
                # Resample to weekly (using last price of week)
                weekly = hist['Close'].resample('W-FRI').last().dropna()
                data[key] = weekly
                logger.info(f"Fetched {len(weekly)} weeks of data for {symbol}")
                
        except Exception as e:
            logger.warning(f"Failed to fetch {symbol}: {e}")
            data[key] = None
    
    return data

def calculate_trend_score(spy_data: pd.Series, ma_weeks: int) -> Tuple[float, str]:
    """
    Calculate trend score based on SPY vs MA
    Returns: (score, reason)
    """
    if spy_data is None or len(spy_data) < ma_weeks:
        return 0, "SPY: insufficient data"
    
    try:
        current_price = spy_data.iloc[-1]
        ma = spy_data.iloc[-ma_weeks:].mean()
        
        if current_price > ma:
            return 1, f"SPY above {ma_weeks}W MA"
        else:
            return -1, f"SPY below {ma_weeks}W MA"
    except Exception as e:
        logger.warning(f"Trend calculation failed: {e}")
        return 0, "SPY: calculation error"

def calculate_vol_score(vix_data: pd.Series, threshold: float) -> Tuple[float, str]:
    """
    Calculate volatility score based on VIX
    Returns: (score, reason)
    """
    if vix_data is None or len(vix_data) == 0:
        return 0, "VIX: no data"
    
    try:
        current_vix = vix_data.iloc[-1]
        
        if current_vix > threshold:
            return -1, f"VIX high ({current_vix:.1f} > {threshold})"
        else:
            return 0, f"VIX normal ({current_vix:.1f})"
    except Exception as e:
        logger.warning(f"VIX calculation failed: {e}")
        return 0, "VIX: calculation error"

def calculate_rate_score(tnx_data: pd.Series, weeks: int, threshold: float) -> Tuple[float, str]:
    """
    Calculate rate shock score based on TNX change
    Returns: (score, reason)
    """
    if tnx_data is None or len(tnx_data) < weeks + 1:
        return 0, "TNX: insufficient data"
    
    try:
        current = tnx_data.iloc[-1]
        past = tnx_data.iloc[-(weeks + 1)]
        change = current - past
        
        if change > threshold:
            return -1, f"TNX shock (+{change:.2f} > {threshold})"
        else:
            return 0, f"TNX stable ({change:.2f})"
    except Exception as e:
        logger.warning(f"TNX calculation failed: {e}")
        return 0, "TNX: calculation error"

def calculate_fx_score(usdjpy_data: pd.Series, weeks: int, threshold_pct: float) -> Tuple[float, str]:
    """
    Calculate FX shock score based on USDJPY change
    Returns: (score, reason)
    """
    if usdjpy_data is None or len(usdjpy_data) < weeks + 1:
        return 0, "USDJPY: insufficient data"
    
    try:
        current = usdjpy_data.iloc[-1]
        past = usdjpy_data.iloc[-(weeks + 1)]
        change_pct = ((current - past) / past) * 100
        
        if abs(change_pct) > threshold_pct:
            return -1, f"USDJPY shock ({change_pct:+.1f}% > {threshold_pct}%)"
        else:
            return 0, f"USDJPY stable ({change_pct:+.1f}%)"
    except Exception as e:
        logger.warning(f"USDJPY calculation failed: {e}")
        return 0, "USDJPY: calculation error"

def detect_regime(cfg: Dict) -> Dict:
    """
    Main regime detection function
    Returns: {
        'state': RegimeState,
        'score': int,
        'reasons': list of str,
        'details': dict
    }
    """
    regime_cfg = cfg.get('regime', {})
    
    # Check if regime detection is enabled
    if not regime_cfg.get('enabled', False):
        logger.info("Regime detection is disabled")
        return {
            'state': RegimeState.NEUTRAL,
            'score': 0,
            'reasons': ['Regime detection disabled'],
            'details': {}
        }
    
    # Fetch market data
    try:
        market_data = fetch_market_data(cfg)
    except Exception as e:
        logger.error(f"Failed to fetch market data: {e}")
        return {
            'state': RegimeState.NEUTRAL,
            'score': 0,
            'reasons': ['Data fetch failed - failsafe to NEUTRAL'],
            'details': {'error': str(e)}
        }
    
    # Extract configuration
    ma_weeks = regime_cfg.get('window_weeks_ma', 40)
    vix_threshold = regime_cfg.get('vix_threshold', 25)
    rate_shock_weeks = regime_cfg.get('rate_shock_weeks', 4)
    rate_shock_threshold = regime_cfg.get('rate_shock_threshold', 0.5)
    fx_shock_weeks = regime_cfg.get('fx_shock_weeks', 4)
    fx_shock_threshold = regime_cfg.get('fx_shock_threshold', 5.0)
    threshold_on = regime_cfg.get('threshold_on', 2)
    threshold_off = regime_cfg.get('threshold_off', -2)
    
    # Calculate scores
    scores = []
    reasons = []
    details = {}
    
    # 1. Trend filter
    trend_score, trend_reason = calculate_trend_score(market_data.get('spy'), ma_weeks)
    scores.append(trend_score)
    reasons.append(trend_reason)
    details['trend'] = {'score': trend_score, 'reason': trend_reason}
    
    # 2. Volatility filter
    vol_score, vol_reason = calculate_vol_score(market_data.get('vix'), vix_threshold)
    scores.append(vol_score)
    reasons.append(vol_reason)
    details['vol'] = {'score': vol_score, 'reason': vol_reason}
    
    # 3. Rate filter
    rate_score, rate_reason = calculate_rate_score(
        market_data.get('tnx'), rate_shock_weeks, rate_shock_threshold
    )
    scores.append(rate_score)
    reasons.append(rate_reason)
    details['rate'] = {'score': rate_score, 'reason': rate_reason}
    
    # 4. FX filter
    fx_score, fx_reason = calculate_fx_score(
        market_data.get('usdjpy'), fx_shock_weeks, fx_shock_threshold
    )
    scores.append(fx_score)
    reasons.append(fx_reason)
    details['fx'] = {'score': fx_score, 'reason': fx_reason}
    
    # Total score
    total_score = sum(scores)
    
    # Determine state
    if total_score >= threshold_on:
        state = RegimeState.RISK_ON
    elif total_score <= threshold_off:
        state = RegimeState.RISK_OFF
    else:
        state = RegimeState.NEUTRAL
    
    logger.info(f"Regime detected: {state.value} (score: {total_score})")
    
    return {
        'state': state,
        'score': total_score,
        'reasons': reasons,
        'details': details
    }
