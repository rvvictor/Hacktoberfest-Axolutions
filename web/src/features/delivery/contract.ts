// Minimal mirror of the run contract (HACK-002, app/schemas) with only the fields this view reads.
// TODO: switch to the shared types once HACK-002 integrates.
export type CheckName = "build" | "lint" | "gitleaks" | "rls" | "smoke";

export interface QualityCheck {
  name: CheckName;
  passed: boolean;
  details: string;
}

export interface Prototype {
  generator: "lovable" | "planb";
  url: string;
  build_url: string | null; // Lovable "Build with URL" link
  repo_url: string | null;
  demo_data: boolean;
}

export interface BacklogItem {
  epic: string;
  title: string;
  acceptance: string[];
  external_id: string;
  demo_data: boolean;
}

export type EventType =
  | "prototype_ready"
  | "quality_check"
  | "linear_issue"
  | "approval_required"
  | "approval_given"
  | "approval_rejected"
  | "error";

export interface StageEvent {
  run_id: string;
  stage: number;
  type: EventType | string;
  payload: Record<string, unknown>;
  ts: number;
  demo_data: boolean;
}
