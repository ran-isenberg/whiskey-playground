import type { Match } from "../types";

function scoreLabel(s: number) {
  if (s >= 90) return "Perfect pour";
  if (s >= 70) return "Great fit";
  return "Worth a try";
}

export default function MatchCard({ match }: { match: Match }) {
  const w = match.whiskey;
  const facts = [w.distillery, `${w.region}, ${w.country}`, w.age ? `${w.age} yrs` : "NAS", `${w.abv.toFixed(1)}% ABV`];
  return (
    <article className="rise overflow-hidden rounded-2xl border border-bar-line bg-bar-panel">
      <div className="flex items-start gap-3 p-4 pb-3">
        <span className="font-display text-2xl font-semibold leading-none text-amber-deep">#{match.rank}</span>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h3 className="font-display text-lg font-semibold leading-snug text-bar-text">{w.name}</h3>
              <p className="mt-0.5 text-xs text-bar-muted">{w.type}</p>
            </div>
            <span className="shrink-0 rounded-full border border-bar-line px-2.5 py-0.5 text-xs font-semibold tracking-wide text-amber-soft" title="Price tier">
              {w.price_tier}
            </span>
          </div>
          <p className="mt-2 text-xs text-bar-faint">{facts.join(" · ")}</p>
        </div>
      </div>

      <div className="px-4">
        <div className="flex items-center justify-between text-xs">
          <span className="font-medium text-bar-muted">{scoreLabel(match.match_score)}</span>
          <span className="font-semibold tabular-nums text-amber-soft">{match.match_score}% match</span>
        </div>
        <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-bar-raised" role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={match.match_score} aria-label="Match score">
          <div className="h-full rounded-full bg-gradient-to-r from-amber-deep to-amber-soft" style={{ width: `${match.match_score}%` }} />
        </div>
      </div>

      <div className="mt-4 border-l-2 border-amber px-4 pl-3.5 mx-4">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-amber">Why it matches you</p>
        <p className="mt-1 text-sm leading-relaxed text-bar-text">{match.why}</p>
      </div>

      <div className="mt-4 flex flex-wrap gap-1.5 px-4">
        {w.flavor_profile.map((f) => (
          <span key={f} className="rounded-full bg-bar-raised px-2.5 py-0.5 text-[11px] text-bar-muted">
            {f}
          </span>
        ))}
      </div>

      <dl className="mt-4 grid gap-2 px-4 text-xs sm:grid-cols-3">
        {(["nose", "palate", "finish"] as const).map((k) => (
          <div key={k}>
            <dt className="font-semibold capitalize text-bar-muted">{k}</dt>
            <dd className="mt-0.5 leading-relaxed text-bar-faint">{w.tasting_notes[k]}</dd>
          </div>
        ))}
      </dl>

      <div className="mt-4 flex items-center gap-2 border-t border-bar-line bg-bar-raised/40 px-4 py-2.5 text-xs">
        <span className="font-semibold text-bar-muted">Serve:</span>
        <span className="text-bar-text">{match.serving}</span>
        <span className="ml-auto shrink-0 text-bar-faint" title="Approximate rating">★ {w.rating}</span>
      </div>
    </article>
  );
}
