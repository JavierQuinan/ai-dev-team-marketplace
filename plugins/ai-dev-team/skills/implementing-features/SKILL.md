---
name: implementing-features
description: Implements a feature or change end-to-end, respecting existing architecture, reusing existing components instead of duplicating them, updating tests, and validating build/lint/typecheck/tests before reporting completion. Use for the actual coding step, after planning-implementation for non-trivial changes.
when_to_use: Use for the IMPLEMENT stage of any change once scope is understood (directly for trivial changes, after planning-implementation for larger ones).
---

# Implementing features

Write the change against the codebase as it actually is, not a rewritten version of it. See [enforcing-safety-baseline](../enforcing-safety-baseline/SKILL.md) — nothing here is reported done without having just verified it.

## Workflow

1. **Orient in the target area.** Read the specific files you're about to change and their immediate neighbors (siblings, callers, tests) before writing — don't pattern-match from a different part of the codebase that may use different conventions.
2. **Search for reuse before writing new code.** Grep for existing utilities, components, or patterns that already do what's needed. Extending or calling existing code beats duplicating it; introducing a near-duplicate abstraction is a defect, not a shortcut.
3. **Implement following existing conventions** — naming, error handling style, layering, framework idioms already present in the codebase, not generic "best practice" that conflicts with local convention.
4. **Preserve backwards compatibility** unless the plan (or the request) explicitly calls for a breaking change — and if it does, make sure that's visible in the diff and the report, not buried.
5. **Update tests alongside the code**: extend existing test files for the module you touched; add new tests for new behavior; never leave a changed code path with stale or now-incorrect test expectations.
6. **Run the project's actual verification commands** — build, lint, typecheck, relevant test subset — using the commands `analyzing-codebase` found (`package.json` scripts, `Makefile`, CI config), not assumed generic ones.
7. **Fix everything the verification surfaces** that your change caused. Don't report "done" while your own change leaves the tree red.
8. **Report exactly what changed**: files touched, why, what was verified and how (command + result), and anything intentionally left out of scope.

## Decisions

- Existing code duplicates itself and the task touches it → fix the immediate task; only refactor the duplication if it's in the direct path of the change and small, otherwise flag it as a follow-up rather than expanding scope.
- Verification command is unknown or missing → check `analyzing-codebase` output or the manifest directly; don't invent a command that may not reflect the project's actual pipeline.
- A verification step can't be run in this environment (e.g. no browser, no DB access) → say so explicitly in the report; do not claim it passed.

## Exit criteria

- Build/lint/typecheck/tests relevant to the change were actually executed in this session, with their real output referenced in the report.
- No known error caused by this change is left unresolved without being called out.
- The report lists exactly what was modified — no vague "various improvements."
