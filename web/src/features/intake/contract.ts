// Minimal mirror of the backend contract (app/schemas, app/routers/runs.py, app/routers/voice.py).
// TODO: switch to `../../lib/types` once HACK-002 lands on main.
export type Mode = "dev" | "client";

export interface Run {
  run_id: string;
  stage: number;
  demo_data: boolean;
}

export interface QuestionEvent {
  stage: number;
  type: "question";
  payload: { text: string; mode?: Mode };
  demo_data: boolean;
}

export const STACKS = ["React", "Next.js", "Supabase", "FastAPI", "Postgres", "Tailwind"] as const;

// Local demo replay (demo_data: true): same questions as app/fixtures/demo/run.jsonl, used when /api is unreachable.
export const DEMO_RUN: Run = { run_id: "run_demo_001", stage: 2, demo_data: true };
export const DEMO_QUESTIONS: Record<Mode, string[]> = {
  dev: [
    "¿Habrá varias empresas (multiempresa) en la misma instalación?",
    "¿Qué roles necesita: empleado, aprobador, finanzas?",
    "¿Qué alertas automáticas deben dispararse y por qué canal?",
  ],
  client: [
    "¿Quiénes usarán la herramienta a diario?",
    "¿Qué decisión te gustaría tomar más rápido?",
    "¿Cómo lo resuelves hoy?",
  ],
};
