import { MarketSnapshot } from "../../infra/marketData";

export function assessTrend(snapshot: MarketSnapshot) {
  const recent = snapshot.closes.slice(-60);
  const start = recent[0] ?? snapshot.closes[0];
  const end = recent[recent.length - 1] ?? snapshot.lastClose;
  const changePct = ((end - start) / start) * 100;
  const normalized = clamp(changePct / 20, -1, 1); // +/-20% → +/-1
  return {
    score: normalized,
    note: changePct >= 0 ? "上昇基調" : "下降・レンジ",
    evidence: { changePct: Number(changePct.toFixed(2)) },
  };
}

function clamp(v: number, min: number, max: number) {
  return Math.min(max, Math.max(min, v));
}
