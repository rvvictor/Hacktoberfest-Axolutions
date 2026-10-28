// Mirror of GET /api/ops/runs (app/services/costs.py).
export interface StageOps {
  stage: number;
  name: string;
  status: "pending" | "running" | "done" | "failed";
  duration_s: number | null;
  failures: number;
  error: string | null;
}

export interface StepCost {
  step: string;
  usd: number;
  unit: string; // tokens | minutes | credits
  units: number;
  estimated: boolean;
  source_url: string;
}

export interface RunOps {
  run_id: string;
  project_id: string;
  status: string;
  demo_data: boolean;
  duration_s: number;
  stages: StageOps[];
  failures: number;
  steps: StepCost[];
  total_usd: number;
  budget_usd: number;
  budget_used: number; // 0–1+
  budget_estimated: boolean;
}

export interface OpsResponse {
  budget_usd: number;
  runs: RunOps[];
}
