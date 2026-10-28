# DESIGN · SpeedHack · "Línea 1" (frozen)

Chosen by Dylan on 2026-10-27 by looking at three directions (`web/public/design-lock/3-1280.png`, `3-390.png`, `3.html`).
Any global change (palette, type, theme) needs a human-approved `uak decision`.

**Intent:** a run of SpeedHack is a trip on a CDMX Metro line. The 9 stages are stations on a rosa mexicano line, and the 3 human approvals are transfer stations ringed in orange. A judge reads where the run is in 3 seconds on a projector. Light background, one family (Archivo) whose width carries the hierarchy.

## Tokens (`web/src/styles/tokens.css`)
| Token | Value | Use |
|---|---|---|
| `--sh-bg` | #FFFFFF | page |
| `--sh-surface` | #F3F1F6 | panels |
| `--sh-raised` | #FFFFFF | rows inside panels |
| `--sh-ink` | #22223A | text, data-model accents, secondary buttons |
| `--sh-muted` | #6A6A80 | meta text |
| `--sh-line` | #DCD8E3 | rail not yet travelled, dashed placeholders |
| `--sh-rosa` | #E4007C | brand: the line, current station, primary action, new items |
| `--sh-naranja` | #F08A00 | approvals (transfer stations), integrations, demo-data badge border |
| `--sh-naranja-ink` | #9A5200 | orange text on white |
| `--sh-ok` / `--sh-error` | #0F8A5F / #C62828 | quality checks pass/fail only |

Type: Archivo variable (Google Fonts). Titles 800 at `font-stretch: 112%`; IDs and big numbers at `62%` (condensed); body 400–600 at 100%. Scale: 12 / 13.5 / 15 / 18 / 26 / 34 px. Radius: 10 px rows, 18 px panels, pill for buttons and chips. No shadows except the rosa ring on new items.

## Components (`web/src/lib/ui/`, import from `../../lib/ui` in a feature)
- `MetroLine current={n}`: the run timeline. Use it on every run screen, at the top, full width. Gates after stages 4, 6, 8 are fixed in `GATES`.
- `Title`, `SectionHeader title meta`: the project name, then each panel's heading with a count ("5 de 12").
- `Panel title meta` + `Item tone pending fresh code meta`: Miro elements (`rosa` screens, `ink` data, `naranja` integrations), Linear issues, research sources. `pending` = still arriving (dashed), `fresh` = just arrived (rosa ring).
- `Button variant="primary"`: only the action that advances the run (Aprobar, Empezar). One per screen. Everything else `secondary`.
- `Chip tone`: small states (ok/error for quality checks, rosa for highlights).
- `DemoBadge show={demo_data}`: required wherever data is recorded or simulated; on a view it sits in the header, top-right.
- `Stat value label`: costs, times, counts (condensed numerals).

## Usage rules
- Every view reuses `MetroLine` and `Panel`; don't build another timeline or card style.
- The wow screen (HACK-016) is two panels side by side: Miro 1.3fr, Linear 1fr; stacked under 820 px. Newest item first in Linear so the arrival is above the 720 px fold.
- Motion: only the current station's pulse and items arriving one by one (≈150 ms stagger). Everything respects `prefers-reduced-motion`.
- Copy in Spanish, sentence case, plain verbs ("Aprobar diseño", "Pedir cambios").

## Never
1. Never a dark theme or a second brand color: rosa is the only accent; orange means approval, integrations or demo data, nothing else (and never as text or focus ring on white: use `--sh-naranja-ink` / `--sh-ink`).
2. Never all-caps labels, gradients or drop shadows on cards.
3. Never show a figure without its source or simulated data without `DemoBadge`.
