"""
マクロ経済データソース（スタブ）
TODO: FRED / IMF / 日銀統計などと統合
"""
import logging
from typing import Dict
import random

logger = logging.getLogger(__name__)

def fetch_macro_indicators() -> Dict[str, float]:
    """
    マクロ経済指標を取得
    
    Returns:
        {indicator_name: value}
    
    TODO: 実際のAPI実装
    - FRED (Federal Reserve Economic Data)
    - IMF Data
    - 日銀統計
    - その他マクロ経済データ
    """
    logger.info("Fetching macro indicators (stub)")
    
    return {
        "interest_rate": round(random.uniform(0, 5), 2),
        "inflation_rate": round(random.uniform(-2, 10), 2),
        "gdp_growth": round(random.uniform(-5, 5), 2),
        "usd_jpy": round(random.uniform(100, 160), 2),
    }
