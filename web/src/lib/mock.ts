import type { StageEvent } from "./types";

/**
 * Replays app/fixtures/demo/run.jsonl with the recorded timing (`ts` seconds).
 * `speed` > 1 plays faster. Returns a cancel function.
 */
export async function replayDemo(
  onEvent: (e: StageEvent) => void,
  opts: { url?: string; speed?: number } = {},
): Promise<() => void> {
  const { url = "/fixtures/demo/run.jsonl", speed = 1 } = opts;
  const text = await (await fetch(url)).text();
  const events = text
    .split("\n")
    .filter((l) => l.trim())
    .map((l) => JSON.parse(l) as StageEvent);
  const timers = events.map((e) => setTimeout(() => onEvent(e), (e.ts * 1000) / speed));
  return () => timers.forEach(clearTimeout);
}
