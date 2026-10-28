import { useEffect, useMemo, useState } from "react";

import { api } from "../../lib/api";
import { currentRunId } from "../../lib/runId";
import { subscribe } from "../../lib/sse";
import { Button, Chip, DemoBadge, Item, MetroLine, Panel, Title } from "../../lib/ui";
import type { BacklogItem, Prototype, QualityCheck, StageEvent } from "./contract";
import { demoDelivery } from "./demo";
import "./delivery.css";

export const path = "/delivery";
export const label = "Entrega";
export const order = 40;

type State = {
  prototype: Prototype | null;
  checks: QualityCheck[];
  backlog: BacklogItem[];
  gate: boolean; // approval 3 waiting
  decided: "approved" | "rejected" | null;
  demo: boolean;
  failed: string | null;
};

const initial: State = { prototype: null, checks: [], backlog: [], gate: false, decided: null, demo: false, failed: null };

const CHECK_LABEL: Record<string, string> = {
  build: "Compilación",
  lint: "Lint",
  gitleaks: "Secretos (gitleaks)",
  rls: "Políticas RLS",
  smoke: "Prueba de humo",
};

export function reduce(s: State, ev: StageEvent): State {
  const next: State = { ...s, demo: s.demo || ev.demo_data };
  const p = ev.payload;
  const approval = Number(p.approval ?? p.number);
  switch (ev.type) {
    case "prototype_ready":
      next.prototype = p as unknown as Prototype;
      break;
    case "quality_check": {
      const c = p as unknown as QualityCheck;
      next.checks = [...s.checks.filter((x) => x.name !== c.name), c];
      break;
    }
    case "linear_issue": {
      const b = p as unknown as BacklogItem;
      next.backlog = [b, ...s.backlog.filter((x) => x.external_id !== b.external_id)];
      break;
    }
    case "approval_required":
      if (approval === 3) next.gate = true;
      break;
    case "approval_given":
      if (approval === 3) {
        next.gate = false;
        next.decided = "approved";
      }
      break;
    case "approval_rejected":
      if (approval === 3) {
        next.gate = false;
        next.decided = "rejected";
      }
      break;
    case "error":
      next.failed = String(p.message ?? "Error en la entrega.");
      break;
  }
  return next;
}

export default function Delivery() {
  const [state, setState] = useState<State>(initial);
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  // `#/delivery?run=ID` follows a real run; without it the labeled demo sample is shown.
  const runId = currentRunId();

  useEffect(() => {
    setError(null);
    if (runId) {
      setState(initial);
      setLoaded(false);
      return subscribe<StageEvent>(
        `/api/runs/${runId}/events`,
        (ev) => {
          setLoaded(true);
          setState((s) => reduce(s, ev));
        },
        () => setError("Sin conexión con el servidor."),
      );
    }
    setState(demoDelivery().reduce(reduce, initial));
    setLoaded(true);
  }, [runId]);

  const failing = useMemo(() => state.checks.filter((c) => !c.passed), [state.checks]);
  const passing = state.checks.length - failing.length;

  const decide = async (approved: boolean) => {
    setBusy(true);
    setError(null);
    try {
      if (runId) await api(`/runs/${runId}/approvals/3`, { method: "POST", body: JSON.stringify({ approved, comment }) });
      else setState((s) => ({ ...s, gate: false, decided: approved ? "approved" : "rejected" }));
      setComment("");
    } catch {
      setError("No se pudo enviar la decisión. Intenta de nuevo.");
    } finally {
      setBusy(false);
    }
  };

  const proto = state.prototype;
  const openUrl = proto?.build_url ?? proto?.url ?? null;
  const status = state.gate
    ? "Revisa el prototipo y la calidad, y decide."
    : state.decided === "approved"
      ? "Entrega aprobada."
      : state.decided === "rejected"
        ? "Pediste cambios al prototipo."
        : "Esperando el prototipo y el reporte de calidad.";

  return (
    <div className="delivery">
      <header className="delivery__head">
        <div>
          <Title>Entrega del prototipo</Title>
          <p>{status}</p>
        </div>
        <DemoBadge show={state.demo} />
      </header>

      <MetroLine current={8} notes={state.decided === "approved" ? { 8: "aprobado" } : undefined} />

      {error && <p className="delivery__err" role="alert">{error}</p>}
      {state.failed && <p className="delivery__err" role="alert">{state.failed}</p>}

      <div className="delivery__body">
        <div className="delivery__col">
          <Panel title="Prototipo" meta={proto ? (proto.generator === "lovable" ? "Generado con Lovable" : "Generado con plan B") : undefined}>
            {!proto ? (
              <Item pending>{runId && !loaded ? "Generando el prototipo…" : "Sin prototipo todavía."}</Item>
            ) : (
              <>
                {proto.url ? (
                  <iframe className="delivery__frame" title="Vista previa del prototipo" src={proto.url} sandbox="allow-scripts allow-same-origin" loading="lazy" />
                ) : (
                  <p className="delivery__empty">Vista previa no disponible: abre el prototipo en Lovable.</p>
                )}
                <div className="delivery__links">
                  {openUrl && <a href={openUrl} target="_blank" rel="noreferrer">Abrir en Lovable</a>}
                  {proto.repo_url ? <a href={proto.repo_url} target="_blank" rel="noreferrer">Ver repositorio</a> : <Chip>Sin repositorio</Chip>}
                </div>
                <dl className="delivery__facts">
                  <div><dt>Generador</dt><dd>{proto.generator === "lovable" ? "Lovable" : "Plan B (pregenerado)"}</dd></div>
                  <div><dt>Repositorio</dt><dd>{proto.repo_url ?? "sin enlace"}</dd></div>
                </dl>
              </>
            )}
          </Panel>


        </div>

        <div className="delivery__col">
          <Panel title="Puerta de calidad" meta={`${passing} de ${state.checks.length || 5} pasan`}>
            {state.checks.length === 0 ? (
              <Item pending>{runId ? "Ejecutando verificaciones…" : "Sin reporte de calidad."}</Item>
            ) : (
              state.checks.map((c) => (
                <Item key={c.name} tone={c.passed ? "rosa" : "ink"} className={c.passed ? "" : "delivery__fail"} meta={c.details || undefined}>
                  <span className="delivery__check">
                    {CHECK_LABEL[c.name] ?? c.name}
                    <Chip tone={c.passed ? "ok" : "error"}>{c.passed ? "Pasa" : "Falla"}</Chip>
                  </span>
                </Item>
              ))
            )}
          </Panel>

        </div>

        <div className="delivery__col delivery__col--side">
          {state.gate && (
            <Panel title="Aprobación 3 de 3" meta="Tras la etapa 8" className="delivery__gate">
              {failing.length > 0 && <p className="delivery__note" role="status">Hay {failing.length} verificación(es) que fallan. Puedes aprobar igualmente o pedir cambios.</p>}
              <textarea aria-label="Comentario (opcional)" rows={2} value={comment} onChange={(ev) => setComment(ev.target.value)} placeholder="Qué cambiarías o por qué apruebas" />
              <div className="delivery__actions">
                <Button variant="primary" disabled={busy} onClick={() => decide(true)}>Aprobar entrega</Button>
                <Button disabled={busy} onClick={() => decide(false)}>Pedir cambios</Button>
              </div>
            </Panel>
          )}
          <Panel title="Backlog restante" meta={`${state.backlog.length} pendientes`}>
            {state.backlog.length === 0 ? (
              <Item pending>{runId && !loaded ? "Cargando backlog…" : "No quedan issues pendientes."}</Item>
            ) : (
              state.backlog.map((b) => (
                <Item key={b.external_id} tone="ink" code={b.external_id} meta={`${b.epic} · ${b.acceptance.length} criterios`}>{b.title}</Item>
              ))
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}
