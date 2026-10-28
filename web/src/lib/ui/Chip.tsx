import type { ReactNode } from "react";

type Tone = "neutral" | "rosa" | "ok" | "error";

export function Chip({ tone = "neutral", children }: { tone?: Tone; children: ReactNode }) {
  return <span className={tone === "neutral" ? "sh-chip" : `sh-chip sh-chip--${tone}`}>{children}</span>;
}

// Mandatory on anything recorded or simulated (`demo_data: true`): fixtures, fictitious prospects, mirrored boards.
export function DemoBadge({ show = true }: { show?: boolean }) {
  return show ? <span className="sh-chip sh-chip--demo">Datos de demostración</span> : null;
}
