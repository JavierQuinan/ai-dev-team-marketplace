# Security policy

## Supported versions

This project is pre-1.0. Security fixes are applied to the latest published version on `main`; there is no long-term-support branch yet.

| Version | Supported |
|---|---|
| 0.1.x | Yes |

## Reporting a vulnerability

**Do not open a public GitHub issue for a security vulnerability.** Publicly disclosing an exploitable issue before a fix is available puts every consumer of this marketplace at risk.

Instead, report it privately:

1. Preferably, use [GitHub's private vulnerability reporting](https://github.com/JavierQuinan/ai-dev-team-marketplace/security/advisories/new) for this repository ("Security" tab → "Report a vulnerability").
2. If that's unavailable, contact the maintainer directly (see the repository owner's GitHub profile) with a description of the issue, steps to reproduce, and potential impact.

Please include:

- The affected skill, agent, script, or manifest.
- Steps to reproduce, or a minimal example.
- The potential impact (e.g. prompt injection via a specific content path, unsafe command construction in a script, secret exposure).

You should receive an acknowledgment within a reasonable timeframe. Once a fix is available, a new version is published and, where appropriate, a GitHub Security Advisory is issued crediting the reporter (unless anonymity is requested).

## Scope

In scope: the marketplace and plugin manifests, `SKILL.md` content, agent definitions, and any scripts shipped in this repository (`scripts/*.py`, etc.) — specifically risks like prompt-injection-susceptible instructions, unsafe shell command construction, or secret handling mistakes.

Out of scope: vulnerabilities in Claude Code itself (report those to Anthropic, not here), and vulnerabilities in a downstream project that merely *uses* this plugin (report those to that project).

## What this project does to reduce risk by default

- Every skill links to a shared evidence-and-safety policy (`plugins/ai-dev-team/references/evidence-and-safety.md`) requiring explicit confirmation before irreversible actions (force-push, hard reset, destructive migrations, production deploys, merges, secret rotation).
- No skill or script in this repository is designed to print, log, or transmit secret values.
- `scripts/validate.py` runs in CI on every PR and push to `main` to catch structural regressions before they reach users.
