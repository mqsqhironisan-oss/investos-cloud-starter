import { MarketSnapshot } from "../../infra/marketData";

export function assessLiquidity(snapshot: MarketSnapshot) {
  const dollarValue = snapshot.lastClose * snapshot.lastVolume;
  const normalized = clamp((Math.log10(Math.max(dollarValue, 1)) - 6) / 2, -1, 1);
  return {
    score: normalized,
    note: normalized < -0.3 ? "板が薄い" : "流動性は十分",
    evidence: {
      turnover_est: Math.round(dollarValue),
    },
  };
}

function clamp(v: number, min: number, max: number) {
  return Math.min(max, Math.max(min, v));
}
