/**
 * Cloudflare Workers - InvestOS Chat API Proxy
 * 
 * This Worker acts as a proxy between the frontend chat interface and OpenAI API.
 * It keeps the API key secure on the server side.
 * 
 * Setup:
 * 1. Create a new Worker in Cloudflare Dashboard
 * 2. Copy this code to the Worker editor
 * 3. Add environment variable: OPENAI_API_KEY (your OpenAI API key)
 * 4. Deploy the Worker
 * 5. Update your frontend to use the Worker URL: window.INVESTOS_CHAT_API = 'https://your-worker.workers.dev/chat'
 */

export default {
  async fetch(request, env) {
    // CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
        },
      });
    }

    // Only allow POST
    if (request.method !== "POST") {
      return new Response("Method Not Allowed", { status: 405 });
    }

    try {
      const { message, context } = await request.json();

      // Validate input
      if (!message || typeof message !== 'string') {
        return new Response(JSON.stringify({ error: "Invalid message" }), {
          status: 400,
          headers: { "Content-Type": "application/json" }
        });
      }

      // System prompt with guardrails (no price prediction)
      const system = `
あなたはInvestOSのアドバイザーです。

【厳守事項】
- 価格予測は禁止：将来の株価・為替・指数の予測や断定は一切行わない
- 売買指示の禁止：「買うべき」「売るべき」などの指示は行わない

【許可されること】
- 現在の状態の説明：レジーム判定、テーマ強度、加速検知、シグナルの意味を説明
- データの解釈：提供されたコンテキスト（CSV）の内容を分かりやすく説明
- 一般的な情報：投資の考え方、リスク管理の重要性など

【回答形式】
1. 結論を簡潔に述べる
2. 理由やデータの根拠を説明
3. 注意事項や次に確認すべきことを提示

常に「投資判断はご自身で」と注意喚起すること。
`;

      // User prompt with context
      const user = `
ユーザー質問: ${message}

コンテキスト（最新データ）:
${JSON.stringify(context ?? {}, null, 2)}
`;

      // Call OpenAI API
      const resp = await fetch("https://api.openai.com/v1/chat/completions", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${env.OPENAI_API_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: "gpt-4o-mini",
          messages: [
            { role: "system", content: system },
            { role: "user", content: user },
          ],
          temperature: 0.2,
          max_tokens: 800,
        }),
      });

      if (!resp.ok) {
        throw new Error(`OpenAI API error: ${resp.status}`);
      }

      const data = await resp.json();
      const text = data?.choices?.[0]?.message?.content ?? "No response";

      return new Response(JSON.stringify({ reply: text }), {
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });

    } catch (error) {
      console.error("Error:", error);
      return new Response(JSON.stringify({ 
        error: "Internal server error",
        message: error.message 
      }), {
        status: 500,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }
  },
};
