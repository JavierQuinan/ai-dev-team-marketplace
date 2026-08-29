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

## Agents

`solution-architect`, `repository-explorer`, `frontend-engineer`, `backend-engineer`, `database-engineer`, `qa-engineer`, `security-reviewer`, `code-reviewer`, `debugger`, `release-manager` — role-scoped subagents used by `orchestrating-development-team` and available for direct delegation.

## Shared references

`references/evidence-and-safety.md`, `references/stack-detection.md`, and `references/context-recovery.md` hold policy shared across skills (evidence discipline, irreversible-action confirmation, stack detection patterns, context-recovery priority order) so individual `SKILL.md` files stay short and consistent.

## Local development

From the marketplace repository root:

```bash
python scripts/validate.py
claude --plugin-dir ./plugins/ai-dev-team
```

See the marketplace root [README.md](../../README.md) and [CONTRIBUTING.md](../../CONTRIBUTING.md) for full installation and contribution instructions.
