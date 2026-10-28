import { useCallback, useEffect, useReducer, useState } from "react";

import type { BacklogItem, EventType, MiroItem, StageEvent } from "./contract";
import { playDemo } from "./demo";

export interface BoardState {
  stage: number;
  miro: MiroItem[];
  issues: BacklogItem[];
  boardId: string | null;
  awaitingApproval: boolean;
  approved: boolean;
  demo: boolean;
}

const EVENT_TYPES: EventType[] = [
  "stage_started", "stage_done", "question", "research_item", "spec_ready", "approval_required", "approval_given",
  "approval_rejected", "miro_item", "linear_issue", "prototype_ready", "quality_check", "pitch_ready", "error",
];

// The runs router (HACK-013) sends named SSE events (`event: <type>`), which `onmessage` in lib/sse.ts never sees.
function listen(url: string, onEvent: (e: StageEvent) => void): () => void {
  const source = new EventSource(url);
  const handle = (m: MessageEvent<string>) => onEvent(JSON.parse(m.data) as StageEvent);
  EVENT_TYPES.forEach((t) => source.addEventListener(t, handle));
  source.onmessage = handle;
  return () => source.close();
}

const initial: BoardState = { stage: 5, miro: [], issues: [], boardId: null, awaitingApproval: false, approved: false, demo: false };

function reduce(state: BoardState, e: StageEvent | "reset"): BoardState {
  if (e === "reset") return initial;
  const next = { ...state, stage: Math.max(state.stage, e.stage), demo: state.demo || e.demo_data };
  const p = e.payload;
  if (typeof p.miro_board_id === "string") next.boardId = p.miro_board_id;
  switch (e.type) {
    case "miro_item":
      return { ...next, miro: [...state.miro, p as unknown as MiroItem] };
    case "linear_issue":
      return { ...next, issues: [...state.issues, p as unknown as BacklogItem] };
    case "approval_required":
      return { ...next, awaitingApproval: p.approval === 2 };
    case "approval_given":
      return p.approval === 2 ? { ...next, awaitingApproval: false, approved: true } : next;
    default:
      return next;
  }
}

/** Live events from `/api/runs/{run}/events` when `?run=` is set; otherwise the recorded demo replay. */
export function useBoardEvents(runId: string | null) {
  const [state, dispatch] = useReducer(reduce, initial);
  const [round, setRound] = useState(0);

  useEffect(() => {
    dispatch("reset");
    if (runId) return listen(`/api/runs/${encodeURIComponent(runId)}/events`, dispatch);
    return playDemo(dispatch);
  }, [runId, round]);

  const replay = useCallback(() => setRound((r) => r + 1), []);
  // Demo only: a live run hears approval_given back from the SSE stream after the POST.
  const approve = useCallback(
    () => dispatch({ run_id: "run_demo_001", stage: 6, type: "approval_given", payload: { approval: 2, by: "demo" }, ts: 0, demo_data: true }),
    [],
  );
  return { state, replay, approve };
}
