import { Item } from "../../lib/ui";
import type { BacklogItem } from "./contract";

function criteria(acceptance: string[]): string {
  if (acceptance.length === 0) return "sin criterios";
  const more = acceptance.length > 1 ? ` (+${acceptance.length - 1})` : "";
  return `${acceptance[0]}${more}`;
}

// Newest first, so the issue that just arrived is always above the fold.
export function IssueFeed({ issues }: { issues: BacklogItem[] }) {
  const ordered = [...issues].reverse();
  if (ordered.length === 0) {
    return <p className="lb-empty">Los tickets se escriben en cuanto termina la arquitectura.</p>;
  }
  return (
    <ol className="lb-feed" aria-live="polite">
      {ordered.map((issue, i) => (
        <li key={issue.external_id}>
          <Item
            code={issue.linear_id ?? issue.external_id}
            fresh={i === 0}
            meta={`Épica ${issue.epic}: ${criteria(issue.acceptance)}`}
          >
            {issue.url ? (
              <a href={issue.url} target="_blank" rel="noreferrer">
                {issue.title}
              </a>
            ) : (
              issue.title
            )}
          </Item>
        </li>
      ))}
    </ol>
  );
}
