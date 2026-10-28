# worklog/WL-1793208792-sebas-2-HACK-032-hack.cI6gdJ.md · HACK-032

## Live summary
- Done: intake POSTs answers for real runs; offline sample only via Ver demostracion; Verify green; browser before FAIL / after PASS
- Decision: offline flag separate from demo_data badge
- Why: demo_data is true for real runs under DEMO_MODE, so it cannot signal the offline sample
- Failing: before fix: no POST, run stuck at stage 2 pending awaiting=answers (judge_intake.py FAIL)
- Commands: bash .uak/bin/q npm --prefix web run build; bash .uak/bin/q bash .uak/bin/design-lint; judge_intake.py 8420
- Next: open PR, uak done

## History
- 1793208792 | CLAIMED | sebas-2 | claim; next: Implement HACK-032 and run: `npm --prefix web run build && bash .uak/bin/design-lint`
- 1793209299 | CLAIMED | sebas-2 | checkpoint; next: open PR, uak done
