# SpeedHack — three-minute demo

Language: Spanish. Budget: 180 seconds. Based on `IDEA.md` §4.
The board starts at 00:55; its completed state must be visible by 01:20
(before the 90-second deadline). Rehearse at 1280×720 with reduced motion.

Before presenting, start the no-key setup in the README. Open these tabs:
`/#/intake`, `/#/run`, `/#/spec`, `/#/live-board`, `/#/delivery`,
`/#/client`, `/#/hunter`, and `/#/pitch`. Standalone pages use independent
recorded fixtures: say `demo_data: true`; do not describe them as one live run.
Keep the [plan-B recording](plan-b.md) downloaded locally.

| Time | Action and narration | Evidence on screen | Fallback |
|---|---|---|---|
| 00:00–00:20 | Open intake in developer mode. “SpeedHack mantiene el contexto desde una idea hasta un pitch defendible. Esta demostración usa datos grabados, `demo_data: true`.” Type: “SaaS de control de gastos corporativos con React, Supabase y alertas automatizadas.” | Developer mode and idea input. | Type instead of dictating if the microphone is unavailable. If submission stalls, open the prepared execution tab. |
| 00:20–00:40 | Show execution and clarification. “Definimos empresas, roles y alertas; el equipo conserva el control con tres aprobaciones.” | Nine-stage timeline and first approval. | Use `/#/run` without a run ID for the labeled replay; do not wait more than five seconds for a provider. |
| 00:40–00:55 | Open spec; show sources and assumptions, then approve spec. “La investigación conserva sus fuentes. Las cifras de una muestra no son precios actuales verificados.” | Versioned spec, source links, approval 1. | Open `/#/spec` fixture. Read assumptions if the source page cannot load. Do not invent a market statistic. |
| 00:55–01:20 | Open board and click **Repetir** if needed. “De este spec salen la arquitectura y el backlog: pantallas, datos e integraciones junto a tickets con criterios de aceptación.” | **Wow:** architecture and Linear issue feed side by side. | Open `/#/live-board` without query parameters for the labeled mirror. If rendering fails, play the corresponding segment of the recording or show the real board screenshot in README. |
| 01:20–01:45 | Approve design, open delivery, inspect checks, approve delivery. “La puerta de calidad muestra qué pasó y qué falló antes de aceptar el prototipo.” | Prototype, quality report, approvals 2 and 3. | Use `/#/delivery` replay. Report fixture results as recorded examples, never as a fresh build or security audit. |
| 01:45–02:05 | Open client, then hunter. “La misma idea se explica sin jerga. Para prospectar, una persona revisa el mensaje y el consentimiento antes del envío.” | Fictional barbershop; draft, consent, opt-out and approval controls. | Show the sample without pressing send. If short on time, describe client mode while showing hunter. No real contact is required. |
| 02:05–02:45 | Open pitch with `demo-pitch`. Ask: “¿Alertas?” “Soy una IA; respondo con el contexto del proyecto y sus fuentes.” Then ask “¿Qué funciones incluye el control de gastos?” to show the current fixture's conservative refusal. | Deck, grounded response, source labels; “no tengo ese dato” when the fixture cannot support an answer. | Type the question instead of speaking. The bundled demo audio is a placeholder, so read the response aloud and identify it as AI-generated. If API fails, play recording, which shows the refusal case. |
| 02:45–03:00 | Close on board or pitch. “El valor es la continuidad del contexto y las decisiones humanas. Hoy mostramos el recorrido grabado; las integraciones reales dependen de sus credenciales.” | Visible `demo_data: true` and the artifacts already shown. | Close on the real board screenshot. Stop at 03:00. |

## Live-run routing and recovery

Standalone fixtures are the reliable no-key presentation path. For a real run,
retain the created run ID and use the route convention of each feature:

- Execution: `/#/run?run=RUN_ID`.
- Board: `/?run=RUN_ID#/live-board` (query before the hash).
- Pitch: `/?run_id=RUN_ID#/pitch` (query before the hash).

Do not promise that moving between fixture tabs preserves a single run. If a live
connection fails, announce the switch to recorded sample data, remove run query
parameters, and continue with the prepared tab. Never retry a provider on stage
for more than five seconds. Keep all three human decisions explicit.
