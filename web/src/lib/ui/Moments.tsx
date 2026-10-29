// The 9 pipeline stages as the 3 moments people think in. Use it as the page-level progress;
// MetroLine stays for the detailed run view.
export const MOMENTS = [
  { label: "Idea", stages: [1, 2] },
  { label: "Plan", stages: [3, 4, 5, 6] },
  { label: "Producto", stages: [7, 8, 9] },
] as const;

export function momentOf(stage: number): number {
  const i = MOMENTS.findIndex((m) => (m.stages as readonly number[]).includes(stage));
  return i === -1 ? 0 : i;
}

export function Moments({ stage }: { stage: number }) {
  const current = momentOf(stage);
  return (
    <ol className="sh-moments" aria-label={`Paso ${current + 1} de 3: ${MOMENTS[current].label}`}>
      {MOMENTS.map((m, i) => (
        <li
          key={m.label}
          data-state={i < current ? "done" : i === current ? "current" : "next"}
          aria-current={i === current ? "step" : undefined}
        >
          <span>{m.label}</span>
        </li>
      ))}
    </ol>
  );
}
