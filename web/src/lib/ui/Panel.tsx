import type { HTMLAttributes, ReactNode } from "react";

import { SectionHeader } from "./SectionHeader";

type Props = HTMLAttributes<HTMLElement> & { title?: string; meta?: ReactNode };

export function Panel({ title, meta, children, className = "", ...rest }: Props) {
  return (
    <section className={`sh-panel ${className}`} {...rest}>
      {title && <SectionHeader title={title} meta={meta} />}
      {children}
    </section>
  );
}

type ItemProps = HTMLAttributes<HTMLDivElement> & {
  tone?: "rosa" | "ink" | "naranja";
  pending?: boolean;
  fresh?: boolean;
  code?: string; // external ID shown condensed in rosa, e.g. "GAS-5"
  meta?: ReactNode; // second line, e.g. "3 criterios de aceptación"
};

// A row inside a Panel: a Miro element, a Linear issue (code + meta), a research source.
export function Item({ tone = "rosa", pending, fresh, code, meta, className = "", children, ...rest }: ItemProps) {
  const rich = code !== undefined || meta !== undefined;
  const mods = [
    tone !== "rosa" && `sh-item--${tone}`,
    pending && "sh-item--pending",
    fresh && "sh-item--new",
    rich && "sh-item--rich",
  ];
  return (
    <div className={["sh-item", ...mods, className].filter(Boolean).join(" ")} {...rest}>
      {rich ? (
        <>
          {code && <span className="sh-item__id">{code}</span>}
          <span className="sh-item__title">{children}</span>
          {meta && <span className="sh-item__meta">{meta}</span>}
        </>
      ) : (
        children
      )}
    </div>
  );
}
