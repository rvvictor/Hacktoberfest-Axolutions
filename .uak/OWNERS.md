# Shared-file owners

One writer per shared file. Others ask the owner with `uak msg ID --kind request`. Patterns are relative, with no spaces; directories end in `/`.
An owner is not a prerequisite for everyone: consumers work on published contracts and mocks. To transfer ownership, open a PR to main.

| Pattern | Owner task |
|---|---|
| pyproject.toml | HACK-001 |
| uv.lock | HACK-001 |
| .env.example | HACK-001 |
| Dockerfile | HACK-069 |
| render.yaml | HACK-069 |
| web/package.json | HACK-001 |
| web/package-lock.json | HACK-001 |
| app/main.py | HACK-001 |
| app/config.py | HACK-001 |
| web/src/App.tsx | HACK-046 |
| web/src/main.tsx | HACK-046 |
| web/src/lib/api.ts | HACK-001 |
| web/src/lib/sse.ts | HACK-001 |
| .github/workflows/ | HACK-001 |
| .uak/PROJECT.md | HACK-001 |
| app/schemas/ | HACK-050 |
| app/fixtures/demo/ | HACK-053 |
| web/src/lib/types.ts | HACK-050 |
| web/src/lib/mock.ts | HACK-002 |
| web/DESIGN.md | HACK-003 |
| web/src/styles/ | HACK-003 |
| web/src/lib/ui/ | HACK-003 |
