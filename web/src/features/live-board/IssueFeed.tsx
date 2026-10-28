import { Chip, Item } from "../../lib/ui";
import type { BacklogItem } from "./contract";

// Newest first, so the issue that just arrived is always above the fold; the list scrolls inside its panel.
export function IssueFeed({ issues }: { issues: BacklogItem[] }) {
  const ordered = [...issues].reverse();
  if (ordered.length === 0) {
    return <p className="lb-empty">Los tickets se escriben en cuanto termina la arquitectura.</p>;
  }
  return (
    <ol className="lb-feed" aria-live="polite">
      {ordered.map((issue, i) => {
        const extra = issue.acceptance.length - 2;
        return (
          <li key={issue.external_id}>
            <Item
              code={issue.linear_id ?? issue.external_id}
              fresh={i === 0}
              meta={
                <span className="lb-issue-meta">
                  <span className="lb-issue-tags">
                    <Chip>{`Épica ${issue.epic}`}</Chip>
                    {i === 0 && <Chip tone="rosa">Recién creado</Chip>}
                    {issue.url && (
                      <a href={issue.url} target="_blank" rel="noreferrer">
                        Abrir en Linear
                      </a>
                    )}
                  </span>
                  <ul>
                    {issue.acceptance.slice(0, 2).map((c) => (
                      <li key={c}>{c}</li>
                    ))}
                    {extra > 0 && <li>{`y ${extra} criterio${extra > 1 ? "s" : ""} más`}</li>}
                  </ul>
                </span>
              }
            >
              {issue.title}
            </Item>
          </li>
        );
      })}
    </ol>
  );
}
