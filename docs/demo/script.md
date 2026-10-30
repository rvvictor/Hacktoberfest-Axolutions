# SpeedHack — three-minute demo

Language: Spanish narration. Budget: 180 seconds. Based on `IDEA.md` §4.
Rehearse at 1280×720 with reduced motion, with the no-key setup from the README
(`DEMO_MODE=1`). One run, one browser tab: the conversation at `#/project` links to
every other view and keeps the run in `?run=`.

Machine time to the wow is about 16 s: stages 1–6 of `app/fixtures/demo/run.jsonl`
end at 33.3 s of recorded time, replayed at `DEMO_SPEED=2` (the default). The rest
of the 90 seconds is the presenter: typing, three answers and one approval.

Rubric: the official rubric is not published (`IDEA.md` §8). Each part names the
`IDEA.md` §4 step it shows and C1; remap the column when the rubric is published.

| Time | Part | Do and say | On screen | `IDEA.md` §4 · rubric | Fallback |
|---|---|---|---|---|---|
| 00:00–00:20 | Problem | “Tienes una idea y necesitas defenderla: investigar, escribir el plan, repartir el trabajo y mostrar algo que funcione. Normalmente son días, y cada herramienta pierde el contexto de la anterior.” | Landing: the idea in one line and the three moments. | context · C1 | Read it off the landing. |
| 00:20–01:50 | Live demo to the wow | **Nuevo proyecto** → type “SaaS de control de gastos corporativos con React, Supabase y alertas automatizadas” (or dictate). Answer the three questions with one short line each. On the plan: “Estas fuentes son reales y cada dato lleva su enlace.” Approve the plan, then click **Ver el tablero en vivo**. | **Wow (by 01:50):** the Miro board and the Linear tickets filled from the same plan, side by side. | steps 1–3 · C1 | The “Datos de demostración” badge stays visible. If the board view fails, go back to `#/project`: the same board and tasks are cards in the conversation. |
| 01:50–02:30 | How it works | Back to the conversation; approve the tasks. “SpeedHack construye el prototipo con tu plan; esta es la app, funcionando aquí mismo.” In the prototype: **Entrar al Sistema** → **Mis Gastos**. Point at the four checks: “se revisan de verdad: compila, sin recursos externos, sin llaves expuestas, abre sin errores.” Approve. | The prototype inside the card, its check chips, approval 3. | steps 4–5 · C1 | **Abrir el prototipo** opens it full screen. |
| 02:30–03:00 | Impact | **Ir a la sala de pitch**. Ask “¿Cómo funcionan las alertas?” or “¿De qué trata el proyecto?”: “Soy una IA; respondo solo con la memoria del proyecto y cito la fuente.” Close: “Una persona decide en cada paso, no se inventa ninguna cifra y todo sale con su fuente.” | Deck, answer with its source. | steps 6–7 · C1 | Type the question instead of speaking. If the answer fails, read the plan card aloud and say so. |

Say once, out loud: the demo uses recorded data (`demo_data: true`); the real
integrations (Tavily, Firecrawl, Miro, Linear, the LLM) need their credentials.
Do not claim a time from idea to pitch: none has been measured.

## Live-run routing and recovery

Every view reads the run from `?run=RUN_ID` before the hash, the form the intake
redirect and the conversation links use:

- Conversation: `/?run=RUN_ID#/project`.
- Board (the wow): `/?run=RUN_ID#/live-board`.
- Nine-stage detail: `/?run=RUN_ID#/run`.
- Pitch: `/?run=RUN_ID#/pitch`.

Without `?run=`, `#/project` plays a recorded example and the other views show their
own labeled samples; do not present those as the same run. If a live provider
fails, say that the run switched to recorded data and continue; never retry a
provider on stage for more than five seconds. Keep all three human decisions explicit.
