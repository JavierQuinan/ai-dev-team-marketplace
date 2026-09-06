# ai-dev-team

A reusable AI software-development team for Claude Code: codebase analysis, project continuity, architecture review, implementation, database migrations, debugging, automated testing, security/DevSecOps review, code review, deployment planning and release preparation — stack-agnostic, detected from repository evidence rather than assumed.

## Skills

| Skill | Use when |
|---|---|
| `continuing-project-work` | "continúa", "resume", "pick up where we left off" |
| `orchestrating-development-team` | Multi-discipline or end-to-end delivery request |
| `analyzing-codebase` | Understanding an unfamiliar repo before planning/implementing |
| `planning-implementation` | Sizing and scoping a non-trivial change before coding, including API-contract compatibility/rollout planning |
| `implementing-features` | The actual coding step |
| `debugging-systematically` | Something is broken and the cause isn't obvious |
| `testing-with-playwright` | E2E test creation, execution, or triage |
| `writing-automated-tests` | Unit/integration test authoring and gap analysis |
| `reviewing-code` | Reviewing a diff/PR before merge, including directional API-contract compatibility review |
| `reviewing-architecture` | ADR generation, module-boundary and tech-debt review |
| `auditing-security` | AppSec review, tenant-isolation checks, DevSecOps/supply-chain checks |
| `managing-database-migrations` | Authoring/reviewing a schema migration safely |
| `planning-deployment` | Platform-aware deployment/rollout/rollback planning — never executes a deploy |
| `preparing-releases` | Release-readiness verification (GO / CONDITIONAL GO / NO-GO) |

Invoke directly as `/ai-dev-team:<skill-name>`, or describe the task in natural language and let Claude select the matching skill.

In addition to the 14 user-facing skills above, the plugin includes one internal, non-user-invocable `enforcing-safety-baseline` skill (`user-invocable: false`) so every skill and all ten agents below can carry the same evidence/safety policy without duplicating it. See [Shared references](#shared-references).

## Agents

`solution-architect`, `repository-explorer`, `frontend-engineer`, `backend-engineer`, `database-engineer`, `qa-engineer`, `security-reviewer`, `code-reviewer`, `debugger`, `release-manager` — role-scoped subagents, invoked as `ai-dev-team:<agent-name>` to disambiguate from any same-named agent another installed plugin or the project/user might define. Used by `orchestrating-development-team` and available for direct delegation. Each agent preloads `enforcing-safety-baseline` at startup (a subagent's context starts fresh and does not inherit anything from a parent skill) and can invoke its mapped workflow skill via the Skill tool, namespaced as `ai-dev-team:<skill-name>`, on demand — see [docs/architecture/token-efficiency.md](https://github.com/JavierQuinan/ai-dev-team-marketplace/blob/main/docs/architecture/token-efficiency.md#agent-context-and-the-safety-baseline) in the marketplace repository for why.

## Shared references

Shared references include `references/stack-detection.md` and `references/context-recovery.md` (stack detection patterns, context-recovery priority order) and `references/api-contract-review.md` (directional API-contract compatibility guidance consumed by `reviewing-code` and `planning-implementation` — not an invocable skill itself), so individual `SKILL.md` files stay short and consistent. The evidence/safety policy lives at `skills/enforcing-safety-baseline/SKILL.md` instead — a skill, not a reference file, specifically so it can be preloaded into every agent's context, not just linked from skill bodies.

## Local development

From the marketplace repository root:

```bash
python scripts/validate.py
claude --plugin-dir ./plugins/ai-dev-team
```

See the marketplace root [README.md](https://github.com/JavierQuinan/ai-dev-team-marketplace#readme) and [CONTRIBUTING.md](https://github.com/JavierQuinan/ai-dev-team-marketplace/blob/main/CONTRIBUTING.md) for full installation and contribution instructions. These are absolute links, not relative ones, because this file ships inside the plugin directory only — installing from the marketplace copies `plugins/ai-dev-team/` alone into the plugin cache, not the rest of this repository.
