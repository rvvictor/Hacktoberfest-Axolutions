import { useEffect, useRef, useState } from "react";

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
  build: "Compila", lint: "Estilo de código", gitleaks: "Sin llaves expuestas", secrets: "Sin llaves expuestas",
  rls: "Datos aislados por empresa", smoke: "Prueba rápida",
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
  const { state: c, busy, answer, decide, retry } = useConversation(runId);
  const own = c.prototype?.generator === "speedhack"; // built here: previewed inline, Lovable only to keep building
  const [answers, setAnswers] = useState<string[]>([]);
  const [turn, setTurn] = useState(0); // the question being answered now
  const end = useRef<HTMLDivElement>(null);
  const progress = [
    turn, c.questions.length, c.research.length, c.spec?.version, c.miro.length, c.issues.length,
    c.prototype?.url, c.checks.length, c.pitch?.slides.length, c.awaiting, c.error, c.warning?.stage,
  ].join("|");

  // Keep the newest turn and its action in view (usability: visibility of system status).
  useEffect(() => {
    const smooth = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    end.current?.scrollIntoView({ behavior: smooth ? "smooth" : "auto", block: "end" });
  }, [progress]);
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
            <Message>Para entenderte mejor, te haré {c.questions.length} preguntas cortas, una a la vez.</Message>
            {c.questions.map((q, i) => {
              const asked = !waiting("answers") || i <= turn;
              if (!asked) return null;
              const done = !waiting("answers") || i < turn;
              return (
                <div key={q} className="pj-turn">
                  <Message>{q}</Message>
                  {done ? (
                    answers[i]?.trim() && <Message from="you">{answers[i].trim()}</Message>
                  ) : (
                    <form
                      className="pj-reply"
                      onSubmit={(e) => {
                        e.preventDefault();
                        if (!(answers[i] ?? "").trim() || busy) return;
                        if (i < c.questions.length - 1) setTurn(i + 1);
                        else void answer(c.questions.map((_, k) => answers[k].trim()));
                      }}
                    >
                      <label className="pj-label sr-only" htmlFor={`r-${i}`}>Tu respuesta</label>
                      <textarea
                        id={`r-${i}`}
                        className="pj-input"
                        rows={2}
                        autoFocus
                        placeholder="Responde lo que sepas; puede ser breve."
                        value={answers[i] ?? ""}
                        onChange={(e) => setAnswers((a) => Object.assign([...a], { [i]: e.target.value }))}
                      />
                      <div className="pj-actions">
                        <Button type="submit" variant="primary" disabled={busy || !(answers[i] ?? "").trim()}>
                          {i < c.questions.length - 1 ? "Responder" : "Responder y seguir"}
                        </Button>
                        <span className="pj-hint">
                          Pregunta {i + 1} de {c.questions.length}
                          {i === c.questions.length - 1 ? " · después investigo tu mercado" : ""}
                        </span>
                      </div>
                    </form>
                  )}
                </div>
              );
            })}
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
            <Panel className="pj-card pj-list">
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
            <Message>
              {own ? "Construí tu prototipo con tu plan y lo revisé antes de mostrártelo. Pruébalo aquí mismo." : "Tu prototipo está listo. Lo revisé antes de mostrártelo."}
            </Message>
            <Panel className="pj-card">
              {own && (
                // Our own generated app: scripts only, no same-origin, so it cannot reach SpeedHack.
                <iframe className="pj-frame" title="Tu prototipo" src={c.prototype.url} sandbox="allow-scripts allow-forms allow-modals" />
              )}
              <a className="sh-btn sh-btn--secondary pj-cta" href={c.prototype.url} target="_blank" rel="noreferrer">
                Abrir el prototipo
              </a>
              {c.prototype.build_url && c.prototype.build_url !== c.prototype.url && (
                <a className="pj-link" href={c.prototype.build_url} target="_blank" rel="noreferrer">
                  {own ? "Seguir construyéndolo en Lovable" : "Construirlo desde tu plan en Lovable"}
                </a>
              )}
              {c.checks.length > 0 && (
                <div className="pj-checks">
                  {c.checks.map((k) => (
                    <Chip key={k.name} tone={k.passed ? "ok" : "error"}>{CHECK_LABEL[k.name] ?? k.name}</Chip>
                  ))}
                </div>
              )}
              {c.checks.some((k) => !k.passed) && (
                <p className="pj-hint">
                  Revisa esto antes de publicar:{" "}
                  {c.checks.filter((k) => !k.passed).map((k) => (CHECK_LABEL[k.name] ?? k.name).toLowerCase()).join(", ")}
                  . Si pides cambios, lo corrijo en el plan.
                </p>
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
              <ol className="pj-slides">
                {c.pitch.slides.map((s, n) => (
                  <li key={s.title}>
                    <small>{n + 1}</small>
                    <b>{s.title}</b>
                    {s.bullets[0] && <span>{s.bullets[0]}</span>}
                  </li>
                ))}
              </ol>
              <div className="pj-actions">
                <a className="sh-btn sh-btn--primary pj-cta" href={`${runQuery}#/pitch`}>Ir a la sala de pitch</a>
              </div>
            </Panel>
          </>
        )}

        {working && <Message><span className="pj-working">{working}</span></Message>}
        {c.warning && (
          <>
            <Message>Casi todo quedó listo, pero me faltó algo.</Message>
            <Panel className="pj-card pj-warning" role="status">
              <h2 className="pj-h">Aviso: quedó algo sin crear</h2>
              <p>
                {c.warning.skipped.length > 0
                  ? `Miro no me dejó crear ${c.warning.skipped.length} ${c.warning.skipped.length === 1 ? "nota" : "notas"}; el resto del tablero se conservó.`
                  : c.warning.message}
              </p>
              {c.warning.skipped.length > 0 && (
                <>
                  <ul className="pj-skipped">{c.warning.skipped.map((t) => <li key={t}>{t}</li>)}</ul>
                  <p className="pj-hint">Puedes agregarlas a mano en Miro cuando quieras.</p>
                </>
              )}
            </Panel>
          </>
        )}
        {c.error && c.retryable && (
          <>
            <Message>Tuve un problema con esta etapa. Pulsa Reintentar y lo intento otra vez.</Message>
            <Panel className="pj-card pj-failed" role="alert">
              <h2 className="pj-h">Esta etapa no terminó</h2>
              <p className="pj-error">{c.error}</p>
              <div className="pj-actions">
                <Button variant="primary" disabled={busy} onClick={() => void retry()}>
                  {busy ? "Reintentando…" : "Reintentar"}
                </Button>
                <span className="pj-hint">Lo que ya se creó no se duplica.</span>
              </div>
            </Panel>
          </>
        )}
        {c.error && !c.retryable && (
          <Message>
            <span className="pj-error">{c.error}</span> Puedes volver a intentarlo desde el <a href={`${runQuery}#/run`}>detalle</a>.
          </Message>
        )}
        <div ref={end} />
      </div>
    </div>
  );
}
