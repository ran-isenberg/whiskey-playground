const EXAMPLES = [
  "Rainy Sunday with a book, I love smoky stuff",
  "I just closed a big deal and want to feel like a boss",
  "Something sweet and easy for a summer barbecue",
  "A quiet nightcap after a long week",
];

export default function ExampleChips({ onPick, disabled }: { onPick: (t: string) => void; disabled: boolean }) {
  return (
    <div className="flex flex-wrap justify-center gap-2">
      {EXAMPLES.map((e) => (
        <button
          key={e}
          disabled={disabled}
          onClick={() => onPick(e)}
          className="rounded-full border border-bar-line bg-bar-panel px-3.5 py-2 text-left text-xs text-bar-muted transition hover:border-amber hover:text-bar-text disabled:opacity-40"
        >
          {e}
        </button>
      ))}
    </div>
  );
}
