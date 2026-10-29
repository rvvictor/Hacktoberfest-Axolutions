import { useCallback, useEffect, useReducer, useRef, useState } from "react";

import { api } from "../../lib/api";
import type {
  BacklogItem,
  EventType,
  MiroItem,
  Pitch,
  Prototype,
  QualityCheck,
  ResearchItem,
  RunStatus,
  Spec,
  StageEvent,
} from "../../lib/types";
import { DEMO_SEGMENTS } from "./demo";

export interface Conversation {
  stage: number;
  status: RunStatus;
  awaiting: string | null; // "answers" | "approval:1" | "approval:2" | "approval:3" | null
  questions: string[];
  research: ResearchItem[];
  spec: Spec | null;
  miro: MiroItem[];
  issues: BacklogItem[];
  prototype: Prototype | null;
  checks: QualityCheck[];
  pitch: Pitch | null;
  decided: Record<number, "approved" | "rejected">;
  demo: boolean;
  error: string | null;
}

const empty: Conversation = {
  stage: 1, status: "pending", awaiting: null, questions: [], research: [], spec: null, miro: [], issues: [],
  prototype: null, checks: [], pitch: null, decided: {}, demo: false, error: null,
};

const EVENT_TYPES: EventType[] = [
  "stage_started", "stage_done", "question", "research_item", "spec_ready", "approval_required", "approval_given",
  "approval_rejected", "miro_item", "linear_issue", "prototype_ready", "quality_check", "pitch_ready", "error",
];

type Action = { type: "event"; e: StageEvent } | { type: "state"; s: Partial<Conversation> } | { type: "reset" };

function reduce(c: Conversation, a: Action): Conversation {
  if (a.type === "reset") return empty;
  if (a.type === "state") return { ...c, ...a.s };
  const { e } = a;
  const p = e.payload as Record<string, unknown>;
  const next = { ...c, stage: Math.max(c.stage, e.stage), demo: c.demo || e.demo_data };
  switch (e.type) {
    case "stage_started":
      // A rerun after "Cambiar algo" starts the stage over: drop what that stage showed before.
      if (e.stage === 3) return { ...next, research: [] };
      if (e.stage === 5) return { ...next, miro: [] };
      if (e.stage === 6) return { ...next, issues: [] };
      if (e.stage === 8) return { ...next, checks: [] };
      return next;
    case "question":
      return { ...next, questions: [...c.questions, String(p.text ?? "")] };
    case "research_item":
      return { ...next, research: [...c.research, p as unknown as ResearchItem] };
    case "spec_ready":
      return { ...next, spec: p as unknown as Spec };
    case "miro_item":
      return { ...next, miro: [...c.miro, p as unknown as MiroItem] };
    case "linear_issue":
      return { ...next, issues: [...c.issues, p as unknown as BacklogItem] };
    case "prototype_ready":
      return { ...next, prototype: p as unknown as Prototype };
    case "quality_check":
      return { ...next, checks: [...c.checks, p as unknown as QualityCheck] };
    case "pitch_ready":
      return { ...next, pitch: p as unknown as Pitch };
    case "approval_required":
      return { ...next, awaiting: `approval:${String(p.approval)}`, status: "awaiting_approval" };
    case "approval_given":
      return { ...next, decided: { ...c.decided, [Number(p.approval)]: "approved" }, awaiting: null };
    case "approval_rejected":
      return { ...next, decided: { ...c.decided, [Number(p.approval)]: "rejected" }, awaiting: null };
    case "error":
      return { ...next, error: String(p.message ?? "Algo falló en el camino."), status: "failed" };
    default:
      return next;
  }
}

/** A run followed live (`?run=ID`) or, without one, the recorded example played turn by turn. */
export function useConversation(runId: string | null) {
  const [state, dispatch] = useReducer(reduce, empty);
  const [busy, setBusy] = useState(false);
  const segment = useRef(0);

  const refresh = useCallback(async () => {
    if (!runId) return;
    const s = await api<{ stage: number; status: RunStatus; awaiting: string | null; demo_data: boolean }>(
      `/runs/${encodeURIComponent(runId)}`,
    );
    dispatch({ type: "state", s: { stage: s.stage, status: s.status, awaiting: s.awaiting } });
  }, [runId]);

  useEffect(() => {
    dispatch({ type: "reset" });
    if (!runId) {
      // Recorded example: play up to the first decision; each answer plays the next segment.
      segment.current = 0;
      DEMO_SEGMENTS[0].events.forEach((e) => dispatch({ type: "event", e }));
      dispatch({ type: "state", s: { awaiting: DEMO_SEGMENTS[0].awaiting, status: "pending" } });
      return;
    }
    // The runs router sends named SSE events; `onmessage` alone never fires for them.
    const source = new EventSource(`/api/runs/${encodeURIComponent(runId)}/events`);
    const onEvent = (m: MessageEvent<string>) => {
      if (typeof m.data !== "string") return;
      dispatch({ type: "event", e: JSON.parse(m.data) as StageEvent });
    };
    EVENT_TYPES.forEach((t) => source.addEventListener(t, onEvent));
    const timer = window.setInterval(() => void refresh().catch(() => undefined), 4000);
    void refresh().catch(() => undefined);
    return () => {
      source.close();
      window.clearInterval(timer);
    };
  }, [runId, refresh]);

  const advanceDemo = useCallback(() => {
    const next = segment.current + 1;
    if (next >= DEMO_SEGMENTS.length) return;
    segment.current = next;
    DEMO_SEGMENTS[next].events.forEach((e) => dispatch({ type: "event", e }));
    dispatch({
      type: "state",
      s: { awaiting: DEMO_SEGMENTS[next].awaiting, status: DEMO_SEGMENTS[next].awaiting ? "pending" : "done" },
    });
  }, []);

  const answer = useCallback(
    async (answers: string[]) => {
      if (!runId) return advanceDemo();
      setBusy(true);
      try {
        await api(`/runs/${encodeURIComponent(runId)}/answers`, { method: "POST", body: JSON.stringify({ answers }) });
        dispatch({ type: "state", s: { awaiting: null, status: "running" } });
      } catch (e) {
        dispatch({ type: "state", s: { error: `No se pudieron enviar tus respuestas: ${(e as Error).message}` } });
      } finally {
        setBusy(false);
      }
    },
    [runId, advanceDemo],
  );

  const decide = useCallback(
    async (approval: number, approved: boolean, comment: string) => {
      if (!runId) {
        dispatch({ type: "state", s: { decided: { ...state.decided, [approval]: approved ? "approved" : "rejected" } } });
        return advanceDemo();
      }
      setBusy(true);
      try {
        await api(`/runs/${encodeURIComponent(runId)}/approvals/${approval}`, {
          method: "POST",
          body: JSON.stringify({ approved, comment: comment || null }),
        });
        dispatch({ type: "state", s: { awaiting: null, status: "running" } });
      } catch (e) {
        dispatch({ type: "state", s: { error: `No se pudo registrar tu decisión: ${(e as Error).message}` } });
      } finally {
        setBusy(false);
      }
    },
    [runId, advanceDemo, state.decided],
  );

  return { state, busy, answer, decide };
}
