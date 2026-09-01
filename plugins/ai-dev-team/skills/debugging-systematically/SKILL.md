---
name: debugging-systematically
description: Debugs an issue through reproduction, isolation, root-cause hypothesis and verification before applying a fix, instead of trial-and-error. Use when something is broken — "the login stopped working", a failing test, an error report, unexpected behavior.
when_to_use: Use whenever behavior contradicts expectation and the cause isn't already obvious from the error message alone.
---

# Debugging systematically

Find the actual cause before changing code. A fix applied without a confirmed cause is a guess that may reappear or mask the real problem. See [enforcing-safety-baseline](../enforcing-safety-baseline/SKILL.md) — an environment-repair step (e.g. resetting local state to isolate a failure) still requires confirmation before anything irreversible, and a fix is never reported working without having just re-verified it.

## Workflow

```
REPRODUCE → ISOLATE → HYPOTHESIZE → VERIFY → FIX → REGRESSION TEST
```

1. **REPRODUCE.** Get the failure happening under your own control — run the failing test, hit the broken endpoint, execute the reported steps. If it can't be reproduced, say so and gather more information (exact steps, environment, recent changes) rather than guessing at a fix for something unconfirmed.
2. **ISOLATE.** Narrow the failure to the smallest surface that still reproduces it: which layer (frontend/backend/DB), which function, which input. Use logs, breakpoints, `git bisect`, or targeted test runs — not broad speculative edits.
3. **HYPOTHESIZE.** State a specific, falsifiable cause ("the query doesn't filter by tenant_id, so it returns cross-tenant rows") — not a vague one ("something's wrong with auth").
4. **VERIFY.** Confirm the hypothesis with evidence — read the exact code path, add a temporary log/assertion, or write a minimal failing test that isolates just that cause — before writing the fix. If verification disproves the hypothesis, form a new one; don't patch around an unconfirmed guess.
5. **FIX.** Apply the smallest change that addresses the confirmed root cause. Avoid large refactors in the same pass unless the root cause genuinely requires structural change — bundle unrelated cleanup separately.
6. **REGRESSION TEST.** Add or update a test that fails before the fix and passes after it, then run the broader relevant suite to confirm nothing else broke. Report the original repro now failing to reproduce, with evidence.

## Distinguishing failure types

Before fixing anything, determine which of these you're looking at — the fix differs completely:

- **Application bug** — the code under test genuinely misbehaves. Fix the code.
- **Test bug** — the test asserts the wrong thing, uses stale fixtures, or is flaky by construction (timing, order-dependence). Fix the test, not the app.
- **Environment failure** — missing env var, unavailable service, version mismatch, dirty local state. Fix the environment/setup, not the code.

Never "fix" a real bug by loosening a test's assertion, and never rewrite application logic to work around what is actually a broken test or environment.

## Decisions

- Root cause implicates a wide refactor → fix the immediate bug first with a regression test, then propose the refactor separately rather than expanding the current fix.
- Cause cannot be confirmed with available tools/access → report the leading hypothesis explicitly as unconfirmed rather than shipping a speculative fix.

## Exit criteria

- The original reproduction step, re-run, no longer fails — shown, not claimed.
- A regression test exists that would have caught this bug.
- The report states the confirmed root cause, not just "fixed it."
