# AI Dev Team Marketplace

Open-source marketplace of reusable AI software-development skills, agents, and workflows for [Claude Code](https://code.claude.com/docs). It packages a full, stack-agnostic "AI software development team" — architecture, implementation, debugging, testing, security review, code review, and release preparation — as a versioned Claude Code plugin any repository can install.

## Why this exists

Reimplementing the same "act as my dev team" instructions per repository doesn't scale, and copy-pasted prompts drift. This marketplace ships that behavior as installable, versioned, discoverable **skills** and **agents** instead — detected from your repository's actual evidence, not hardcoded to one framework or one project.

## Architecture

```
ai-dev-team-marketplace/
├── .claude-plugin/marketplace.json   # marketplace manifest (registers plugins below)
├── plugins/
│   └── ai-dev-team/                  # the plugin: skills, agents, references
├── docs/                             # architecture notes, ADRs
├── scripts/validate.py               # local validator (no external deps)
├── tests/evals/                      # scenario-based evals, one set per skill
└── .github/                          # CI, issue/PR templates
```

The marketplace is designed to hold more than one plugin over time (see [ROADMAP.md](ROADMAP.md)); v0.1.0 ships exactly one: `ai-dev-team`. See [docs/adr/0001-marketplace-architecture.md](docs/adr/0001-marketplace-architecture.md) for the reasoning behind this structure, and [docs/architecture/token-efficiency.md](docs/architecture/token-efficiency.md) for how skills stay cheap to have installed.

## What's in `ai-dev-team` v0.1.0

**10 user-facing skills**, each a clearly-scoped responsibility rather than a framework-specific clone:

`continuing-project-work` · `orchestrating-development-team` · `analyzing-codebase` · `planning-implementation` · `implementing-features` · `debugging-systematically` · `testing-with-playwright` · `reviewing-code` · `auditing-security` · `preparing-releases`

Plus one internal, non-user-invocable skill, `enforcing-safety-baseline`, that carries the shared evidence/safety policy and is preloaded into every agent below (see [Agent safety model](#agent-safety-model)).

**10 agents** for role-scoped delegation, invoked as `ai-dev-team:<agent-name>`: `solution-architect`, `repository-explorer`, `frontend-engineer`, `backend-engineer`, `database-engineer`, `qa-engineer`, `security-reviewer`, `code-reviewer`, `debugger`, `release-manager`.

### Agent safety model

A Claude Code subagent starts with a fresh, isolated context window — it does not inherit anything from a parent skill, including safety/evidence discipline. So every `ai-dev-team` agent explicitly preloads the small `enforcing-safety-baseline` skill via its own `skills:` frontmatter field, guaranteeing the same evidence rule, irreversible-action confirmation, secret hygiene, and least-privilege discipline whether the agent is reached through `orchestrating-development-team` or invoked directly. Each agent also gets `Skill`-tool access and a pointer to its one mapped workflow skill (e.g. `backend-engineer` → `implementing-features`), pulled in on demand rather than preloaded in full, so a trivial delegation doesn't pay for a workflow it doesn't need. Full reasoning: [docs/architecture/token-efficiency.md](docs/architecture/token-efficiency.md#agent-context-and-the-safety-baseline).

Full descriptions: [plugins/ai-dev-team/README.md](plugins/ai-dev-team/README.md).

### Stack coverage (detected, not hardcoded)

No skill assumes a specific framework. Detection patterns (`plugins/ai-dev-team/references/stack-detection.md`) cover, among others:

- **Frontend:** Angular, React, Next.js, Vue, Svelte, Nuxt
- **Backend:** NestJS, Express, Fastify, Laravel, Django, FastAPI, Spring
- **Database:** PostgreSQL, Supabase, MySQL, SQL Server, SQLite
- **Testing:** Playwright, Cypress, Jest, Vitest, PHPUnit, Pytest
- **Infrastructure:** Docker, GitHub Actions, Vercel, Cloudflare, nginx

A technology is only reported when its evidence actually exists in the target repo — see [analyzing-codebase](plugins/ai-dev-team/skills/analyzing-codebase/SKILL.md).

## Installation

```text
/plugin marketplace add JavierQuinan/ai-dev-team-marketplace
/plugin install ai-dev-team@ai-dev-team-marketplace
```

If the install summary reports "Run `/reload-plugins` to activate," run that command.

### Update

```bash
claude plugin marketplace update ai-dev-team-marketplace
```

### Uninstall

```text
/plugin uninstall ai-dev-team@ai-dev-team-marketplace
```

## Usage examples

Skills are namespaced under the plugin (`/ai-dev-team:<skill-name>`), and Claude also invokes them automatically when your request matches:

```text
Continúa donde quedamos con el módulo de agenda.
→ triggers continuing-project-work

Analiza este proyecto y dime qué stack usa.
→ triggers analyzing-codebase

Implementa un endpoint para exportar reportes a CSV.
→ triggers planning-implementation → implementing-features

El login dejó de funcionar después del último deploy.
→ triggers debugging-systematically

Prueba el flujo de checkout completo con Playwright.
→ triggers testing-with-playwright

Haz code review de este PR.
→ triggers reviewing-code

Audita el aislamiento multi-tenant de este sistema.
→ triggers auditing-security

Deja esto listo para producción.
→ triggers preparing-releases (GO / CONDITIONAL GO / NO-GO)
```

Or invoke any skill directly, e.g. `/ai-dev-team:reviewing-code`.

## Local development

```bash
git clone https://github.com/JavierQuinan/ai-dev-team-marketplace.git
cd ai-dev-team-marketplace

# Validate manifests, skill frontmatter, structure, and eval schemas
python scripts/validate.py

# Load the plugin locally, without installing from the marketplace
claude --plugin-dir ./plugins/ai-dev-team
```

## Validation

Two validators run, for different reasons — `claude plugin validate` is the schema authority; `scripts/validate.py` checks this repo's own invariants that the official CLI doesn't:

- `claude plugin validate . --strict`, then `claude plugin validate <plugin-root> --strict` for every plugin `scripts/list_local_plugins.py` finds locally — the actual `marketplace.json` / `plugin.json` / frontmatter schema check. Install with `npm install -g @anthropic-ai/claude-code` (no Anthropic credentials required).
- `scripts/validate.py` (dependency-free, Python standard library only) checks required repository-specific frontmatter invariants and cross-file structure that the official CLI does not, empirically confirmed (see [docs/architecture/token-efficiency.md](docs/architecture/token-efficiency.md#frontmatter-validation-what-this-repos-validator-does-and-does-not-check)):
  - `marketplace.json` and every local plugin's `plugin.json` are valid JSON and structurally consistent with each other (name, version)
  - Every skill's `SKILL.md` frontmatter `name` is present, kebab-case, unique within its plugin, and matches its own directory name
  - Skill and agent names are unique per plugin and kebab-case
  - Every local link inside a plugin's own `skills/`/`agents/` files resolves, *and* stays inside that plugin's root — a link that exists in this full checkout but points outside the plugin directory is rejected, because a marketplace install copies only the plugin's own directory
  - `tests/evals/*.json` conform to the eval schema and give each `(plugin, skill)` pair at least 3 evals

CI (`.github/workflows/validate.yml`) runs both on every pull request and push to `main`, against every plugin the marketplace declares locally — not hardcoded to `ai-dev-team`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) — in short: prefer extending an existing skill's `references/` over adding a new skill, keep `SKILL.md` files small and evidence-driven, and include evals with any new/changed skill.

## Security

See [SECURITY.md](SECURITY.md) for responsible disclosure. Every skill in this plugin follows a shared safety policy: no success claim without having just verified it, and explicit user confirmation required before any irreversible action (force-push, destructive migration, production deploy, merge, secret rotation).

## Roadmap

See [ROADMAP.md](ROADMAP.md) for skill/agent families under consideration beyond v0.1.0 (QA depth, DevSecOps, database specialization, GitHub automation, delivery/incident support, and opt-in vertical reference packs).

## Language

This project's canonical documentation is in English for international open-source reach. Issues and discussions in other languages, including Spanish, are welcome.

## License

[Apache License 2.0](LICENSE).
