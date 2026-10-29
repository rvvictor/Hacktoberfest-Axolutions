# DESIGN · SpeedHack · "Conversación" (frozen)

Chosen by Dylan on 2026-10-29 by looking at three directions (`web/public/design-lock/3-1280.png`, `3-390.png`, `3.html`). It replaces "Línea 1", whose references are kept in `web/public/design-lock/v1/`.
Any global change (palette, type, theme) needs a human-approved `uak decision`.

**Why this direction (design thinking, empathize → define):** Dylan found the old UI flat, hard to follow and overloaded, and too many steps before the product. That distracts the user. The feeling to give is warm and close, including for a small business with no technical vocabulary.

**Intent:** SpeedHack talks you through the project. Each result (questions, plan, board, tasks, prototype, pitch) arrives as a card in a conversation, and you answer with one button. The 9 pipeline stages are shown as **3 moments**: Idea, Plan, Producto.

## 60-30-10 (`web/src/styles/tokens.css`)
| Share | Tokens | Value | Use |
|---|---|---|---|
| 60 % | `--sh-bg` | #F8F6FB | the page |
| 30 % | `--sh-raised` / `--sh-surface` / `--sh-line` | #FFFFFF / #EFEAF6 / #E1D9EE | cards / quiet groups and "you" bubbles / borders |
| 30 % | `--sh-ink` / `--sh-muted` | #2E2640 / #6F6582 | text, done steps, the SpeedHack avatar |
| 10 % | `--sh-accent` / `--sh-accent-soft` | #6D4AE6 / #E9E2FB | **only** the primary action, the current step and a just-arrived item |
| states | `--sh-ok` · `--sh-error` · `--sh-demo` / `--sh-demo-soft` | #23845A · #C2410C · #8A6A2F / #F6EBD4 | results only; never decoration, never the accent |

`--sh-rosa*` and `--sh-naranja*` are **deprecated aliases** (accent and demo) so every screen adopted the palette at once. New code uses the names above, and screens migrate as they are redesigned.

Type: **DM Sans** for everything people read (16 px base, line height 1.55). **Gloock** only for page titles (`Title`). Radius: 12 px rows, 14 px buttons, 20 px cards. Cards are white with a 1 px line, with no heavy shadows.

## Components (`web/src/lib/ui/`)
- `Moments stage={n}`: the page-level progress (Idea · Plan · Producto). `momentOf(stage)` maps stages 1-2, 3-6 and 7-9. Use it at the top of every run screen.
- `Message from="speedhack"|"you"`: one turn of the conversation. SpeedHack explains in one or two plain sentences what it did and what it needs.
- `Panel` + `Item`: the result cards inside the conversation (plan, board, tasks…).
- `Button variant="primary"`: the single next action ("Sí, sigamos", "Aprobar plan"). One per screen. Everything else `secondary`.
- `Chip`, `DemoBadge`, `Stat`, `SectionHeader`, `Title` as before. `DemoBadge` is now amber on soft amber.
- `MetroLine`: the 9 detailed stages, only in the run detail; quieter (ink done, accent current, dashed approval gates).

## Usability rules (Nielsen)
1. **Visibility of status:** every run screen shows `Moments` plus one sentence of what is happening now. A stage that takes long says how long it usually takes.
2. **Match the real world:** say "Tu plan", "Tareas", "Revisión" and "Prototipo", not "Spec", "Backlog", "Calidad" or "Stage". Client mode uses no technical words at all.
3. **User control:** every approval offers "Cambiar algo" next to the primary action, and says what happens after approving.
4. **Consistency:** violet always means "your next action", and nothing else is violet.
5. **Error prevention:** a disabled primary button always explains why next to it.
6. **Recognition over recall:** the current project name and moment are always visible. Navigation has at most 3 visible entries (Nuevo proyecto, Mis proyectos, Más); Cliente, Cazador and Costos live under "Más".
7. **Minimalist design:** one result card and one decision per view; details expand on demand.
8. **Errors:** say what failed and what to do, in the interface's voice ("Miro no respondió. Reintentamos en 4 s.").
9. **Help:** a one-line hint under each decision, never a manual.

## Never
1. Never use the accent for anything but the next action, the current step or a just-arrived item.
2. Never show the 9 stages as the main progress: people see 3 moments.
3. Never show a figure without its source, or simulated data without `DemoBadge`.
