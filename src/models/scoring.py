"""
スコアリングモジュール
"""
import logging
import pandas as pd
import datetime as dt
from typing import List, Dict

logger = logging.getLogger(__name__)

def score_stocks(
    asof: dt.date,
    top_theme: str,
    symbols: List[str],
    price_data: dict,
    price_history: dict,
    filings_data: dict,
    cfg: dict
) -> pd.DataFrame:
    """
    銘柄をスコアリングしてシグナルを生成
    
    Args:
        asof: 基準日
        top_theme: トップテーマ
        symbols: スクリーニング済み銘柄リスト
        price_data: 価格データ（現在値）
        price_history: 価格履歴データ（時系列）
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
    
    # 加速検知モジュールをインポート
    from . import acceleration
    
    # 設定から投資額を取得
    import os
    stock_monthly = float(os.getenv("STOCK_MONTHLY_JPY", cfg["execution"]["stock_monthly_jpy"]))
    extra = float(os.getenv("EXTRA_CASH_JPY", cfg["execution"]["extra_cash_jpy"]))
    
    # 加速検知が有効か確認
    accel_enabled = cfg.get('acceleration', {}).get('enabled', True)
    score_impact = cfg.get('acceleration', {}).get('score_impact', 10)
    mode = cfg.get('strategy', {}).get('mode', 'normal')
    
    # 各銘柄の加速スコアを計算
    accel_scores = {}
    if accel_enabled and price_history:
        for symbol in symbols:
            if symbol in price_history:
                hist = price_history[symbol]
                accel_result = acceleration.calculate_acceleration_score(
                    symbol, hist['prices'], hist['volumes'], cfg
                )
                accel_scores[symbol] = accel_result
            else:
                accel_scores[symbol] = {
                    'accel_score': 0.0,
                    'reason': 'Acceleration: No data'
                }
    
    # return_firstモードの場合、加速スコアで並び替え
    if mode == 'return_first' and accel_scores:
        # 加速スコアの高い順にソート
        sorted_symbols = sorted(
            symbols,
            key=lambda s: accel_scores.get(s, {}).get('accel_score', 0.0),
            reverse=True
        )
        logger.info(f"return_first mode: Prioritizing by acceleration score")
    else:
        sorted_symbols = symbols
    
    # ルール：月5,000円はトップテーマの上位1銘柄へ
    main = sorted_symbols[0] if sorted_symbols else ""
    
    rows = []
    if main:
        # 基本スコア
        base_score = 80.0
        
        # 加速スコアを加算（0-10点の範囲）
        accel_info = accel_scores.get(main, {})
        accel_bonus = (accel_info.get('accel_score', 0.0) / 100.0) * score_impact
        total_score = base_score + accel_bonus
        
        # 理由に加速情報を追加
        base_reason = "TopTheme+TopPick"
        accel_reason = accel_info.get('reason', '')
        if accel_reason and accel_reason != 'Acceleration: No data':
            full_reason = f"{base_reason}; {accel_reason}"
        else:
            full_reason = base_reason
        
        rows.append({
            "asof": asof.isoformat(),
            "symbol": main,
            "action": "買う/追加",
            "score": round(total_score, 1),
            "theme": top_theme,
            "reason": full_reason,
            "side": "BUY",
            "qty_jpy": int(stock_monthly),
        })
    
    if extra and len(sorted_symbols) > 1:
        second = sorted_symbols[1]
        base_score = 75.0
        
        # 加速スコアを加算
        accel_info = accel_scores.get(second, {})
        accel_bonus = (accel_info.get('accel_score', 0.0) / 100.0) * score_impact
        total_score = base_score + accel_bonus
        
        # 理由に加速情報を追加
        base_reason = "TopTheme+ExtraCash"
        accel_reason = accel_info.get('reason', '')
        if accel_reason and accel_reason != 'Acceleration: No data':
            full_reason = f"{base_reason}; {accel_reason}"
        else:
            full_reason = base_reason
        
        rows.append({
            "asof": asof.isoformat(),
            "symbol": second,
            "action": "追加(余力)",
            "score": round(total_score, 1),
            "theme": top_theme,
            "reason": full_reason,
            "side": "BUY",
            "qty_jpy": int(extra),
        })
    
    logger.info(f"Generated {len(rows)} signals")
    return pd.DataFrame(rows)
