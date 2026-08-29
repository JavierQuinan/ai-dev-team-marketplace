# ai-dev-team

A reusable AI software-development team for Claude Code: codebase analysis, project continuity, architecture, implementation, debugging, testing, security review, code review and release preparation — stack-agnostic, detected from repository evidence rather than assumed.

## Skills

| Skill | Use when |
|---|---|
| `continuing-project-work` | "continúa", "resume", "pick up where we left off" |
| `orchestrating-development-team` | Multi-discipline or end-to-end delivery request |
| `analyzing-codebase` | Understanding an unfamiliar repo before planning/implementing |
| `planning-implementation` | Sizing and scoping a non-trivial change before coding |
| `implementing-features` | The actual coding step |
| `debugging-systematically` | Something is broken and the cause isn't obvious |
| `testing-with-playwright` | E2E test creation, execution, or triage |
| `reviewing-code` | Reviewing a diff/PR before merge |
| `auditing-security` | AppSec review, tenant-isolation checks |
| `preparing-releases` | Release-readiness verification (GO / CONDITIONAL GO / NO-GO) |

Invoke directly as `/ai-dev-team:<skill-name>`, or describe the task in natural language and let Claude select the matching skill.

There is an eleventh skill, `enforcing-safety-baseline`, that is infrastructure rather than a workflow: it's `user-invocable: false` (not meant to be run directly) and exists so every one of the ten skills above and all ten agents below can carry the same evidence/safety policy without duplicating it. See [Shared references](#shared-references).

## Agents

`solution-architect`, `repository-explorer`, `frontend-engineer`, `backend-engineer`, `database-engineer`, `qa-engineer`, `security-reviewer`, `code-reviewer`, `debugger`, `release-manager` — role-scoped subagents, invoked as `ai-dev-team:<agent-name>` to disambiguate from any same-named agent another installed plugin or the project/user might define. Used by `orchestrating-development-team` and available for direct delegation. Each agent preloads `enforcing-safety-baseline` at startup (a subagent's context starts fresh and does not inherit anything from a parent skill) and can invoke its mapped workflow skill via the Skill tool on demand — see [docs/architecture/token-efficiency.md](../../docs/architecture/token-efficiency.md#agent-context-and-the-safety-baseline) for why.

## Shared references

`references/stack-detection.md` and `references/context-recovery.md` hold policy shared across skills (stack detection patterns, context-recovery priority order) so individual `SKILL.md` files stay short and consistent. The evidence/safety policy lives at `skills/enforcing-safety-baseline/SKILL.md` instead — a skill, not a reference file, specifically so it can be preloaded into every agent's context, not just linked from skill bodies.

## Local development

From the marketplace repository root:

```bash
python scripts/validate.py
claude --plugin-dir ./plugins/ai-dev-team
```

See the marketplace root [README.md](../../README.md) and [CONTRIBUTING.md](../../CONTRIBUTING.md) for full installation and contribution instructions.
