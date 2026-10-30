import { Item } from "../../lib/ui";
import type { MiroItem } from "./contract";

// Miro board units (app/fixtures/demo/run.jsonl): items sit on a 220 × 160 grid. The canvas keeps the board's aspect
// ratio and fixed minimum bounds so the layout stays still while items arrive.
const ITEM_W = 200;
const ITEM_H = 64;
const TONE = { screen: "rosa", data_model: "ink", integration: "naranja" } as const;
const GROUPS = [
  ["screen", "Pantallas"],
  ["data_model", "Datos"],
  ["integration", "Integraciones"],
] as const;

type Box = { x: number; y: number };

// Edge to edge: down to the next row from bottom-center to top-center, sideways from the facing side edges.
function route(a: Box, b: Box) {
  if (Math.abs(a.y - b.y) >= ITEM_H) {
    const down = b.y > a.y;
    return {
      x1: a.x + ITEM_W / 2, y1: down ? a.y + ITEM_H : a.y,
      x2: b.x + ITEM_W / 2, y2: down ? b.y : b.y + ITEM_H,
    };
  }
  const right = b.x > a.x;
  return {
    x1: right ? a.x + ITEM_W : a.x, y1: a.y + ITEM_H / 2,
    x2: right ? b.x : b.x + ITEM_W, y2: b.y + ITEM_H / 2,
  };
}

// The live board (app/services/miro.py) puts each kind in a frame with its notes inside, at frame-relative
// positions: drawn as one column per frame, notes stacked so long titles wrap, and a dashed link where a
// connector joins the first notes of neighbouring columns.
function FrameColumns({ items }: { items: MiroItem[] }) {
  const frames = items.filter((i) => i.kind === "frame");
  const notes = items.filter((i) => i.kind !== "frame" && i.kind !== "connector");
  const kinds = GROUPS.filter(([kind]) => notes.some((n) => n.kind === kind));
  const starts = new Set(items.filter((i) => i.kind === "connector").map((c) => c.title.split("→")[0].trim()));
  const newest = notes[notes.length - 1];
  const tone = (kind: string) => TONE[kind as keyof typeof TONE] ?? "rosa";
  return (
    <div className="lb-canvas lb-canvas--columns" role="img" aria-label={`Espejo del tablero de Miro con ${notes.length} elementos`}>
      <div className="lb-columns" style={{ gridTemplateColumns: `repeat(${kinds.length}, minmax(0, 1fr))` }}>
        {kinds.map(([kind, label], col) => (
          <div key={kind} className="lb-column">
            <h3>{frames[col]?.title ?? label}</h3>
            {notes
              .filter((n) => n.kind === kind)
              .map((n, row) => (
                <Item
                  key={n.miro_id ?? n.title}
                  tone={tone(kind)}
                  fresh={n === newest}
                  className={row === 0 && col < kinds.length - 1 && starts.has(n.title) ? "lb-joined" : undefined}
                >
                  {n.title}
                </Item>
              ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export function MirrorCanvas({ items }: { items: MiroItem[] }) {
  const framed = items.some((i) => i.kind === "frame");
  const boxes = items.filter((i) => i.kind !== "connector" && i.kind !== "frame");
  const minX = Math.min(0, ...boxes.map((i) => i.x));
  const minY = Math.min(0, ...boxes.map((i) => i.y));
  const width = Math.max(860, ...boxes.map((i) => i.x + ITEM_W)) - minX;
  const height = Math.max(384, ...boxes.map((i) => i.y + ITEM_H)) - minY;
  const at = (title: string) => {
    const b = boxes.find((i) => i.title === title);
    return b ? { x: b.x - minX, y: b.y - minY } : null;
  };
  const links = items
    .filter((i) => i.kind === "connector")
    .map((c) => {
      const [from, to] = c.title.split("→").map((s) => at(s.trim()));
      return from && to ? { id: c.miro_id ?? c.title, ...route(from, to) } : null;
    })
    .filter((l) => l !== null);
  const newest = boxes[boxes.length - 1];
  const tone = (kind: string) => TONE[kind as keyof typeof TONE] ?? "rosa";

  return (
    <>
      {framed ? <FrameColumns items={items} /> : (
      <div className="lb-canvas" role="img" aria-label={`Espejo del tablero de Miro con ${boxes.length} elementos`}>
        <div className="lb-board" style={{ aspectRatio: `${width} / ${height}` }}>
          <svg viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
            {links.map(({ id, ...l }) => (
              <line key={id} className="lb-link" {...l} />
            ))}
          </svg>
          {boxes.map((i) => (
            <Item
              key={i.miro_id ?? i.title}
              tone={tone(i.kind)}
              fresh={i === newest}
              className="lb-node"
              style={{
                left: `${((i.x - minX) / width) * 100}%`,
                top: `${((i.y - minY) / height) * 100}%`,
                width: `${(ITEM_W / width) * 100}%`,
              }}
            >
              {i.title}
            </Item>
          ))}
        </div>
      </div>
      )}

      {/* Phones: the same items grouped by kind, so nothing is clipped or shrunk past reading size. */}
      <div className="lb-groups">
        {GROUPS.map(([kind, label]) => (
          <div key={kind}>
            <h3>{label}</h3>
            {boxes
              .filter((i) => i.kind === kind)
              .map((i) => (
                <Item key={i.miro_id ?? i.title} tone={tone(kind)} fresh={i === newest}>
                  {i.title}
                </Item>
              ))}
          </div>
        ))}
      </div>
    </>
  );
}
