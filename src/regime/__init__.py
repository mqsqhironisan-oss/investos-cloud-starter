"""
Regime detection module
Determines market regime (RISK_ON / RISK_OFF / NEUTRAL) based on rules and statistics
No prediction models - only rule-based + statistical analysis
"""

from .regime_detector import detect_regime, RegimeState

__all__ = ['detect_regime', 'RegimeState']
