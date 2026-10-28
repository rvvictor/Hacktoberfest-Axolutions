import type { StageEvent } from "./contract";

// demo_data: recorded sample (shape of the HACK-010 / HACK-012 events), shown until a real run is followed.
// One check fails on purpose so the failure state is visible.
const e = (stage: number, type: string, payload: Record<string, unknown>, ts: number): StageEvent => ({
  run_id: "run_demo_001",
  stage,
  type,
  payload,
  ts,
  demo_data: true,
});

export const demoDelivery = (): StageEvent[] => [
  e(7, "prototype_ready", { generator: "planb", url: "", build_url: "https://lovable.dev/?autosubmit=true#prompt=demo", repo_url: "https://github.com/example/speedhack-demo", demo_data: true }, 0),
  e(8, "quality_check", { name: "build", passed: true, details: "vite build en 14 s" }, 1),
  e(8, "quality_check", { name: "lint", passed: false, details: "3 avisos sin resolver en src/App.tsx" }, 2),
  e(8, "quality_check", { name: "gitleaks", passed: true, details: "0 secretos encontrados" }, 3),
  e(8, "quality_check", { name: "rls", passed: true, details: "todas las tablas con políticas" }, 4),
  e(8, "quality_check", { name: "smoke", passed: true, details: "GET / responde 200" }, 5),
  e(6, "linear_issue", { epic: "Catálogo", title: "Filtros por categoría", acceptance: ["Filtra sin recargar"], external_id: "GAS-7", demo_data: true }, 6),
  e(6, "linear_issue", { epic: "Pedidos", title: "Pago con tarjeta", acceptance: ["Muestra recibo"], external_id: "GAS-9", demo_data: true }, 7),
  e(8, "approval_required", { approval: 3 }, 8),
];
