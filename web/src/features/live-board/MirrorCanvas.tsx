import { Item } from "../../lib/ui";
import type { MiroItem } from "./contract";

// Miro board units: items sit on a 220 × 160 grid (app/fixtures/demo/run.jsonl). Fixed bounds keep the layout still
// while items arrive; a larger board grows the bounds.
const ITEM_W = 200;
const ITEM_H = 64;
const TONE = { screen: "rosa", data_model: "ink", integration: "naranja" } as const;

export function MirrorCanvas({ items }: { items: MiroItem[] }) {
  const boxes = items.filter((i) => i.kind !== "connector");
  const width = Math.max(860, ...boxes.map((i) => i.x + ITEM_W));
  const height = Math.max(384, ...boxes.map((i) => i.y + ITEM_H));
  const center = (title: string) => {
    const b = boxes.find((i) => i.title === title);
    return b ? { x: b.x + ITEM_W / 2, y: b.y + ITEM_H / 2 } : null;
  };
  const lines = items
    .filter((i) => i.kind === "connector")
    .map((c) => {
      const [from, to] = c.title.split("→").map((s) => center(s.trim()));
      return from && to ? { id: c.miro_id ?? c.title, from, to } : null;
    })
    .filter((l) => l !== null);
  const newest = boxes[boxes.length - 1];

  return (
    <div className="lb-canvas" role="img" aria-label={`Espejo del tablero de Miro con ${boxes.length} elementos`}>
      <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" aria-hidden="true">
        {lines.map((l) => (
          <line key={l.id} className="lb-link" x1={l.from.x} y1={l.from.y} x2={l.to.x} y2={l.to.y} />
        ))}
      </svg>
      {boxes.map((i) => (
        <Item
          key={i.miro_id ?? i.title}
          tone={TONE[i.kind as keyof typeof TONE] ?? "rosa"}
          fresh={i === newest}
          className="lb-node"
          style={{
            left: `${(i.x / width) * 100}%`,
            top: `${(i.y / height) * 100}%`,
            width: `${(ITEM_W / width) * 100}%`,
          }}
        >
          {i.title}
        </Item>
      ))}
    </div>
  );
}
