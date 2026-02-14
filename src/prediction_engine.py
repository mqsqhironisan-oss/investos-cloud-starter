"""
AI株価予想エンジン
- 簡易的なトレンド分析とテクニカル指標を用いて株価予想を生成
- 実装：移動平均、トレンド判定、予想価格算出
"""
import pandas as pd
import datetime as dt
import random
from typing import Tuple, List, Dict

def calculate_moving_averages(prices: List[float]) -> Dict[str, float]:
    """移動平均を計算（簡易版）"""
    if len(prices) < 5:
        return {"ma5": prices[-1] if prices else 50.0, "ma20": prices[-1] if prices else 50.0}
    
    ma5 = sum(prices[-5:]) / 5
    ma20 = sum(prices[-20:]) / 20 if len(prices) >= 20 else sum(prices) / len(prices)
    return {"ma5": ma5, "ma20": ma20}

def determine_trend(current_price: float, ma5: float, ma20: float) -> str:
    """トレンドを判定"""
    if current_price > ma5 > ma20:
        return "UP"
    elif current_price < ma5 < ma20:
        return "DOWN"
    else:
        return "NEUTRAL"

def calculate_momentum(prices: List[float]) -> float:
    """モメンタムを計算（価格変化率）"""
    if len(prices) < 2:
        return 0.0
    recent_change = (prices[-1] - prices[-5]) / prices[-5] if len(prices) >= 5 else 0.0
    return recent_change

def generate_prediction(symbol: str, theme: str, asof: dt.date) -> Dict:
    """
    個別銘柄の予想を生成
    
    実際の実装では、ここで以下を行う：
    1. 過去の価格データを取得
    2. テクニカル指標を計算
    3. AIモデル（または統計モデル）で予想
    
    現在はダミーデータで動作確認用の構造を提供
    """
    # ダミーの過去価格データ（実装時はAPIから取得）
    base_price = random.uniform(1000, 10000)
    historical_prices = [base_price * (1 + random.uniform(-0.05, 0.05)) for _ in range(30)]
    current_price = historical_prices[-1]
    
    # 移動平均計算
    ma_data = calculate_moving_averages(historical_prices)
    ma5 = ma_data["ma5"]
    ma20 = ma_data["ma20"]
    
    # トレンド判定
    trend = determine_trend(current_price, ma5, ma20)
    
    # モメンタム計算
    momentum = calculate_momentum(historical_prices)
    
    # 予想価格の算出（簡易版：トレンドとモメンタムベース）
    if trend == "UP":
        # 上昇トレンド：1週間で+2-5%, 1ヶ月で+5-15%
        predicted_1w = current_price * (1 + random.uniform(0.02, 0.05))
        predicted_1m = current_price * (1 + random.uniform(0.05, 0.15))
        signal = "BUY"
        confidence = random.uniform(65, 85)
        reason = "上昇トレンド継続。短期MA > 長期MA。モメンタム強い。"
    elif trend == "DOWN":
        # 下降トレンド：1週間で-2-5%, 1ヶ月で-5-15%
        predicted_1w = current_price * (1 - random.uniform(0.02, 0.05))
        predicted_1m = current_price * (1 - random.uniform(0.05, 0.15))
        signal = "SELL"
        confidence = random.uniform(60, 80)
        reason = "下降トレンド。短期MA < 長期MA。売り圧力強い。"
    else:
        # 中立：1週間で±1%, 1ヶ月で±3%
        predicted_1w = current_price * (1 + random.uniform(-0.01, 0.01))
        predicted_1m = current_price * (1 + random.uniform(-0.03, 0.03))
        signal = "HOLD"
        confidence = random.uniform(50, 70)
        reason = "レンジ相場。様子見推奨。明確なトレンドなし。"
    
    # テーマの強さも考慮（theme_strengthと連動させる）
    if theme in ["半導体", "AIインフラ"] and trend != "DOWN":
        # 強いテーマの場合、予想を上方修正
        predicted_1w *= 1.02
        predicted_1m *= 1.05
        confidence += 5
        reason += f" {theme}テーマが強い。"
    
    return {
        "asof": asof.isoformat(),
        "symbol": symbol,
        "theme": theme,
        "current_price": round(current_price, 2),
        "predicted_1w": round(predicted_1w, 2),
        "predicted_1m": round(predicted_1m, 2),
        "trend": trend,
        "signal": signal,
        "confidence": round(min(confidence, 95), 1),
        "ma5": round(ma5, 2),
        "ma20": round(ma20, 2),
        "momentum": round(momentum * 100, 2),
        "reason": reason
    }

def generate_predictions_for_stocks(stocks: List[Tuple[str, str]], asof: dt.date) -> pd.DataFrame:
    """
    複数銘柄の予想を一括生成
    
    Args:
        stocks: [(symbol, theme), ...] のリスト
        asof: 予想日
    
    Returns:
        予想結果のDataFrame
    """
    predictions = []
    for symbol, theme in stocks:
        pred = generate_prediction(symbol, theme, asof)
        predictions.append(pred)
    
    df = pd.DataFrame(predictions)
    # 信頼度が高い順にソート
    df = df.sort_values("confidence", ascending=False)
    return df

def get_stock_recommendations(predictions_df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    """
    予想から推奨銘柄を抽出
    
    Args:
        predictions_df: 予想結果のDataFrame
        top_n: 上位N件を抽出
    
    Returns:
        推奨銘柄のDataFrame
    """
    # BUYシグナルで信頼度が高いものを抽出
    buy_signals = predictions_df[predictions_df["signal"] == "BUY"].copy()
    buy_signals = buy_signals.sort_values("confidence", ascending=False).head(top_n)
    return buy_signals
