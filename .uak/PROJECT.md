# PROJECT · SpeedHack (marathon mode)

> The project constitution. Humans change it by reviewed PR. uak reads the last block from the remote `main`.
> Switched from sprint (Hacktoberfest Hack Day CDMX, 2026-10-27/28) to marathon on 2026-10-29: SpeedHack is now
> Dylan's own product, maintained by one human. The event's dates, rubric, team roster and plan B are in git history.

## Purpose
For technical founders and small businesses without a digital presence who split the path from an idea to a
defensible pitch across tools that share no context: SpeedHack turns one idea into cited research, a plan, a Miro
architecture, a Linear backlog, a working prototype it builds itself, and a pitch with Q&A, on one thread of context
(`IDEA.md` §1–§2). Measurable outcome: `<to define by Dylan>`.

## Non-negotiable principles
1. Secure and private by default: least privilege, personal data encrypted and minimized.
2. Nothing reaches `main` without green CI, a passing merge gate and another identity's approval (agents review on claims; the gate merges approved tasks, Auto-Merge: yes since 2026-10-30).
3. Every decision that is costly to reverse has an ADR in `docs/adr/`.
4. The LLM never produces figures: prices and features come from research with their URL, LLM output is
   validated against a schema before it is used, and anything simulated or recorded carries `demo_data: true`.

## Non-functional requirements (measurable)
Targets are not set yet; Dylan defines them before the first public launch. No agent fills these in.
| Attribute | Target | Measured by |
|---|---|---|
| Latency | `<to define>` (today: the prototype stage takes ~2.5 min with gemma-4-26b) | `<to define>` |
| Availability | `<to define>` | `<to define>` |
| Data | RPO `<to define>` · RTO `<to define>` (today: one local SQLite file under `DATA_DIR`) | `<to define>` |
| Frontend | `<to define>` | `<to define>` |
| Coverage | `<to define>` | `<to define>` |
| Cost | `<to define>` per run (Gemini, Tavily, Firecrawl, Miro, Linear) | provider billing |

## Environments and ownership
| Env | URL | Deploys | Secrets in |
|---|---|---|---|
| dev | local (`DEMO_MODE=1` without keys) | `uv run uvicorn app.main:app` | `.env` (git-ignored) |
| prod | none yet | `<to define>` | `<to define>` |

CODEOWNERS: Dylan (all paths) · On-call: Dylan · Runbook: `docs/runbook.md` (not written yet).

## Executable config
```text
Mode: marathon
Backlog-Proposed-Epoch: 0
Backlog-Approved: yes
Autonomy: yes
Auto-Merge: yes
Review-Mode: claims
Plan-Channel: main
Freeze-Epoch: 0
Lease-Seconds: 14400
Review-Lease-Seconds: 86400
Events-Per-Session: 150
Checkpoint-Percent: 60
Merge-Lease-Seconds: 1800
Merge-Wait-Seconds: 180
Max-Parallel-Subagents: 3
Opus-Subagents-Per-Session: 4
Pace: auto
Subagent-Hard-Cap: 4
Strong-Hard-Cap: 4
Subagents-Per-Session: 30
Subagents-Per-Machine: 6
Subagent-Burst-Per-Minute: 6
Max-Worktree-Agents: 4
Blackbox: on
Additive-Paths: -
```
