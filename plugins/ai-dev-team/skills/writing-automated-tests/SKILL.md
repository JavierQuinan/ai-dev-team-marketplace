---
name: writing-automated-tests
description: Authors and reviews unit and integration tests — test-gap analysis, coverage strategy, and regression tests for bug fixes — using the project's existing test framework. Explicitly not E2E/browser testing (that's testing-with-playwright). Use when asked to write unit or integration tests, analyze test coverage gaps, or add a regression test for a bug.
when_to_use: USE for unit/integration test authoring, gap analysis, coverage strategy, or regression tests — "escribe tests unitarios para...", "añade tests de integración...", "cubre este bug con un regression test", "qué falta probar aquí", "revisa la cobertura de tests", "testea esta función", "agrega casos edge", "necesitamos unit/integration tests". NOT USE for anything naming Playwright, E2E, browser, or a user-journey flow — that always stays with `testing-with-playwright`, never duplicated here; also NOT USE for plain debugging with no test-authoring ask, or a bare "run the tests" request that needs no new authoring or gap analysis.
---

# Writing automated tests

Unit and integration tests only — E2E/browser/user-journey work belongs to [testing-with-playwright](../testing-with-playwright/SKILL.md); a request naming Playwright explicitly always routes there, never absorbed here. See [enforcing-safety-baseline](../enforcing-safety-baseline/SKILL.md): a test result is only real once it actually ran in this session.

## Workflow

1. **Discover the test stack.** Read package manifests, test config, existing test directories, naming conventions, fixtures/factories/helpers/mocks, and CI test scripts. Detect the framework in use (Jest, Vitest, Pytest, PHPUnit, JUnit, etc.) — never assume, and never introduce a second test framework alongside one that already exists.
2. **Identify the behavior under test**: what must keep working, inputs/outputs, boundaries, dependencies, permission/tenant behavior, and — for a bug fix — the actual failure being fixed. Don't write a test that just mirrors the implementation line-by-line.
3. **Choose the test level.** Unit: behavior isolates cleanly with small, controllable dependencies. Integration: the behavior that matters depends on real collaboration across a boundary — a DB adapter, an HTTP boundary, a queue, a repository, serialization/persistence. Never call a test "integration" when it mocks every boundary that would make it one. E2E/browser flows redirect to `testing-with-playwright` instead of being written here.
4. **Do a test-gap analysis** before adding anything: happy path, boundary values, empty/null/error conditions where they apply, authorization/permissions, tenant isolation where applicable, the regression path, state transitions, idempotency/concurrency where material. Prioritize load-bearing behavior over combinatorial completeness.
5. **Author**, following existing conventions. Prefer behavioral assertions against public contracts and observable outcomes. Avoid asserting on private implementation details, fragile call-count checks with no real reason, snapshot abuse, mocks that just restate the implementation, and arbitrary sleeps as synchronization.
6. **Decide what to mock.** Mock only a dependency that's external, non-deterministic, slow/costly, or outside the test's boundary. For integration tests, prefer a real or disposable dependency over mocking the very boundary the test exists to exercise — a suite that mocks the whole persistence/API boundary and calls itself "integration coverage" is misrepresenting what it verifies.
7. **For a bug fix, prefer red→green evidence**: show the new test fails against the pre-fix code, then passes after the fix. If the pre-fix state can't actually be reproduced and shown failing, say so explicitly — never fabricate a red-then-green narrative.
8. **Run every test written**, and report the real pass/fail result. On failure, classify before touching anything: **application bug** (the code is genuinely wrong — fix the code, don't weaken the test), **test bug** (wrong assertion/setup — fix the test), or **environment failure** (missing fixture, no DB access — fix or report the environment). Never loosen an assertion just to turn a real failure green.

## Coverage philosophy

Coverage exists to find unexercised code, not as a quality metric to chase. When asked for a "coverage strategy," prioritize critical behavior, financial/security boundaries, authorization, tenant isolation, error handling, and state transitions — never recommend "100% coverage" as a default target.

## Multi-tenant systems

A happy-path test for tenant A alone is not sufficient. Include at least one negative test proving tenant A cannot read, modify, or act on tenant B's data through the actual boundary being tested — not asserted in the abstract.

## Decisions

- The project already has a test framework → extend it; introducing a second one is a defect, not a shortcut, even if you'd prefer a different tool.
- A request explicitly names Playwright, E2E, or a browser/user-journey flow → hand off to `testing-with-playwright` entirely; don't author a partial E2E-shaped test here.
- A suite passes but mocks out the entire boundary an "integration test" claims to cover → flag it as not real integration coverage, don't accept it at face value.
- A regression test's pre-fix failure can't be reproduced in this environment → state that limitation explicitly rather than presenting an assumed red-then-green result.
- The request is a bare "run the tests" with no authoring or gap-analysis ask → that's within `implementing-features`'s own verification step, not a reason to invoke this skill.

## Exit criteria

- Every test written in this session was actually executed, with the real result reported.
- A failure is classified (application bug / test bug / environment failure) before any fix is applied.
- No assertion was weakened to force a failing test green.
- A claimed regression test either demonstrates red→green or explicitly states why the pre-fix state couldn't be reproduced.
- No E2E/browser test was authored here instead of being routed to `testing-with-playwright`.
