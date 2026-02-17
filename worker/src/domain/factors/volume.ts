import { MarketSnapshot } from "../../infra/marketData";

export function assessVolume(snapshot: MarketSnapshot) {
  const volumeMultiple = snapshot.lastVolume / Math.max(1, snapshot.volumeMedian);
  const normalized = Math.min(1, Math.max(-1, (volumeMultiple - 1) / 2)); // 3x -> 1
  return {
    score: normalized,
    note: volumeMultiple >= 1 ? "出来高増加" : "出来高減少",
    evidence: {
      volume_multiple: Number(volumeMultiple.toFixed(2)),
      volume_median: snapshot.volumeMedian,
    },
  };
}
