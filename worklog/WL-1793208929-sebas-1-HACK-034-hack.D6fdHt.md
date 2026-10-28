# worklog/WL-1793208929-sebas-1-HACK-034-hack.D6fdHt.md · HACK-034

## Live summary
- Done: q npm --prefix web run build -> OK built; q design-lint -> DESIGN_LINT_PASS; browser check on a finished run: without fix 2 page errors '"undefined" is not valid JSON', with fix PASS no page errors
- Decision: same guard as delivery listen()
- Why: browser error event has no data when the stream closes
- Failing: -
- Commands: q npm --prefix web run build; q design-lint
- Next: Integrated in main: 63e4e837a08d7197b870c8b772c102fa53a66330

## History
- 1793208929 | CLAIMED | sebas-1 | claim; next: Implement HACK-034 and run: `npm --prefix web run build && bash .uak/bin/design-lint`
- 1793209191 | CLAIMED | sebas-1 | checkpoint; next: PR + done
- 1793209269 | REVIEW | sebas-1 | done; PR https://github.com/rvvictor/Hacktoberfest-Axolutions/pull/31; evidence: q npm --prefix web run build -> OK built; q design-lint -> DESIGN_LINT_PASS; browser check on a finished run: without fix 2 page errors '"undefined" is not valid JSON', with fix PASS no page errors; reviewer: -
- 1793213689 | REVIEW | fer-2 | review; approve; SHA a5d3a1ff7eb190320dd354e6093fb84749a8ed82; reviewer fer-2
- 1793215826 | INTEGRATED | jabi-1 | merge; smoke and Verify PASS; commit 63e4e837a08d7197b870c8b772c102fa53a66330; reviewer fer-2
