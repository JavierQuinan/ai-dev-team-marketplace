# Security policy

## Supported versions

This project is pre-1.0. Security fixes are applied to the latest published minor release and to the current development line on `main`; there is no long-term-support branch yet.

| Version | Supported |
|---|---|
| 0.2.x | Yes |
| 0.1.x | No |

Users should upgrade to the latest published release before reporting an issue that may already have been fixed.

## Reporting a vulnerability

**Do not open a public GitHub issue for a security vulnerability.** Publicly disclosing an exploitable issue before a fix is available puts every consumer of this marketplace at risk.

Instead, report it privately:

1. Preferably, use [GitHub's private vulnerability reporting](https://github.com/JavierQuinan/ai-dev-team-marketplace/security/advisories/new) for this repository ("Security" tab → "Report a vulnerability").
2. If that's unavailable, contact the maintainer directly (see the repository owner's GitHub profile) with a description of the issue, steps to reproduce, and potential impact.

Please include:

- The affected skill, agent, script, manifest, or release version.
- Steps to reproduce, or a minimal example.
- The potential impact (e.g. prompt injection via a specific content path, unsafe command construction in a script, secret exposure).
- Any known prerequisites, affected configurations, or mitigations.

You should receive an acknowledgment within a reasonable timeframe. Once a fix is available, a new version is published and, where appropriate, a GitHub Security Advisory is issued crediting the reporter (unless anonymity is requested).

## Scope

In scope: the marketplace and plugin manifests, `SKILL.md` content, agent definitions, and any scripts shipped in this repository (`scripts/*.py`, etc.) — specifically risks like prompt-injection-susceptible instructions, unsafe shell command construction, privilege or trust-boundary mistakes, or secret handling failures caused by this project.

Out of scope: vulnerabilities in Claude Code itself (report those to Anthropic, not here), and vulnerabilities in a downstream project that merely *uses* this plugin (report those to that project), unless the vulnerability is caused by behavior shipped by this marketplace.

## Disclosure and remediation

Please allow maintainers a reasonable opportunity to investigate and remediate a vulnerability before public disclosure. Security fixes may be prepared privately and released together with an advisory when coordinated disclosure is appropriate.

No bounty, payment, or specific remediation deadline is promised by this policy.

## What this project does to reduce risk by default

- Every skill links to, and every agent preloads, a shared evidence-and-safety policy (`plugins/ai-dev-team/skills/enforcing-safety-baseline/SKILL.md`) requiring explicit confirmation before irreversible actions (force-push, hard reset, destructive migrations, production deploys, merges, secret rotation). It's preloaded rather than just referenced because a subagent's context starts fresh and does not inherit anything a parent skill loaded — see [docs/architecture/token-efficiency.md](docs/architecture/token-efficiency.md#agent-context-and-the-safety-baseline).
- No skill or script in this repository is designed to print, log, or transmit secret values.
- `scripts/validate.py` and `claude plugin validate` both run in CI on every PR and push to `main` to catch structural regressions before they reach users.
