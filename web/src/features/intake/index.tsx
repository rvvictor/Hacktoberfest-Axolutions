import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";

import { Button, Message, Moments, Title } from "../../lib/ui";
import { ApiError, api } from "../../lib/api";
import type { LimitRefusal } from "../../lib/types";
import { refreshAccount, resetText, useAccount } from "../account/store";
import { STACKS } from "./contract";
import type { Mode, Run } from "./contract";
import "./intake.css";

export const path = "/intake";
export const label = "Nueva idea";
export const order = 1;

const MODES: { id: Mode; name: string; hint: string }[] = [
  { id: "dev", name: "Soy desarrollador", hint: "Te pregunto de arquitectura y stack" },
  { id: "client", name: "Tengo un negocio", hint: "Te pregunto en palabras simples, sin tecnicismos" },
];

// The idea is the first turn of the conversation; the questions and everything after live in #/project.
function goToProject(runId?: string) {
  const query = runId ? `?run=${encodeURIComponent(runId)}` : "";
  window.location.href = `${window.location.pathname}${query}#/project`;
}

// Signing in leaves the page; the draft survives the round trip so the idea is not lost.
const DRAFT_KEY = "sh_idea_draft";
function readDraft(): string {
  try {
    return window.sessionStorage.getItem(DRAFT_KEY) ?? "";
  } catch {
    return "";
  }
}
function writeDraft(text: string) {
  try {
    if (text) window.sessionStorage.setItem(DRAFT_KEY, text);
    else window.sessionStorage.removeItem(DRAFT_KEY);
  } catch {
    /* storage blocked: the draft just does not survive */
  }
}

export default function Intake() {
  const account = useAccount();
  const [limit, setLimit] = useState<LimitRefusal | null>(null);
  const [mode, setMode] = useState<Mode>("dev");
  const [idea, setIdeaText] = useState(readDraft);
  const setIdea: typeof setIdeaText = (value) =>
    setIdeaText((cur) => {
      const next = typeof value === "function" ? value(cur) : value;
      writeDraft(next);
      return next;
    });
  const [stack, setStack] = useState<string[]>([]);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const recorder = useRef<MediaRecorder | null>(null);
  const stopMic = useRef<(() => void) | null>(null);

  useEffect(() => () => stopMic.current?.(), []);

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
      stopMic.current = () => stream.getTracks().forEach((t) => t.stop());
      const chunks: Blob[] = [];
      const rec = new MediaRecorder(stream);
      rec.ondataavailable = (e) => chunks.push(e.data);
      rec.onstop = async () => {
        stopMic.current?.();
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
          setError("No pude transcribir el audio. Escribe tu idea o intenta de nuevo.");
        } finally {
          setTranscribing(false);
        }
      };
      recorder.current = rec;
      rec.start();
      setRecording(true);
    } catch {
      setError("No tengo acceso al micrófono. Revisa el permiso del navegador o escribe tu idea.");
    }
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!idea.trim() || creating) return;
    setError(null);
    setCreating(true);
    try {
      const run = await api<Run>("/projects", {
        method: "POST",
        body: JSON.stringify({ mode, idea: idea.trim(), stack_prefs: mode === "dev" ? stack : [] }),
      });
      writeDraft("");
      goToProject(run.run_id);
    } catch (err) {
      setCreating(false);
      if (err instanceof ApiError && err.status === 401) return; // the sign-in prompt in the top bar takes over
      if (err instanceof ApiError && (err.status === 429 || err.status === 503) && err.detail) {
        setLimit({ ...(err.body as unknown as LimitRefusal), detail: err.detail });
        void refreshAccount();
        return;
      }
      setError("No pude crear tu proyecto. Intenta de nuevo o mira el ejemplo.");
    }
  };

  // Why "Empezar" is disabled (DESIGN rule 5): a refused project, or no projects left for today.
  const left = account.user?.runs_left_today;
  const localReset = resetText(limit?.resets_at ?? account.user?.resets_at);
  const blocked = limit
    ? [limit.detail, localReset && `Se renueva el ${localReset} (tu hora).`].filter(Boolean)
    : left !== undefined && left <= 0
      ? [
          "Hoy ya usaste tus proyectos.",
          `Podrás crear otro el ${localReset ?? "día de mañana"} (tu hora).`,
        ]
      : null;
  const hint = blocked
    ? null
    : account.needsSignIn
      ? "Entra con Google para empezar tu proyecto."
      : recording
        ? "Te escucho… habla con calma."
        : !idea.trim() && !creating
          ? "Escribe o dicta tu idea para empezar."
          : creating
            ? "Ahora te haré unas preguntas cortas."
            : "";

  return (
    <div className="intake">
      <div className="intake__head">
        <Title>Cuéntame tu idea</Title>
        <Moments stage={1} />
      </div>

      <div className="intake__chat">
        <Message>
          ¡Hola! Cuéntame qué quieres construir, como se lo contarías a un amigo.
        </Message>

        <form className="intake__main" onSubmit={submit}>
          <div className="intake__modes" role="radiogroup" aria-label="¿Cómo quieres que te pregunte?">
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
              placeholder={
                mode === "dev"
                  ? "Ej. Un SaaS para controlar los gastos de la empresa, con alertas"
                  : "Ej. Quiero que mis clientes reserven cita en mi barbería desde el celular"
              }
              disabled={creating}
            />
          </label>

          {mode === "dev" && (
            <fieldset className="intake__stack">
              <legend className="intake__label">¿Ya tienes un stack en mente? (opcional)</legend>
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
            <Button variant="primary" type="submit" disabled={!idea.trim() || creating || !!blocked}>
              {creating ? "Creando tu proyecto…" : "Empezar"}
            </Button>
            <Button onClick={toggleMic} disabled={transcribing || creating} aria-pressed={recording}>
              {recording ? "Detener y transcribir" : transcribing ? "Transcribiendo…" : "Dictar por voz"}
            </Button>
            <span className="intake__status" role="status">
              {blocked ? blocked.join(" ") : hint}
            </span>
          </div>
        </form>

        <p className="intake__example">
          ¿Prefieres ver cómo funciona primero? <a href="#/project">Mira un ejemplo completo</a>.
        </p>
      </div>
    </div>
  );
}
