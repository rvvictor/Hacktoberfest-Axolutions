import { useState } from "react";

import { Button, DemoBadge, MetroLine, Panel, Stat, Title } from "../../lib/ui";
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
  const { state, replay } = useBoardEvents(runId);
  const [view, setView] = useState<"mirror" | "miro">("mirror");
  const boxes = state.miro.filter((i) => i.kind !== "connector").length;
  const showMiro = view === "miro" && state.boardId !== null;

  return (
    <div className="lb">
      <div className="lb-top">
        <div>
          <Title>Control de gastos corporativos</Title>
          <p>Spec aprobado. Miro y Linear se llenan desde el mismo spec.</p>
        </div>
        <div className="lb-stats">
          <Stat value={String(boxes)} label="elementos en Miro" />
          <Stat value={String(state.issues.length)} label="issues en Linear" />
          <DemoBadge show={state.demo} />
        </div>
      </div>

      <MetroLine current={state.stage} notes={{ 4: "aprobado" }} />

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
            <div className="lb-scroll">
              <MirrorCanvas items={state.miro} />
            </div>
          )}
        </Panel>

        <Panel title="Tickets en Linear" meta={`${state.issues.length} creados`}>
          <IssueFeed issues={state.issues} />
          <div className="lb-actions">
            {!runId && <Button onClick={replay}>Repetir</Button>}
            {state.awaitingApproval && (
              <Button variant="primary" onClick={() => (window.location.hash = "/run")}>
                Revisar y aprobar diseño
              </Button>
            )}
          </div>
        </Panel>
      </div>
    </div>
  );
}
