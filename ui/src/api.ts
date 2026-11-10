import { ApiError, type ChatResponse, type ErrorCode } from "./types";
import matchesFixture from "./fixtures/matches.json";
import zeroFixture from "./fixtures/zero.json";

const USE_FIXTURES = import.meta.env.VITE_USE_FIXTURES === "true";
const TIMEOUT_MS = 30_000;

let apiUrlPromise: Promise<string> | null = null;

function apiUrl(): Promise<string> {
  if (!apiUrlPromise) {
    const fromEnv = import.meta.env.VITE_API_URL as string | undefined;
    apiUrlPromise = fromEnv
      ? Promise.resolve(fromEnv)
      : fetch("/config.json").then((r) => r.json()).then((c: { apiUrl: string }) => c.apiUrl);
  }
  return apiUrlPromise;
}

const FRIENDLY: Record<ErrorCode, string> = {
  INVALID_REQUEST: "Please send a message between 1 and 500 characters.",
  THROTTLED: "The bar is busy, try again in a moment.",
  TIMEOUT: "The sommelier is taking too long. Try again.",
  AGENT_ERROR: "Something spilled. Try again.",
};

async function post(body: object): Promise<unknown> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(await apiUrl(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      const code = (data?.error?.code as ErrorCode) ?? (res.status === 429 ? "THROTTLED" : res.status === 504 ? "TIMEOUT" : "AGENT_ERROR");
      const known = code in FRIENDLY ? code : "AGENT_ERROR";
      throw new ApiError(known, known === "INVALID_REQUEST" ? data?.error?.message ?? FRIENDLY[known] : FRIENDLY[known]);
    }
    return data;
  } catch (e) {
    if (e instanceof ApiError) throw e;
    if (e instanceof DOMException && e.name === "AbortError") throw new ApiError("TIMEOUT", FRIENDLY.TIMEOUT);
    throw new ApiError("AGENT_ERROR", FRIENDLY.AGENT_ERROR);
  } finally {
    clearTimeout(timer);
  }
}

function fixture(sessionId: string, text: string): Promise<ChatResponse> {
  return new Promise((resolve, reject) =>
    setTimeout(() => {
      const t = text.toLowerCase();
      if (t.includes("error")) return reject(new ApiError("AGENT_ERROR", FRIENDLY.AGENT_ERROR));
      if (t.includes("slow")) return reject(new ApiError("TIMEOUT", FRIENDLY.TIMEOUT));
      const base = /vodka|france|capital|forget/.test(t) ? zeroFixture : matchesFixture;
      resolve({ ...(base as ChatResponse), session_id: sessionId });
    }, 800),
  );
}

export function sendMessage(sessionId: string, text: string): Promise<ChatResponse> {
  if (USE_FIXTURES) return fixture(sessionId, text);
  return post({ session_id: sessionId, message: text }) as Promise<ChatResponse>;
}

export function warmup(sessionId: string): void {
  if (USE_FIXTURES) return;
  post({ session_id: sessionId, warmup: true }).catch(() => undefined);
}
