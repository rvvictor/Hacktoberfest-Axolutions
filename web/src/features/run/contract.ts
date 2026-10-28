// Minimal mirror of web/src/lib/types.ts (HACK-002) with only the fields this view reads.
// TODO: switch to `import type { StageEvent } from "../../lib/types"` once HACK-002 integrates.
export type EventType =
  | "stage_started" | "stage_done" | "approval_required" | "approval_given" | "approval_rejected" | "error";

export interface StageEvent {
  run_id: string;
  stage: number; // 1–9
  type: EventType | string;
  payload: Record<string, unknown>;
  ts: number; // seconds since the run started
  demo_data: boolean;
}
