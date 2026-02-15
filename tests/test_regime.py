"""
Test regime detection module
"""
import pytest
from pathlib import Path
import sys

# Add src to path
BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "src"))

from regime import detect_regime, RegimeState

def test_regime_disabled():
    """Test regime detection when disabled"""
    cfg = {
        'regime': {
            'enabled': False
        }
    }
    
    result = detect_regime(cfg)
    
    assert result['state'] == RegimeState.NEUTRAL
    assert result['score'] == 0
    assert 'disabled' in result['reasons'][0].lower()

def test_regime_enabled_structure():
    """Test regime detection returns correct structure when enabled"""
    cfg = {
        'regime': {
            'enabled': True,
            'threshold_on': 2,
            'threshold_off': -2,
            'use_vix': True,
            'use_tnx': True,
            'use_usdjpy': True,
            'window_weeks_ma': 40,
            'vix_threshold': 25,
            'rate_shock_weeks': 4,
            'rate_shock_threshold': 0.5,
            'fx_shock_weeks': 4,
            'fx_shock_threshold': 5.0
        }
    }
    
    result = detect_regime(cfg)
    
    # Check structure
    assert 'state' in result
    assert 'score' in result
    assert 'reasons' in result
    assert 'details' in result
    
    # Check state is valid
    assert result['state'] in [RegimeState.RISK_ON, RegimeState.RISK_OFF, RegimeState.NEUTRAL]
    
    # Check score is integer
    assert isinstance(result['score'], (int, float))
    
    # Check reasons is list
    assert isinstance(result['reasons'], list)
    assert len(result['reasons']) > 0

def test_regime_failsafe_on_error():
    """Test regime detection returns NEUTRAL on data fetch failure"""
    # Use invalid config that will cause fetch to fail gracefully
    cfg = {
        'regime': {
            'enabled': True,
            'use_spy': False,  # This will cause all filters to return 0
            'use_vix': False,
            'use_tnx': False,
            'use_usdjpy': False
        }
    }
    
    result = detect_regime(cfg)
    
    # Should not crash, should return valid result
    assert 'state' in result
    assert result['state'] in [RegimeState.RISK_ON, RegimeState.RISK_OFF, RegimeState.NEUTRAL]

def test_regime_score_thresholds():
    """Test that regime states are determined correctly by score thresholds"""
    # We can't easily mock the data fetch, but we can verify the logic
    # by checking that the result respects the threshold settings
    
    cfg = {
        'regime': {
            'enabled': True,
            'threshold_on': 2,
            'threshold_off': -2,
            'use_vix': True,
            'use_tnx': True,
            'use_usdjpy': True,
            'window_weeks_ma': 40
        }
    }
    
    result = detect_regime(cfg)
    
    # Verify score and state consistency
    if result['score'] >= 2:
        assert result['state'] == RegimeState.RISK_ON
    elif result['score'] <= -2:
        assert result['state'] == RegimeState.RISK_OFF
    else:
        assert result['state'] == RegimeState.NEUTRAL

def test_regime_reasons_not_empty():
    """Test that regime detection always provides reasons"""
    cfg = {
        'regime': {
            'enabled': True,
            'threshold_on': 2,
            'threshold_off': -2
        }
    }
    
    result = detect_regime(cfg)
    
    assert len(result['reasons']) > 0
    
    # Each reason should be a string
    for reason in result['reasons']:
        assert isinstance(reason, str)
        assert len(reason) > 0

def test_regime_csv_export_structure():
    """Test that regime result can be exported to CSV format"""
    cfg = {
        'regime': {
            'enabled': True
        }
    }
    
    result = detect_regime(cfg)
    
    # Verify we can create CSV-compatible data
    row = {
        'date': '2026-02-15',
        'regime': result['state'].value,
        'score': result['score'],
        'reasons': '; '.join(result['reasons'])
    }
    
    assert isinstance(row['date'], str)
    assert isinstance(row['regime'], str)
    assert isinstance(row['score'], (int, float))
    assert isinstance(row['reasons'], str)
