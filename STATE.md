# STATE

Phase: feature freeze; authorized fixes, rehearsal and submission only
Updated: 1793243117
AVAILABLE: HACK-025 
CLAIMED: HACK-039 
BLOCKED: -
REVIEW: HACK-038 
INTEGRATED: (35; last 12) ... HACK-024 HACK-026 HACK-027 HACK-028 HACK-029 HACK-031 HACK-032 HACK-033 HACK-034 HACK-035 HACK-036 HACK-037 
CANCELLED: HACK-030 

Claims (first 24; status --task ID shows detail):
HACK-038 | REVIEW | dylan-1 | until 1793257508
HACK-039 | CLAIMED | dylan-2 | until 1793245377

Blockers: BLOCKED tasks; use status --task ID --summary.
Current decisions (last 5):
- 1793242364 | HACK-038 | follow-up of HACK-011 by dylan-1: Hunter AI drafts use Gemma 4 via the Gemini API when LLM_MODEL selects it | Why: same Paths, no scope change
- 1793242370 | HACK-039 | follow-up of HACK-001 by dylan-2: Test isolation: app/tests/conftest.py blanks provider keys and forces DEMO_MODE so a developer .env never makes real API
- 1793242639 | allow | Dylan | freeze exception: HACK-038 | Why: Post-hackathon: borradores del Cazador con Gemma 4
- 1793242646 | allow | Dylan | freeze exception: HACK-039 | Why: Post-hackathon: las pruebas no deben usar llaves reales
- 1793242652 | plan --amend | Dylan/Dylan | amended: HACK-039 Paths: pyproject.toml, uv.lock, .python-version, .env.example, Dockerfile, .dockerignore, render.yaml, .uak/bin/smoke-

Global next step: available P0; else review PRs, tests, demo, rehearsal.
Why: bounded snapshot to resume without rereading history.
