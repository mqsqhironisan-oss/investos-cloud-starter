#!/usr/bin/env python3
"""
予想結果の簡易表示スクリプト
predictions.csvを読み込んで、見やすく表示する
"""
import pandas as pd
from pathlib import Path

def display_predictions():
    """予想結果を表示"""
    base = Path(__file__).resolve().parents[1]
    predictions_file = base / "out" / "predictions.csv"
    recommendations_file = base / "out" / "recommendations.csv"
    
    if not predictions_file.exists():
        print("❌ predictions.csvが見つかりません。先にpipeline_weekly.pyを実行してください。")
        return
    
    # 予想結果を読み込み
    df = pd.read_csv(predictions_file)
    
    print("=" * 80)
    print("🤖 AI株価予想レポート")
    print("=" * 80)
    print()
    
    # 統計情報
    total = len(df)
    buy = len(df[df["signal"] == "BUY"])
    sell = len(df[df["signal"] == "SELL"])
    hold = len(df[df["signal"] == "HOLD"])
    
    print(f"📊 総銘柄数: {total}")
    print(f"   🟢 BUY: {buy} 銘柄")
    print(f"   🔴 SELL: {sell} 銘柄")
    print(f"   🟡 HOLD: {hold} 銘柄")
    print()
    
    # トレンド別統計
    trend_up = len(df[df["trend"] == "UP"])
    trend_down = len(df[df["trend"] == "DOWN"])
    trend_neutral = len(df[df["trend"] == "NEUTRAL"])
    
    print(f"📈 トレンド分析:")
    print(f"   ⬆️  上昇: {trend_up} 銘柄")
    print(f"   ⬇️  下降: {trend_down} 銘柄")
    print(f"   ➡️  中立: {trend_neutral} 銘柄")
    print()
    
    # 推奨銘柄トップ5
    if recommendations_file.exists():
        rec_df = pd.read_csv(recommendations_file)
        print("=" * 80)
        print("⭐ 推奨銘柄トップ5（信頼度が高い買い推奨）")
        print("=" * 80)
        print()
        
        for rank, (_, row) in enumerate(rec_df.head(5).iterrows(), start=1):
            print(f"{rank}. {row['symbol']:8s} ({row['theme']})")
            print(f"   現在価格: ¥{row['current_price']:,.2f}")
            print(f"   1週間後: ¥{row['predicted_1w']:,.2f} ({(row['predicted_1w']/row['current_price']-1)*100:+.2f}%)")
            print(f"   1ヶ月後: ¥{row['predicted_1m']:,.2f} ({(row['predicted_1m']/row['current_price']-1)*100:+.2f}%)")
            print(f"   信頼度: {row['confidence']:.1f}%")
            print(f"   理由: {row['reason']}")
            print()
    
    # 警告: 大幅下落予想銘柄
    sell_stocks = df[df["signal"] == "SELL"].head(3)
    if len(sell_stocks) > 0:
        print("=" * 80)
        print("⚠️  注意: 下落予想銘柄（売却検討）")
        print("=" * 80)
        print()
        
        for i, row in sell_stocks.iterrows():
            print(f"• {row['symbol']:8s} ({row['theme']})")
            print(f"  現在価格: ¥{row['current_price']:,.2f}")
            print(f"  1週間後: ¥{row['predicted_1w']:,.2f} ({(row['predicted_1w']/row['current_price']-1)*100:+.2f}%)")
            print(f"  理由: {row['reason']}")
            print()
    
    print("=" * 80)
    print("💡 このレポートは過去データに基づく統計的予想です。")
    print("   投資判断は複数の情報源を総合して、自己責任で行ってください。")
    print("=" * 80)

if __name__ == "__main__":
    display_predictions()
