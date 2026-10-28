/** Current run id: `?run=ID` before the hash (intake redirect) or inside it (`#/path?run=ID`). */
export function currentRunId(): string | null {
  const fromHash = new URLSearchParams(window.location.hash.split("?")[1] ?? "").get("run");
  return fromHash ?? new URLSearchParams(window.location.search).get("run");
}

/** Link to a view that keeps the run in `?run=` before the hash, the form intake uses and every view reads. */
export function withRun(href: string, runId: string | null): string {
  return runId ? `${window.location.pathname}?run=${encodeURIComponent(runId)}${href}` : href;
}
