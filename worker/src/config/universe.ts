type Theme =
  | "semiconductor"
  | "ai_infra"
  | "robotics"
  | "ev_supply"
  | "mobility"
  | "general";

const themeCatalog: Record<Theme, { keywords: string[]; examples: string[] }> = {
  semiconductor: {
    keywords: ["TSM", "NVDA", "SOX", "半導体", "chip", "arm", "amd"],
    examples: ["TSM", "NVDA", "ASML", "8035.T", "6857.T"],
  },
  ai_infra: {
    keywords: ["AI", "cloud", "data", "GPU", "DC"],
    examples: ["AMZN", "MSFT", "GOOGL", "META", "9753.T"],
  },
  robotics: {
    keywords: ["robot", "automation", "factory", "sensor"],
    examples: ["6645.T", "6902.T", "FANUY"],
  },
  ev_supply: {
    keywords: ["battery", "EV", "電池", "charging", "rare metal"],
    examples: ["7203.T", "TSLA", "6752.T"],
  },
  mobility: {
    keywords: ["auto", "mobility", "car", "rail"],
    examples: ["7203.T", "7267.T", "JR"],
  },
  general: {
    keywords: [],
    examples: [],
  },
};

export function inferThemeFromTicker(ticker: string): Theme {
  const upper = ticker.toUpperCase();
  for (const [theme, { keywords, examples }] of Object.entries(themeCatalog)) {
    if (examples.includes(upper)) return theme as Theme;
    if (keywords.some((word) => upper.includes(word.toUpperCase()))) {
      return theme as Theme;
    }
  }
  if (upper.endsWith(".T")) return "mobility";
  return "general";
}

export function describeTheme(theme: Theme): string {
  switch (theme) {
    case "semiconductor":
      return "半導体・先端製造";
    case "ai_infra":
      return "AIインフラ・クラウド";
    case "robotics":
      return "ロボティクス・自動化";
    case "ev_supply":
      return "EV・蓄電池サプライチェーン";
    case "mobility":
      return "モビリティ";
    default:
      return "汎用";
  }
}
