import { useState } from "react";

import { Button, Chip, DemoBadge, Item, Message, Moments, Panel, Title } from "../../lib/ui";
import type { ResearchItem } from "../../lib/types";
import { useConversation } from "./useConversation";
import "./project.css";

export const path = "/project";
export const label = "Proyecto";
export const order = 5;

// What SpeedHack is doing while a stage runs, and how long it usually takes (live runs, Gemma + APIs).
const WORKING: Record<number, string> = {
  2: "Estoy pensando qué preguntarte… suele tardar unos 20 segundos.",
  3: "Estoy buscando competidores y precios con su fuente… suele tardar menos de un minuto.",
  4: "Estoy escribiendo tu plan con tus respuestas…",
  5: "Estoy dibujando la arquitectura en Miro… suele tardar uno o dos minutos.",
  6: "Estoy creando las tareas en Linear…",
  7: "Estoy preparando tu prototipo…",
  8: "Estoy revisando el prototipo…",
  9: "Estoy armando tu pitch… suele tardar un minuto.",
};
const KIND_LABEL: Record<string, string> = { screen: "Pantallas", data_model: "Datos", integration: "Integraciones" };
const CHECK_LABEL: Record<string, string> = {
  build: "Compila", lint: "Estilo de código", gitleaks: "Sin llaves expuestas", rls: "Datos aislados por empresa", smoke: "Prueba rápida",
};

function runFromUrl(): string | null {
  return new URLSearchParams(window.location.search).get("run");
}

function Decision(props: {
  approval: number;
  waiting: boolean;
  decided?: "approved" | "rejected";
  busy: boolean;
  next: string;
  onDecide: (approved: boolean, comment: string) => void;
}) {
  const [changing, setChanging] = useState(false);
  const [comment, setComment] = useState("");
  if (props.decided === "approved") return <p className="pj-done">Aprobado. Seguimos.</p>;
  if (!props.waiting) return null;
  if (changing) {
    return (
      <div className="pj-decide">
        <label className="pj-label" htmlFor={`cambios-${props.approval}`}>¿Qué cambiarías? Dilo con tus palabras.</label>
        <textarea
          id={`cambios-${props.approval}`}
          className="pj-input"
          rows={3}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Ej. Agrega un rol de auditor que solo pueda ver los gastos."
        />
        <div className="pj-actions">
          <Button onClick={() => setChanging(false)}>Volver</Button>
          <Button variant="primary" disabled={props.busy || !comment.trim()} onClick={() => props.onDecide(false, comment)}>
            Rehacer con mis cambios
          </Button>
        </div>
        {!comment.trim() && <p className="pj-hint">Escribe qué cambiarías para poder rehacerlo.</p>}
      </div>
    );
  }
  return (
    <div className="pj-decide">
      <div className="pj-actions">
        <Button variant="primary" disabled={props.busy} onClick={() => props.onDecide(true, "")}>Sí, sigamos</Button>
        <Button disabled={props.busy} onClick={() => setChanging(true)}>Cambiar algo</Button>
      </div>
      <p className="pj-hint">Después: {props.next}</p>
    </div>
  );
}

function Source({ item }: { item: ResearchItem }) {
  return (
    <Item code={undefined} meta={item.pricing ? `Precio: ${item.pricing}` : "Sin precio publicado"}>
      <a href={item.url} target="_blank" rel="noreferrer">{item.competitor}</a>
    </Item>
  );
}

export default function Project() {
  const [runId] = useState(runFromUrl);
  const { state: c, busy, answer, decide } = useConversation(runId);
  const [answers, setAnswers] = useState<string[]>([]);
  const waiting = (what: string) => c.awaiting === what;
  const working = c.status === "running" && !c.awaiting && !c.error ? WORKING[c.stage] : null;
  const runQuery = runId ? `?run=${encodeURIComponent(runId)}` : "";
  const groups = Object.entries(KIND_LABEL)
    .map(([kind, name]) => ({ name, titles: c.miro.filter((m) => m.kind === kind).map((m) => m.title) }))
    .filter((g) => g.titles.length);

  return (
    <div className="pj">
      <header className="pj-top">
        <div>
          <Title>{c.spec ? "Tu proyecto" : "Empecemos tu proyecto"}</Title>
          {runId && (
            <a className="pj-detail" href={`${runQuery}#/run`}>Ver el detalle de las 9 etapas</a>
          )}
        </div>
        <div className="pj-status">
          <Moments stage={c.stage} />
          <DemoBadge show={c.demo || !runId} />
        </div>
      </header>

      <div className="pj-chat">
        {!runId && (
          <Message>
            Este es un ejemplo grabado para que veas cómo funciona. <a href="#/intake">Cuéntame tu idea</a> y lo hacemos
            con la tuya.
          </Message>
        )}

        {c.questions.length > 0 && (
          <>
            <Message>Para entenderte mejor, tengo {c.questions.length} preguntas.</Message>
            <Panel className="pj-card">
              {c.questions.map((q, i) => (
                <div key={q} className="pj-q">
                  <label className="pj-label" htmlFor={`r-${i}`}>{q}</label>
                  {waiting("answers") ? (
                    <textarea
                      id={`r-${i}`}
                      className="pj-input"
                      rows={2}
                      value={answers[i] ?? ""}
                      onChange={(e) => setAnswers((a) => Object.assign([...a], { [i]: e.target.value }))}
                    />
                  ) : (
                    <p className="pj-answered">{answers[i]?.trim() || "Respondida"}</p>
                  )}
                </div>
              ))}
              {waiting("answers") && (
                <div className="pj-decide">
                  <div className="pj-actions">
                    <Button
                      variant="primary"
                      disabled={busy || c.questions.some((_, i) => !(answers[i] ?? "").trim())}
                      onClick={() => answer(c.questions.map((_, i) => answers[i].trim()))}
                    >
                      Enviar respuestas
                    </Button>
                  </div>
                  <p className="pj-hint">Responde las {c.questions.length} para seguir. Después: investigo tu mercado.</p>
                </div>
              )}
            </Panel>
          </>
        )}

        {c.research.length > 0 && (
          <>
            <Message>Revisé {c.research.length} fuentes de tu mercado. Cada dato tiene su enlace.</Message>
            <Panel className="pj-card">
              {c.research.map((r) => <Source key={r.url} item={r} />)}
            </Panel>
          </>
        )}

        {c.spec && (
          <>
            <Message>Con tus respuestas y esas fuentes armé tu plan. ¿Lo dejamos así?</Message>
            <Panel className="pj-card">
              <h2 className="pj-h">Qué vamos a construir</h2>
              <dl className="pj-plan">
                <dt>El problema</dt><dd>{c.spec.problem}</dd>
                {c.spec.users.length > 0 && (<><dt>Para quién</dt><dd>{c.spec.users.join(", ")}</dd></>)}
                <dt>Lo primero que tendrá</dt>
                <dd><ul>{c.spec.mvp_features.map((f) => <li key={f}>{f}</li>)}</ul></dd>
              </dl>
              <Decision
                approval={1}
                waiting={waiting("approval:1")}
                decided={c.decided[1]}
                busy={busy}
                next="dibujo la arquitectura en Miro y creo las tareas en Linear."
                onDecide={(ok, comment) => decide(1, ok, comment)}
              />
            </Panel>
          </>
        )}

        {groups.length > 0 && (
          <>
            <Message>
              Dibujé la arquitectura en Miro: {groups.map((g) => `${g.titles.length} ${g.name.toLowerCase()}`).join(", ")}.
            </Message>
            <Panel className="pj-card">
              <div className="pj-groups">
                {groups.map((g) => (
                  <div key={g.name}>
                    <h3 className="pj-label">{g.name}</h3>
                    {g.titles.map((t) => <Item key={t}>{t}</Item>)}
                  </div>
                ))}
              </div>
              <a className="pj-link" href={`${runQuery}#/live-board`}>Ver el tablero en vivo</a>
            </Panel>
          </>
        )}

        {c.issues.length > 0 && (
          <>
            <Message>Creé {c.issues.length} tareas en Linear, cada una con sus criterios de aceptación.</Message>
            <Panel className="pj-card">
              {c.issues.map((i) => (
                <Item key={i.external_id} code={i.linear_id ?? undefined} meta={i.epic}>
                  {i.url ? <a href={i.url} target="_blank" rel="noreferrer">{i.title}</a> : i.title}
                </Item>
              ))}
              <Decision
                approval={2}
                waiting={waiting("approval:2")}
                decided={c.decided[2]}
                busy={busy}
                next="preparo tu prototipo y lo reviso."
                onDecide={(ok, comment) => decide(2, ok, comment)}
              />
            </Panel>
          </>
        )}

        {c.prototype && (
          <>
            <Message>Tu prototipo está listo. Lo revisé antes de mostrártelo.</Message>
            <Panel className="pj-card">
              <a className="pj-link" href={c.prototype.url} target="_blank" rel="noreferrer">Abrir el prototipo</a>
              {c.prototype.build_url && c.prototype.build_url !== c.prototype.url && (
                <a className="pj-link" href={c.prototype.build_url} target="_blank" rel="noreferrer">Construirlo desde tu plan en Lovable</a>
              )}
              {c.checks.length > 0 && (
                <div className="pj-checks">
                  {c.checks.map((k) => (
                    <Chip key={k.name} tone={k.passed ? "ok" : "error"}>{CHECK_LABEL[k.name] ?? k.name}</Chip>
                  ))}
                </div>
              )}
              <Decision
                approval={3}
                waiting={waiting("approval:3")}
                decided={c.decided[3]}
                busy={busy}
                next="armo tu pitch con las fuentes del proyecto."
                onDecide={(ok, comment) => decide(3, ok, comment)}
              />
            </Panel>
          </>
        )}

        {c.pitch && (
          <>
            <Message>Preparé tu pitch: {c.pitch.slides.length} diapositivas, y un juez puede preguntarte por voz.</Message>
            <Panel className="pj-card">
              <ol className="pj-slides">{c.pitch.slides.map((s) => <li key={s.title}>{s.title}</li>)}</ol>
              <div className="pj-actions">
                <a className="sh-btn sh-btn--primary pj-cta" href={`${runQuery}#/pitch`}>Ir a la sala de pitch</a>
              </div>
            </Panel>
          </>
        )}

        {working && <Message><span className="pj-working">{working}</span></Message>}
        {c.error && (
          <Message>
            <span className="pj-error">{c.error}</span> Puedes volver a intentarlo desde el <a href={`${runQuery}#/run`}>detalle</a>.
          </Message>
        )}
      </div>
    </div>
  );
}
