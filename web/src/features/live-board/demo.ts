import type { StageEvent } from "./contract";

// Recorded-style replay of approval 1 → approval 2 for the IDEA.md §3 case. Simulated: demo_data on every event.
// Same event shapes as app/fixtures/demo/run.jsonl; the whole wow plays in ~16 s.
const run_id = "run_demo_001";

const miro: [string, string, number, number][] = [
  ["screen", "Login", 0, 0],
  ["screen", "Dashboard de gastos", 220, 0],
  ["screen", "Captura de ticket", 440, 0],
  ["screen", "Aprobaciones", 660, 0],
  ["data_model", "Empresa", 0, 160],
  ["data_model", "Usuario y rol", 220, 160],
  ["data_model", "Gasto", 440, 160],
  ["data_model", "Política de gasto", 660, 160],
  ["integration", "Supabase Auth y RLS", 110, 320],
  ["integration", "Correo de alertas", 440, 320],
  ["integration", "Exportación contable", 660, 320],
  ["connector", "Gasto → Política de gasto", 0, 0],
  ["connector", "Usuario y rol → Supabase Auth y RLS", 0, 0],
  ["connector", "Política de gasto → Correo de alertas", 0, 0],
];

const issues: [string, string, string[]][] = [
  ["Multiempresa y roles", "Alta de empresa y primer administrador", ["Una empresa nueva queda aislada de las demás", "El primer usuario es administrador"]],
  ["Multiempresa y roles", "Políticas RLS por empresa", ["Ningún usuario lee gastos de otra empresa", "Prueba automática de RLS en CI"]],
  ["Gastos", "Captura de gasto con foto del ticket", ["Monto, fecha y categoría obligatorios", "La foto se guarda en el almacenamiento de la empresa", "Funciona en móvil"]],
  ["Gastos", "Dashboard de gastos del mes", ["Total por categoría y por persona", "Filtro por fechas"]],
  ["Aprobaciones", "Aprobación del gerente", ["El gerente aprueba o rechaza con comentario", "El empleado ve el estado"]],
  ["Alertas", "Alerta al exceder la política", ["Correo al gerente cuando un gasto supera el límite", "Sin alertas duplicadas"]],
  ["Alertas", "Resumen semanal por correo", ["Se envía cada lunes", "Se puede desactivar"]],
  ["Exportación", "Exportar gastos aprobados a CSV", ["Columnas compatibles con el contador", "Solo gastos aprobados"]],
];

function ev(stage: number, type: StageEvent["type"], payload: Record<string, unknown>, ts: number): StageEvent {
  return { run_id, stage, type, payload, ts, demo_data: true };
}

export const DEMO_EVENTS: StageEvent[] = [
  ev(4, "approval_given", { approval: 1, by: "demo" }, 0),
  ev(5, "stage_started", { name: "architecture" }, 0.6),
  ...miro.map(([kind, title, x, y], i) =>
    ev(5, "miro_item", { kind, title, miro_id: `demo_miro_${i + 1}`, x, y, demo_data: true }, 1.2 + i * 0.5),
  ),
  ev(5, "stage_done", { name: "architecture" }, 8.4),
  ev(6, "stage_started", { name: "backlog" }, 8.8),
  ...issues.map(([epic, title, acceptance], i) =>
    ev(6, "linear_issue", {
      epic, title, acceptance, external_id: `demo-ext-${i + 1}`, linear_id: `GAS-${i + 1}`, url: null, demo_data: true,
    }, 9.4 + i * 0.7),
  ),
  ev(6, "stage_done", { name: "backlog" }, 15.4),
  ev(6, "approval_required", { approval: 2 }, 15.8),
];

/** Plays the events with their recorded timing. Returns a cancel function. */
export function playDemo(onEvent: (e: StageEvent) => void, speed = 1): () => void {
  const timers = DEMO_EVENTS.map((e) => window.setTimeout(() => onEvent(e), (e.ts * 1000) / speed));
  return () => timers.forEach((t) => window.clearTimeout(t));
}
