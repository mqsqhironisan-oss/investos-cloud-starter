import { ActionDecision } from "../domain/score";
import { buildUserPrompt, systemPrompt } from "./prompts";

type OpenAIResponse = {
  output_text?: string;
  output?: Array<{ content: Array<{ text: string }> }>;
};

type EnvVars = { OPENAI_API_KEY?: string };

export async function buildRationale(options: {
  env: EnvVars;
  ticker: string;
  decision: ActionDecision;
  scoreTotal: number;
  scoreBreakdown: Record<string, number>;
  evidence: Record<string, unknown>;
}): Promise<string> {
  const apiKey = (options.env as { OPENAI_API_KEY?: string }).OPENAI_API_KEY;
  const prompt = buildUserPrompt({
    ticker: options.ticker,
    decision: options.decision,
    scoreTotal: options.scoreTotal,
    scoreBreakdown: options.scoreBreakdown,
    evidence: options.evidence,
  });

  if (!apiKey) {
    return fallbackText(options.decision, options.scoreTotal, options.evidence);
  }

  try {
    const response = await fetch("https://api.openai.com/v1/responses", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "gpt-4.1-mini",
        input: [
          { role: "system", content: [{ type: "text", text: systemPrompt }] },
          { role: "user", content: [{ type: "text", text: prompt }] },
        ],
        max_output_tokens: 600,
        response_format: { type: "text" },
      }),
    });

    if (!response.ok) {
      const err = await safeParseError(response);
      return fallbackText(options.decision, options.scoreTotal, {
        ...options.evidence,
        error: err,
      });
    }

    const data = (await response.json()) as OpenAIResponse;
    const text =
      data.output_text ??
      data.output?.[0]?.content?.[0]?.text ??
      fallbackText(options.decision, options.scoreTotal, options.evidence);
    return text;
  } catch (error) {
    return fallbackText(options.decision, options.scoreTotal, {
      ...options.evidence,
      error: String(error),
    });
  }
}

function fallbackText(
  decision: ActionDecision,
  score: number,
  evidence: Record<string, unknown>
): string {
  const hints = Object.entries(evidence)
    .slice(0, 4)
    .map(([k, v]) => `${k}: ${v}`)
    .join(" / ");
  return `決定: ${decision} (スコア ${score})。計算済みの指標を要約: ${hints}。AIキー未設定または利用不可のため、簡易説明のみを表示しています。投資判断は自己責任で。`;
}

async function safeParseError(resp: Response): Promise<string> {
  try {
    const json = (await resp.json()) as any;
    if (json?.error?.message) return json.error.message as string;
    return JSON.stringify(json ?? {});
  } catch {
    return `${resp.status} ${resp.statusText}`;
  }
}
