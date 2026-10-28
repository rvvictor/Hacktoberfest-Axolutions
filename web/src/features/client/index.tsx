import { useEffect, useRef, useState } from "react";

import { api } from "../../lib/api";
import { Button, Chip, DemoBadge, Item, Panel, Stat, Title } from "../../lib/ui";
import "./client.css";
import { FALLBACK_JOURNEY, type Journey } from "./fixture";

export const path = "/client";
export const label = "Modo Cliente";
export const order = 20;

const STEPS = ["Lo que nos contó", "Su página", "Cómo vamos", "Para compartir"] as const;

function minutes(seconds: number): string {
  return `${Math.round(seconds / 60)} min`;
}

function AudioGuide({ guide }: { guide: Journey["audio_guide"] }) {
  const [speaking, setSpeaking] = useState(false);
  const canSpeak = typeof window !== "undefined" && "speechSynthesis" in window;

  useEffect(() => () => { if (canSpeak) window.speechSynthesis.cancel(); }, [canSpeak]);

  function toggle() {
    if (!canSpeak) return;
    if (speaking) {
      window.speechSynthesis.cancel();
      setSpeaking(false);
      return;
    }
    const voice = new SpeechSynthesisUtterance(guide.transcript.join(" "));
    voice.lang = "es-MX";
    voice.onend = () => setSpeaking(false);
    window.speechSynthesis.speak(voice);
    setSpeaking(true);
  }

  return (
    <Panel title={guide.title} meta={minutes(guide.duration_seconds)}>
      <div className="cl-audio">
        {guide.src ? (
          <audio controls src={guide.src} aria-label={guide.title} />
        ) : (
          canSpeak && (
            <Button variant="secondary" onClick={toggle}>
              {speaking ? "Detener audio" : "Escuchar la guía"}
            </Button>
          )
        )}
        {!guide.recorded && <p>{guide.note}</p>}
      </div>
      <ol className="cl-transcript" aria-label="Texto de la guía">
        {guide.transcript.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ol>
    </Panel>
  );
}

function StepContent({ step, j }: { step: number; j: Journey }) {
  if (step === 0)
    return (
      <Panel title={`${j.business.name}, ${j.business.owner}`} meta={`${j.questions.length} preguntas`}>
        <div className="cl-stack">
          {j.questions.map((q, i) => (
            <Item key={q.id} code={String(i + 1)} meta={q.answer}>
              {q.question}
            </Item>
          ))}
        </div>
      </Panel>
    );
  if (step === 1)
    return (
      <div className="cl-body">
        <Panel title="En pocas palabras">
          <p className="cl-lead">{j.summary.headline}</p>
          <ul className="cl-points">
            {j.summary.points.map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ul>
        </Panel>
        <Panel title="Las pantallas de su página" meta={`${j.screens.length} pantallas`}>
          <div className="cl-phones">
            {j.screens.map((s, i) => (
              <div key={s.id} className="cl-phone">
                <strong>
                  {i + 1}. {s.title}
                </strong>
                <span>{s.description}</span>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    );
  if (step === 2)
    return (
      <div className="cl-body">
        <Panel title="Cómo va su página">
          <div className="cl-big">
            <b>{j.progress.percent}%</b>
            <span>listo</span>
          </div>
          <div className="cl-bar" role="progressbar" aria-valuenow={j.progress.percent} aria-valuemin={0} aria-valuemax={100} aria-label="Avance de su página">
            <b style={{ width: `${j.progress.percent}%` }} />
          </div>
          <ol className="cl-list">
            {j.progress.steps.map((s) => (
              <li key={s.id} data-state={s.state} aria-current={s.state === "current" ? "step" : undefined}>
                {s.title}
              </li>
            ))}
          </ol>
        </Panel>
        <Panel title="Aviso por WhatsApp" meta="Vista previa, no se envió">
          <div className="cl-wa">
            <small>Para: {j.whatsapp.to_name}</small>
            <div className="cl-wa__bubble">{j.whatsapp.message}</div>
            <Chip tone="ok">{j.whatsapp.opt_in}</Chip>
            <small>{j.whatsapp.opt_out}</small>
          </div>
        </Panel>
      </div>
    );
  return (
    <div className="cl-body">
      <Panel title="Su página en internet" meta="Enlace de ejemplo">
        <a className="cl-link" href={j.published_app.url} onClick={(e) => e.preventDefault()}>
          {j.published_app.url}
        </a>
        <p>{j.published_app.note}</p>
        <Stat value={`${j.screens.length}`} label="pantallas dibujadas para sus clientes" />
      </Panel>
      <AudioGuide guide={j.audio_guide} />
    </div>
  );
}

export default function ClientMode() {
  const [journey, setJourney] = useState<Journey>(FALLBACK_JOURNEY);
  const [step, setStep] = useState(0);
  const top = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let alive = true;
    api<Journey>("/client/journey")
      .then((data) => alive && setJourney(data))
      .catch(() => undefined); // the local copy of the fixture stays on screen
    return () => {
      alive = false;
    };
  }, []);

  const last = STEPS.length - 1;
  return (
    <div className="cl" ref={top}>
      <div className="cl__head">
        <div>
          <Title>Su página, paso a paso</Title>
          <p>Le explicamos con palabras sencillas qué estamos armando para {journey.business.name}.</p>
        </div>
        <DemoBadge show={journey.demo_data} />
      </div>
      <ol className="cl-steps" aria-label="Pasos">
        {STEPS.map((name, i) => (
          <li key={name} data-state={i < step ? "done" : i === step ? "current" : "next"} aria-current={i === step ? "step" : undefined}>
            <span>
              {i + 1}. {name}
            </span>
          </li>
        ))}
      </ol>
      <StepContent step={step} j={journey} />
      <div className="cl-nav">
        <Button disabled={step === 0} onClick={() => setStep(step - 1)}>
          Atrás
        </Button>
        {step < last ? <Button variant="primary" onClick={() => setStep(step + 1)}>Siguiente</Button> : <Button onClick={() => setStep(0)}>Volver al inicio</Button>}
      </div>
    </div>
  );
}
