export type FactorKey =
  | "trend"
  | "breakout"
  | "volume"
  | "volatility_risk"
  | "liquidity"
  | "event_risk"
  | "theme_fit";

export type WeightProfile = Record<FactorKey, number>;

export const championWeights: WeightProfile = {
  trend: 18,
  breakout: 20,
  volume: 12,
  volatility_risk: 14,
  liquidity: 10,
  event_risk: 6,
  theme_fit: 20,
};

export const challengerWeights: WeightProfile = {
  trend: 16,
  breakout: 18,
  volume: 14,
  volatility_risk: 16,
  liquidity: 8,
  event_risk: 8,
  theme_fit: 20,
};

export const defaultWeightProfile = championWeights;
