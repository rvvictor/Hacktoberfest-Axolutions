# PROJECT · Hacktoberfest (sprint mode)

> Filled in by `/uak-setup` with the human at minute 0. uak reads the flat fields of the last block from
> the remote `main`, so a stale worktree can never change permissions.

## Event
| Field | Value |
|---|---|
| Event / challenge | Hacktoberfest: Hack Day in Mexico City, Build Day + Demos (MLH) · https://events.mlh.com/events/14760-hacktoberfest-hack-day-in-mexico-city-build-day-demos · challenge: TBD · product: SpeedHack (IDEA.md) |
| Start | 2026-10-27 15:30 America/Mexico_City |
| Official deadline | 2026-10-28 19:00 America/Mexico_City · platforms: probably the MLH event page (to be confirmed) |
| Freeze | 2026-10-28 14:52 (Freeze-Epoch 1793220750) · design lock Tue 16:30 · first claim by Tue 17:30 · walking skeleton Tue 17:30 · plan-B video Wed 05:15 |
| Clean rehearsal / plan B | 2026-10-28 17:00 |
| Internal submission | 2026-10-28 18:00 |
| Humans | Victor, Sebas, Dylan, Fer, Jabi (Jabi uses Codex; the rest Claude Code) · submission owner: Victor (starts at T−8 h) |
| Agents | victor-1, victor-2, sebas-1, sebas-2, dylan-1, dylan-2, fer-1, fer-2, jabi-1, jabi-2 · all are reviewers |
| Machines | `<laptop, Jetson…>` · ports already taken: `<8000…>` |

## Official rubric (weights sum to 100)
| ID | Criterion | Weight | Evidence in the demo |
|---|---|---:|---|
| C1 | TBD: official rubric not published yet | - | - |

## Event rules
| Topic | Confirmed rule | Source |
|---|---|---|
| AI use / prior code | AI allowed · prior code allowed | organizers (verbal) |
| Data and licenses | TBD | - |
| Format and video limits | TBD (video limit not announced yet) | - |

## Plan B
- A video of the whole flow at `<path>` (v1 at T−50%, final at T−2 h). Use it if `<network, mic, external API>` fails.

## Executable config
A human sets `yes`. A missing field means `no`.

```text
Mode: sprint
Backlog-Proposed-Epoch: 0
Backlog-Approved: yes
Autonomy: yes
Auto-Merge: yes
Review-Mode: claims
Plan-Channel: claims
Freeze-Epoch: 1793220750
Lease-Seconds: 2700
Review-Lease-Seconds: 14400
Events-Per-Session: 100
Checkpoint-Percent: 60
Merge-Lease-Seconds: 1800
Merge-Wait-Seconds: 180
Merge-Adopt-Seconds: 300
Max-Parallel-Subagents: 4
Opus-Subagents-Per-Session: 2
Pace: auto
Subagent-Hard-Cap: 6
Strong-Hard-Cap: 3
Subagents-Per-Session: 40
Subagents-Per-Machine: 8
Subagent-Burst-Per-Minute: 6
Max-Worktree-Agents: 6
Blackbox: on
Additive-Paths: -
```
