import { MarketSnapshot } from "../../infra/marketData";

export function assessRisk(snapshot: MarketSnapshot) {
  const atrPenalty = snapshot.atrPercent / 6; // 6% ATR -> -1
  const ddPenalty = Math.abs(snapshot.maxDrawdown90d) / 20; // 20% DD -> -1
  const penalty = Math.min(1, atrPenalty + ddPenalty);
  const normalized = -penalty;
  return {
    score: normalized,
    note: penalty > 0.8 ? "ボラティリティ高" : "リスク許容範囲",
    evidence: {
      atr_percent: snapshot.atrPercent,
      max_drawdown_90d: snapshot.maxDrawdown90d,
    },
  };
}
