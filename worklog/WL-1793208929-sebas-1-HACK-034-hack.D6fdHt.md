# worklog/WL-1793208929-sebas-1-HACK-034-hack.D6fdHt.md · HACK-034

## Live summary
- Done: run view guards JSON.parse on events without data; build + design-lint pass; browser check: 2 'undefined is not valid JSON' page errors without fix, 0 with it
- Decision: same guard as delivery listen()
- Why: browser error event has no data when the stream closes
- Failing: -
- Commands: q npm --prefix web run build; q design-lint
- Next: PR + done

## History
- 1793208929 | CLAIMED | sebas-1 | claim; next: Implement HACK-034 and run: `npm --prefix web run build && bash .uak/bin/design-lint`
- 1793209191 | CLAIMED | sebas-1 | checkpoint; next: PR + done
