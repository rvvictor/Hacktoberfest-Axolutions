import type { ReactNode } from "react";

export function SectionHeader({ title, meta }: { title: string; meta?: ReactNode }) {
  return (
    <header className="sh-header">
      <h2>{title}</h2>
      {meta && <small>{meta}</small>}
    </header>
  );
}

// The page title of a view (the project name on the run screen).
export function Title({ children }: { children: ReactNode }) {
  return <h1 className="sh-title">{children}</h1>;
}
