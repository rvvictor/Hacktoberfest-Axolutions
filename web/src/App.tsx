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
      <nav className="mx-auto flex max-w-7xl gap-4 px-4 py-4">
        {features.map(({ path: href, label }) => (
          <a
            key={href}
            href={`#${href}`}
            aria-current={href === active?.path ? "page" : undefined}
            className="text-sm aria-[current=page]:font-semibold"
          >
            {label}
          </a>
        ))}
      </nav>
      <main className="mx-auto max-w-7xl px-4 py-8">{Active ? <Active /> : <p>SpeedHack</p>}</main>
    </div>
  );
}
