import type { StageEvent } from "./contract";

// Local replay so the view works without a backend. Every event is demo_data (the view shows DemoBadge).
const ev = (ts: number, stage: number, type: string, payload: Record<string, unknown> = {}): StageEvent => ({
  run_id: "demo",
  stage,
  type,
  payload,
  ts,
  demo_data: true,
});

export const GATE_STAGE: Record<number, number> = { 1: 4, 2: 6, 3: 8 };

// Events of stages `from`..`to` starting at time `t0`, 3 s each, ending in a gate when `to` is a gate stage.
function stages(from: number, to: number, t0: number): StageEvent[] {
  const out: StageEvent[] = [];
  let t = t0;
  for (let s = from; s <= to; s++) {
    out.push(ev(t, s, "stage_started"));
    t += 3;
    out.push(ev(t, s, "stage_done"));
  }
  if (Object.values(GATE_STAGE).includes(to)) out.push(ev(t, to, "approval_required", { number: Object.keys(GATE_STAGE).find((k) => GATE_STAGE[+k] === to) }));
  return out;
}

export const demoStart = (): StageEvent[] => stages(1, 4, 0);

// What the "server" does after the human decides on gate `n` at time `t`.
export function demoAfterDecision(n: number, approved: boolean, t: number): StageEvent[] {
  const gate = GATE_STAGE[n];
  if (approved) return [ev(t, gate, "approval_given", { number: n }), ...stages(gate + 1, n === 3 ? 9 : GATE_STAGE[n + 1], t + 1)];
  return [ev(t, gate, "approval_rejected", { number: n }), ...stages(gate - 1, gate, t + 1)];
}
