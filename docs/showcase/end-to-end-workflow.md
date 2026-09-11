# End-to-end workflow walkthrough

This walkthrough shows how the `ai-dev-team` plugin composes its existing
skills and agents around one realistic software-delivery task. It is an
**illustrative routing example**, not a benchmark result or a claim that a
specific repository was executed successfully.

## Scenario

A maintainer asks:

> Add CSV export to the reports module, keep tenant isolation intact, add tests,
> and leave the change ready for a safe production rollout.

That request crosses architecture, implementation, tests, security, review, and
release preparation. The goal of `ai-dev-team` is not to answer all of that
with one giant prompt. It decomposes the work into evidence-backed stages.

## 1. Recover the repository context

The first useful step is to understand the repository that actually exists.

Relevant workflow:

- `analyzing-codebase`
- optionally `repository-explorer`

Expected evidence:

- framework and package evidence from files that are actually present;
- the reports module and its call sites;
- current authorization / tenant-scoping mechanisms;
- test framework and test locations;
- deployment and CI surfaces.

The analysis should **not** claim a stack because it is common or because the
request mentions it. Stack claims must be tied to repository evidence.

Example outcome:

```text
Reports endpoint: server/modules/reports/*
Tenant boundary: request context -> tenantId -> repository query filter
Tests: Vitest integration tests under server/modules/reports/__tests__
Deployment: Docker image built in GitHub Actions
```

## 2. Turn the request into an implementation plan

Relevant workflow:

- `planning-implementation`
- optionally `solution-architect`

A useful plan identifies the smallest set of changes and names the risks before
code is written.

Example task packet:

```text
Goal:
  Add CSV export for the existing report result set.

Evidence:
  Existing report query is tenant-scoped by tenantId.
  Existing JSON export path already centralizes report filtering.

Constraints:
  Reuse the same tenant-scoped query.
  Do not create a second authorization path.
  Preserve the existing API response contract.

Validation:
  Unit test CSV serialization.
  Integration test export authorization and tenant isolation.
  Verify existing report tests remain green.
```

The plan should stay small enough that a reviewer can tell which evidence led to
which change.

## 3. Implement only the scoped change

Relevant workflow:

- `implementing-features`
- commonly `backend-engineer` for an API/export slice

The implementation agent receives the task packet rather than the entire project
history. That keeps the delegated context focused and makes the work easier to
review.

The agent should:

1. reuse the existing report-query path;
2. add only the CSV serialization / response behavior needed by the feature;
3. preserve tenant filtering;
4. avoid unrelated refactors;
5. stop and report if repository evidence contradicts the plan.

## 4. Add automated tests

Relevant workflow:

- `writing-automated-tests`
- `qa-engineer`

For this scenario, meaningful coverage would include:

- a normal CSV export;
- escaping / delimiter-sensitive values;
- an unauthorized request;
- tenant A being unable to export tenant B's report;
- a regression check that the existing non-CSV path still behaves as before.

The test workflow should use the test stack already present in the repository
instead of introducing a new framework merely for the feature.

## 5. Review the diff independently

Relevant workflow:

- `reviewing-code`
- `code-reviewer`

The review should inspect the resulting diff rather than repeat the original
plan. High-value questions include:

- Does the new path bypass the existing tenant filter?
- Is user-controlled CSV content escaped safely?
- Did the implementation duplicate authorization logic?
- Did the API contract change unintentionally?
- Do tests actually fail if tenant isolation is removed?

Findings should cite concrete files / lines or test evidence.

## 6. Run a security-focused pass

Relevant workflow:

- `auditing-security`
- `security-reviewer`

For this feature, the security pass is narrow:

- authorization and tenant isolation;
- CSV injection / spreadsheet-formula risks if exported data may be opened in
  spreadsheet software;
- accidental exposure of fields not present in the original report view;
- dependency changes, if any.

A security review should not invent vulnerabilities without evidence. If a
risk cannot be confirmed, it should be reported as a hypothesis or follow-up,
not as a finding.

## 7. Prepare the rollout without deploying

Relevant workflow:

- `planning-deployment`
- `release-manager`

The deployment workflow produces a plan, not an automatic production deploy.

Example rollout checks:

```text
Pre-deploy:
  - relevant tests green
  - no new migration required
  - API compatibility reviewed

Deploy:
  - normal application release path

Health checks:
  - existing reports still render
  - CSV export returns expected content type
  - tenant-isolation regression test remains green

Rollback:
  - revert the application release if export errors or authorization regressions appear
```

Any irreversible or production action still requires explicit user confirmation
under the shared safety baseline.

## 8. Make a release-readiness decision

Relevant workflow:

- `preparing-releases`

The final result should be a decision backed by current evidence:

- **GO** — required checks were actually run and passed;
- **CONDITIONAL GO** — known, bounded evidence is still missing;
- **NO-GO** — a blocking test, security, compatibility, or deployment issue remains.

The plugin should never turn “the code looks fine” into “ready for production”
without fresh verification.

## Why the composition matters

The same request touches several disciplines, but not every role needs the full
context. The orchestration model keeps each delegated task scoped, preserves the
shared evidence / safety rules, and lets the final review inspect concrete
artifacts rather than trusting a single long reasoning chain.

That is the central design goal of this marketplace: reusable software-delivery
workflows that are **installable, composable, evidence-driven, and reviewable**.

## Try the scenario

After installing the plugin, start with a repository you control and ask:

```text
Add CSV export to the existing reports module. Preserve the current authorization
and tenant-isolation behavior, add appropriate automated tests, review the change
for security and compatibility risks, and leave me a deployment plan. Do not
deploy anything.
```

The exact routing depends on the evidence found in that repository, which is
intentional. The plugin should adapt to the codebase rather than force the
codebase into a preset stack.
