import { useEffect, useRef, useState } from "react";
import { Microphone, Pause, Play, Printer, SpeakerHigh, Stop } from "@phosphor-icons/react";
import { api } from "../../lib/api";
import { Button, DemoBadge, MetroLine, Panel } from "../../lib/ui";
import { currentRunId } from "../run/runId";
import "./pitch.css";

export const path = "/pitch";
export const label = "Sala de pitch";
export const order = 90;
type Slide = { title: string; bullets: string[]; sources: string[] };
type Deck = { slides: Slide[]; demo_data: boolean };
type Answer = { answer: string; sources: string[]; demo_data: boolean; question: string };

function Sources({ sources }: { sources: string[] }) {
  return <ul className="pitch-sources" aria-label="Fuentes">{sources.map(source => <li key={source}>
    {/^https?:\/\//.test(source) ? <a href={source} target="_blank" rel="noreferrer">{source}</a> : source}
  </li>)}</ul>;
}

type Narration = "idle" | "loading" | "playing" | "paused";
const NARRATION_FAILED = "La voz no está disponible. Lee el texto de la diapositiva.";

export default function PitchRoom() {
  const [run, setRun] = useState(() => currentRunId() || "demo-pitch");
  const [draft, setDraft] = useState(run);
  const [revision, setRevision] = useState(0);
  const [deck, setDeck] = useState<Deck | null>(null);
  const [slide, setSlide] = useState(0);
  const [question, setQuestion] = useState("");
  const [answers, setAnswers] = useState<Answer[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [recording, setRecording] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState("");
  const generation = useRef(0);
  const recorder = useRef<MediaRecorder | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const audio = useRef<HTMLAudioElement | null>(null);
  const audioUrl = useRef("");
  const locked = useRef(false);
  const [narration, setNarration] = useState<Narration>("idle");
  const [narrationDemo, setNarrationDemo] = useState(false);
  const [narrationError, setNarrationError] = useState("");
  const narrating = useRef(0);
  function stopNarration() { ++narrating.current; setNarration("idle"); stopAudio(); }
  function stopAudio() {
    audio.current?.pause(); audio.current = null;
    if (audioUrl.current) URL.revokeObjectURL(audioUrl.current);
    audioUrl.current = "";
  }
  function stopTracks() { stream.current?.getTracks().forEach(track => track.stop()); stream.current = null; }

  useEffect(() => {
    const current = ++generation.current;
    const controller = new AbortController();
    setDeck(null); setAnswers([]); setSlide(0); setQuestion(""); setError(""); setLoading(true);
    setBusy(false); locked.current = false; setRecording(false); setVoiceStatus("");
    setNarration("idle"); setNarrationError(""); setNarrationDemo(false); ++narrating.current;
    api<Deck>(`/pitch/${encodeURIComponent(run)}`, { signal: controller.signal })
      .then(result => { if (current === generation.current) setDeck(result); })
      .catch(() => { if (!controller.signal.aborted) setError("No pudimos cargar el deck. Reintenta o abre la demostración."); })
      .finally(() => { if (current === generation.current) setLoading(false); });
    return () => {
      ++generation.current; controller.abort();
      if (recorder.current?.state === "recording") recorder.current.stop();
      stopTracks(); stopAudio(); ++narrating.current;
    };
  }, [run, revision]);

  async function fetchNarration(slides: Slide[], index: number, current: number) {
    const response = await fetch(`/api/pitch/${encodeURIComponent(run)}/narration`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ index, slide: slides[index] }) });
    if (!response.ok) throw new Error("voice");
    const blob = await response.blob();
    if (current !== narrating.current) throw new Error("stopped");
    return { blob, demo: response.headers.get("X-Demo-Data") === "true" };
  }

  // Each slide's script is spoken in order; the next slide's audio is requested while the current one plays.
  async function present(from = 0) {
    if (!deck?.slides.length) return;
    const slides = deck.slides, current = ++narrating.current, gen = generation.current;
    stopAudio(); setNarrationError(""); setNarration("loading"); setError("");
    let upcoming: ReturnType<typeof fetchNarration> | null = null;
    try {
      for (let i = from; i < slides.length; i++) {
        setSlide(i); setNarration("loading");
        const next = upcoming ?? fetchNarration(slides, i, current);
        upcoming = null;
        const { blob, demo } = await next;
        if (current !== narrating.current || gen !== generation.current) return;
        setNarrationDemo(demo);
        if (i + 1 < slides.length) { upcoming = fetchNarration(slides, i + 1, current); upcoming.catch(() => undefined); }
        audioUrl.current = URL.createObjectURL(blob);
        const player = new Audio(audioUrl.current); audio.current = player;
        const ended = new Promise<void>((resolve, reject) => { player.onended = () => resolve(); player.onerror = () => reject(new Error("play")); });
        await player.play();
        if (current !== narrating.current) return;
        setNarration("playing");
        await ended;
        if (current !== narrating.current) return;
        stopAudio();
      }
      setNarration("idle");
    } catch {
      if (current !== narrating.current) return;
      stopAudio(); setNarration("idle"); setNarrationError(NARRATION_FAILED);
    }
  }

  function pauseNarration() { audio.current?.pause(); setNarration("paused"); }
  function resumeNarration() { audio.current?.play().then(() => setNarration("playing")).catch(() => { stopNarration(); setNarrationError(NARRATION_FAILED); }); }
  function goTo(index: number) { stopNarration(); setSlide(index); }

  async function ask(text: string, spoken = false, current = generation.current) {
    if (!text.trim() || locked.current || current !== generation.current) return;
    locked.current = true; setBusy(true); setError(""); stopNarration();
    try {
      const result = await api<Answer>(`/pitch/${encodeURIComponent(run)}/ask`, { method: "POST", body: JSON.stringify({ question: text }) });
      if (current !== generation.current) return;
      setAnswers(previous => [result, ...previous]); setQuestion("");
      if (spoken) {
        setVoiceStatus("Preparando la voz…");
        const response = await fetch("/api/voice/tts", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: result.answer }) });
        if (!response.ok) throw new Error("voice");
        const blob = await response.blob();
        if (current !== generation.current) return;
        audioUrl.current = URL.createObjectURL(blob);
        const player = new Audio(audioUrl.current); audio.current = player;
        player.onended = () => { if (current === generation.current) setVoiceStatus(""); stopAudio(); };
        player.onerror = () => { if (current === generation.current) setVoiceStatus("No pudimos reproducir la voz. Lee la respuesta."); stopAudio(); };
        await player.play();
        if (current === generation.current) setVoiceStatus("Escuchando la respuesta de IA…");
      }
    } catch {
      if (current === generation.current) setError(spoken ? "La voz no está disponible. Puedes preguntar y leer la respuesta aquí." : "No pudimos consultar la memoria. Intenta de nuevo.");
    } finally {
      if (current === generation.current) { locked.current = false; setBusy(false); }
    }
  }

  async function toggleVoice() {
    if (recording && recorder.current) { recorder.current.stop(); setRecording(false); return; }
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setError("Este navegador no permite grabar. Escribe tu pregunta."); return;
    }
    const current = generation.current;
    setBusy(true); setError(""); stopNarration();
    try {
      const media = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (current !== generation.current) { media.getTracks().forEach(track => track.stop()); return; }
      stream.current = media;
      const capture = new MediaRecorder(media); recorder.current = capture;
      const chunks: Blob[] = [];
      capture.ondataavailable = event => { if (event.data.size) chunks.push(event.data); };
      capture.onerror = () => { media.getTracks().forEach(track => track.stop()); if (current === generation.current) { setBusy(false); setRecording(false); setError("No pudimos grabar. Escribe tu pregunta."); } };
      capture.onstop = async () => {
        media.getTracks().forEach(track => track.stop());
        if (current !== generation.current) return;
        setRecording(false); setVoiceStatus("Transcribiendo…");
        try {
          const form = new FormData(); form.append("audio", new Blob(chunks, { type: capture.mimeType }), "question.webm");
          const response = await fetch("/api/voice/stt", { method: "POST", body: form });
          if (!response.ok) throw new Error("stt");
          const result = await response.json() as { text: string };
          if (current !== generation.current) return;
          if (!result.text?.trim()) throw new Error("empty");
          setQuestion(result.text); setVoiceStatus("");
          await ask(result.text, true, current);
        } catch { if (current === generation.current) setError("No pudimos transcribir. Escribe tu pregunta."); }
        finally { if (current === generation.current) { setBusy(false); setVoiceStatus(""); } }
      };
      capture.start(); setRecording(true); setVoiceStatus("Grabando. Pulsa otra vez para enviar.");
    } catch { if (current === generation.current) { stopTracks(); setBusy(false); setError("Permite el micrófono o escribe tu pregunta."); } }
  }

  return <div className="pitch-room">
    <header className="pitch-header"><div><h1>Sala de pitch</h1><p>Presenta tu proyecto. Defiende cada respuesta con su fuente.</p></div><DemoBadge show={deck?.demo_data || answers.some(a => a.demo_data)} /></header>
    <MetroLine current={9} />
    <details className="pitch-settings"><summary>Ejecución: {run}</summary><form className="pitch-run" onSubmit={event => { event.preventDefault(); if (draft.trim()) setRun(draft.trim()); }}>
      <label htmlFor="pitch-run">Ejecución</label><input id="pitch-run" value={draft} onChange={event => setDraft(event.target.value)} required />
      <Button type="submit">Abrir</Button>
      <Button onClick={() => { setDraft("demo-pitch"); setRun("demo-pitch"); }}>Ver demostración</Button>
    </form></details>
    {error && <div role="alert" className="pitch-error">{error} <Button onClick={() => setRevision(value => value + 1)}>Reintentar carga</Button></div>}
    <div className="pitch-layout">
      <Panel title="Tu presentación" meta={deck?.slides.length ? `${slide + 1} de ${deck.slides.length}` : undefined} className="pitch-deck">
        {loading ? <p role="status">Preparando las diapositivas…</p> : !deck?.slides.length ? <p>Aún no hay un deck para esta ejecución. Completa el proyecto o abre la demostración.</p> : <>
          <div className="pitch-controls pitch-narration" role="group" aria-label="Presentar con voz">
            {narration === "idle" ? <Button variant="primary" onClick={() => void present(slide)}><SpeakerHigh size={18} /> Presentar con voz</Button> : <>
              {narration === "paused" ? <Button onClick={resumeNarration}><Play size={18} /> Reanudar</Button> : <Button disabled={narration === "loading"} onClick={pauseNarration}><Pause size={18} /> Pausar</Button>}
              <Button onClick={stopNarration}><Stop size={18} /> Detener</Button>
            </>}
            {narration !== "idle" && <span className="pitch-ai-badge" role="status">Narrado por IA{narrationDemo ? " · voz grabada de demostración" : ""}{narration === "loading" ? " · preparando la voz…" : narration === "paused" ? " · en pausa" : ""}</span>}
          </div>
          {narrationError && <p role="alert" className="pitch-error">{narrationError}</p>}
          <div className="pitch-slides">{deck.slides.map((item, i) => <article className="pitch-slide" key={i} data-active={i === slide}>
            <span className="pitch-slide-label">SpeedHack · Pitch</span><h2>{item.title}</h2><ul>{item.bullets.map((text, n) => <li key={n}>{text}</li>)}</ul><Sources sources={item.sources} />
          </article>)}</div>
          <div className="pitch-controls"><Button disabled={slide === 0} onClick={() => goTo(slide - 1)}>Anterior</Button><Button disabled={slide === deck.slides.length - 1} onClick={() => goTo(slide + 1)}>Siguiente</Button><Button onClick={() => window.print()}><Printer size={18} /> Imprimir / PDF</Button></div>
        </>}
      </Panel>
      <Panel title="Pregúntale al proyecto" className="pitch-qa">
        <p>Soy una IA. Solo respondo con fuentes de esta ejecución.</p>
        <form onSubmit={event => { event.preventDefault(); void ask(question); }}>
          <label htmlFor="pitch-question">Tu pregunta</label>
          <textarea id="pitch-question" maxLength={2000} value={question} onChange={event => setQuestion(event.target.value)} placeholder="¿Cómo funcionan las alertas?" required />
          <div className="pitch-controls"><Button variant="primary" type="submit" disabled={busy || !question.trim()}>Preguntar</Button><Button aria-pressed={recording} disabled={busy && !recording} onClick={() => void toggleVoice()}><Microphone size={18} />{recording ? "Terminar y enviar" : "Hablar"}</Button></div>
        </form>
        <p role="status">{voiceStatus || (busy ? "Consultando la memoria…" : "Puedes escribir o usar el micrófono.")}</p>
        <div className="pitch-answers" aria-live="polite">{!answers.length && <p className="pitch-empty">Las respuestas y sus fuentes aparecerán aquí.</p>}{answers.map((answer, i) => <article key={i}><h3>{answer.question}</h3><p>{answer.answer}</p><DemoBadge show={answer.demo_data && !deck?.demo_data} /><Sources sources={answer.sources} />{!answer.sources.length && <p className="pitch-empty">Sin pasajes de respaldo.</p>}</article>)}</div>
      </Panel>
    </div>
  </div>;
}
