import { MarketSnapshot } from "../../infra/marketData";

export function assessEventRisk(snapshot: MarketSnapshot) {
  const atrRisk = snapshot.atrPercent > 4 ? -0.4 : -0.1;
  const ddRisk = snapshot.maxDrawdown90d < -10 ? -0.4 : -0.1;
  const normalized = Math.max(-1, atrRisk + ddRisk);
  return {
    score: normalized,
    note: normalized < -0.5 ? "イベントリスク警戒" : "イベントリスク小",
    evidence: {
      risk_flag: normalized < -0.5,
    },
  };
}
