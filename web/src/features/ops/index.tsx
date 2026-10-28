import { useEffect, useState } from "react";

import { api } from "../../lib/api";
import { Chip, DemoBadge, Item, Panel, Stat, Title } from "../../lib/ui";
import type { OpsResponse, RunOps, StageOps } from "./contract";
import "./ops.css";

export const path = "/ops";
export const label = "Costos";
export const order = 60;

const usd = (n: number) => `$${n.toFixed(2)}`;
const STATUS: Record<StageOps["status"], string> = {
  pending: "Pendiente", running: "En curso", done: "Listo", failed: "Falló",
};

function RunOpsView({ run }: { run: RunOps }) {
  const pct = Math.min(100, Math.round(run.budget_used * 100));
  return (
    <div className="ops__run">
      <div className="ops__top">
      <div className="ops__stats">
        <Stat value={usd(run.total_usd)} label="Costo del proyecto" />
        <Stat value={`${Math.round(run.duration_s)} s`} label="Duración" />
        <Stat value={String(run.failures)} label="Fallas" />
      </div>
      <Panel title="Presupuesto del plan" meta={`${usd(run.total_usd)} de ${usd(run.budget_usd)} (estimado)`}>
        <div className="ops__bar" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}
          aria-label="Costo contra presupuesto del plan">
          <span style={{ width: `${pct}%` }} />
        </div>
      </Panel>
      </div>
      <div className="ops__cols">
        <Panel title="Costo por paso" meta={`${run.steps.length} pasos`}>
          {run.steps.map((s) => (
            <Item key={s.step} tone="ink" code={usd(s.usd)}
              meta={<>{Math.round(s.units).toLocaleString("es-MX")} {s.unit}{s.estimated ? " · estimado · " : " · "}
                <a href={s.source_url} target="_blank" rel="noreferrer">precio</a></>}>
              {s.step}
            </Item>
          ))}
        </Panel>
        <Panel title="Estado por etapa" meta={`${run.stages.filter((s) => s.status === "done").length} de ${run.stages.length}`}>
          {run.stages.map((s) => (
            <Item key={s.stage} tone="ink" code={String(s.stage)}
              meta={<>{s.duration_s !== null ? `${s.duration_s} s` : "—"}{s.error ? ` · ${s.error}` : ""}</>}>
              {s.name} <Chip tone={s.status === "done" ? "ok" : s.status === "failed" ? "error" : "neutral"}>{STATUS[s.status]}</Chip>
            </Item>
          ))}
        </Panel>
      </div>
    </div>
  );
}

export default function Ops() {
  const [data, setData] = useState<OpsResponse | null>(null);
  const [error, setError] = useState(false);
  const [picked, setPicked] = useState(0);

  useEffect(() => {
    api<OpsResponse>("/ops/runs").then(setData).catch(() => setError(true));
  }, []);

  const run = data?.runs[picked];
  return (
    <div className="ops">
      <header className="ops__head">
        <Title>Costos y observabilidad</Title>
        <DemoBadge show={run?.demo_data} />
      </header>
      {error && <p className="ops__err" role="alert">No se pudo cargar la información de costos.</p>}
      {data && data.runs.length === 0 && <p>Aún no hay ejecuciones.</p>}
      {data && data.runs.length > 1 && (
        <select aria-label="Ejecución" value={picked} onChange={(e) => setPicked(Number(e.target.value))}>
          {data.runs.map((r, i) => <option key={r.run_id} value={i}>{r.run_id}</option>)}
        </select>
      )}
      {run && <RunOpsView run={run} />}
    </div>
  );
}
