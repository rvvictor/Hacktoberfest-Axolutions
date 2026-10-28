import { useState } from "react";

import { api } from "../../lib/api";
import { Button, DemoBadge, MetroLine, Panel, Title } from "../../lib/ui";
import { IssueFeed } from "./IssueFeed";
import { MirrorCanvas } from "./MirrorCanvas";
import { useBoardEvents } from "./useBoardEvents";
import "./live-board.css";

export const path = "/live-board";
export const label = "Tablero en vivo";
export const order = 30;

function runFromUrl(): string | null {
  return new URLSearchParams(window.location.search).get("run");
}

export default function LiveBoard() {
  const [runId] = useState(runFromUrl);
  const { state, replay, approve } = useBoardEvents(runId);
  const [view, setView] = useState<"mirror" | "miro">("mirror");
  const [error, setError] = useState<string | null>(null);
  const boxes = state.miro.filter((i) => i.kind !== "connector").length;
  const showMiro = view === "miro" && state.boardId !== null;

  async function approveDesign() {
    setError(null);
    if (!runId) return approve();
    try {
      // Same body as the run view (HACK-015); the SSE stream then sends approval_given.
      await api(`/runs/${encodeURIComponent(runId)}/approvals/2`, {
        method: "POST",
        body: JSON.stringify({ approved: true, comment: "" }),
      });
    } catch (e) {
      setError(`No se pudo aprobar: ${(e as Error).message}. Intenta de nuevo o apruébalo desde la vista de la corrida.`);
    }
  }

  return (
    <div className="lb">
      <div className="lb-top">
        <div>
          <Title>Control de gastos corporativos</Title>
          <p>Spec aprobado. Miro y Linear se llenan desde el mismo spec.</p>
        </div>
        <DemoBadge show={state.demo} />
      </div>

      <MetroLine current={state.stage} notes={{ 4: "aprobado", ...(state.approved ? { 6: "aprobado" } : {}) }} />

      <div className="lb-grid">
        <Panel
          title="Arquitectura en Miro"
          meta={
            state.boardId ? (
              <span className="lb-toggle">
                <Button onClick={() => setView("mirror")} aria-pressed={view === "mirror"}>Espejo</Button>
                <Button onClick={() => setView("miro")} aria-pressed={view === "miro"}>Miro en vivo</Button>
              </span>
            ) : (
              `${boxes} elementos`
            )
          }
        >
          {showMiro ? (
            <iframe
              className="lb-embed"
              title="Tablero de Miro en vivo"
              src={`https://miro.com/app/live-embed/${encodeURIComponent(state.boardId ?? "")}/?embedMode=view_only_without_ui`}
              allow="fullscreen"
            />
          ) : (
            <MirrorCanvas items={state.miro} />
          )}
        </Panel>

        <Panel className="lb-linear" title="Tickets en Linear" meta={`${state.issues.length} creados`}>
          <IssueFeed issues={state.issues} />
          {error && <p role="alert">{error}</p>}
          <div className="lb-actions">
            {!runId && <Button onClick={replay}>Repetir</Button>}
            <span className="lb-spacer" />
            {state.awaitingApproval && (
              <>
                <Button onClick={() => (window.location.hash = "/run")}>Pedir cambios</Button>
                <Button variant="primary" onClick={approveDesign}>Aprobar diseño</Button>
              </>
            )}
            {state.approved && <span>Diseño aprobado. Sigue el prototipo.</span>}
          </div>
        </Panel>
      </div>
    </div>
  );
}
