import type { ResearchItem, Spec } from "../../lib/types";

// Local demo (no ?run=): simulated content, every item carries demo_data and example.invalid URLs.
const base = { demo_data: true, fetched_at: null };

export const DEMO_RESEARCH: ResearchItem[] = [
  { ...base, competitor: "Competidor demo A", pricing: "Precio de ejemplo, no real", features: ["Tarjetas virtuales", "Conciliación bancaria", "Reglas de aprobación"], url: "https://example.invalid/demo/competidor-a" },
  { ...base, competitor: "Competidor demo B", pricing: null, features: ["Captura de recibos con OCR", "Reportes por centro de costo"], url: "https://example.invalid/demo/competidor-b" },
  { ...base, competitor: "Competidor demo C", pricing: "Precio de ejemplo, no real", features: ["Alertas de límite", "Multiempresa", "Exportación contable"], url: "https://example.invalid/demo/competidor-c" },
  { ...base, competitor: "Competidor demo D", pricing: null, features: ["Viáticos y anticipos", "App móvil"], url: "https://example.invalid/demo/competidor-d" },
];

const v1: Spec = {
  version: 1, demo_data: true,
  problem: "Las áreas de finanzas de pymes reconcilian gastos de equipo en hojas de cálculo y correos: los reembolsos tardan semanas y los excesos se descubren al cierre del mes.",
  users: ["Finanzas: controla presupuesto y cierre", "Aprobadores: líderes de equipo que autorizan gastos", "Empleados: capturan recibos y piden reembolso"],
  mvp_features: ["Registro de gastos con foto del recibo", "Aprobación por roles", "Alertas al acercarse al límite", "Varias empresas en una cuenta"],
  assumptions: ["Las pymes ya pagan con tarjeta corporativa o reembolsan en efectivo", "La contabilidad se exporta en CSV al inicio", "Sin cifras de mercado hasta tener fuentes verificadas"],
  sources: ["https://example.invalid/demo/competidor-a"],
};

export const DEMO_SPECS: Spec[] = [
  v1,
  {
    ...v1, version: 2,
    mvp_features: [...v1.mvp_features, "Exportación CSV para contabilidad"],
    assumptions: [...v1.assumptions, "El primer cliente piloto usa un solo país y una sola moneda"],
    sources: ["https://example.invalid/demo/competidor-a", "https://example.invalid/demo/competidor-c"],
  },
];
