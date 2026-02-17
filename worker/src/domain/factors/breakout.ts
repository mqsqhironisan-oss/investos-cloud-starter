import { MarketSnapshot } from "../../infra/marketData";

export function assessBreakout(snapshot: MarketSnapshot) {
  const ratio = snapshot.lastClose / snapshot.high60;
  const distance = (snapshot.high60 - snapshot.lastClose) / snapshot.high60;
  const normalized = Math.min(1, Math.max(-1, (ratio - 0.95) / 0.07)); // >=1.02 -> 1
  return {
    score: normalized,
    note: ratio >= 1 ? "60日高値更新" : "高値圏を試す",
    evidence: {
      breakout_60d: ratio >= 1,
      position_vs_high: Number((distance * 100).toFixed(2)),
    },
  };
}
