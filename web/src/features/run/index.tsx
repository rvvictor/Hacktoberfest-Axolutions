import { useCallback, useEffect, useRef, useState } from "react";

import { api } from "../../lib/api";
import { subscribe } from "../../lib/sse";
import { Button, Chip, DemoBadge, MetroLine, Panel, Stat, STAGE_LABELS, Title } from "../../lib/ui";
import type { StageEvent } from "./contract";
import { demoAfterDecision, demoStart, GATE_STAGE } from "./demo";
import "./run.css";

export const path = "/run";
export const label = "Ejecución";
export const order = 20;

type Status = "pending" | "running" | "done";
type StageInfo = { status: Status; start?: number; end?: number };
type State = {
  stages: StageInfo[]; // index 0 = stage 1
  current: number;
  gate: number | null; // 1–3 while waiting for a human
  rejected: string | null;
  last: number; // last event ts
  demo: boolean;
  finished: boolean;
};

const initial: State = {
  stages: STAGE_LABELS.map(() => ({ status: "pending" })),
  current: 1,
  gate: null,
  rejected: null,
  last: 0,
  demo: false,
  finished: false,
};

export function reduce(s: State, e: StageEvent): State {
  const stages = s.stages.map((x) => ({ ...x }));
  const i = e.stage - 1;
  const next: State = { ...s, stages, last: Math.max(s.last, e.ts), demo: s.demo || e.demo_data };
  if (!stages[i]) return next;
  switch (e.type) {
    case "stage_started":
      // Going back one stage: everything after it is pending again.
      for (let k = i; k < stages.length; k++) stages[k] = { status: "pending" };
      stages[i] = { status: "running", start: e.ts };
      next.current = e.stage;
      next.finished = false;
      break;
    case "stage_done":
      stages[i] = { ...stages[i], status: "done", end: e.ts };
      next.finished = e.stage === stages.length;
      break;
    case "approval_required": {
      const n = Number(e.payload.number) || Object.keys(GATE_STAGE).find((k) => GATE_STAGE[+k] === e.stage);
      next.gate = n ? Number(n) : null;
      next.rejected = null;
      break;
    }
    case "approval_given":
      next.gate = null;
      next.rejected = null;
      break;
    case "approval_rejected":
      next.gate = null;
      next.rejected = `Se pidieron cambios en la aprobación ${e.payload.number ?? ""}: la ejecución vuelve a la etapa ${Math.max(1, e.stage - 1)}.`;
      break;
  }
  return next;
}

const fmt = (sec: number) => `${Math.floor(sec / 60)}:${String(Math.floor(sec % 60)).padStart(2, "0")}`;

function stageTime(x: StageInfo, last: number): string {
  if (x.status === "done" && x.start !== undefined && x.end !== undefined) return fmt(x.end - x.start);
  if (x.status === "running" && x.start !== undefined) return fmt(last - x.start);
  return "–";
}

const LINKS = [
  { href: "#/spec", text: "Spec" },
  { href: "#/live-board", text: "Tablero en vivo" },
  { href: "#/delivery", text: "Entrega" },
  { href: "#/pitch", text: "Pitch" },
];

export default function Run() {
  const [state, setState] = useState<State>(initial);
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timers = useRef<number[]>([]);
  const clock = useRef(0);

  // `#/run?run=ID` follows a real run; without it (or without a backend) the local demo replay plays.
  const runId = new URLSearchParams(window.location.hash.split("?")[1] ?? "").get("run");

  const play = useCallback((events: StageEvent[]) => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    events.forEach((e, k) => {
      const t = window.setTimeout(() => {
        clock.current = Math.max(clock.current, e.ts);
        setState((s) => reduce(s, e));
      }, reduced ? k * 40 : e.ts * 350 - (events[0].ts * 350));
      timers.current.push(t);
    });
  }, []);

  useEffect(() => {
    setState(initial);
    clock.current = 0;
    if (runId) {
      return subscribe<StageEvent>(
        `/api/runs/${runId}/events`,
        (e) => setState((s) => reduce(s, e)),
        () => setError("Sin conexión con el servidor."),
      );
    }
    play(demoStart());
    const pending = timers.current;
    return () => {
      pending.forEach(clearTimeout);
      timers.current = [];
    };
  }, [runId, play]);

  const decide = async (approved: boolean) => {
    const n = state.gate;
    if (!n) return;
    setBusy(true);
    setError(null);
    try {
      if (runId) await api(`/runs/${runId}/approvals/${n}`, { method: "POST", body: JSON.stringify({ approved, comment }) });
      else play(demoAfterDecision(n, approved, clock.current));
      setComment("");
      if (!runId) setState((s) => ({ ...s, gate: null }));
    } catch {
      setError("No se pudo enviar la decisión. Intenta de nuevo.");
    } finally {
      setBusy(false);
    }
  };

  const done = state.stages.filter((x) => x.status === "done").length;
  const waiting = state.gate !== null;

  return (
    <div className="run">
      <header className="run__head">
        <div>
          <Title>Ejecución del proyecto</Title>
          <p>{waiting ? "Esperando tu decisión para continuar." : state.finished ? "Ejecución terminada." : "El agente trabaja la etapa en curso."}</p>
        </div>
        <DemoBadge show={state.demo} />
      </header>

      <MetroLine current={state.current} />

      <div className="run__body">
        <Panel title="Etapas" meta={`${done} de ${STAGE_LABELS.length}`}>
          <ol className="run__stages">
            {STAGE_LABELS.map((name, k) => {
              const x = state.stages[k];
              const isGate = waiting && GATE_STAGE[state.gate!] === k + 1;
              return (
                <li key={name} className="run__stage" data-state={x.status}>
                  <span className="run__n">{k + 1}</span>
                  <span>{name}</span>
                  <span className="run__status">{isGate ? <Chip tone="rosa">Esperando aprobación</Chip> : x.status === "running" ? <Chip tone="rosa">En curso</Chip> : x.status === "done" ? <Chip>Hecha</Chip> : null}</span>
                  <span className="run__time">{stageTime(x, state.last)}</span>
                </li>
              );
            })}
          </ol>
        </Panel>

        <div className="run__side">
          {waiting && (
            <Panel title={`Aprobación ${state.gate} de 3`} meta={`Tras la etapa ${GATE_STAGE[state.gate!]}`} className="run__gate">
              <label htmlFor="run-comment">Comentario (opcional)</label>
              <textarea id="run-comment" value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Qué cambiarías o por qué apruebas" />
              <div className="run__actions">
                <Button variant="primary" disabled={busy} onClick={() => decide(true)}>Aprobar</Button>
                <Button disabled={busy} onClick={() => decide(false)}>Pedir cambios</Button>
              </div>
            </Panel>
          )}
          {state.rejected && <p className="run__note" role="status">{state.rejected}</p>}
          {error && <p className="run__err" role="alert">{error}</p>}
          <Panel title="Resumen">
            <div className="run__stats">
              <Stat value={fmt(state.last)} label="tiempo total" />
              <Stat value={`${done}/${STAGE_LABELS.length}`} label="etapas hechas" />
            </div>
            <nav className="run__links" aria-label="Vistas del proyecto">
              {LINKS.map((l) => (
                <a key={l.href} href={l.href}>{l.text}</a>
              ))}
            </nav>
          </Panel>
        </div>
      </div>
    </div>
  );
}
