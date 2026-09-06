# API contract review reference

Shared reference for `reviewing-code`'s API-contracts check and `planning-implementation`'s API-impact section. Narrow, framework-agnostic, evidence-driven — this is a compatibility-diffing lens on an existing contract change, not an API-design skill and not an OpenAPI specification tutorial. Load it only when a diff or plan actually touches a request/response contract (an HTTP API's request/response shape, status codes, or route surface).

## The question this reference answers

**Can an existing client/consumer of the OLD contract keep working, unmodified, against the NEW contract?**

Every rule below exists to answer that one question for one specific change. Never evaluate a change in isolation from that question — a change that looks superficially similar to another (e.g. "a field went from optional to required") can be compatible or breaking depending on which side of the wire it's on.

Before applying any rule, establish four things:

1. **OLD contract** — what existing clients were built against.
2. **NEW contract** — what the provider will actually serve/accept after this change.
3. **REQUEST or RESPONSE** — these are not symmetric (see below); never apply a request rule to a response change or vice versa.
4. **Who PRODUCES the value and who CONSUMES it** — for a request field, the client produces and the new provider consumes; for a response field, the new provider produces and the existing client consumes. Compatibility always means "can the consumer handle what the producer now sends/expects," never a comparison of the two contract versions in the abstract.

## Evidence first — never assume a formal spec exists

Detect, don't assume, exactly like `stack-detection.md`'s discipline. Look for:

- `openapi.yaml`/`openapi.yml`/`openapi.json`, `swagger.yaml`/`swagger.json`.
- A build/CI step that actually generates a schema (e.g. a documented `npm run generate:openapi`, a NestJS `@nestjs/swagger` bootstrap call, a FastAPI app whose `/openapi.json` route is referenced in code or tests, a `springdoc`/`swagger-ui` dependency actually wired up) — evidence of *generation*, not merely a compatible framework.
- A committed generated-schema artifact already in the repo.

**Framework-compatible is not the same as OpenAPI actually used** — the same lesson already learned the hard way for `planning-deployment`'s Vercel detection applies here identically. A NestJS or FastAPI project is *capable* of serving an OpenAPI doc; that capability is never itself evidence the project publishes or relies on one.

If no verifiable formal spec exists, say so explicitly (`NOT VERIFIED: no OpenAPI/Swagger spec found`) and fall back to a manual, evidence-based comparison of the actual source: route/handler definitions, request validation/schema code (e.g. a Zod/Joi/class-validator/Pydantic schema), response DTOs/serializers, and existing tests that assert on request/response shape. Manual comparison is a fully valid method here, not a degraded fallback to apologize for — just report which method was actually used.

## Optional tooling

If a real diffing tool (`oasdiff`, `openapi-diff`, or an equivalent) is **already installed and available** in the environment, it may be used as additional evidence alongside the manual read — never as a replacement for actually reading the changed contract. Never install one (`npm install`, `pip install`, `go install`, a package manager, a download, or a SaaS spec-upload) to make this capability work; if no such tool is available, proceed with the manual method and say so. This mirrors the DevSecOps extension's real-tool-if-available, evidence-based-otherwise precedent (ADR 0004 adjustment #3) exactly.

## Request compatibility

For a request field: **the existing client produces it, the new provider consumes it.** The new provider must keep accepting what old clients still send.

| Change | Usual verdict | Why |
|---|---|---|
| Field: optional → required | **Breaking** | An existing client that legitimately omits the field (per the old contract) now fails validation it never used to. |
| Field: required → optional | Compatible/additive | Old clients still send it; the provider now also tolerates its absence. |
| New field added, optional | Compatible/additive | Old clients don't know about it; the provider doesn't require it. |
| New field added, required | **Breaking** | No old client sends it. |
| Accepted-value set (request enum) narrowed | **Breaking** for clients still sending a removed value | The client production side didn't change; the provider now rejects input it used to accept. |
| Accepted-value set (request enum) expanded | Usually compatible | Old clients only ever sent the old subset; the provider still accepts it. |
| Type narrowed / stricter validation (e.g. string → specific format, wider numeric range → narrower) | **Breaking** if old, valid requests can now fail | Evaluate against what old clients could legitimately send under the old contract, not just the type name. |
| Nullable → non-nullable (or vice versa) on a request field | Evaluate like optional/required — treat "was allowed to send null" the same as "was allowed to omit" | Only material when a client could actually have sent null under the old contract. |

## Response compatibility

**Do not assume symmetry with requests.** For a response field: **the new provider produces it, the existing client consumes it.**

| Change | Usual verdict | Why |
|---|---|---|
| Field: required → optional (provider may now omit it) | **Breaking** | An existing consumer that assumed the field was always present (per the old contract) can now fail or misbehave when it's missing. |
| Field: optional → required (provider now always sends it) | Usually compatible from a presence standpoint | Existing consumers already had to handle it being absent; always receiving it is a superset of that. Still check the field's actual semantics — if consumers branch on its *absence* as a meaningful signal, always-present changes that meaning. |
| New field added to the response | Usually compatible/additive | Existing consumers that don't know about a field ignore it — *unless* there's evidence of strict/closed deserialization (schemas with `additionalProperties: false` or equivalent, strict decoders) that would reject an unrecognized field. Check for that evidence before calling it safe. |
| Field removed from the response | **Breaking** for any consumer that reads it | Treat like required → optional's failure mode, just total instead of partial. |

## Enums — do not apply a blanket rule

This is the section most likely to be gotten wrong by an under-specified rule, so it gets extra weight.

**Never write or conclude "enum expansion is safe" as a general rule.** Whether an enum change is compatible depends on which side produces it and on real evidence about how existing consumers handle unrecognized values:

- **Response enum, expanded** (the provider can now return a new value it never returned before): only compatible if there's evidence the client uses a **tolerant-reader pattern** — ignores/defaults on unrecognized values, doesn't switch exhaustively, doesn't validate against a closed set. Absent that evidence, treat it as a genuine risk, not an automatic pass: a client with an exhaustive `switch`, a closed enum type in a strongly-typed consumer, or strict response validation can break or misbehave on an unrecognized value. State explicitly whether tolerant-reader evidence exists or not — don't default to "safe."
- **Response enum, narrowed** (a value the provider used to return is now never returned): breaking only if a client actually depended on that specific value being produced — evaluate whether the old contract actually promised it and whether removing it changes real client-visible behavior, not just "a value disappeared."
- **Request enum, narrowed** (the provider no longer accepts a value it used to accept): breaking for any client still sending the removed value — same logic as the general request-narrowing rule above.
- **Request enum, expanded** (the provider now accepts a value it didn't before): usually compatible — old clients only ever sent the old subset.

State the actual direction (request/response) and the actual evidence (or absence of it) for every enum finding — never emit a finding, or a clearance, based on the enum change alone without naming which side it's on.

## Paths / methods

- **Removal** (a path or method disappears): usually breaking for any existing consumer of that path/method — but only report it as a finding when there's evidence the removed surface was actually a real, consumed contract (referenced in a formal spec, called from a client/SDK in the same repo or a documented integration, or otherwise evidenced as public/committed) — not for an internal, never-exposed, or already-unused route.
- **Addition** (a new path or method): usually additive, not breaking.

## Status-code compatibility

Never do a bare count-diff ("2 status codes added, 1 removed"). Evaluate:

- What status codes did the old contract actually promise for this operation (documented, tested, or evidenced in the handler)?
- What can the new provider actually produce now?
- Is there evidence existing clients branch on a specific code (an `if status === 404` in a client/SDK in the repo, a test asserting a specific code)?
- Does the *shape* of an error body change even if the status code itself doesn't (e.g. error object restructured) — that can break a consumer that parses the error body just as much as a status-code change can.
- A newly-introduced status code is not automatically safe (a closed client that only handles a known set may mishandle an unrecognized code) and not automatically breaking (a client with sane default/fallback handling for unknown codes is unaffected) — this needs the same evidence-first treatment as everything else here, never a default assumption either way.

## Versioning / deprecation / rollout strategies

For `planning-implementation` to draw from when a plan involves a breaking or borderline contract change — these are strategies to *plan*, never to execute as part of this reference:

- **Additive rollout** — ship the new field/endpoint alongside the old, no removal yet; safe by construction, only applicable when the change is genuinely additive.
- **Deprecate then remove** — mark the old field/endpoint deprecated (docs, response headers, or a sunset date), give consumers a real migration window, remove only after evidence of migration (or an agreed deadline).
- **Dual-field / write-both, read-both transition** — during migration, accept/produce both old and new shapes; commonly paired with a client migration window before the old shape is dropped.
- **Parallel versions (`v1`/`v2`, or a version header/param)** — old contract keeps serving unmodified consumers while new consumers move to the new version; heavier to maintain, justified when the breaking change is unavoidable and consumers can't migrate in lockstep.
- **Coordinated rollout** — viable only when the environment evidences that provider and all consumers deploy together (e.g. a monorepo with a single deploy pipeline for both sides) — never assume this is safe for a public or third-party-consumed API without that evidence.

State which strategy (if any) applies and why; a plan is never required to force a version bump for a change this reference would classify as compatible/additive.

## False-positive guardrails — never flag these as breaking on their own

- An additive change with no evidence of conflict (new optional request field, new response field with no strict-decoding evidence, a genuinely new endpoint).
- A purely internal change with no observable effect on the wire contract (refactoring the handler's internal implementation, renaming an internal variable, changing internal validation order that doesn't change accepted/produced values).
- Spec formatting-only changes (YAML/JSON reformatting, key reordering) with no semantic change to what's accepted or produced.
- Description/example/documentation-only changes in a spec, with no change to the schema itself.

A reviewer that flags every API-adjacent diff as risky is a worse reviewer than a selective one — false positives are an explicit failure mode for this reference, on par with missing a real breaking change.

## Evidence / reporting checklist

For every contract-compatibility finding (or explicit clearance), state:

- OLD contract and NEW contract, specifically (not "the API changed").
- REQUEST or RESPONSE.
- Who produces, who consumes.
- The concrete failure scenario for a breaking finding (what an existing client/consumer actually does that fails, not just "this could break someone").
- The evidence basis (formal spec found, manual source read, or tool output) and, if a formal spec wasn't found, that limitation stated explicitly.
- For a non-finding (clearance), why it's compatible — not just silence.
