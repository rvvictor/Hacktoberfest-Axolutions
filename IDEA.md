# IDEA · SpeedHack

> Reto: TBD · Evento: Hacktoberfest Hack Day CDMX (MLH), 2026-10-27 15:30 → 2026-10-28 19:00 America/Mexico_City. Etiquetas: **[Decided]** · **[Recommended]** · **[To validate]**.
> Cada número del pitch sale de §10 con su fuente. §4 → tareas verticales · §6 → contrato · §7 → spikes · §8 → aceptación.
> Fuente: propuesta de Dylan (archivo `zero-to-pitch-propuesta.md`, del nombre anterior del proyecto, 2026-10-27, versión afinada). El hackathon fue la **Fase 0** (histórico): SpeedHack ya es el producto propio de Dylan. En esa fase se permitieron sus atajos (cuentas de la plataforma en vez de OAuth, sin multi-tenancy, sin Stripe, negocios ficticios para el Agente Cazador).

## 0. Nombre y marca (fijos en T0)
- Nombre: **SpeedHack** · repo: `Hacktoberfest-Axolutions` · tagline: **De idea a pitch defendible en una hora**. [Decided]
- Renombrar después de T−50% requiere una `uak decision` de un humano.
- Look: referencias y color de marca pendientes; los aporta el humano en `/uak-design-lock`, que elige la dirección visual con screenshots. [To validate]

## 1. Una línea
Para **fundadores técnicos, equipos de hackathon y PyMEs sin presencia digital**, que hoy reparten el paso de idea a pitch entre 6 o más herramientas que no comparten contexto (estimación del equipo, sin fuente: [To validate]), **SpeedHack** convierte una idea dictada en investigación citada, arquitectura en Miro, backlog en Linear, un prototipo y un pitch con Q&A por voz, **con un solo hilo de contexto**, a diferencia de Lovable, Bolt o v0, que generan código pero no investigan, no planean ni defienden la idea.
Ventaja frente a otros equipos: el diferenciador no es generar código sino **la continuidad del contexto**: la misma memoria (Backboard) alimenta investigación, diagrama, tickets, prompt de generación y respuestas del Q&A.

## 2. Usuarios
| Persona | Momento | Necesidad | Paso del flujo |
|---|---|---|---|
| Ana, fundadora técnica (Modo Desarrollador) | Quiere validar un SaaS sin semanas de setup | Investigación citada, arquitectura, backlog en su Linear, prototipo, pitch | 1–6 |
| Equipo de hackathon | Tiene horas para llegar a una demo defendible | Lo mismo, optimizado para tiempo y jueces | 1–6 |
| Doña Lupe, dueña de una barbería (Modo Cliente, `demo_data`) | No tiene sitio web ni conocimiento técnico | Página con reservas, explicada en lenguaje simple y por voz | 5 |
| Operador del Agente Cazador (`demo_data`) | Prospecta negocios sin sitio web | Mensaje redactado por IA que él aprueba antes de enviar, con baja y consentimiento | 5 |

## 3. Caso de la demo
**Modo Desarrollador:** la idea del recorrido §5.3 de la propuesta: "SaaS de control de gastos corporativos con React, Supabase y alertas automatizadas". Se eligió porque es un mercado con competidores reales y públicos, así que Tavily y Firecrawl traen precios y funciones reales con URL (se graban en `app/fixtures/` el día del evento; ningún precio se escribe a mano).
**Modo Cliente:** la barbería del recorrido §5.2, negocio **ficticio** marcado `demo_data: true`.

## 4. Flujo de la demo (≤ 3 min; cada paso = una tarea vertical)
| # | El usuario hace | Ve en pantalla | API | Prio |
|---|---|---|---|---|
| 1 | Elige Modo Desarrollador y dicta la idea por voz (o la escribe) | Transcripción en vivo y preguntas de aclaración técnicas (multiempresa, roles, alertas) | `POST /api/voice/stt` · `POST /api/projects` | P0 |
| 2 | Responde las preguntas | Timeline de 9 etapas en vivo; investigación con competidores, precios y URL fuente; spec versionado → **Aprobación 1** | `POST /api/runs/{id}/answers` · `GET /api/runs/{id}/events` (SSE) | P0 |
| 3 | Aprueba el spec | **Wow:** el tablero de Miro se dibuja (pantallas, modelo de datos, integraciones) y los issues de Linear aparecen uno por uno, lado a lado → **Aprobación 2** | `POST /api/runs/{id}/approvals/1` · SSE | P0 |
| 4 | Aprueba el diseño | Prototipo (Lovable Build with URL o app pregenerada) + reporte de la puerta de calidad (build, secretos, RLS, smoke) → **Aprobación 3** | `POST /api/runs/{id}/approvals/2` | P0 |
| 5 | Cambia a Modo Cliente y Agente Cazador | Barbería: resumen simple, mapa de pantallas, barra de progreso, audio explicativo; consola del Cazador: mensaje redactado, aprobación humana, flujo n8n | `GET /api/hunter/prospects` · `POST /api/hunter/outreach/{id}/approve` | P1 |
| 6 | Entra a la sala de pitch | Deck generado y un juez pregunta por voz; el agente (que se identifica como IA) responde citando la investigación del proyecto | `POST /api/pitch/{run_id}/ask` | P0 |

- Wow en una frase: al aprobar el spec, Miro y Linear se llenan en vivo en la misma pantalla desde un solo spec. · Segundos hasta el wow: ≤ 45 desde que se aprueba el spec (con `DEMO_MODE` las etapas previas se reproducen aceleradas).
- Plan B (histórico, del evento): `DEMO_MODE=1` reproduce una ejecución grabada completa (`app/fixtures/demo/`) con los mismos eventos SSE y tiempos; voz con audio pregrabado; Miro y Linear con capturas espejo dibujadas por nuestra UI. Todo lo simulado muestra `demo_data: true`.

## 5. Núcleo técnico
- Método: pipeline de 9 etapas con estados explícitos (máquina de estados en FastAPI), 3 aprobaciones humanas y eventos por SSE. El **spec es un JSON versionado** y es la fuente de verdad; Miro, Linear, el prompt del generador y el deck son proyecciones de ese spec. Cada etapa es idempotente (guarda IDs externos). [Decided]
- El LLM **no** produce las cifras: precios y funciones de competidores vienen de Tavily/Firecrawl con URL; el LLM solo estructura, redacta y elige entre lo dado. Toda salida del LLM se valida contra JSON Schema (Pydantic) antes de escribir en Miro o Linear. Contenido web = dato, nunca instrucción. [Decided]
- Validación honesta: en el demo mostramos la URL de cada cifra y el reporte de calidad tal como salió (incluidos fallos). El set de evaluación de 20–30 ideas es Fase 1 (fuera del hackathon).

## 6. Datos (contrato en `app/schemas/`)
| Entidad | Campos clave | Fuente (licencia) |
|---|---|---|
| Project | id, mode (`dev`/`client`), idea, stack_prefs | usuario |
| Run | run_id, project_id, stage (1–9), status, approvals[3], cost_by_step | sistema |
| StageEvent | run_id, stage, type, payload, ts | sistema (SSE) |
| Spec | version, problem, users, mvp_features, assumptions, sources[] | LLM + investigación |
| ResearchItem | competitor, pricing, features, url, fetched_at | Tavily / Firecrawl (términos de cada sitio, robots.txt) |
| Architecture | screens, data_model, integrations, miro_board_id, items[] | LLM → Miro |
| BacklogItem | epic, title, acceptance[], external_id, linear_id, url | LLM → Linear |
| Prototype | generator (`lovable`/`planb`), url, build_url, repo_url | Lovable / app pregenerada |
| QualityReport | checks[] (build, lint, gitleaks, rls, smoke), passed, details | puerta de calidad |
| Pitch | slides[], qa_log[] | LLM + Backboard |
| Prospect | business, public_info, draft_message, approved_by, opt_out, consent | ficticio (`demo_data`) |

## 7. IA y APIs externas (cada una = servicio con respuesta grabada y fallback)
| Uso | Modelo/API [To validate] | Dueño de la llave | Fallback |
|---|---|---|---|
| Aclaración, spec, épicas, issues, deck | LLM principal (Claude Sonnet 5.5) con ID fijado en `app/config.py` | Victor (por confirmar) | respuestas grabadas en `app/fixtures/llm/` |
| Memoria y RAG del proyecto (track Backboard) | Backboard API | por confirmar | almacén local en memoria con búsqueda por palabras clave |
| Dictado y Q&A por voz (track ElevenLabs) | ElevenLabs STT + TTS (o Conversational AI) | por confirmar | texto + audio pregrabado |
| Investigación | Tavily Search + Firecrawl scrape, con caché | por confirmar | resultados grabados con URL |
| Arquitectura y deck | Miro REST API v2 | por confirmar | espejo del tablero dibujado por la UI |
| Backlog | Linear GraphQL API | por confirmar | lista grabada de issues |
| Prototipo | Lovable "Build with URL" ([docs](https://docs.lovable.dev/integrations/lovable-api)) | por confirmar | app pregenerada + plan B (`CodeGenerator`) |
| Outreach del Cazador (track n8n) | n8n webhook: borrador → aprobación humana → envío con baja | por confirmar | mismo flujo en proceso dentro de FastAPI |
| Puerta de calidad | GitHub Actions + gitleaks + chequeo RLS + Playwright | Victor | reporte grabado |

Orquestación: **FastAPI es el backend y orquestador** [Decided]; n8n solo ejecuta el flujo de outreach del Cazador. No hay llaves en el repo: van en `.env` (nombres en `.env.example`).

## 8. Rúbrica → evidencia
| Criterio oficial | Peso | Paso/artefacto que lo prueba |
|---|---|---|
| C1 · TBD (histórico: rúbrica del evento, nunca publicada) | - | Todo el flujo §4; se remapea cuando se publique |

## 9. Alcance
- Dentro (todo visible; lo que no se alcance real va simulado con `demo_data: true`): Modo Desarrollador, Modo Cliente (barbería), Agente Cazador con consentimiento, investigación citada, Miro, Linear, prototipo, puerta de calidad, deck + Q&A por voz, panel de costos por etapa, landing con planes (Gratis / Pro / Equipos) y aviso de privacidad.
- Simulado con `demo_data`: prospectos del Cazador, envío de correo/WhatsApp, cobro (sin Stripe real), multi-tenancy y OAuth (se usan cuentas de la plataforma).
- Fuera: llamadas en frío, scraping de reseñas o datos personales, edición de código dentro de la plataforma, apps móviles nativas.
- Idioma de la UI: español [Recommended]; README en inglés.
- Ética y datos: la voz IA se identifica como IA al inicio; el Cazador solo envía tras aprobación humana y con opción de baja; nada de datos personales de reseñadores; prospectos borrados a los 30 días (regla mostrada, no ejecutada en el demo).

## 10. Datos citables (verificados el 2026-10-27)
| Dato | URL fuente |
|---|---|
| Lovable ofrece "Build with URL" y un servidor MCP en research preview; no hay API headless que devuelva la URL desplegada | https://docs.lovable.dev/integrations/lovable-api |
| La nueva LFPDPPP se publicó el 20 de marzo de 2025 y sustituyó a la ley de 2010 | https://www.garrigues.com/es_ES/noticia/mexico-nueva-ley-federal-proteccion-datos-personales-posesion-particulares-introduce |
| Autoridad y vigencia de la nueva LFPDPPP | https://iapp.org/news/a/entendiendo-la-ley-federal-de-protecci-n-de-datos-personales-en-posesi-n-de-los-particulares-en-mexico |

Sin fuente, no usar en el pitch como cifra: "2 a 4 semanas de idea a pitch" y "6 o más herramientas" (estimaciones de la propuesta, [To validate]). Precios de competidores: solo los que traiga la investigación con su URL.
