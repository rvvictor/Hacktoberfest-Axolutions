# HACK-052
ID: HACK-052
State: REVIEW
Owner: dylan-1
Branch: feat/hack-052
Worktree: /Users/dylanmartinezcastillo/Documents/Repositorios/Hackathon/Hacktoberfest-Axolutions-wt/hack-052
Worklog: worklog/WL-1793314866-dylan-1-HACK-052-hack.TrUnr5.md
Priority: P1
Paths: web/src/features/project/, web/public/demo-prototype/, app/services/pipeline.py, app/tests/test_pipeline_prototype.py
Depends: HACK-051
Verify: `uv run pytest -q && uv run ruff check app && npm --prefix web run build && bash .uak/bin/design-lint && uv run python e2e/judge_path.py`
Lease-Until: 1793329382
Updated: 1793314982
Task-Base: 1dc8d86b84b46aeacce86522623cc78411e7ec36
Next: Humano: Base moved; revalidate the candidate
PR: https://github.com/rvvictor/Hacktoberfest-Axolutions/pull/54
Evidence: -
