// Mirrors app/schemas/ (IDEA.md §6). Keep in sync with the Pydantic models.
export type Mode = "dev" | "client";
export type RunStatus = "pending" | "running" | "awaiting_approval" | "done" | "failed";
export type ApprovalState = "pending" | "approved" | "rejected";

export type EventType =
  | "stage_started" | "stage_done" | "question" | "research_item" | "spec_ready"
  | "approval_required" | "approval_given" | "approval_rejected" | "miro_item"
  | "linear_issue" | "prototype_ready" | "quality_check" | "pitch_ready" | "error";

export interface Project { id: string; mode: Mode; idea: string; stack_prefs: string[]; demo_data: boolean }
export interface Approval { number: 1 | 2 | 3; state: ApprovalState; decided_by: string | null }
export interface Run {
  run_id: string; project_id: string; stage: number; status: RunStatus;
  approvals: Approval[]; cost_by_step: Record<string, number>; demo_data: boolean;
}
/** `ts` = seconds since the run started. */
export interface StageEvent {
  run_id: string; stage: number; type: EventType;
  payload: Record<string, unknown>; ts: number; demo_data: boolean;
}

export interface ResearchItem {
  competitor: string; pricing: string | null; features: string[];
  url: string; fetched_at: string | null; demo_data: boolean;
}
export interface Spec {
  version: number; problem: string; users: string[]; mvp_features: string[];
  assumptions: string[]; sources: string[]; demo_data: boolean;
}
export interface MiroItem {
  kind: string; title: string; miro_id: string | null; x: number; y: number; demo_data: boolean;
}
export interface Architecture {
  screens: string[]; data_model: string[]; integrations: string[];
  miro_board_id: string | null; items: MiroItem[]; demo_data: boolean;
}
export interface BacklogItem {
  epic: string; title: string; acceptance: string[]; external_id: string;
  linear_id: string | null; url: string | null; demo_data: boolean;
}
export interface Prototype {
  generator: "lovable" | "planb"; url: string; build_url: string | null;
  repo_url: string | null; demo_data: boolean;
}
export interface QualityCheck { name: "build" | "lint" | "gitleaks" | "rls" | "smoke"; passed: boolean; details: string }
export interface QualityReport { checks: QualityCheck[]; passed: boolean; details: string; demo_data: boolean }
export interface Slide { title: string; bullets: string[]; sources: string[] }
export interface QAEntry { question: string; answer: string; sources: string[] }
export interface Pitch { slides: Slide[]; qa_log: QAEntry[]; demo_data: boolean }
export interface Prospect {
  business: string; public_info: string; draft_message: string;
  approved_by: string | null; opt_out: boolean; consent: boolean; demo_data: boolean;
}
