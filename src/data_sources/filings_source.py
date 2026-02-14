"""
公式開示情報データソース（スタブ）
TODO: EDINET / TDnet(有料) / 企業IRページと統合
"""
import logging
from typing import Dict, List
import random

logger = logging.getLogger(__name__)

def fetch_filings_data(symbols: List[str]) -> Dict[str, List[Dict]]:
    """
    公式開示情報を取得
    
    Args:
        symbols: 銘柄コードのリスト
    
    Returns:
        {symbol: [filing_info, ...]}
    
    TODO: 実際のデータソース統合
    - EDINET（有報等）: 無料、公式
    - TDnet（適時開示）: 有料API、将来拡張
    - 企業IRページRSS/PR: スクレイピング注意
    """
    logger.info(f"Fetching filings data for {len(symbols)} symbols (stub)")
    
    result = {}
    for symbol in symbols:
        # スタブ: 空リストを返す
        result[symbol] = []
    
    return result
