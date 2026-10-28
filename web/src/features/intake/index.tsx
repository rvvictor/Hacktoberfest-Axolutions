import { useCallback, useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";

import { Button, Chip, DemoBadge, MetroLine, SectionHeader, Title } from "../../lib/ui";
import { api } from "../../lib/api";
import { DEMO_QUESTIONS, DEMO_RUN, STACKS } from "./contract";
import type { Mode, QuestionEvent, Run } from "./contract";
import "./intake.css";

export const path = "/intake";
export const label = "Nueva idea";
export const order = 1;

type Phase = "idea" | "creating" | "questions" | "sending";

const MODES: { id: Mode; name: string; hint: string }[] = [
  { id: "dev", name: "Desarrollador", hint: "Preguntas técnicas y stack a tu medida" },
  { id: "client", name: "Cliente", hint: "Preguntas de negocio, sin jerga" },
];

function goToRun(runId: string) {
  window.location.href = `${window.location.pathname}?run=${encodeURIComponent(runId)}#/run`;
}

export default function Intake() {
  const [mode, setMode] = useState<Mode>("dev");
  const [idea, setIdea] = useState("");
  const [stack, setStack] = useState<string[]>([]);
  const [phase, setPhase] = useState<Phase>("idea");
  const [error, setError] = useState<string | null>(null);
  const [demo, setDemo] = useState(false);
  const [run, setRun] = useState<Run | null>(null);
  const [questions, setQuestions] = useState<string[]>([]);
  const [answers, setAnswers] = useState<string[]>([]);
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const recorder = useRef<MediaRecorder | null>(null);
  const closeStream = useRef<(() => void) | null>(null);

  useEffect(() => () => closeStream.current?.(), []);

  const toggleStack = (name: string) =>
    setStack((cur) => (cur.includes(name) ? cur.filter((s) => s !== name) : [...cur, name]));

  // Dictation: record, POST the audio to /api/voice/stt, append the transcript.
  const toggleMic = async () => {
    setError(null);
    if (recording) {
      recorder.current?.stop();
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const chunks: Blob[] = [];
      const rec = new MediaRecorder(stream);
      rec.ondataavailable = (e) => chunks.push(e.data);
      rec.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        setRecording(false);
        setTranscribing(true);
        try {
          const body = new FormData();
          body.append("audio", new Blob(chunks, { type: rec.mimeType || "audio/webm" }), "idea.webm");
          const res = await fetch("/api/voice/stt", { method: "POST", body });
          if (!res.ok) throw new Error(String(res.status));
          const { text } = (await res.json()) as { text: string };
          setIdea((cur) => (cur ? `${cur} ${text}` : text));
        } catch {
          setError("No pudimos transcribir el audio. Escribe tu idea o intenta de nuevo.");
        } finally {
          setTranscribing(false);
        }
      };
      recorder.current = rec;
      rec.start();
      setRecording(true);
    } catch {
      setError("No hay acceso al micrófono. Revisa el permiso del navegador o escribe tu idea.");
    }
  };

  const showQuestions = useCallback((qs: string[]) => {
    setQuestions(qs);
    setAnswers(qs.map(() => ""));
    setPhase("questions");
  }, []);

  const startDemo = () => {
    setDemo(true);
    setRun(DEMO_RUN);
    showQuestions(DEMO_QUESTIONS[mode]);
  };

  const submitIdea = async (e: FormEvent) => {
    e.preventDefault();
    if (!idea.trim()) return;
    setError(null);
    setPhase("creating");
    try {
      const created = await api<Run>("/projects", {
        method: "POST",
        body: JSON.stringify({ mode, idea: idea.trim(), stack_prefs: mode === "dev" ? stack : [] }),
      });
      setRun(created);
      setDemo(created.demo_data);
      // The backend emits named SSE events (`question`), so listen by type.
      const source = new EventSource(`/api/runs/${created.run_id}/events`);
      const found: string[] = [];
      let timer: number | undefined;
      const stop = () => {
        window.clearTimeout(timer);
        source.close();
      };
      closeStream.current = stop;
      source.addEventListener("question", (msg) => {
        const ev = JSON.parse((msg as MessageEvent).data) as QuestionEvent;
        found.push(ev.payload.text);
        window.clearTimeout(timer);
        // Questions arrive one by one; show them once the burst ends.
        timer = window.setTimeout(() => {
          stop();
          showQuestions([...found]);
        }, 1200);
      });
      source.onerror = () => {
        if (!found.length) {
          stop();
          setPhase("idea");
          setError("Se cortó la conexión con el servidor. Intenta de nuevo o usa la demostración.");
        }
      };
    } catch {
      setPhase("idea");
      setError("No pudimos crear el proyecto. Intenta de nuevo o usa la demostración.");
    }
  };

  const submitAnswers = async (e: FormEvent) => {
    e.preventDefault();
    if (!run) return;
    setPhase("sending");
    setError(null);
    if (demo) {
      goToRun(run.run_id);
      return;
    }
    try {
      await api(`/runs/${run.run_id}/answers`, { method: "POST", body: JSON.stringify({ answers }) });
      goToRun(run.run_id);
    } catch {
      setPhase("questions");
      setError("No pudimos enviar tus respuestas. Intenta de nuevo.");
    }
  };

  const answered = answers.filter((a) => a.trim()).length;
  const step = phase === "questions" || phase === "sending" ? 2 : 1;

  return (
    <div className="intake">
      <MetroLine current={step} />
      <div className="intake__head">
        <Title>{step === 1 ? "Cuéntanos tu idea" : "Afinemos los detalles"}</Title>
        <DemoBadge show={demo} />
      </div>

      {step === 1 ? (
        <form className="intake__main" onSubmit={submitIdea}>
          <div className="intake__modes" role="radiogroup" aria-label="Modo">
            {MODES.map((m) => (
              <button
                key={m.id}
                type="button"
                role="radio"
                aria-checked={mode === m.id}
                className="intake__mode"
                onClick={() => setMode(m.id)}
              >
                <strong>{m.name}</strong>
                <span>{m.hint}</span>
              </button>
            ))}
          </div>

          <label className="intake__field">
            <span className="intake__label">Tu idea</span>
            <textarea
              value={idea}
              onChange={(e) => setIdea(e.target.value)}
              rows={3}
              placeholder="Ej. Una app para que mi equipo apruebe gastos desde el celular"
              disabled={phase === "creating"}
            />
          </label>

          <div className="intake__row">
            <Button onClick={toggleMic} disabled={transcribing || phase === "creating"} aria-pressed={recording}>
              {recording ? "Detener grabación" : transcribing ? "Transcribiendo…" : "Dictar por voz"}
            </Button>
            <span className="intake__status" role="status">
              {recording ? "Grabando… habla con calma" : ""}
            </span>
          </div>

          {mode === "dev" && (
            <fieldset className="intake__stack">
              <legend className="intake__label">Stack preferido (opcional)</legend>
              <div className="intake__chips">
                {STACKS.map((s) => (
                  <button
                    key={s}
                    type="button"
                    className="intake__pin"
                    aria-pressed={stack.includes(s)}
                    onClick={() => toggleStack(s)}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </fieldset>
          )}

          {error && (
            <p className="intake__error" role="alert">
              {error}
            </p>
          )}

          <div className="intake__row">
            <Button variant="primary" type="submit" disabled={!idea.trim() || phase === "creating"}>
              {phase === "creating" ? "Preparando preguntas…" : "Empezar"}
            </Button>
            <Button onClick={startDemo} disabled={phase === "creating"}>
              Ver demostración
            </Button>
          </div>
          {phase === "creating" && (
            <div className="intake__skeleton" aria-hidden="true">
              <i /> <i /> <i />
            </div>
          )}
        </form>
      ) : (
        <form className="intake__main" onSubmit={submitAnswers}>
          <SectionHeader title="Preguntas de aclaración" meta={`${answered} de ${questions.length}`} />
          <p className="intake__idea">
            <Chip tone="rosa">{mode === "dev" ? "Desarrollador" : "Cliente"}</Chip> {idea || "Idea de demostración"}
          </p>
          {questions.map((q, i) => (
            <label key={q} className="intake__field">
              <span className="intake__q">
                <b>{i + 1}</b>
                {q}
              </span>
              <textarea
                rows={2}
                value={answers[i] ?? ""}
                onChange={(e) => setAnswers((cur) => cur.map((a, j) => (j === i ? e.target.value : a)))}
              />
            </label>
          ))}
          {error && (
            <p className="intake__error" role="alert">
              {error}
            </p>
          )}
          <div className="intake__row intake__sticky">
            <Button variant="primary" type="submit" disabled={phase === "sending" || answered === 0}>
              {phase === "sending" ? "Enviando…" : "Enviar respuestas"}
            </Button>
            <Button onClick={() => setPhase("idea")} disabled={phase === "sending"}>
              Volver
            </Button>
          </div>
        </form>
      )}
    </div>
  );
}
