---
name: auditing-security
description: Performs an AppSec review (authentication, authorization, IDOR, tenant isolation, RLS, injection, XSS, CSRF, SSRF, secrets, crypto, upload handling, rate limiting, OWASP Top 10 / API Security Top 10) and a DevSecOps/supply-chain review (dependency/SCA via real ecosystem tools, GitHub Actions CI security, lockfile reproducibility, secret-scanning depth) — without destructive testing and without building a homegrown vulnerability scanner. Use when asked to audit security, review multi-tenant isolation, assess a change for security risk, audit dependencies, or review CI/supply-chain security.
when_to_use: Use for security-focused review, before releases touching auth/data/tenancy, or whenever asked to "audita seguridad", "check for vulnerabilities", "review multi-tenant isolation", "revisa dependencias vulnerables", "audita el supply chain", "revisa la seguridad de este pipeline/CI", "audita GitHub Actions". A request can be AppSec-only, DevSecOps-only, or both — scope to what's actually asked rather than always running the full combined audit.
---

# Auditing security

Analyze for real, evidenced risk — never run destructive or intrusive tests against systems you don't have explicit authorization to test that way. See [enforcing-safety-baseline](../enforcing-safety-baseline/SKILL.md) for the shared safety policy this skill enforces most strictly.

## Areas to analyze (as applicable to the code in scope)

- **Authentication** — session/token handling, password storage (hashing algorithm, no plaintext), MFA bypass paths, token expiry/revocation.
- **Authorization** — every privileged action checks the caller's actual permission, not just that they're logged in; no client-side-only authorization.
- **IDOR** — object references (IDs in URLs/bodies) are checked against the caller's ownership/tenant before use, not trusted as-is.
- **Tenant isolation / RLS** — every query touching tenant-scoped data is scoped correctly; for Postgres/Supabase, RLS policies exist and actually restrict by tenant (read the policy, don't assume it's correct because it exists).
- **Injection** — SQL/NoSQL/command injection: parameterized queries vs. string concatenation, unsafe `eval`/`exec`.
- **XSS** — unescaped user input rendered in HTML/JS contexts, unsafe use of `dangerouslySetInnerHTML`/`innerHTML`/`v-html`.
- **CSRF** — state-changing endpoints protected by tokens or same-site cookies where relevant.
- **SSRF** — server-side requests built from user-controlled URLs without allowlisting.
- **Secrets** — hardcoded credentials/keys in code or config, secrets logged, `.env` committed.
- **Crypto misuse** — weak algorithms (MD5/SHA1 for passwords), predictable IVs/nonces, home-rolled crypto.
- **Insecure storage** — sensitive data unencrypted at rest where it shouldn't be.
- **Upload handling** — file type/size validation, path traversal on stored filenames, served uploads not executable.
- **Rate limiting** — auth and other abuse-prone endpoints have some throttling.
- **Dependency risk** — known-vulnerable dependency versions (check lockfile against advisories if tooling allows).
- **Insecure defaults / privilege escalation** — default configs that are open, roles that can grant themselves more access.
- **Sensitive data in logs** — PII, tokens, or credentials written to logs.

## DevSecOps / supply-chain (second dimension, not a separate skill)

A distinct area of this same skill — application security above analyzes *what the code does*; this analyzes *what the codebase depends on and how it ships*. Never build a homegrown CVE database, SAST engine, or version-hardcoded "X is vulnerable" heuristic here — see `references/devsecops-security.md` for the full real-tool matrix, the `pull_request`/`pull_request_target` security model, and advisory-vs-exploitability tracing; load it only when a DevSecOps-scoped request is actually in progress.

1. **Run the bundled deterministic inventory** when dependency/supply-chain/CI-security posture is in scope: `node "${CLAUDE_PLUGIN_ROOT}/scripts/devsecops-inventory.mjs" --root "${CLAUDE_PROJECT_DIR}" --json`. Always use these two portable variables, never a hardcoded or relative path — `${CLAUDE_PLUGIN_ROOT}` for the packaged script, `${CLAUDE_PROJECT_DIR}` for the repo being audited. This script is read-only/offline/deterministic and reports **signals**, never vulnerabilities — treat its `signals` array as leads to inspect, not conclusions.
2. **Audit dependencies with real tools.** Detect the project's actual ecosystem/lockfile and use the matching real tool (`npm audit`, `pip-audit`, `osv-scanner`, `cargo audit`, etc. — see the reference for the full matrix) when it's already available in the environment. Never install a scanner to complete the audit, and never run a "fix" variant (`npm audit fix`, etc.) — this skill audits, it doesn't remediate. If no matching tool is available, report dependency vulnerabilities as **not verified** and name the specific tool that would have been used — never report "no vulnerable dependencies found" from the absence of a check.
3. **Separate advisory match from exploitability.** A real tool finding a known-vulnerable installed version is a **confirmed dependency advisory match**, not automatically a confirmed application vulnerability — trace reachability and attacker control (see the reference) before escalating it to confirmed/likely; report the advisory match either way, since even an unreachable vulnerable dependency is a supply-chain liability worth surfacing.
4. **Review CI/supply-chain evidence**: GitHub Actions pinning (tag/branch vs. immutable SHA), workflow permissions (explicit least-privilege vs. `write-all` vs. no explicit block), `pull_request_target` usage — trace whether it's actually combined with untrusted-code checkout/execution and secret/write access before calling it exploitable, install/build script trust, and lockfile/reproducibility gaps.
5. **Prefer a real secret scanner** (`gitleaks`, `trufflehog`, a repo-provided scanner) over ad hoc pattern matching when one is available; without one, a limited evidence-driven check is fine but must be labeled "full secret scan not verified," never presented as equivalent. Never print a discovered secret's value, ever — location only.
6. **No data egress.** Never upload source code, lockfiles, or secrets to an external service to complete an audit, beyond what a chosen tool normally and transparently does (e.g. `osv-scanner` querying its public advisory database with package names/versions) — and never without the user having chosen to run that tool.

## Workflow

1. **Scope the audit first**: AppSec, DevSecOps/supply-chain, or both — a request for one doesn't imply running the other, and a full combined audit only when explicitly asked or genuinely undetermined from the request. Scope further to what's actually in the diff/area under review — a full-repo audit only when explicitly asked.
2. For tenant isolation specifically: read the actual query/policy code, don't infer safety from the presence of a `tenant_id` column — confirm every read/write path filters by it, and confirm RLS policies (if any) match.
3. Classify each finding:
   - **Confirmed vulnerability** — demonstrated with evidence (a code path that unambiguously allows the exploit).
   - **Likely vulnerability** — strong indicator but not fully traced end-to-end (e.g. couldn't confirm because of missing runtime access).
   - **Hardening recommendation** — not currently exploitable but weakens defense-in-depth.
   - **Dependency advisory** — a real tool matched an installed version to a known advisory; exploitability in this application not yet traced.
   - **Supply-chain review signal** — a deterministic inventory/CI-config finding (unpinned action, broad permissions, missing lockfile, etc.) that needs contextual inspection before it's a finding at all.
   - **Not verified** — a check that could not actually be run in this environment (no dependency-audit tool, no secret scanner) — state this explicitly rather than omitting the section.
4. Never perform destructive testing (no actual data exfiltration, no production traffic manipulation, no live exploitation, no scanner "fix"/auto-remediation commands) — analysis and, where safe, non-destructive local reproduction only.
5. Report findings by severity, each with the affected file/line and the concrete exploit scenario.

## Decisions

- A tenancy check exists in one code path but a sibling path (e.g. an admin/bulk endpoint) skips it → report as confirmed IDOR/tenant-isolation gap, not a hardening note.
- Dependency scanning tooling isn't available in this environment → say so explicitly rather than skipping the section silently, and never call this the DevSecOps script's job — the bundled script inventories posture, it never substitutes for a real SCA tool.
- The bundled inventory script reports a signal (e.g. an unpinned action, `pull_request_target` usage) → inspect the actual context before classifying it as anything beyond a review signal; a script signal is never reported as a confirmed vulnerability on its own.
- A dependency-audit tool reports an advisory match → report it as a confirmed advisory/known-vulnerable-version match; only escalate to a confirmed *application* vulnerability once reachability and attacker control are actually traced, per `references/devsecops-security.md`.

## Exit criteria

- Every finding is labeled confirmed / likely / hardening / dependency advisory / supply-chain review signal / not verified — never presented as uniformly "vulnerabilities found."
- No destructive or unauthorized-scope testing was performed, and no scanner was installed or invoked in a fix/auto-remediate mode.
- Tenant isolation claims are backed by having read the actual filtering/policy code, not inferred from schema alone.
- No dependency-advisory finding is reported as a confirmed application-level exploit without a stated reachability/attacker-control trace.
- No secret value was printed, logged, or quoted in full anywhere in the response.
