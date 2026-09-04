# First-time setup

A short walkthrough for installing `ai-dev-team` for the first time, from a fresh Claude Code session to a verified, working install. This is the detailed path — see the [README](../../README.md#installation) for the quick one.

## 1. Prerequisites

- [Claude Code](https://code.claude.com/docs) installed.
- An authenticated, usable Claude Code session (you can already run a normal prompt).
- Git available where relevant — needed to work inside a cloned repository, not needed to install the plugin itself.

## 2. First Claude Code launch

If this is your first time running Claude Code at all, it may walk you through its own one-time setup — for example, a theme selection (dark/light/etc.). That setup belongs to Claude Code itself, not to `ai-dev-team`; pick whatever you prefer. The exact wording and steps can vary between Claude Code versions — follow what's on your screen rather than this document if the two disagree.

## 3. Add the marketplace

```text
/plugin marketplace add JavierQuinan/ai-dev-team-marketplace
```

Expect a confirmation that the marketplace was added and that it lists `ai-dev-team` as an available plugin. If it reports the marketplace was already added, that's fine — continue to the next step.

## 4. Install the plugin

```text
/plugin install ai-dev-team@ai-dev-team-marketplace
```

If Claude Code shows an install-scope choice, the recommended default for an individual developer is **"Install for you (user scope)"** — this makes the plugin available to you across your own projects. This guide only documents user scope; if another scope option is presented and its behavior isn't covered here, treat it as unverified rather than assuming what it does.

## 5. Activation

- If Claude Code reports the plugin is already active, there's nothing else to do.
- If it asks you to run `/reload-plugins`, run that command.
- If Claude Code separately installed a CLI update that requires a restart, you can restart before continuing if your version calls for it.

## 6. Verify the installation

A few small checks, cheapest first:

**Automatic routing** — in any project, ask:

```text
Analiza este proyecto y dime qué stack usa.
```

Expect this to route to `ai-dev-team:analyzing-codebase`.

**Explicit skill invocation:**

```text
/ai-dev-team:reviewing-code
```

**Full-team routing:**

```text
Actúa como el equipo completo. Analiza este proyecto y propón un plan,
pero no implementes nada.
```

Expect this to route to `ai-dev-team:orchestrating-development-team`.

## 7. Optional: direct agent check

From a terminal, you can invoke an agent directly:

```bash
claude --agent ai-dev-team:backend-engineer
```

Then give it a read-only prompt, e.g. "list the API routes in this project" — no code changes needed to confirm the agent resolves and responds.

## 8. What success looks like

- The plugin is recognized (no "unknown plugin" error on install).
- Namespaced skills (`/ai-dev-team:<skill-name>`) are available and invocable.
- Agents (`ai-dev-team:<agent-name>`) resolve when addressed directly or through the orchestrator.
- No "unknown skill," "unknown agent," or "unknown plugin" error appears during the checks in step 6.

## 9. Update

Use the repository's currently documented update command — see [README: Update](../../README.md#update). Don't hand-roll a different update flow; the README command is kept current with each release.

## 10. Uninstall

Use the repository's currently documented uninstall command — see [README: Uninstall](../../README.md#uninstall).

## 11. Troubleshooting

- **"Marketplace already added"** — expected if you've run step 3 before; continue to step 4.
- **"Plugin already installed"** — expected if you've run step 4 before; continue to step 5 to confirm activation.
- **Claude Code asks for `/reload-plugins`** — run it; this is a normal part of activation, not an error.
- **Claude Code update asks for a restart** — restart, then re-run the step 6 checks to confirm the plugin is still recognized.
- **A skill/agent isn't recognized right after install** — run `/reload-plugins` (or restart if a CLI update is pending), then re-run the step 6 checks before assuming something is broken.
- **Don't reinstall repeatedly as a first response.** Check the current state (is the marketplace added? is the plugin installed? does it need a reload?) before installing again — repeated blind reinstalls make the actual problem harder to diagnose, not easier.

## 12. Security note

Installing and verifying `ai-dev-team` never requires printing project secrets. None of the checks above, and none of this plugin's workflows, should ever ask you to paste `.env` contents or credentials into a prompt, a troubleshooting step, or documentation output. If something appears to require that, treat it as a bug, not a normal step.
