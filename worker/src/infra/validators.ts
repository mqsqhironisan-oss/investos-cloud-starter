const jpTicker = /^[0-9]{4}\.T$/i;
const usTicker = /^[A-Za-z]{1,5}(\.[A-Za-z]{1,2})?$/;

export function validateTicker(ticker: string): { ok: boolean; reason?: string } {
  if (!ticker) return { ok: false, reason: "ticker_required" };
  const trimmed = ticker.trim();
  if (jpTicker.test(trimmed) || usTicker.test(trimmed)) {
    return { ok: true };
  }
  return { ok: false, reason: "invalid_format" };
}
