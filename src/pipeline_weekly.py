
"""
週次パイプライン（スタブ）
- このスターターは「構造」を提供する。データソースは後で差し替え可能。
- 出力：out/theme_strength.csv, out/scores.csv, out/signals.csv, out/orders.csv
"""
from pathlib import Path
import pandas as pd
import datetime as dt
import yaml
import os
import math
import random

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "out"
CFG = BASE / "config.yaml"

THEMES = ["半導体","AIインフラ","レアメタル","ロボティクス"]

def load_cfg():
    with open(CFG, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def theme_strength_stub(asof: dt.date) -> pd.DataFrame:
    # TODO: 実装：指数/代表銘柄群/マクロ/公式資料テキストで算出
    # 今はダミー（構造確認用）
    rows = []
    for t in THEMES:
        rows.append({"asof": asof.isoformat(), "theme": t, "strength": round(random.uniform(40, 80), 2)})
    df = pd.DataFrame(rows).sort_values("strength", ascending=False)
    return df

def screening_stub(theme: str) -> list[str]:
    # TODO: 実装：財務＋トレンド＋流動性で日米スクリーニング
    # 今はダミーのシンボル
    if theme == "半導体":
        return ["NVDA","TSM","ASML","8035","6857"]
    if theme == "AIインフラ":
        return ["MSFT","AMZN","GOOGL","9432","9984"]
    if theme == "レアメタル":
        return ["FCX","BHP","RIO","5713","5802"]
    if theme == "ロボティクス":
        return ["FANUY","ABB","TER","6954","6146"]
    return []

def build_signals(asof: dt.date, top_theme: str, cfg: dict) -> pd.DataFrame:
    stock_monthly = float(os.getenv("STOCK_MONTHLY_JPY", cfg["execution"]["stock_monthly_jpy"]))
    extra = float(os.getenv("EXTRA_CASH_JPY", cfg["execution"]["extra_cash_jpy"]))

    # ルール：月5,000円はトップテーマの上位1銘柄へ
    picks = screening_stub(top_theme)
    main = picks[0] if picks else ""

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
    if extra and len(picks) > 1:
        rows.append({
            "asof": asof.isoformat(),
            "symbol": picks[1],
            "action": "追加(余力)",
            "score": 75.0,
            "theme": top_theme,
            "reason": "TopTheme+ExtraCash",
            "side": "BUY",
            "qty_jpy": int(extra),
        })
    return pd.DataFrame(rows)

def build_orders(asof: dt.date, signals: pd.DataFrame) -> pd.DataFrame:
    # B運用：CSVを作り、手動発注 or RSSに流す
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
    return pd.DataFrame(rows)

def main():
    cfg = load_cfg()
    asof = dt.date.today()
    OUT.mkdir(exist_ok=True)

    ts = theme_strength_stub(asof)
    ts.to_csv(OUT/"theme_strength.csv", index=False, encoding="utf-8")

    top_theme = ts.iloc[0]["theme"] if len(ts) else THEMES[0]
    signals = build_signals(asof, top_theme, cfg)
    signals.to_csv(OUT/"signals.csv", index=False, encoding="utf-8")

    orders = build_orders(asof, signals)
    orders.to_csv(OUT/"orders.csv", index=False, encoding="utf-8")

    # scores.csv は将来拡張
    pd.DataFrame([{"asof": asof.isoformat(), "note": "stub"}]).to_csv(OUT/"scores.csv", index=False, encoding="utf-8")

    print("weekly pipeline done", asof, top_theme)

if __name__ == "__main__":
    main()
