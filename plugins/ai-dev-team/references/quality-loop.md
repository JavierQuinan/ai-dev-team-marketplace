# Quality loop

This reference defines semantic coordination, not a deterministic runtime or a replacement for repository tests.

## Acceptance matrix

Before TEST, map each material acceptance criterion to an ID, source (task/design/API contract), test level, positive/negative case, owner and required check. Reuse existing tools. Record exact command, target revision/worktree state, observed exit status, evidence reference and PASS/FAIL/BLOCKED/INCONCLUSIVE/NOT RUN. A skipped required check is not a pass; a green unrelated suite is not coverage.

## Findings ledger

Assign stable finding IDs; retain original severity (BLOCKER/HIGH/MEDIUM/LOW/NIT), evidence and concrete trigger, affected scope, owner, required/optional disposition, verification criteria and status (open/fixed-verified/deferred). Security confidence classification is separate from severity. A fix without verification remains open. Deduplicate by root cause, not by suppressing independent findings. An explicit deferral records human decision, residual risk and owner; it does not make the finding pass or authorize release with unresolved required blockers.

## Bounded loop

1. TEST and REVIEW with one primary executor per stage; independent code/security review only where applicable. Security is mandatory for authorization, tenancy, payments, secrets and supply-chain surfaces.
2. Triage application/test/environment failures; preserve failing evidence. Never weaken assertions to conceal a defect.
3. FIX only reversible in-scope findings. Assign one writer, record changed paths and link finding IDs. Default budget: at most three repair rounds per run; honor a lower user budget. A round is a batch of scoped fixes followed by verification. No implicit budget extension.
4. VERIFY reruns the failing checks and affected regression checks against the changed state. Targeted re-review by the relevant reviewer when a finding requires it; this is not a duplicate initial review. Record evidence for the actual post-fix state.
5. Stop when required checks pass and required findings are fixed-verified, or when the budget is exhausted, no progress is possible, or a material safety/scope boundary is reached. Report remaining findings as unresolved. No successful completion or GO with missing required evidence.
6. Escalate before irreversible actions, dependency additions, material scope changes, destructive migrations, production access or secrets operations. Never merge or deploy via this loop.

## Reporting

List acceptance matrix, findings ledger, rounds and changed paths, commands/results, required checks not run, residual risks and human actions. Distinguish task completion from release readiness. If evidence is stale after a change, mark it stale and rerun affected checks. Static eval definitions are not runtime evidence.
