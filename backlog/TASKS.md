# Backlog published on claims (uak plan)

Append-only; added to .uak/TASKS.md from main. Why: adding tasks never waits for a PR.
## HACK-025 · Record real fixtures: Tavily, Firecrawl and LLM with Fer's keys

- **Type:** integration
- **Priority:** P0
- **Estimate:** 45 min
- **Rubric / Spec:** C1 · `IDEA.md` §3, §10
- **Depends on:** HACK-005
- **Paths:** app/fixtures/research/, app/fixtures/llm/, scripts/record_fixtures.py
- **Freeze-Allowed:** no
- **Acceptance:**
  - Fer (the human) puts `TAVILY_API_KEY`, `FIRECRAWL_API_KEY` and `ANTHROPIC_API_KEY` in `.env` on the machine where this runs, from his editor. The agent never reads, prints or writes `.env`; it only checks that the variables are set (for example with `uv run python -c "from app.config import settings; print(bool(settings.TAVILY_API_KEY))"`).
  - `python -m app.services.research --record` records the real results for the `IDEA.md` §3 case: no `example.invalid` URL remains and every item keeps its source URL.
  - `scripts/record_fixtures.py` calls each `app/services/llm.py` function once with the real key and saves its validated output in `app/fixtures/llm/`, with `demo_data: false`.
  - The committed fixtures contain API responses only, never a key (the pre-commit secret scan passes).
- **Verify:** `uv run pytest -q app/tests/test_research.py app/tests/test_llm.py && ! grep -rq 'example.invalid' app/fixtures/research/`
- **Next step:** ask Fer to add the three keys to `.env`; then run `python -m app.services.research --record`.
## HACK-026 · Screen polish from the 1280x720 browser check: delivery, intake, spec, mobile nav, costs

- **Type:** bug
- **Priority:** P1
- **Estimate:** 45 min
- **Rubric / Spec:** C1 · `.uak/modes/sprint.md` §A stunning frontend
- **Depends on:** None
- **Paths:** web/src/features/delivery/, web/src/features/intake/, web/src/features/spec/, web/src/features/ops/, web/src/App.tsx
- **Freeze-Allowed:** yes
- **Acceptance:**
  - Delivery (`#/delivery`, demo step 4) fits 1280x720 with no vertical scroll: the quality-gate card, the remaining backlog and the approval 3 controls are all visible (today the page is 988 px tall).
  - Intake: the primary "Empezar" button explains why it is disabled (a hint or placeholder such as "Escribe o dicta tu idea"), so it never looks broken on screen.
  - Spec: the competitor table reads cleanly; the price cell no longer wraps awkwardly ("Precio simulado" / "sin precio publicado").
  - Mobile nav (390x844, `web/src/App.tsx`): the top nav no longer wraps into 3 lines or clips "Entrega"; use a horizontal scroll strip or a compact menu.
  - Costs (`#/ops`): amounts and labels are not cramped; the page fits 1280x720 or scrolls only inside a panel.
  - No regression on the wow (`#/live-board`) or the run view: both still fit 1280x720 with no scroll.
  - Only design-system tokens and `web/src/lib/ui/` components; `bash .uak/bin/design-lint` passes. Screenshots of each fixed screen at 1280x720 (and the nav at 390x844) in the PR.
- **Verify:** `npm --prefix web run build && bash .uak/bin/design-lint`
- **Next step:** run the app with `DEMO_MODE=1`, screenshot `#/delivery` at 1280x720 with Playwright (reduced motion) to reproduce the 988 px height, then fix delivery first.
