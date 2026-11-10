import { useEffect, useRef } from "react";
import type { ApiError, ChatResponse } from "../types";
import AgentMessage from "./AgentMessage";
import ErrorBanner from "./ErrorBanner";
import ExampleChips from "./ExampleChips";
import TypingIndicator from "./TypingIndicator";

export type ChatItem = { role: "user"; text: string } | { role: "agent"; response: ChatResponse };

const MAX = 500;

interface Props {
  items: ChatItem[];
  loading: boolean;
  error: ApiError | null;
  draft: string;
  onDraft: (v: string) => void;
  onSend: (text: string) => void;
  onRetry: () => void;
}

export default function ChatWindow({ items, loading, error, draft, onDraft, onSend, onRetry }: Props) {
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [items.length, loading, error]);

  useEffect(() => {
    if (!loading) inputRef.current?.focus();
  }, [loading]);

  const submit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (draft.trim() && !loading) onSend(draft);
  };

  return (
    <>
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto flex max-w-2xl flex-col gap-5 px-4 py-6">
          {items.length === 0 && (
            <section className="rise py-6 text-center sm:py-10">
              <h2 className="font-display text-3xl font-semibold text-bar-text sm:text-4xl">What's the occasion?</h2>
              <p className="mx-auto mt-3 max-w-md text-sm leading-relaxed text-bar-muted">
                Describe a mood, a moment or a memory. I'll pick from our cellar, tell you how well each bottle fits
                and why.
              </p>
              <div className="mt-7">
                <ExampleChips onPick={onSend} disabled={loading} />
              </div>
            </section>
          )}

          {items.map((it, i) =>
            it.role === "user" ? (
              <div key={i} className="rise flex justify-end">
                <p className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-md bg-amber px-4 py-2.5 text-sm text-bar-bg">
                  {it.text}
                </p>
              </div>
            ) : (
              <AgentMessage key={i} response={it.response} />
            ),
          )}

          {loading && <TypingIndicator />}
          {error && <ErrorBanner error={error} onRetry={onRetry} />}
          <div ref={endRef} />
        </div>
      </main>

      <form onSubmit={submit} className="border-t border-bar-line bg-bar-bg">
        <div className="mx-auto flex max-w-2xl items-end gap-2 px-4 py-3">
          <div className="relative flex-1">
            <textarea
              ref={inputRef}
              value={draft}
              onChange={(e) => onDraft(e.target.value.slice(0, MAX))}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) submit(e);
              }}
              disabled={loading}
              rows={1}
              maxLength={MAX}
              placeholder={loading ? "The sommelier is choosing…" : "Rainy Sunday with a book…"}
              aria-label="Message"
              className="block max-h-32 min-h-[44px] w-full resize-none rounded-xl border border-bar-line bg-bar-panel px-4 py-2.5 pr-14 text-sm text-bar-text placeholder:text-bar-faint focus:border-amber focus:outline-none disabled:opacity-60"
            />
            {draft.length > 400 && (
              <span className="absolute bottom-2.5 right-3 text-[11px] tabular-nums text-bar-faint">
                {draft.length}/{MAX}
              </span>
            )}
          </div>
          <button
            type="submit"
            disabled={loading || !draft.trim()}
            className="h-[44px] rounded-xl bg-amber px-5 text-sm font-semibold text-bar-bg transition hover:bg-amber-soft disabled:cursor-not-allowed disabled:opacity-40"
          >
            Send
          </button>
        </div>
      </form>
    </>
  );
}
