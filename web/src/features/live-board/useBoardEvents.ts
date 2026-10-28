import { useCallback, useEffect, useReducer, useState } from "react";

import { subscribe } from "../../lib/sse";
import type { BacklogItem, MiroItem, StageEvent } from "./contract";
import { playDemo } from "./demo";

export interface BoardState {
  stage: number;
  miro: MiroItem[];
  issues: BacklogItem[];
  boardId: string | null;
  awaitingApproval: boolean;
  demo: boolean;
}

const initial: BoardState = { stage: 5, miro: [], issues: [], boardId: null, awaitingApproval: false, demo: false };

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
      return { ...next, awaitingApproval: false };
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
    if (runId) return subscribe<StageEvent>(`/api/runs/${encodeURIComponent(runId)}/events`, dispatch);
    return playDemo(dispatch);
  }, [runId, round]);

  const replay = useCallback(() => setRound((r) => r + 1), []);
  return { state, replay };
}
