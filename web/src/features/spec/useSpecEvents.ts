import { useEffect, useState } from "react";

import type { EventType, ResearchItem, Spec, StageEvent } from "../../lib/types";
import { DEMO_RESEARCH, DEMO_SPECS } from "./demo";

export interface SpecState {
  specs: Spec[];
  research: ResearchItem[];
  awaiting: boolean; // approval 1 requested
  decided: "approved" | "rejected" | null;
  demo: boolean;
}

const EVENT_TYPES: EventType[] = [
  "stage_started", "stage_done", "question", "research_item", "spec_ready", "approval_required", "approval_given",
  "approval_rejected", "miro_item", "linear_issue", "prototype_ready", "quality_check", "pitch_ready", "error",
];

const initial: SpecState = { specs: [], research: [], awaiting: false, decided: null, demo: false };

function reduce(s: SpecState, e: StageEvent): SpecState {
  const p = e.payload;
  const demo = s.demo || e.demo_data;
  switch (e.type) {
    case "research_item":
      return { ...s, demo, research: [...s.research, p as unknown as ResearchItem] };
    case "spec_ready": {
      const spec = p as unknown as Spec;
      return { ...s, demo, specs: [...s.specs.filter((x) => x.version !== spec.version), spec].sort((a, b) => a.version - b.version), awaiting: false, decided: null };
    }
    case "approval_required":
      return p.approval === 1 ? { ...s, demo, awaiting: true, decided: null } : { ...s, demo };
    case "approval_given":
      return p.approval === 1 ? { ...s, demo, awaiting: false, decided: "approved" } : { ...s, demo };
    case "approval_rejected":
      return p.approval === 1 ? { ...s, demo, awaiting: false, decided: "rejected" } : { ...s, demo };
    default:
      return { ...s, demo };
  }
}

// The runs router sends NAMED SSE events (`event: <type>`), which lib/sse.ts (onmessage) never sees.
function listen(url: string, onEvent: (e: StageEvent) => void): () => void {
  const source = new EventSource(url);
  const handle = (m: MessageEvent<string>) => onEvent(JSON.parse(m.data) as StageEvent);
  EVENT_TYPES.forEach((t) => source.addEventListener(t, handle));
  source.onmessage = handle;
  return () => source.close();
}

/** Live events when `?run=` is set; otherwise a local demo state with an open approval 1. */
export function useSpecEvents(runId: string | null) {
  const [state, setState] = useState<SpecState>(initial);

  useEffect(() => {
    if (!runId) {
      setState({ specs: DEMO_SPECS, research: DEMO_RESEARCH, awaiting: true, decided: null, demo: true });
      return;
    }
    setState(initial);
    return listen(`/api/runs/${encodeURIComponent(runId)}/events`, (e) => setState((s) => reduce(s, e)));
  }, [runId]);

  return { state, setState };
}
