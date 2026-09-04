# DevSecOps / supply-chain reference

Deep patterns for `auditing-security`'s DevSecOps dimension, loaded only when a dependency/supply-chain/CI-security audit is actually in scope. This project never builds its own CVE database or SAST engine — real vulnerability data always comes from real ecosystem tools; this reference is about *interpreting* their output and the deterministic signals from `scripts/devsecops-inventory.mjs` correctly, not replacing them.

## Real-tool matrix by ecosystem

Use whichever tool the project's own lockfile indicates; don't default to one tool for every project.

| Evidence | Ecosystem | Real audit tool(s) | Notes |
|---|---|---|---|
| `package-lock.json` | npm | `npm audit` | Add `--omit=dev` to scope to production deps if relevant. |
| `pnpm-lock.yaml` | pnpm | `pnpm audit` | |
| `yarn.lock` | Yarn | `yarn npm audit` | Modern Yarn (Berry) syntax; classic Yarn uses `yarn audit`. |
| `poetry.lock` / `uv.lock` | Python | `pip-audit`, `osv-scanner` | `pip-audit` needs the environment's installed packages or a requirements export. |
| `requirements.txt` alone | Python | `pip-audit -r requirements.txt` | Works directly against the manifest without an installed env. |
| `Cargo.lock` | Rust | `cargo audit` | Requires the `cargo-audit` subcommand to already be installed — don't install it yourself. |
| `go.sum` | Go | `govulncheck ./...` | Checks actual call-graph reachability, not just presence — closer to exploitability than most SCA tools. |
| `Gemfile.lock` | Ruby | `bundler-audit` | |
| Any/unknown | Cross-ecosystem fallback | `osv-scanner` | Works from lockfiles directly for several ecosystems without installing a package-manager-specific tool. |

None of these get installed automatically. If the tool isn't already available in the environment, report dependency vulnerabilities as **NOT VERIFIED** and name exactly which tool would have been used.

## GitHub Actions supply-chain checklist

- **Pinning**: an action referenced by tag (`@v4`) or branch (`@main`) can start pointing at different code the moment the tag/branch moves, without the consuming repo's history showing anything changed. A full 40-character commit SHA is immutable. Third-party actions (not `actions/*` or another org-trusted namespace) are higher priority to pin than first-party ones, but both benefit from it.
- **`pull_request` vs. `pull_request_target`** — the security-relevant distinction:
  - `pull_request` runs with a read-only, fork-scoped token and no access to the base repo's secrets by default — safe to check out and run the PR's own code.
  - `pull_request_target` runs with the **base repository's** token and secrets, *even for a fork PR* — its intent is to let maintainers safely comment/label without exposing secrets to fork code, on the assumption the workflow never runs fork-controlled code with that elevated context.
  - The dangerous combination is `pull_request_target` **plus** a step that checks out the PR's head ref (`actions/checkout` with `ref: ${{ github.event.pull_request.head.sha }}` or similar) **plus** that checked-out code being executed (build script, test run, lint with a repo-provided config file) **while secrets or write permissions are available in the same job**. That combination lets a fork PR's own code run with the base repo's credentials. Trace all three conditions before calling this exploitable — `pull_request_target` alone is a review signal, not a finding.
- **Permissions**: the least-privilege default is `permissions: contents: read` (or narrower) at the workflow level, with any broader grant (`pull-requests: write`, `issues: write`, `id-token: write` for OIDC, etc.) scoped to the specific job that needs it, not the whole workflow. `write-all` is almost never actually needed. No explicit `permissions:` block means the effective permissions come from the repository/organization's default setting, which isn't visible from the workflow file alone — say so rather than assuming either a safe or unsafe default.
- **Third-party actions**: an action outside a well-known first-party namespace runs arbitrary code with the job's permissions and secret access. Unpinned third-party actions are a materially higher-priority finding than unpinned first-party ones.
- **Install/build scripts**: a `postinstall` script (npm), a `Makefile` target, or any build step invoked from CI runs with the CI job's access — the same supply-chain trust question applies to what a dependency's install script does as to what the workflow's own steps do.

## Lockfile / reproducibility interpretation

A manifest without a corresponding lockfile means dependency versions aren't pinned at install time — two installs on two machines (or two days apart) can resolve different transitive versions, which undermines both reproducibility and the meaningfulness of a point-in-time audit. This is a supply-chain **hygiene** signal, not a vulnerability by itself. Different ecosystems have different conventions (a bare `requirements.txt` with `==` pins is a legitimate, lockfile-less pattern in Python) — don't apply one ecosystem's lockfile convention to another.

## Dependency advisory vs. exploitability

A real tool reporting "package X\<version> has a known advisory" means exactly that: **confirmed advisory match / known-vulnerable version installed.** It does not by itself mean this application is exploitable through it. To move from advisory match to a likely/confirmed application-level finding, trace:

1. **Reachability** — is the vulnerable code path actually invoked by this application (a vulnerable function called, a vulnerable transitive feature enabled), or is the dependency present but the affected code path unused?
2. **Attacker control** — can externally-controlled input reach that code path?
3. **Impact in this context** — does the advisory's stated impact (e.g. a ReDoS in a rarely-called formatting function) actually matter for how this specific application uses the dependency?

Report the advisory match itself as **Dependency advisory** (always worth surfacing — even an unreachable vulnerable dependency is a supply-chain liability). Only escalate to **Confirmed vulnerability** once reachability and attacker control are actually traced in this codebase, and to **Likely vulnerability** when the trace is strongly suggestive but incomplete. Never present "advisory exists" as "exploitable in this app" without doing that tracing.

## Safe secret scanning

Prefer a real tool already available in the environment (`gitleaks`, `trufflehog`, a repo-provided pre-commit secret scanner) over ad hoc pattern matching — they carry maintained rule sets and lower false-positive rates. Don't install one automatically. Without a real scanner, a more limited, evidence-driven inspection (tracked filenames matching credential-shaped patterns, obvious hardcoded-looking assignments actually read in code review) is still worth doing, but state explicitly that a full secret scan was **not verified** rather than implying the limited check was equivalent to one. Never print, log, or quote a discovered secret's value in full — flag file and location only, exactly as `enforcing-safety-baseline` already requires for any secret found during any other kind of review.

## Docker hardening quick signals

Deterministic, low-noise checks only — this project is not building a Docker-hardening skill:

- No `USER <non-root>` instruction → the image runs as root by default; a hardening recommendation, not an automatic finding (some images legitimately need root for their entrypoint).
- A `COPY`/`ADD` of the entire build context (`COPY . .`) early in the Dockerfile defeats layer caching and can copy secrets/`.env` files into the image if they aren't excluded via `.dockerignore` — worth checking whether a `.dockerignore` exists and covers sensitive files, without reading their contents.
- Base image pinned to a mutable tag (`node:latest`, `python:3`) rather than a specific version (and, ideally, a digest) is the same supply-chain concern as an unpinned GitHub Action, applied to the image itself.
