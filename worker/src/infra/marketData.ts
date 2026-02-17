export interface MarketSnapshot {
  ticker: string;
  asof: string;
  closes: number[];
  volumes: number[];
  high60: number;
  low60: number;
  lastClose: number;
  lastVolume: number;
  atrPercent: number;
  maxDrawdown90d: number;
  volumeMedian: number;
}

function seededRandom(seed: string): () => number {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = Math.imul(31, h) + seed.charCodeAt(i);
  return () => {
    h ^= h << 13;
    h ^= h >> 17;
    h ^= h << 5;
    return ((h >>> 0) % 1000) / 1000;
  };
}

export async function fetchMarketData(ticker: string): Promise<MarketSnapshot> {
  const rand = seededRandom(ticker.toUpperCase());
  const base = 50 + rand() * 100;
  const closes: number[] = [];
  const volumes: number[] = [];

  let price = base;
  for (let i = 0; i < 120; i++) {
    const drift = (rand() - 0.45) * 0.6;
    price = Math.max(5, price * (1 + drift / 100));
    closes.push(Number(price.toFixed(2)));
    const vol = 500000 * (0.8 + rand() * 0.6);
    volumes.push(Math.round(vol));
  }

  const lastClose = closes[closes.length - 1];
  const lastVolume = volumes[volumes.length - 1];
  const tail60 = closes.slice(-60);
  const tail60Vol = volumes.slice(-60);

  const high60 = Math.max(...tail60);
  const low60 = Math.min(...tail60);
  const volumeMedian = median(tail60Vol);
  const atrPercent = calcAtrPercent(closes);
  const maxDrawdown90d = calcMaxDrawdown(closes.slice(-90));

  return {
    ticker,
    asof: new Date().toISOString(),
    closes,
    volumes,
    high60,
    low60,
    lastClose,
    lastVolume,
    atrPercent,
    maxDrawdown90d,
    volumeMedian,
  };
}

function median(values: number[]): number {
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  if (sorted.length % 2 === 0) return (sorted[mid - 1] + sorted[mid]) / 2;
  return sorted[mid];
}

function calcAtrPercent(closes: number[]): number {
  if (closes.length < 2) return 0;
  let total = 0;
  for (let i = 1; i < closes.length; i++) {
    total += Math.abs(closes[i] - closes[i - 1]);
  }
  const atr = total / (closes.length - 1);
  const last = closes[closes.length - 1] || 1;
  return Number(((atr / last) * 100).toFixed(2));
}

function calcMaxDrawdown(series: number[]): number {
  let peak = series[0] ?? 0;
  let maxDd = 0;
  for (const price of series) {
    if (price > peak) peak = price;
    const dd = (price - peak) / peak;
    if (dd < maxDd) maxDd = dd;
  }
  return Number((maxDd * 100).toFixed(2));
}
