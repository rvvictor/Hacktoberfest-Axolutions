/** A failed call. `detail` is the Spanish sentence the backend sent (HTTPException detail), when it sent one. */
export class ApiError extends Error {
  status: number;
  detail: string | null;
  body: Record<string, unknown> | null;
  constructor(status: number, statusText: string, body: Record<string, unknown> | null) {
    super(`${status} ${statusText}`);
    this.status = status;
    this.body = body;
    this.detail = typeof body?.detail === "string" ? body.detail : null;
  }
}

/** Fired on any 401 so the top bar can ask the person to sign in (web/src/features/account/). */
export const UNAUTHORIZED_EVENT = "sh:unauthorized";

// The only door to the backend: every route lives under /api.
export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    const body = await response.json().then(
      (json: unknown) => (json && typeof json === "object" ? (json as Record<string, unknown>) : null),
      () => null,
    );
    if (response.status === 401) window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
    throw new ApiError(response.status, response.statusText, body);
  }
  return (await response.json()) as T;
}
