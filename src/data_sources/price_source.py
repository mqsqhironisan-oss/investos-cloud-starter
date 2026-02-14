"""
価格データソース（スタブ）
TODO: Yahoo Finance API / Alpha Vantage / 他の価格APIと統合
"""
import logging
from typing import Dict, List
import random
import datetime as dt

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

def fetch_price_history(symbols: List[str], days: int = 90) -> Dict[str, Dict]:
    """
    銘柄の価格履歴データを取得（時系列）
    
    Args:
        symbols: 銘柄コードのリスト
        days: 取得する日数
    
    Returns:
        {symbol: {
            'dates': List[str],
            'prices': List[float],
            'volumes': List[int]
        }}
    
    TODO: 実際のAPI実装
    - Yahoo Finance - yfinance.download()
    - Alpha Vantage - TIME_SERIES_DAILY
    """
    logger.info(f"Fetching {days} days price history for {len(symbols)} symbols (stub)")
    
    result = {}
    today = dt.date.today()
    
    for symbol in symbols:
        # ダミーデータ生成：ランダムウォーク + トレンド
        base_price = random.uniform(1000, 10000)
        trend = random.uniform(-0.001, 0.002)  # 日次トレンド
        volatility = random.uniform(0.01, 0.03)  # 日次ボラティリティ
        
        dates = []
        prices = []
        volumes = []
        
        current_price = base_price
        
        for i in range(days):
            date = today - dt.timedelta(days=days - i - 1)
            dates.append(date.isoformat())
            
            # ランダムウォーク
            daily_return = random.gauss(trend, volatility)
            current_price *= (1 + daily_return)
            prices.append(round(current_price, 2))
            
            # 出来高：基準値からランダム変動
            base_volume = random.randint(1000000, 5000000)
            volume_factor = random.uniform(0.5, 2.0)
            
            # 稀に異常出来高（10%の確率で2-3倍）
            if random.random() < 0.1:
                volume_factor *= random.uniform(2.0, 3.0)
            
            volumes.append(int(base_volume * volume_factor))
        
        # 最後の5日間は上昇トレンドにすることもある（30%の確率でブレイクアウト）
        if random.random() < 0.3:
            for i in range(-5, 0):
                prices[i] *= random.uniform(1.01, 1.03)
                volumes[i] = int(volumes[i] * random.uniform(1.5, 2.5))
        
        result[symbol] = {
            'dates': dates,
            'prices': prices,
            'volumes': volumes
        }
    
    return result
