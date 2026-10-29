import type { StageEvent } from "../../lib/types";

// Recorded example for the expense-control case (IDEA.md §3), played one decision at a time when no run is open.
// Simulated end to end: every event carries demo_data and links point to example.invalid.
const run_id = "run_demo_project";

function ev(stage: number, type: StageEvent["type"], payload: Record<string, unknown>): StageEvent {
  return { run_id, stage, type, payload, ts: 0, demo_data: true };
}

const src = (n: number) => `https://example.invalid/fuente-${n}`;

export const DEMO_SEGMENTS: { events: StageEvent[]; awaiting: string | null }[] = [
  {
    awaiting: "answers",
    events: [
      ev(2, "question", { text: "¿Varias empresas usarán el sistema, cada una con sus datos aparte?", mode: "dev" }),
      ev(2, "question", { text: "¿Quién aprueba los gastos y quién solo los captura?", mode: "dev" }),
      ev(2, "question", { text: "¿Cómo quieres enterarte cuando alguien pasa el límite?", mode: "dev" }),
    ],
  },
  {
    awaiting: "approval:1",
    events: [
      ev(3, "stage_started", { name: "research" }),
      ev(3, "research_item", { competitor: "Competidor de ejemplo A", pricing: null, features: ["tarjetas", "reglas de aprobación"], url: src(1), fetched_at: null, demo_data: true }),
      ev(3, "research_item", { competitor: "Competidor de ejemplo B", pricing: null, features: ["captura con OCR"], url: src(2), fetched_at: null, demo_data: true }),
      ev(3, "research_item", { competitor: "Competidor de ejemplo C", pricing: null, features: ["alertas de límite"], url: src(3), fetched_at: null, demo_data: true }),
      ev(4, "spec_ready", {
        version: 1,
        problem: "Los reembolsos tardan semanas y los excesos se descubren hasta el cierre del mes.",
        users: ["Finanzas", "Gerentes que aprueban", "Empleados"],
        mvp_features: ["Gastos con foto del ticket", "Aprobación del gerente", "Alerta al pasar el límite", "Exportar a CSV"],
        assumptions: ["Cada empresa ve solo sus datos"],
        sources: [src(1), src(2), src(3)],
        demo_data: true,
      }),
      ev(4, "approval_required", { approval: 1 }),
    ],
  },
  {
    awaiting: "approval:2",
    events: [
      ev(5, "stage_started", { name: "architecture" }),
      ...["Inicio de sesión", "Mis gastos", "Nuevo gasto", "Aprobaciones"].map((title, i) =>
        ev(5, "miro_item", { kind: "screen", title, miro_id: `demo_s${i}`, x: i * 220, y: 0, demo_data: true }),
      ),
      ...["Empresa", "Usuario", "Gasto"].map((title, i) =>
        ev(5, "miro_item", { kind: "data_model", title, miro_id: `demo_d${i}`, x: i * 220, y: 160, demo_data: true }),
      ),
      ...["Supabase Auth", "Correo de alertas"].map((title, i) =>
        ev(5, "miro_item", { kind: "integration", title, miro_id: `demo_i${i}`, x: i * 220, y: 320, demo_data: true }),
      ),
      ev(6, "stage_started", { name: "backlog" }),
      ...[
        ["Cuentas", "Alta de empresa y primer administrador"],
        ["Gastos", "Captura de gasto con foto"],
        ["Aprobaciones", "Aprobación del gerente con comentario"],
        ["Alertas", "Correo al pasar el límite"],
      ].map(([epic, title], i) =>
        ev(6, "linear_issue", { epic, title, acceptance: ["Criterio verificable"], external_id: `BL-00${i + 1}`, linear_id: `DEMO-${i + 1}`, url: null, demo_data: true }),
      ),
      ev(6, "approval_required", { approval: 2 }),
    ],
  },
  {
    awaiting: "approval:3",
    events: [
      ev(7, "prototype_ready", { generator: "planb", url: "https://example.invalid/prototipo", build_url: null, repo_url: null, demo_data: true }),
      ...["build", "lint", "gitleaks", "rls", "smoke"].map((name) =>
        ev(8, "quality_check", { name, passed: name !== "rls", details: name === "rls" ? "Una tabla sin aislamiento por empresa" : "ok" }),
      ),
      ev(8, "approval_required", { approval: 3 }),
    ],
  },
  {
    awaiting: null,
    events: [
      ev(9, "pitch_ready", {
        slides: [
          { title: "El problema", bullets: ["Reembolsos que tardan semanas"], sources: [] },
          { title: "La solución", bullets: ["Gastos con foto y aprobación en un toque"], sources: [] },
          { title: "Por qué ahora", bullets: ["Competidores sin alertas en tiempo real"], sources: [src(3)] },
        ],
        qa_log: [],
        demo_data: true,
      }),
    ],
  },
];
