import { useEffect, useState } from "react";
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

function currentPath(): string {
  return window.location.hash.replace(/^#/, "") || features[0]?.path || "/";
}

export default function App() {
  const [path, setPath] = useState(currentPath);

  useEffect(() => {
    const onChange = () => setPath(currentPath());
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);

  const active = features.find((feature) => feature.path === path) ?? features[0];
  const Active = active?.default;

  return (
    <div className="min-h-[100dvh] font-sans">
      <nav className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-4 py-2 [scrollbar-width:none]" aria-label="Vistas">
        {features.map(({ path: href, label }) => (
          <a
            key={href}
            href={`#${href}`}
            aria-current={href === active?.path ? "page" : undefined}
            className="flex min-h-11 shrink-0 items-center whitespace-nowrap rounded-full px-3 text-sm aria-[current=page]:font-semibold aria-[current=page]:underline underline-offset-4"
          >
            {label}
          </a>
        ))}
      </nav>
      <main className="mx-auto max-w-7xl px-4 pb-6 pt-2">{Active ? <Active /> : <p>SpeedHack</p>}</main>
    </div>
  );
}
