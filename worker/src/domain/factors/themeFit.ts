import { inferThemeFromTicker } from "../../config/universe";

export function assessThemeFit(ticker: string) {
  const theme = inferThemeFromTicker(ticker);
  const normalized = theme === "general" ? 0.2 : 0.7;
  return {
    score: normalized,
    note: theme === "general" ? "汎用銘柄" : "テーマ適合",
    evidence: { theme },
  };
}
