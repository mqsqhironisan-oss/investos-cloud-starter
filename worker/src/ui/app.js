const form = document.getElementById("ticker-form");
const input = document.getElementById("ticker-input");
const result = document.getElementById("result");
const emptyState = document.getElementById("empty-state");
const errorState = document.getElementById("error-state");
const decisionText = document.getElementById("decision-text");
const scoreTotal = document.getElementById("score-total");
const breakdownBars = document.getElementById("breakdown-bars");
const rationaleText = document.getElementById("rationale-text");
const dataGrid = document.getElementById("data-grid");
const analyzeBtn = document.getElementById("analyze-btn");
const decisionCard = document.getElementById("decision-card");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const ticker = input.value.trim();
  if (!ticker) return;
  setLoading(true);
  hideError();
  try {
    const res = await fetch(`/api/analyze?ticker=${encodeURIComponent(ticker)}`);
    const data = await res.json();
    if (!res.ok || data.error) {
      throw new Error(data.reason || data.error || "Unexpected error");
    }
    render(data);
  } catch (err) {
    showError(err.message);
  } finally {
    setLoading(false);
  }
});

function render(payload) {
  emptyState.classList.add("hidden");
  result.classList.remove("hidden");
  errorState.classList.add("hidden");

  decisionText.textContent = payload.action;
  decisionCard.setAttribute("data-decision", payload.action);
  decisionCard.classList.remove("buy", "watch", "pass");
  decisionCard.classList.add(payload.action.toLowerCase());
  scoreTotal.textContent = payload.score_total;
  renderBreakdown(payload.score_breakdown);
  rationaleText.textContent = payload.rationale_ai;
  renderData(payload);
}

function renderBreakdown(breakdown) {
  const labels = {
    trend: "トレンド",
    breakout: "ブレイクアウト",
    volume: "出来高",
    volatility_risk: "ボラ・リスク",
    liquidity: "流動性",
    event_risk: "イベントリスク",
    theme_fit: "テーマ適合",
  };
  breakdownBars.innerHTML = "";
  Object.entries(breakdown).forEach(([key, value]) => {
    const bar = document.createElement("div");
    bar.className = "bar";
    const track = document.createElement("div");
    track.className = "track";
    const fill = document.createElement("div");
    fill.className = "fill";
    fill.style.width = `${Math.min(Math.abs(value), 100)}%`;
    fill.style.background = value >= 0 ? "#34d399" : "#f87171";
    fill.style.transformOrigin = value >= 0 ? "left" : "right";
    track.appendChild(fill);
    bar.innerHTML = `
      <span class="name">${labels[key] ?? key}</span>
    `;
    bar.appendChild(track);
    const val = document.createElement("span");
    val.className = "value";
    val.textContent = value.toString();
    bar.appendChild(val);
    breakdownBars.appendChild(bar);
  });
}

function renderData(payload) {
  const entries = {
    ティッカー: payload.ticker,
    更新: new Date(payload.asof).toLocaleString(),
    終値: payload.market?.close,
    "60日高値": payload.market?.high_60d,
    "60日安値": payload.market?.low_60d,
    出来高: payload.market?.volume,
    "ATR%": payload.market?.atr_percent,
    "90日DD%": payload.market?.max_drawdown_90d,
    "出来高倍率": payload.evidence?.volume_multiple,
  };
  dataGrid.innerHTML = "";
  Object.entries(entries).forEach(([k, v]) => {
    const item = document.createElement("div");
    item.className = "item";
    item.innerHTML = `<p class="label">${k}</p><p>${v ?? "—"}</p>`;
    dataGrid.appendChild(item);
  });
}

function showError(message) {
  errorState.textContent = message;
  errorState.classList.remove("hidden");
  result.classList.add("hidden");
}

function hideError() {
  errorState.classList.add("hidden");
  errorState.textContent = "";
}

function setLoading(loading) {
  analyzeBtn.disabled = loading;
  analyzeBtn.textContent = loading ? "分析中..." : "Analyze";
}
