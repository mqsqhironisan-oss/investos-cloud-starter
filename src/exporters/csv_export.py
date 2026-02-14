"""
CSV出力モジュール
"""
import logging
import pandas as pd
from pathlib import Path
import datetime as dt

logger = logging.getLogger(__name__)

def export_theme_strength(df: pd.DataFrame, output_dir: Path) -> None:
    """テーマ強度をCSV出力"""
    filepath = output_dir / "theme_strength.csv"
    df.to_csv(filepath, index=False, encoding="utf-8")
    logger.info(f"Exported theme_strength.csv ({len(df)} rows)")

def export_signals(df: pd.DataFrame, output_dir: Path) -> None:
    """シグナルをCSV出力"""
    filepath = output_dir / "signals.csv"
    df.to_csv(filepath, index=False, encoding="utf-8")
    logger.info(f"Exported signals.csv ({len(df)} rows)")

def export_orders(df: pd.DataFrame, output_dir: Path) -> None:
    """注文をCSV出力"""
    filepath = output_dir / "orders.csv"
    df.to_csv(filepath, index=False, encoding="utf-8")
    logger.info(f"Exported orders.csv ({len(df)} rows)")

def export_scores(asof: dt.date, output_dir: Path) -> None:
    """スコア詳細をCSV出力（将来拡張用）"""
    filepath = output_dir / "scores.csv"
    pd.DataFrame([{"asof": asof.isoformat(), "note": "stub"}]).to_csv(
        filepath, index=False, encoding="utf-8"
    )
    logger.info("Exported scores.csv (stub)")

def build_orders(asof: dt.date, signals: pd.DataFrame) -> pd.DataFrame:
    """
    シグナルから注文データを生成
    
    Args:
        asof: 基準日
        signals: シグナルDataFrame
    
    Returns:
        注文DataFrame
    """
    rows = []
    for _, r in signals.iterrows():
        rows.append({
            "asof": asof.isoformat(),
            "symbol": r["symbol"],
            "market": "AUTO",
            "side": r["side"],
            "order_type": "LIMIT",
            "limit_price": "",
            "qty": r["qty_jpy"],
            "note": r["reason"],
        })
    
    logger.info(f"Built {len(rows)} orders from signals")
    return pd.DataFrame(rows)
