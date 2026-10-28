/** The run being followed: `?run=ID` (intake), `?run_id=ID` (pitch) or `#/view?run=ID`. */
export function currentRunId(): string | null {
  const search = new URLSearchParams(window.location.search);
  const hash = new URLSearchParams(window.location.hash.split("?")[1] ?? "");
  return search.get("run") ?? search.get("run_id") ?? hash.get("run");
}

/** A hash link to `view` that keeps the run in the query, so no view loses it. */
export function viewHref(view: string): string {
  const run = currentRunId();
  return run ? `${window.location.pathname}?run=${encodeURIComponent(run)}${view}` : view;
}
