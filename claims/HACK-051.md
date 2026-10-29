# HACK-051
ID: HACK-051
State: CLAIMED
Owner: dylan-1
Branch: feat/hack-051
Worktree: /Users/dylanmartinezcastillo/Documents/Repositorios/Hackathon/Hacktoberfest-Axolutions-wt/hack-051
Worklog: worklog/WL-1793312785-dylan-1-HACK-051-hack.EEFv7O.md
Priority: P0
Paths: web/src/features/project/, web/public/demo-prototype/, app/services/pipeline.py, app/tests/test_pipeline_prototype.py
Depends: HACK-050
Verify: `uv run pytest -q && uv run ruff check app && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
Lease-Until: 1793315485
Updated: 1793312785
Task-Base: 45ebbf070bedf1c1d6d5f6783c4404fa89fa0149
Next: in pipeline `_produce`, allow stages 7-8 through `_provider` under DEMO_MODE; then the project card iframe.
PR: -
Evidence: -
