import { useSyncExternalStore } from "react";

import { UNAUTHORIZED_EVENT } from "../../lib/api";
import type { Account } from "../../lib/types";

// Who is signed in, shared by the top bar and the intake. Not a feature screen (no index.tsx), so App.tsx skips it.
export type AccountState = {
  /** "loading" until the first /api/auth/me answers; "anon" covers 401 and an unreachable backend. */
  status: "loading" | "anon" | "user";
  user: Account | null;
  /** A call answered 401: show the sign-in prompt instead of an error. */
  needsSignIn: boolean;
  /** Why sign-in did not start (Google not configured), in the interface's voice. */
  signInError: string | null;
};

let state: AccountState = { status: "loading", user: null, needsSignIn: false, signInError: null };
const listeners = new Set<() => void>();

function set(next: Partial<AccountState>) {
  state = { ...state, ...next };
  listeners.forEach((l) => l());
}

export function useAccount(): AccountState {
  return useSyncExternalStore(
    (l) => {
      listeners.add(l);
      return () => listeners.delete(l);
    },
    () => state,
  );
}

// Plain fetch on purpose: a 401 here only means "nobody is signed in", not "a call failed".
export async function refreshAccount(): Promise<void> {
  try {
    const response = await fetch("/api/auth/me", { headers: { Accept: "application/json" } });
    if (response.ok) {
      set({ status: "user", user: (await response.json()) as Account, needsSignIn: false, signInError: null });
      return;
    }
  } catch {
    /* backend unreachable: behave as signed out, the screens report their own errors */
  }
  set({ status: "anon", user: null });
}

/** Ask for the Google redirect first, so a 503 ("not configured") shows its Spanish detail instead of raw JSON. */
export async function signIn(): Promise<void> {
  set({ signInError: null });
  try {
    const response = await fetch("/api/auth/google/login", { redirect: "manual" });
    if (response.type === "opaqueredirect" || response.ok) {
      window.location.assign("/api/auth/google/login");
      return;
    }
    const body = (await response.json().catch(() => null)) as { detail?: unknown } | null;
    set({
      signInError:
        typeof body?.detail === "string" ? body.detail : "No pude iniciar sesión con Google. Intenta de nuevo.",
    });
  } catch {
    set({ signInError: "No pude conectar con Google. Revisa tu conexión e intenta de nuevo." });
  }
}

export async function signOut(): Promise<void> {
  try {
    await fetch("/api/auth/logout", { method: "POST" });
  } catch {
    /* the cookie expires by itself; the interface still shows signed out */
  }
  set({ status: "anon", user: null, needsSignIn: false });
}

window.addEventListener(UNAUTHORIZED_EVENT, () => set({ needsSignIn: true }));
void refreshAccount();

/** "Te queda 1 proyecto hoy" / "Te quedan 3 proyectos hoy" / "Hoy ya no te quedan proyectos". */
export function runsLeftText(n: number): string {
  if (n <= 0) return "Hoy ya no te quedan proyectos";
  return n === 1 ? "Te queda 1 proyecto hoy" : `Te quedan ${n} proyectos hoy`;
}

/** "1 de noviembre, 18:00" in the person's own time zone. */
export function resetText(resetsAt: string | undefined): string | null {
  const date = resetsAt ? new Date(resetsAt) : null;
  if (!date || Number.isNaN(date.getTime())) return null;
  return new Intl.DateTimeFormat("es", { day: "numeric", month: "long", hour: "2-digit", minute: "2-digit" }).format(date);
}
