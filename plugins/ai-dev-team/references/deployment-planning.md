# Deployment planning reference (by platform)

Deep, platform-specific patterns for `planning-deployment`, loaded once a target has been identified — from repo evidence, from an explicit user request, or ruled unverifiable (see `SKILL.md` step 1 for the current-evidence-vs-requested-target distinction: a user-requested target governs the plan even when it conflicts with what the repo currently shows, as long as that's labeled honestly rather than presented as repo-confirmed). None of these ever get executed by the skill itself — every command shown here is a *human-run* command in the plan, never a `Bash` call this skill makes.

## A. Vercel

**Evidence must be Vercel-specific, not merely framework-compatible.** `vercel.json`, `.vercel/project.json` (or a `.vercel/` directory generally), a CI/deploy job that actually invokes `vercel`/the Vercel API, or deployment docs explicitly naming Vercel. A framework Vercel happens to auto-detect (Next.js, etc.) is **not evidence by itself** — that same Next.js app can just as legitimately deploy to Docker, a VPS, AWS/Azure/GCP, Netlify, or Kubernetes, and framework compatibility says nothing about which target this specific repo actually uses. Never infer Vercel from the framework alone.

The user may also explicitly name Vercel as the target even when the repo currently shows no Vercel config, or shows evidence of a *different* current deployment shape entirely (e.g. a `Dockerfile`/`docker-compose.yml` — the repo is currently deployed via Docker, but the user is asking to plan a move to Vercel). That's a valid request: produce the Vercel plan, state the target as `SOURCE: USER-PROVIDED`, `REPO SUPPORT: NOT VERIFIED` (naming what the repo currently shows instead, if anything), and add a short migration/config-gap note (e.g. "currently Docker/VPS — moving to Vercel means introducing `vercel.json` or accepting framework auto-detection, migrating env vars from compose/host config to the Vercel project, and retiring the Docker/VPS deploy path"). Never present the user-requested Vercel target as if the repo's own evidence confirmed it, and never silently produce a Docker plan instead just because that's what the repo currently runs — the user asked for Vercel.

- **Preconditions**: build passes locally/in CI, correct project linked (`vercel link` already run — check for `.vercel/project.json`, don't re-link).
- **Build command**: read from `vercel.json`/framework defaults/`package.json` scripts — state what was actually found, not a guessed default.
- **Preview vs. production**: if the repo/CI shows a preview-deploy-per-PR pattern, note it; production is a distinct, deliberate action.
- **Config/env**: list variable **names** from `.env.example`/Vercel project settings references found in code — never values. Note which are build-time vs. runtime if the evidence shows a distinction.
- **Production deploy — human step**: `vercel --prod` (or `vercel deploy --prod`) run by the human, with the exact working directory/project context named.
- **Health/verification**: the production URL responding, plus any evidenced health/status endpoint in the app itself.
- **Rollback**: Vercel keeps prior deployments — rollback is promoting the previous production deployment (`vercel rollback` or the dashboard's "promote to production" on the prior deployment), not a redeploy-from-scratch.
- **Logs**: `vercel logs` / the Vercel dashboard's function/build logs.

## B. Docker / Compose

Evidence: `Dockerfile`, `docker-compose*.yml`/`compose*.yml`.

- **Preconditions**: image builds locally/in CI without error.
- **Artifact/tag strategy**: state the actual tagging convention found (git SHA, semver, `latest` — flag `latest`-only as a rollback risk since it isn't immutable).
- **Registry**: name it only if evidenced (a `docker push` target in CI, a registry reference in compose) — otherwise `NOT VERIFIED`.
- **Config/env**: names from `docker-compose.yml`'s `environment`/`env_file` keys and `.env.example` — never values.
- **Migration ordering**: if a migration service/step exists in compose, sequence it explicitly relative to app container startup.
- **Deploy — human steps**: pull/build the new image, `docker compose pull && docker compose up -d` (or the project's actual equivalent) run by the human against the target host.
- **Health checks**: the compose file's own `healthcheck:` blocks if present; otherwise the app's health endpoint if evidenced.
- **Logs**: `docker compose logs -f <service>`.
- **Rollback**: redeploy the prior immutable image tag/digest — never "rebuild from source and hope it matches."

## C. VPS / systemd / nginx / Caddy

Evidence: systemd unit files, `nginx.conf`/`caddy` config, a deploy script targeting a host, no containerization evidence.

- **Preconditions**: artifact (build output, package) ready; backup of current deployed version/data taken where material (state if evidenced this is normally done).
- **Artifact delivery**: how the built artifact reaches the host, per what's evidenced (rsync, scp, a CI artifact step) — `NOT VERIFIED` if nothing shows this.
- **Config/env verification**: names of required config/env on the host, never values.
- **Migration ordering**: sequence relative to service restart.
- **Service restart/reload — human step**: `systemctl restart <service>` (or `reload` if the app supports zero-downtime reload) run by the human on the target host — this skill never opens an SSH connection or runs a remote command itself.
- **Reverse proxy check**: confirm nginx/Caddy config points at the correct upstream/port after the change, where evidenced.
- **Health endpoints**: whatever the app exposes, per evidence.
- **Logs**: `journalctl -u <service>` / the configured log path.
- **Rollback**: keep the previous artifact/build available and documented as the rollback target; a rollback is restoring and restarting that prior artifact, not re-deploying "an older commit" from scratch without a concrete artifact to point at.

## D. Kubernetes / Helm

Evidence: Kubernetes manifests (`*.yaml` with `apiVersion`/`kind: Deployment` etc.), a Helm chart (`Chart.yaml`).

- Only produce this plan when the repo actually contains this evidence — never assume Kubernetes because the app is containerized (that's evidence for Docker/Compose, not K8s, unless manifests/charts are also present).
- **Artifact**: image tag/digest referenced in the manifest/chart values.
- **Migration/job ordering**: sequence any migration `Job`/init container relative to the rollout.
- **Rollout — human step**: `kubectl apply -f ...` or `helm upgrade ...`, run by the human, with the exact manifest/chart/values referenced.
- **Rollout status**: `kubectl rollout status deployment/<name>` as the verification step.
- **Readiness/liveness**: cite the manifest's actual probes, don't invent generic ones.
- **Rollback**: `kubectl rollout undo` or `helm rollback <release> <revision>` — name the specific prior revision when it's evidenced, not "the previous version" vaguely.

## E. Unknown / custom platform

When no platform evidence exists, or the evidence doesn't cleanly match A–D:

- Never invent platform-specific commands or tooling.
- Still produce the same 14-section structure (see `SKILL.md`), with each platform-specific item marked `NOT VERIFIED` and a one-line note on what evidence would resolve it (e.g. "no deploy config found — a `Dockerfile`, `vercel.json`, or CI deploy job would let this plan get more specific").
- Preconditions, artifact identification, config-by-name, migration ordering, a generic health-check expectation ("the running process/service responds"), and a rollback expectation ("keep the previous deployable artifact available") can usually still be stated in general terms even without platform specifics — state them, don't leave the whole plan empty just because the platform is unknown.
