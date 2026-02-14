"""
価格データソース（スタブ）
TODO: Yahoo Finance API / Alpha Vantage / 他の価格APIと統合
"""
import logging
from typing import Dict, List
import random

logger = logging.getLogger(__name__)

def fetch_price_data(symbols: List[str]) -> Dict[str, Dict]:
    """
    銘柄の価格データを取得
    
    Args:
        symbols: 銘柄コードのリスト
    
    Returns:
        {symbol: {price: float, volume: int, ...}}
    
    TODO: 実際のAPI実装
    - Yahoo Finance
    - Alpha Vantage
    - その他価格データプロバイダー
    """
    logger.info(f"Fetching price data for {len(symbols)} symbols (stub)")
    
    result = {}
    for symbol in symbols:
        result[symbol] = {
            "price": round(random.uniform(1000, 10000), 2),
            "volume": random.randint(100000, 10000000),
            "change_pct": round(random.uniform(-5, 5), 2),
        }
    
    return result
