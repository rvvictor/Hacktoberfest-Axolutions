# DECISIONS

Coordination decisions on the claims branch.
Why: a reversible option after 15 min keeps work moving.
- 1793157589 | deadline backlog/proposed/1793143081 | ALLOW_P0 | Only P0 with active autonomy; a timeout grants no permissions.
- 1793158535 | HACK-002 | payload validated per event type in test; ts = relative seconds | Why: contract for downstream tasks
- 1793158634 | HACK-001 | keep oxlint from Vite template | Why: template ships oxlint, not eslint
- 1793159248 | HACK-004 | fixtures hand-written, no ANTHROPIC key | Why: cannot make real call
- 1793159302 | HACK-013 | Hold PR/uak done until HACK-001/002 integrate (branch carries their merge) | Why: diff outside Paths otherwise
- 1793159442 | HACK-003 | Direction 3 Línea 1 | Why: human pick
- 1793159885 | HACK-006 | tests con asyncio.run, sin pytest-asyncio | Why: evitar tocar pyproject compartido
- 1793159895 | HACK-007 | fixtures hand-written, no LINEAR key | Why: cannot record real call
- 1793159895 | HACK-008 | httpx direct to ElevenLabs REST (respx-mocked), not SDK; fixtures are placeholders marked demo_data | Why: no API key yet; keeps tests offline
- 1793160123 | HACK-012 | CI-only checks (build, lint, gitleaks, npm audit, smoke) are named in report.details, not reported as passed; QualityCheck has no 'skipped' state | Why: run() cannot build or scan a generated repo in-process without installing its deps; a passed=True for unrun checks would be a false green (IDEA.md §5 honest validation)
- 1793160148 | HACK-011 | nothing sent without approved_by; opt-out line appended in code; opted-out prospects skipped before any n8n call; in-process fallback; mock send only | Why: acceptance rules enforced in code and tested, not only in UI
- 1793160199 | deadline decision/HACK-003-1793159298/1793160198 | BLOCKED_OTHER_TASK | Option: Direction 3 · Línea 1; Why: Dylan picked it looking at the gallery: the 9 stages and 3 approvals read in 3 s on a projector as a CDMX Metro line; no money, accounts, publishing or scope expansion.
- 1793160307 | HACK-010 | Prompt built only from Spec/BacklogItem fields; plan B url = LOVABLE_PREBUILT_URL or /fixtures/generator/planb/index.html (router must serve it) | Why: no raw web content in prompt; honest demo_data
- 1793161562 | HACK-009 | Missing key uses process-local keyword cache and honest local demo recording | Why: No Backboard key or prior recording exists; preserve source provenance and never invent live evidence
- 1793161993 | HACK-009 | Keep draft and BLOCKED; no false claim of real Backboard evidence | Why: No configured key and no pre-existing provider recording
- 1793162281 | deadline lease/HACK-013/1793162002 | REQUIRES_RECOVERY | Claim kept; read the summary and use release --expired --read-summary. No work is deleted.
- 1793162656 | deadline lease/HACK-007/1793162595 | REQUIRES_RECOVERY | Claim kept; read the summary and use release --expired --read-summary. No work is deleted.
- 1793163805 | deadline queue-lock/hack.47kElW-jabi-2-HACK-003/1793163805 | HUMAN | Lock lease expired; revalidate before merging
- 1793164000 | HACK-015 | local contract.ts+demo replay | Why: HACK-002 not on main
- 1793164244 | HACK-014 | local contract.ts, demo fallback | Why: HACK-002 not on main
- 1793164360 | HACK-016 | local contract.ts until HACK-002 integrates | Why: HACK-002 not on main
- 1793164497 | deadline lease/HACK-008/1793164303 | REQUIRES_RECOVERY | Claim kept; read the summary and use release --expired --read-summary. No work is deleted.
- 1793164497 | deadline lease/HACK-011/1793164305 | REQUIRES_RECOVERY | Claim kept; read the summary and use release --expired --read-summary. No work is deleted.
- 1793164951 | HACK-017 | versions from spec_ready events; client mode via ?mode=client toggle (Run has no mode) | Why: backend lacks versions endpoint
- 1793164988 | HACK-020 | speechSynthesis for audio, no recorded mp3 | Why: no paid API, HACK-008 absent
- 1793164996 | HACK-019 | Use integrated LLM; explicit demo run only; reject foreign and fabricated sources | Why: Preserve run scope and evidence provenance
- 1793165182 | HACK-013 | Left SSE named events as is (HACK-016 listens per type) | Why: changing breaks useBoardEvents
- 1793165271 | HACK-021 | Merged feat/hack-011 for outreach.py contract | Why: 011 not in main yet
- 1793165595 | HACK-009 | Ship with local index; AC3 flagged partial, fixture demo_data:true | Why: No Backboard key
- 1793165653 | HACK-023 | no prices (none in IDEA §10) | Why: no source
- 1793165665 | HACK-022 | Read HACK-013 sqlite tables directly; units derived from usd via estimated price table | Why: HACK-013 only stores usd per step and is unmerged
