export default function TypingIndicator() {
  return (
    <div className="flex items-center gap-2.5" role="status" aria-label="The sommelier is choosing">
      <span aria-hidden className="flex h-7 w-7 items-center justify-center rounded-full border border-bar-line bg-bar-panel text-sm">🥃</span>
      <div className="flex gap-1 rounded-2xl rounded-tl-md bg-bar-panel px-4 py-3.5">
        <span className="dot h-1.5 w-1.5 rounded-full bg-amber" />
        <span className="dot h-1.5 w-1.5 rounded-full bg-amber" />
        <span className="dot h-1.5 w-1.5 rounded-full bg-amber" />
      </div>
      <span className="text-xs text-bar-faint">Checking the cellar…</span>
    </div>
  );
}
