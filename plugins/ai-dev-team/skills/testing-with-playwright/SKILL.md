---
name: testing-with-playwright
description: Writes and runs Playwright end-to-end tests using the project's existing config and fixtures, prioritizing resilient selectors and real assertions over sleeps, and distinguishing test bugs from application bugs from environment failures. Use when asked to test a flow with Playwright, add E2E coverage, or verify a user journey end-to-end.
when_to_use: Use for E2E test creation, running, or triage whenever a project has (or should have) Playwright coverage — "prueba todo con Playwright", "add E2E tests for X", "test the login flow".
---

# Testing with Playwright

Extend the project's actual Playwright setup rather than inventing a parallel one. See [enforcing-safety-baseline](../enforcing-safety-baseline/SKILL.md) for the evidence rule this skill leans on hardest: a test result is only real once it has actually run.

## Workflow

1. **Discover existing setup.** Read `playwright.config.*`, existing `tests/`/`e2e/` structure, fixtures, page objects, and helper utilities already in use. Match the existing patterns instead of introducing a new style.
2. **Reuse fixtures and helpers** for auth, test data setup/teardown, and navigation instead of duplicating that logic per test.
3. **Prefer resilient selectors**: role/label/text-based locators (`getByRole`, `getByLabel`, `getByText`) over brittle CSS/XPath tied to implementation details, unless the project's existing convention already uses `data-testid` — then follow that convention.
4. **Never use arbitrary sleeps.** Use Playwright's built-in waiting (auto-waiting assertions, `waitForResponse`, `waitForURL`) instead of `waitForTimeout` as a synchronization mechanism.
5. **Cover the happy path** for the requested flow, then the relevant error/edge cases (invalid input, permission denied, empty states) — not exhaustive combinatorics, just what's realistically load-bearing.
6. **Check multi-tenant isolation when applicable**: if the flow touches tenant-scoped data, add a negative test proving user/tenant A cannot see or act on tenant B's data — don't assume isolation, prove it.
7. **Run the tests.** Execute the actual Playwright command (`npx playwright test ...` or the project's script) — never report results without running them. Capture evidence: failure screenshots/traces Playwright already generates, or explicit pass/fail output.
8. **Triage failures** before touching anything:
   - **Application bug** — the app genuinely does the wrong thing → hand off to `debugging-systematically`, don't just patch the test to match broken behavior.
   - **Test bug** — flaky/brittle test, wrong selector, wrong assertion → fix the test.
   - **Environment failure** — dev server not running, missing seed data, port conflict → fix the environment, report it as such.
9. **Report** what ran, pass/fail counts, and root cause for any failure — never "tests probably pass" or "should work now."

## Decisions

- No Playwright config exists yet but E2E coverage is requested → check whether Playwright is the right tool for this project (see `stack-detection.md`) before scaffolding a new config; confirm with the user if another E2E tool is already in use.
- A flaky test is found unrelated to the current task → report it, don't silently rewrite unrelated test infrastructure without being asked.

## Exit criteria

- Every test added was actually executed at least once in this session, with the real result reported.
- Failures are classified (app/test/environment) with the reasoning, not just re-run until green.
- No `waitForTimeout`-as-synchronization was introduced.
