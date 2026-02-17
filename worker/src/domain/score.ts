import { championWeights, defaultWeightProfile, FactorKey, WeightProfile } from "../config/weights";
import { assessBreakout } from "./factors/breakout";
import { assessEventRisk } from "./factors/eventRisk";
import { assessLiquidity } from "./factors/liquidity";
import { assessRisk } from "./factors/risk";
import { assessThemeFit } from "./factors/themeFit";
import { assessTrend } from "./factors/trend";
import { assessVolume } from "./factors/volume";
import { MarketSnapshot } from "../infra/marketData";

export type ActionDecision = "BUY" | "WATCH" | "PASS";

type FactorAssessment = {
  score: number; // -1..1
  note: string;
  evidence: Record<string, unknown>;
};

export type ScoreOutput = {
  total: number;
  breakdown: Record<FactorKey, number>;
  decision: ActionDecision;
  evidence: Record<string, unknown>;
};

export function calculateScore(
  ticker: string,
  snapshot: MarketSnapshot,
  weights: WeightProfile = defaultWeightProfile
): ScoreOutput {
  const factors: Record<FactorKey, FactorAssessment> = {
    trend: assessTrend(snapshot),
    breakout: assessBreakout(snapshot),
    volume: assessVolume(snapshot),
    volatility_risk: assessRisk(snapshot),
    liquidity: assessLiquidity(snapshot),
    event_risk: assessEventRisk(snapshot),
    theme_fit: assessThemeFit(ticker),
  };

  const breakdown: Record<FactorKey, number> = {
    trend: 0,
    breakout: 0,
    volume: 0,
    volatility_risk: 0,
    liquidity: 0,
    event_risk: 0,
    theme_fit: 0,
  };

  let total = 0;
  for (const key of Object.keys(factors) as FactorKey[]) {
    const contribution = Math.round(factors[key].score * weights[key]);
    breakdown[key] = contribution;
    total += contribution;
  }

  const evidence = collectEvidence(snapshot, factors);
  const normalizedTotal = clamp(total, 0, 100);
  const decision = decide(normalizedTotal, snapshot);

  return {
    total: normalizedTotal,
    breakdown,
    decision,
    evidence,
  };
}

function decide(score: number, snapshot: MarketSnapshot): ActionDecision {
  if (score >= 80 && snapshot.atrPercent <= 6 && snapshot.maxDrawdown90d > -20) {
    return "BUY";
  }
  if (score >= 60) return "WATCH";
  return "PASS";
}

function collectEvidence(
  snapshot: MarketSnapshot,
  factors: Record<FactorKey, FactorAssessment>
): Record<string, unknown> {
  return {
    breakout_60d: factors.breakout.evidence.breakout_60d ?? false,
    volume_multiple: factors.volume.evidence.volume_multiple,
    atr_percent: snapshot.atrPercent,
    max_drawdown_90d: snapshot.maxDrawdown90d,
    high_60d: snapshot.high60,
    last_close: snapshot.lastClose,
    last_volume: snapshot.lastVolume,
    theme: factors.theme_fit.evidence.theme,
  };
}

function clamp(v: number, min: number, max: number) {
  return Math.min(max, Math.max(min, v));
}

export const weightProfiles = {
  champion: championWeights,
  default: defaultWeightProfile,
};
