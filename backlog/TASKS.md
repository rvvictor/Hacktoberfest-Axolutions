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
