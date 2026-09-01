# Stack detection patterns

Shared reference for identifying a project's technology stack from evidence in the repository. Used by `analyzing-codebase` and consulted by any skill that needs to adapt its behavior to the detected stack. Detect, don't assume — a stack claim must be backed by a file or config entry actually found in the repo.

## Package managers / monorepo signals

| Evidence file | Signal |
|---|---|
| `pnpm-workspace.yaml`, `pnpm-lock.yaml` | pnpm, possibly monorepo |
| `package-lock.json` | npm |
| `yarn.lock` | Yarn |
| `bun.lockb` | Bun |
| `lerna.json`, `nx.json`, `turbo.json` | monorepo tooling |
| `composer.json` / `composer.lock` | PHP/Composer |
| `requirements.txt`, `pyproject.toml`, `Pipfile` | Python |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `pom.xml`, `build.gradle` | Java/Kotlin (Maven/Gradle) |

## Frontend

| Evidence | Framework |
|---|---|
| `angular.json` | Angular |
| `next.config.*` | Next.js |
| dependency `react` without Next config | React (CRA/Vite/custom) |
| `vite.config.*` + `vue` dependency | Vue |
| `svelte.config.*` | Svelte |
| `nuxt.config.*` | Nuxt |

## Backend

| Evidence | Framework |
|---|---|
| `@nestjs/core` dependency, `nest-cli.json` | NestJS |
| `express` dependency, no Nest/Fastify markers | Express |
| `fastify` dependency | Fastify |
| `artisan`, `composer.json` with `laravel/framework` | Laravel |
| `manage.py`, `settings.py`, `INSTALLED_APPS` | Django |
| `main.py` + `fastapi` dependency | FastAPI |
| `pom.xml`/`build.gradle` + `spring-boot` | Spring Boot |

## Database / persistence

| Evidence | System |
|---|---|
| `supabase/config.toml`, `@supabase/supabase-js` | Supabase |
| `.sql` migrations + `pg`/`postgres` driver, `DATABASE_URL` with `postgres://` | PostgreSQL |
| `mysql2`/`mysql` driver | MySQL |
| `mssql`/`tedious` driver, `.sqlproj` | SQL Server |
| `better-sqlite3`, `*.sqlite`/`*.db` files | SQLite |
| `prisma/schema.prisma` | Prisma ORM (check `provider` for the real DB engine) |
| `*.rls.sql`, `policies` under Supabase migrations | Row-Level Security in use — relevant for `auditing-security` |

## Testing

| Evidence | Tool |
|---|---|
| `playwright.config.*` | Playwright |
| `cypress.config.*`, `cypress/` | Cypress |
| `jest.config.*`, `jest` in `package.json` | Jest |
| `vitest.config.*` | Vitest |
| `phpunit.xml` | PHPUnit |
| `pytest.ini`, `conftest.py` | Pytest |

## Infrastructure / CI/CD

| Evidence | System |
|---|---|
| `Dockerfile`, `docker-compose.yml` | Docker |
| `.github/workflows/*.yml` | GitHub Actions |
| `vercel.json`, `.vercel/` | Vercel |
| `wrangler.toml` | Cloudflare Workers |
| `nginx.conf` | nginx |
| `supabase/` directory | Supabase-managed infra |

## Applying detection

1. Enumerate evidence files with a fast glob before reading anything (`Glob`, not full-tree `Read`).
2. Only report a technology when its evidence file/dependency actually exists — never infer from the project's domain or name.
3. When two candidate frameworks both have partial evidence, read the relevant config/manifest to disambiguate before reporting either.
4. Record findings as a verifiable map (evidence → conclusion), not a bare list of guesses, so downstream skills and the user can check the reasoning.
