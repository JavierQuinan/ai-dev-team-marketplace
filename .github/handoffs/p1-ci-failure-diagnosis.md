# P1 CI-failure diagnosis — implementation handoff

Issue: #25
Base SHA: `ce65381cb52c54ce618c6c43343f58e93a6d7d12`
Branch: `feat/p1-ci-failure-diagnosis`

## Objective

Implement the focused, evidence-driven CI-failure diagnosis reference for the existing `debugging-systematically` skill. Do not create a new top-level skill or agent.

## Owned scope

Expected implementation surface:

- `plugins/ai-dev-team/skills/debugging-systematically/SKILL.md`
- `plugins/ai-dev-team/references/ci-failure-diagnosis.md`
- `tests/evals/debugging-systematically.json`
- validation/test files only if repository evidence proves they must change

Do not include Issue #26, frontend reference work, delegation/right-sizing changes, API-contract changes, or unrelated refactors.

## Required behavior

The reference must:

1. treat GitHub Actions failure logs (including `gh run view --log-failed`) as evidence, not infallible truth;
2. distinguish deterministic test/build failures, dependency/setup failures, timeouts, and infrastructure/transient failures;
3. require concrete log evidence before asserting root cause;
4. distinguish a diagnostic rerun from a rerun that merely hides a deterministic failure;
5. remain stack-agnostic and provider-aware while keeping this slice GitHub Actions focused;
6. define insufficient-evidence behavior: gather more evidence instead of fabricating a diagnosis.

## Required eval coverage

Add at least these scenarios to `tests/evals/debugging-systematically.json`:

- deterministic test failure;
- missing dependency/tooling failure;
- transient runner/network failure;
- insufficient evidence / no premature diagnosis.

Include negative assertions that prevent unsupported root-cause claims and inappropriate rerun recommendations.

## Validation gates

Before declaring READY:

- run the repository validator;
- run Python validator tests;
- run DevSecOps inventory tests;
- run strict Claude plugin validation for the root and `plugins/ai-dev-team`;
- run any eval/static validation already defined by the repository;
- run `git diff --check`;
- verify the final diff contains only the owned scope.

Report exact commands, pass/fail counts, final HEAD SHA, and any limitation that was not runtime-validated.

## Stop conditions

Stop and report instead of broadening scope if:

- implementing #25 requires changing an unrelated skill/agent contract;
- existing tests expose a pre-existing failure unrelated to this branch;
- a provider-specific assumption would be presented as stack-agnostic fact;
- the requested behavior cannot be supported by repository evidence.

Do not merge the PR. Leave it reviewable with evidence for an independent reviewer.
