import { useEffect, useRef, useState } from "react";
import type { ComponentType } from "react";

// Each feature is web/src/features/<name>/index.tsx exporting `default`, `path`, `label` and `order`.
// Adding a feature = creating its folder; App.tsx never becomes a conflict point.
type FeatureModule = {
  default: ComponentType;
  path: string;
  label: string;
  order?: number;
};

const features = Object.values(
  import.meta.glob<FeatureModule>("./features/*/index.tsx", { eager: true }),
).sort((a, b) => (a.order ?? 100) - (b.order ?? 100));

// Navigation (web/DESIGN.md rule 6): at most three visible entries; every other screen lives under "Más".
const PRIMARY = new Set(["/", "/intake", "/project"]);
// Plain-language names for the menu (rule 2: say "Tu plan", not "Spec"); a screen without one keeps its label.
const MENU_NAMES: Record<string, string> = {
  "/client": "Modo cliente",
  "/run": "Detalle de las 9 etapas",
  "/spec": "Tu plan",
  "/live-board": "Tablero en vivo",
  "/delivery": "Prototipo y revisión",
  "/hunter": "Cazador de clientes",
  "/ops": "Costos",
  "/pitch": "Sala de pitch",
};

function currentPath(): string {
  return window.location.hash.replace(/^#/, "") || features[0]?.path || "/";
}

function openRun(): string | null {
  return new URLSearchParams(window.location.search).get("run");
}

const link =
  "flex min-h-11 items-center whitespace-nowrap rounded-[var(--sh-radius-sm)] px-3 text-[length:var(--sh-text-sm)] text-[color:var(--sh-ink)] no-underline hover:bg-[color:var(--sh-surface)] aria-[current=page]:bg-[color:var(--sh-surface)] aria-[current=page]:font-bold focus-visible:outline-3 focus-visible:outline-[color:var(--sh-accent)]";

export default function App() {
  const [path, setPath] = useState(currentPath);
  const more = useRef<HTMLDetailsElement>(null);
  const run = openRun();

  useEffect(() => {
    const onChange = () => {
      setPath(currentPath());
      if (more.current) more.current.open = false; // close the menu after choosing a screen
    };
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);

  const active = features.find((feature) => feature.path === path) ?? features[0];
  const Active = active?.default;
  const secondary = features.filter((f) => !PRIMARY.has(f.path));
  const inMore = secondary.some((f) => f.path === active?.path);

  return (
    <div className="min-h-[100dvh] font-sans">
      <header className="mx-auto flex max-w-7xl flex-wrap items-center gap-2 px-4 py-3">
        <a
          href="#/"
          className="mr-auto flex min-h-11 items-center gap-2 text-[color:var(--sh-ink)] no-underline"
          aria-label="SpeedHack, inicio"
        >
          <span
            aria-hidden="true"
            className="grid size-8 place-items-center rounded-[var(--sh-radius-sm)] bg-[color:var(--sh-ink)] font-[family-name:var(--sh-display)] text-[color:var(--sh-bg)]"
          >
            S
          </span>
          <span className="font-[family-name:var(--sh-display)] text-[length:var(--sh-text-lg)]">SpeedHack</span>
        </a>
        <nav aria-label="Principal" className="flex items-center gap-1">
          {run && (
            <a href="#/project" aria-current={active?.path === "/project" ? "page" : undefined} className={link}>
              Tu proyecto
            </a>
          )}
          <a
            href={`${window.location.pathname}#/intake`}
            aria-current={active?.path === "/intake" ? "page" : undefined}
            className={link}
          >
            Nuevo proyecto
          </a>
          <details ref={more} className="relative">
            <summary
              aria-current={inMore ? "page" : undefined}
              className={`${link} cursor-pointer list-none [&::-webkit-details-marker]:hidden`}
            >
              Más <span aria-hidden="true">▾</span>
            </summary>
            <ul
              aria-label="Más pantallas"
              className="absolute right-0 z-10 mt-2 flex w-60 flex-col gap-0.5 rounded-[var(--sh-radius-lg)] border border-[color:var(--sh-line)] bg-[color:var(--sh-raised)] p-2"
            >
              {secondary.map(({ path: href, label }) => (
                <li key={href}>
                  <a href={`#${href}`} aria-current={href === active?.path ? "page" : undefined} className={link}>
                    {MENU_NAMES[href] ?? label}
                  </a>
                </li>
              ))}
            </ul>
          </details>
        </nav>
      </header>
      <main className="mx-auto max-w-7xl px-4 pb-6 pt-2">{Active ? <Active /> : <p>SpeedHack</p>}</main>
    </div>
  );
}
