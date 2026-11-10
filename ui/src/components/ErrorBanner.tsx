import type { ApiError } from "../types";

const RETRYABLE = new Set(["TIMEOUT", "AGENT_ERROR"]);

export default function ErrorBanner({ error, onRetry }: { error: ApiError; onRetry: () => void }) {
  return (
    <div role="alert" className="rise flex items-center gap-3 rounded-xl border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-bar-text">
      <span aria-hidden>⚠</span>
      <span className="flex-1">{error.message}</span>
      {RETRYABLE.has(error.code) && (
        <button onClick={onRetry} className="rounded-lg border border-danger/60 px-3 py-1 text-xs font-semibold text-danger transition hover:bg-danger/20">
          Retry
        </button>
      )}
    </div>
  );
}
