import type { ChatResponse } from "../types";
import MatchCard from "./MatchCard";

export default function AgentMessage({ response }: { response: ChatResponse }) {
  const empty = response.matches.length === 0;
  return (
    <div className="rise flex flex-col gap-3">
      <div className="flex items-start gap-2.5">
        <span aria-hidden className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-bar-line bg-bar-panel text-sm">
          🥃
        </span>
        <p
          className={
            "max-w-[85%] rounded-2xl rounded-tl-md px-4 py-2.5 text-sm leading-relaxed " +
            (empty ? "border border-dashed border-bar-line bg-transparent text-bar-muted" : "bg-bar-panel text-bar-text")
          }
        >
          {empty && <span className="mb-1 block text-xs font-medium uppercase tracking-wider text-bar-faint">Nothing in our cellar fits</span>}
          {response.message}
        </p>
      </div>
      {!empty && (
        <div className="flex flex-col gap-3 sm:pl-9">
          {response.matches.map((m) => (
            <MatchCard key={m.id} match={m} />
          ))}
        </div>
      )}
    </div>
  );
}
