"""
スコアリングモジュール
"""
import logging
import pandas as pd
import datetime as dt
from typing import List

logger = logging.getLogger(__name__)

def score_stocks(
    asof: dt.date,
    top_theme: str,
    symbols: List[str],
    price_data: dict,
    filings_data: dict,
    cfg: dict
) -> pd.DataFrame:
    """
    銘柄をスコアリングしてシグナルを生成
    
    Args:
        asof: 基準日
        top_theme: トップテーマ
        symbols: スクリーニング済み銘柄リスト
        price_data: 価格データ
        filings_data: 開示情報データ
        cfg: 設定
    
    Returns:
        シグナルDataFrame
    
    TODO: 実装の詳細化
    - メタトレンド（weights.meta）
    - テクニカル（weights.tech）
    - イベント（weights.event）
    - マクロ（weights.macro）
    - 各要素のスコア算出と統合
    """
    logger.info(f"Scoring {len(symbols)} stocks for theme: {top_theme}")
    
    # 設定から投資額を取得
    import os
    stock_monthly = float(os.getenv("STOCK_MONTHLY_JPY", cfg["execution"]["stock_monthly_jpy"]))
    extra = float(os.getenv("EXTRA_CASH_JPY", cfg["execution"]["extra_cash_jpy"]))
    
    # ルール：月5,000円はトップテーマの上位1銘柄へ
    main = symbols[0] if symbols else ""
    
    rows = []
    if main:
        rows.append({
            "asof": asof.isoformat(),
            "symbol": main,
            "action": "買う/追加",
            "score": 80.0,
            "theme": top_theme,
            "reason": "TopTheme+TopPick",
            "side": "BUY",
            "qty_jpy": int(stock_monthly),
        })
    
    if extra and len(symbols) > 1:
        rows.append({
            "asof": asof.isoformat(),
            "symbol": symbols[1],
            "action": "追加(余力)",
            "score": 75.0,
            "theme": top_theme,
            "reason": "TopTheme+ExtraCash",
            "side": "BUY",
            "qty_jpy": int(extra),
        })
    
    logger.info(f"Generated {len(rows)} signals")
    return pd.DataFrame(rows)
