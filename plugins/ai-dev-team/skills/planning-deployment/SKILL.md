---
name: planning-deployment
description: Produces a platform-aware deployment plan — preconditions, artifact/version, config, migration ordering, exact human-run commands, health checks, rollback — detected from real repo evidence (Vercel, Docker/Compose, VPS/systemd, Kubernetes, or an honestly-scoped generic plan when the platform can't be verified). Planning only — never executes a deployment, not even after explicit confirmation. Use when asked to plan a deployment, rollout, or rollback, not to check release readiness or to actually deploy.
when_to_use: USE for "planifica el despliegue", "cómo desplegamos esto", "genera el plan de deployment", "dame rollout y rollback", "deployment plan para producción", "cómo subimos esto a Vercel/Docker/VPS", "qué hacemos después del release", "health checks post-deploy". NOT USE for "¿está listo para producción?" (stays with `preparing-releases`), "corrige el código" (`implementing-features`), "haz la migration" (`managing-database-migrations`), or an actual "despliega ahora" request — this skill may still produce the plan for that request, but capability-wise it never executes the deploy regardless of what's asked or confirmed.
---

# Planning deployment

**Advisory / planning only.** This skill never executes a deployment — not after "sí", "confirmo", "hazlo", "autorizado", or any other phrasing of consent. See [enforcing-safety-baseline](../enforcing-safety-baseline/SKILL.md): production/shared-environment deployment always requires separate, explicit human execution outside this skill.

## Workflow

1. **Detect the platform from repo evidence** — never assume. Look for `vercel.json`/`.vercel/project.json` (Vercel), `Dockerfile`/`docker-compose*`/`compose*` (Docker), systemd units/`nginx`/`caddy` config (VPS), Kubernetes manifests/Helm charts (K8s), `Procfile`, CI deploy jobs, or deployment docs naming the platform. A framework being *compatible* with a platform (e.g. Next.js auto-detecting on Vercel) is never itself evidence of the actual target — that same app could just as legitimately run on Docker, a VPS, or elsewhere; only platform-specific config/CI/docs count. Repo evidence beats a user's explicitly stated target, which is still valid but must be labeled **TARGET PROVIDED BY USER, not repo-verified**; neither beats inventing a platform from inference. If no platform evidence and no user-stated target exists, state **DEPLOY TARGET NOT VERIFIED** and produce the generic bounded plan (see `references/deployment-planning.md`) — never default to inventing Vercel/AWS/Kubernetes.
2. **Design the plan** against the structure below, filling only what applies; mark anything not evidenced as `N/A` with a one-line reason or `NOT VERIFIED` — never a silent omission, never an empty checklist.
3. **If the release includes a database change**, invoke `ai-dev-team:managing-database-migrations` for the migration itself; this skill only sequences *when* the migration runs relative to code deploys (e.g. backward-compatible code first → human applies migration → verify → follow-up code). It never executes a migration itself, and ADR 0005's LEVEL 4 (shared/staging/production requires separate human execution) applies in full regardless of what this skill's own plan says.
4. **Never print a secret value.** List required configuration by `ENV_VAR_NAME`/secret name only. If a command normally embeds a secret inline, show `<SECRET_FROM_SECURE_STORE>` in its place, never a real or plausible-looking value.
5. **Stop before execution.** Deliver the plan, the exact human-run command(s) where evidenced, and the explicit statement that production/shared execution is a separate, human-controlled step outside this skill — then stop. No `Bash` call in this skill ever runs an actual deploy command (see the forbidden list below), regardless of user confirmation.

## Deployment plan structure

Produce, in order, marking non-applicable items `N/A` with a reason rather than omitting them:

1. **Target/platform evidence** — what was found, or `DEPLOY TARGET NOT VERIFIED`.
2. **Preconditions** — what must already be true (readiness verdict, branch state, build artifact exists).
3. **Artifact/version** — what's being deployed and how it's identified (tag, image digest, build ID).
4. **Configuration/env** — required variable **names** only, never values.
5. **Database/migration dependency** — whether this deploy needs a migration, and its ordering (step 3 above).
6. **Deployment ordering** — the exact sequence of operations.
7. **Human-run commands** — exact commands where the evidence supports them, explicitly labeled as commands *the user runs*, not commands this skill executes.
8. **Health checks** — concrete, observable success criteria (HTTP/API/worker/queue/DB connectivity), only where evidenced — never declare success without something to actually check.
9. **Smoke verification** — the minimal real check that the deploy worked, tied to what's actually observable.
10. **Logs/observability** — where to look if something goes wrong.
11. **Rollback trigger** — concrete conditions that mean "roll back," not "if needed."
12. **Rollback procedure** — the actual steps/commands, not "just roll back."
13. **Human gates** — every point requiring a human to act (execute the deploy, apply a migration, approve a promotion).
14. **Not-verified items** — anything the plan couldn't confirm from evidence, named explicitly.

Platform-specific detail (Vercel, Docker/Compose, VPS/systemd, Kubernetes/Helm, and the generic-unknown shape) lives in `references/deployment-planning.md`, loaded only once a platform is identified or ruled unverifiable.

## Release readiness vs. deployment planning — different contracts

- **`preparing-releases`** answers *"is this ready to ship?"* (build/tests/lint/secrets/docs/version/migrations) → GO / CONDITIONAL GO / NO-GO.
- **`planning-deployment`** answers *"how do we deploy this safely?"* (ordering, artifact, commands, health, rollback) → a deployment plan.

A GO from `preparing-releases` does not authorize this skill to deploy, and a deployment plan from this skill does not imply readiness is GO — they compose (readiness first, then a plan), but never substitute for each other. Never let a user's "is this ready for production?" be answered by this skill instead of `preparing-releases`.

## Decisions

- Platform can't be determined from evidence → say `DEPLOY TARGET NOT VERIFIED` and produce the generic bounded plan; never guess a default platform.
- User says "deploy now"/"confirmo"/"autorizado" → still only produce the plan and the exact human-run command; still never execute it. Capability, not caution, is the boundary — there is no confirmation that unlocks execution for this skill.
- A required env var's value is needed to write a realistic command → use `<SECRET_FROM_SECURE_STORE>` (or the var name alone), never a real or plausible value.
- Deploy includes a schema change → sequence code/migration ordering explicitly, but the migration's actual execution is `managing-database-migrations`'s job under ADR 0005, never this skill's, and never against shared/staging/production regardless of this plan.
- Health checks would need to be invented with no evidence they exist → say so (`NOT VERIFIED`) rather than listing generic checks that don't correspond to anything in this repo.
- The request is really "is this ready to ship?" → that's `preparing-releases`; don't let a deployment-planning request eclipse it, and don't answer a readiness question with a deployment plan.

## Exit criteria

- The platform is stated as verified-from-evidence or explicitly `DEPLOY TARGET NOT VERIFIED` — never assumed.
- No secret value appears anywhere in the plan — names/placeholders only.
- No `Bash` call in this session executed an actual deployment, migration-apply, or remote-mutating command — the plan stops at the human-run command, every time, regardless of confirmation wording.
- Rollback has a concrete trigger and procedure, never "roll back if needed."
- Every structure section is present, filled or explicitly `N/A`/`NOT VERIFIED` with a reason.
