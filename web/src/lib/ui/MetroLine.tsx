// The run as a metro line: 9 stations, approvals are transfer stations (orange ring) after stages 4, 6 and 8.
export const STAGE_LABELS = [
  "Idea",
  "Preguntas",
  "Investigación",
  "Spec",
  "Arquitectura",
  "Backlog",
  "Prototipo",
  "Calidad",
  "Pitch",
] as const;

export const GATES: Record<number, string> = { 4: "aprobación 1", 6: "aprobación 2", 8: "aprobación 3" };

type Props = {
  current: number; // 1–9
  failed?: boolean;
  notes?: Partial<Record<number, string>>; // e.g. { 4: "aprobado" } overrides the gate label
};

export function MetroLine({ current, failed, notes = {} }: Props) {
  const progress = ((current - 1) / (STAGE_LABELS.length - 1)) * 100;
  return (
    <nav className="sh-metro" aria-label={`Etapa ${current} de 9: ${STAGE_LABELS[current - 1]}`}>
      <div className="sh-metro__rail">
        <b style={{ width: `${progress}%` }} />
      </div>
      <ol>
        {STAGE_LABELS.map((label, i) => {
          const n = i + 1;
          const state = n < current ? "done" : n === current ? (failed ? "failed" : "current") : "next";
          const note = notes[n] ?? GATES[n];
          return (
            <li key={n} data-state={state} data-gate={GATES[n] ? "" : undefined} aria-current={n === current ? "step" : undefined}>
              <span className="sh-metro__dot">{n}</span>
              {label}
              {note && <span className="sh-metro__note">{note}</span>}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
