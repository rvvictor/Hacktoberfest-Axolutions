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
};

// A row inside a Panel: a Miro element, a Linear issue, a research source.
export function Item({ tone = "rosa", pending, fresh, className = "", ...rest }: ItemProps) {
  const mods = [tone !== "rosa" && `sh-item--${tone}`, pending && "sh-item--pending", fresh && "sh-item--new"];
  return <div className={["sh-item", ...mods, className].filter(Boolean).join(" ")} {...rest} />;
}
