---
name: auditing-security
description: Performs an AppSec review covering authentication, authorization, IDOR, tenant isolation, RLS, injection, XSS, CSRF, SSRF, secrets, crypto, upload handling, rate limiting, dependency risk and the OWASP Top 10 / API Security Top 10, without destructive testing. Use when asked to audit security, review multi-tenant isolation, or assess a change for security risk.
when_to_use: Use for security-focused review, before releases touching auth/data/tenancy, or whenever asked to "audita seguridad", "check for vulnerabilities", "review multi-tenant isolation".
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

## Workflow

1. Scope the audit to what's actually in the diff/area under review — a full-repo audit only when explicitly asked.
2. For tenant isolation specifically: read the actual query/policy code, don't infer safety from the presence of a `tenant_id` column — confirm every read/write path filters by it, and confirm RLS policies (if any) match.
3. Classify each finding:
   - **Confirmed vulnerability** — demonstrated with evidence (a code path that unambiguously allows the exploit).
   - **Likely vulnerability** — strong indicator but not fully traced end-to-end (e.g. couldn't confirm because of missing runtime access).
   - **Hardening recommendation** — not currently exploitable but weakens defense-in-depth.
4. Never perform destructive testing (no actual data exfiltration, no production traffic manipulation, no live exploitation) — analysis and, where safe, non-destructive local reproduction only.
5. Report findings by severity, each with the affected file/line and the concrete exploit scenario.

## Decisions

- A tenancy check exists in one code path but a sibling path (e.g. an admin/bulk endpoint) skips it → report as confirmed IDOR/tenant-isolation gap, not a hardening note.
- Dependency scanning tooling isn't available in this environment → say so explicitly rather than skipping the section silently.

## Exit criteria

- Every finding is labeled confirmed / likely / hardening — never presented as uniformly "vulnerabilities found."
- No destructive or unauthorized-scope testing was performed.
- Tenant isolation claims are backed by having read the actual filtering/policy code, not inferred from schema alone.
