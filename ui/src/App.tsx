import { useCallback, useEffect, useState } from "react";
import { sendMessage, warmup } from "./api";
import { ApiError, type ChatResponse } from "./types";
import ChatWindow, { type ChatItem } from "./components/ChatWindow";
import Footer from "./components/Footer";

const newId = () => crypto.randomUUID();

export default function App() {
  const [sessionId, setSessionId] = useState(newId);
  const [items, setItems] = useState<ChatItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const [draft, setDraft] = useState("");

  useEffect(() => warmup(sessionId), [sessionId]);

  const send = useCallback(
    async (text: string, { retry = false } = {}) => {
      const msg = text.trim();
      if (!msg || loading) return;
      setError(null);
      setLastMessage(msg);
      if (!retry) setItems((prev) => [...prev, { role: "user", text: msg }]);
      setDraft("");
      setLoading(true);
      try {
        const res: ChatResponse = await sendMessage(sessionId, msg);
        setItems((prev) => [...prev, { role: "agent", response: res }]);
      } catch (e) {
        const err = e instanceof ApiError ? e : new ApiError("AGENT_ERROR", "Something spilled. Try again.");
        setError(err);
        if (err.code === "INVALID_REQUEST") {
          // keep the user's input so they can fix it, and drop the bubble we optimistically added
          setDraft(msg);
          if (!retry) setItems((prev) => prev.slice(0, -1));
        }
      } finally {
        setLoading(false);
      }
    },
    [loading, sessionId],
  );

  const reset = () => {
    setSessionId(newId());
    setItems([]);
    setError(null);
    setLastMessage(null);
    setDraft("");
  };

  return (
    <div className="flex h-full flex-col">
      <header className="sticky top-0 z-10 border-b border-bar-line bg-bar-bg/90 backdrop-blur">
        <div className="mx-auto flex max-w-2xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2.5">
            <img src="/favicon.svg" alt="" className="h-7 w-7" />
            <div>
              <h1 className="font-display text-lg font-semibold leading-tight text-bar-text">The Sommelier</h1>
              <p className="text-xs text-bar-faint">Tell me the moment. I'll pour the bottle.</p>
            </div>
          </div>
          <button
            onClick={reset}
            disabled={loading}
            className="rounded-full border border-bar-line px-3 py-1.5 text-xs font-medium text-bar-muted transition hover:border-amber hover:text-amber-soft disabled:opacity-40"
          >
            New conversation
          </button>
        </div>
      </header>

      <ChatWindow
        items={items}
        loading={loading}
        error={error}
        draft={draft}
        onDraft={setDraft}
        onSend={(t) => send(t)}
        onRetry={() => lastMessage && send(lastMessage, { retry: true })}
      />
      <Footer />
    </div>
  );
}
