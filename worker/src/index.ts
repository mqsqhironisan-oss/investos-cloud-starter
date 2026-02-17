import appHtml from "./ui/app.html";
import appCss from "./ui/app.css";
import appClientJs from "./ui/app.js";
import { fetchMarketData } from "./infra/marketData";
import { validateTicker } from "./infra/validators";
import { buildRationale } from "./ai/rationale";
import { calculateScore } from "./domain/score";
import { getCache, readThrough } from "./infra/cache";

export interface Env {
  OPENAI_API_KEY?: string;
  CACHE?: KVNamespace;
}

const DISCLAIMER =
  "本情報は過去データに基づく説明であり、将来の価格を予測しません。投資判断は自己責任でお願いします。";

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname === "/") return respondHtml(appHtml);
    if (url.pathname === "/app.css") return new Response(appCss, { headers: { "content-type": "text/css" } });
    if (url.pathname === "/app.js")
      return new Response(appClientJs, { headers: { "content-type": "text/javascript" } });
    if (url.pathname === "/api/health") return respondJson(health(env));
    if (url.pathname === "/api/analyze") return handleAnalyze(url, env);
    return new Response("Not found", { status: 404 });
  },
};

async function handleAnalyze(url: URL, env: Env): Promise<Response> {
  const ticker = url.searchParams.get("ticker")?.trim() ?? "";
  const skipAi = url.searchParams.get("skip_ai") === "1";
  const validation = validateTicker(ticker);
  if (!validation.ok) {
    return respondJson({ error: "invalid_ticker", reason: validation.reason }, 400);
  }

  const cache = getCache(env);
  const payload = await readThrough(cache, `analyze:${ticker}`, async () => {
    const snapshot = await fetchMarketData(ticker);
    const score = calculateScore(ticker, snapshot);
    const rationale = skipAi
      ? "AI生成をスキップしました（skip_ai=1）。"
      : await buildRationale({
          env,
          ticker,
          decision: score.decision,
          scoreTotal: score.total,
          scoreBreakdown: score.breakdown,
          evidence: score.evidence,
        });

    return {
      ticker,
      asof: snapshot.asof,
      action: score.decision,
      score_total: score.total,
      score_breakdown: score.breakdown,
      evidence: score.evidence,
      rationale_ai: rationale,
      disclaimer: DISCLAIMER,
      market: {
        close: snapshot.lastClose,
        high_60d: snapshot.high60,
        low_60d: snapshot.low60,
        volume: snapshot.lastVolume,
        atr_percent: snapshot.atrPercent,
        max_drawdown_90d: snapshot.maxDrawdown90d,
      },
    };
  }, 600);

  return respondJson(payload);
}

function health(env: Env) {
  return {
    status: "ok",
    has_openai_key: Boolean(env.OPENAI_API_KEY),
    cache: env.CACHE ? "kv" : "memory",
    timestamp: new Date().toISOString(),
  };
}

function respondHtml(body: string): Response {
  return new Response(body, {
    headers: { "content-type": "text/html; charset=UTF-8", "cache-control": "no-cache" },
  });
}

function respondJson(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body, null, 2), {
    status,
    headers: {
      "content-type": "application/json; charset=UTF-8",
      "cache-control": "no-store",
    },
  });
}
