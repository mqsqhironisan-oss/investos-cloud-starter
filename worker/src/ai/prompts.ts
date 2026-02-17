import { ActionDecision } from "../domain/score";

export const systemPrompt = `
You are an investment explainer. You never predict future prices.
Summarize pre-calculated signals for an equity ticker in Japanese.
Follow the output template strictly. Keep it concise and specific for retail investors.
`;

export function buildUserPrompt(input: {
  ticker: string;
  decision: ActionDecision;
  scoreTotal: number;
  scoreBreakdown: Record<string, number>;
  evidence: Record<string, unknown>;
}): string {
  const { ticker, decision, scoreTotal, scoreBreakdown, evidence } = input;
  const breakdown = Object.entries(scoreBreakdown)
    .map(([k, v]) => `${k}: ${v}`)
    .join(", ");
  const evidenceLines = Object.entries(evidence)
    .map(([k, v]) => `${k}: ${v}`)
    .join(", ");

  return `
ティッカー: ${ticker}
判定: ${decision}
スコア: ${scoreTotal}
スコア内訳: ${breakdown}
指標: ${evidenceLines}

出力フォーマット:
- 結論（BUY/WATCH/PASSのいずれか、1文）
- 根拠（最大5点、番号付き、具体的な数値を含める）
- 反証（2点。リスクや注意点）
- 次のアクション（監視条件、損切り/利確目安）
- ディスクレーマ（投資判断は自己責任）
  `;
}
