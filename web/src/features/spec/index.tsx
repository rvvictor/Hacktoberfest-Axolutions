import { useState } from "react";

import { api } from "../../lib/api";
import type { Spec } from "../../lib/types";
import { Button, Chip, DemoBadge, Item, MetroLine, Panel, Title } from "../../lib/ui";
import { useSpecEvents } from "./useSpecEvents";
import "./spec.css";

export const path = "/spec";
export const label = "Spec";
export const order = 20;

const params = () => new URLSearchParams(window.location.search);

function ClientSummary({ spec }: { spec: Spec }) {
  return (
    <div className="sp-plain">
      <p><strong>Qué problema resolvemos.</strong> {spec.problem}</p>
      <p><strong>Para quién.</strong> {spec.users.map((u) => u.split(":")[0]).join(", ")}.</p>
      <p><strong>Qué podrás hacer desde el primer día.</strong> {spec.mvp_features.join("; ")}.</p>
      <p><strong>Lo que damos por cierto por ahora.</strong> {spec.assumptions.join("; ")}. Si algo no es así, dínoslo antes de aprobar.</p>
    </div>
  );
}

function SpecBody({ spec }: { spec: Spec }) {
  const blocks: [string, string[]][] = [
    ["Usuarios", spec.users], ["Funciones del MVP", spec.mvp_features], ["Supuestos", spec.assumptions],
  ];
  return (
    <div className="sp-spec">
      <section>
        <h3>Problema</h3>
        <p>{spec.problem}</p>
      </section>
      {blocks.map(([title, rows]) => (
        <section key={title}>
          <h3>{title}</h3>
          <ul>{rows.map((r) => <li key={r}>{r}</li>)}</ul>
        </section>
      ))}
    </div>
  );
}

export default function SpecReview() {
  const [runId] = useState(() => params().get("run"));
  const { state, setState } = useSpecEvents(runId);
  const [client, setClient] = useState(() => params().get("mode") === "client");
  const [picked, setPicked] = useState<number | null>(null);
  const [changing, setChanging] = useState(false);
  const [comment, setComment] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const spec = state.specs.find((s) => s.version === picked) ?? state.specs[state.specs.length - 1];
  const latest = state.specs[state.specs.length - 1];
  const canDecide = state.awaiting && spec === latest;

  async function decide(approved: boolean) {
    setError(null);
    if (!approved && !comment.trim()) { setError("Cuéntanos qué cambiar para pedir cambios."); return; }
    setBusy(true);
    try {
      if (runId) {
        await api(`/runs/${encodeURIComponent(runId)}/approvals/1`, {
          method: "POST",
          body: JSON.stringify({ approved, comment }),
        });
      } else {
        setState((s) => ({ ...s, awaiting: false, decided: approved ? "approved" : "rejected" }));
      }
      setChanging(false);
    } catch (e) {
      setError(`No se pudo enviar: ${(e as Error).message}. Intenta de nuevo.`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="sp">
      <div className="sp-top">
        <div>
          <Title>Control de gastos corporativos</Title>
          <p>Revisa lo que entendimos y de dónde sale cada cifra antes de diseñar.</p>
        </div>
        <DemoBadge show={state.demo} />
      </div>

      <MetroLine current={4} notes={state.decided === "approved" ? { 4: "aprobado" } : undefined} />

      <div className="sp-grid">
        <Panel
          title={client ? "Resumen para ti" : "Spec"}
          meta={
            <span className="sp-tools">
              {state.specs.length > 1 && (
                <select aria-label="Versión del spec" value={spec?.version} onChange={(e) => setPicked(Number(e.target.value))}>
                  {state.specs.map((s) => <option key={s.version} value={s.version}>Versión {s.version}</option>)}
                </select>
              )}
              <Button onClick={() => setClient((c) => !c)} aria-pressed={client}>{client ? "Ver spec técnico" : "Vista cliente"}</Button>
            </span>
          }
        >
          <div className="sp-scroll">
            {!spec ? <p className="sp-empty">Esperando el spec…</p> : client ? <ClientSummary spec={spec} /> : <SpecBody spec={spec} />}
          </div>
        </Panel>

        <Panel title="Competidores" meta={`${state.research.length} fuentes`}>
          <div className="sp-scroll">
            {state.research.length === 0 ? (
              <p className="sp-empty">La investigación llega aquí, con su enlace.</p>
            ) : (
              <table className="sp-table">
                <thead>
                  <tr><th>Competidor</th><th>Precio</th><th>Funciones</th></tr>
                </thead>
                <tbody>
                  {state.research.map((r) => (
                    <tr key={r.url}>
                      <th scope="row"><a href={r.url} target="_blank" rel="noreferrer">{r.competitor}</a></th>
                      <td>
                        {r.pricing ? <a href={r.url} target="_blank" rel="noreferrer">{r.pricing}</a> : <span className="sp-none">sin precio publicado</span>}
                        {r.fetched_at && <small>consultado {r.fetched_at.slice(0, 10)}</small>}
                      </td>
                      <td>
                        <ul>{r.features.map((f) => <li key={f}>{f}</li>)}</ul>
                        <a className="sp-src" href={r.url} target="_blank" rel="noreferrer">Fuente</a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </Panel>
      </div>

      <Item tone="naranja" className="sp-approval" aria-label="Aprobación 1">
        <div className="sp-approval__text">
          <strong>Aprobación 1</strong>
          <span>
            {state.decided === "approved" ? "Spec aprobado. Sigue la arquitectura."
              : state.decided === "rejected" ? "Pediste cambios. Generaremos una nueva versión."
              : canDecide ? "Si el spec y las fuentes se ven bien, aprueba para pasar al diseño."
              : "Esperando la versión final del spec."}
          </span>
        </div>
        {state.decided ? (
          <Chip tone={state.decided === "approved" ? "ok" : "error"}>{state.decided === "approved" ? "Aprobado" : "Cambios pedidos"}</Chip>
        ) : (
          <div className="sp-approval__actions">
            {changing && (
              <textarea aria-label="Qué debemos cambiar" rows={2} placeholder="¿Qué debemos cambiar?" value={comment} onChange={(e) => setComment(e.target.value)} />
            )}
            <Button variant="primary" disabled={!canDecide || busy} onClick={() => decide(true)}>Aprobar spec</Button>
            <Button disabled={!canDecide || busy} onClick={() => (changing ? decide(false) : setChanging(true))}>
              {changing ? "Enviar cambios" : "Pedir cambios"}
            </Button>
          </div>
        )}
        {error && <span className="sp-error" role="alert">{error}</span>}
      </Item>
    </div>
  );
}
