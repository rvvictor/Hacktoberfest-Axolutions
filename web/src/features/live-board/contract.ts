// Subset of the HACK-002 contract (web/src/lib/types.ts on feat/hack-002) that this view reads.
// Switch these imports to "../../lib/types" once HACK-002 is integrated.
export type EventType =
  | "stage_started" | "stage_done" | "question" | "research_item" | "spec_ready"
  | "approval_required" | "approval_given" | "approval_rejected" | "miro_item"
  | "linear_issue" | "prototype_ready" | "quality_check" | "pitch_ready" | "error";

/** `ts` = seconds since the run started. */
export interface StageEvent {
  run_id: string; stage: number; type: EventType;
  payload: Record<string, unknown>; ts: number; demo_data: boolean;
}
export interface MiroItem {
  kind: string; title: string; miro_id: string | null; x: number; y: number; demo_data: boolean;
  w?: number; h?: number; // the live board's frames and notes carry their size
}
export interface BacklogItem {
  epic: string; title: string; acceptance: string[]; external_id: string;
  linear_id: string | null; url: string | null; demo_data: boolean;
}
