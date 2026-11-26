# Ecosystem architecture and evolution

Status: proposed strategy; existing release evidence remains authoritative. Marketplace is the public distribution surface for native Claude Code skills and agents. Core is the public canonical specification and conformance foundation. External clients may implement the contracts independently. Existing plugin remains self-contained; generate or vendor versioned public artifacts only when packaging tests prove installability. No private service dependency for OSS workflows.

## Boundaries and governance
Apache-2.0 remains unchanged; preserve notices, attribution and third-party licenses. No customer data, private prompts, credentials, internal service implementation or business-sensitive material in public commits. Brand rights are separate; no trademark registration is claimed. Review contributor rights and dependency provenance before publication. Use synthetic fixtures, independent review and explicit approvals for irreversible actions. No release claims without exact-head evidence.

## Contract authority transition
Phase 2A semantic handoffs remain authoritative for the current plugin. Core may draft candidate wire schemas in parallel, but cannot publish a canonical version until #36 acceptance and explicit mapping review. Preserve semantic equivalent wording for native Claude workflows; schema serialization is an adapter boundary, not a mandatory prompt output format. No public dependency on private packages. Do not require full 2E completion merely to draft a schema; integration and release remain gated.

## Delivery sequence
1. v0.3: preserve stacked draft PR #35/#36 and issues #30–34. Validate semantic handoffs, contract freeze, disjoint write ownership and runtime regression before expansion.
2. v0.4: expand specialist roles and team templates incrementally; separate plugins only after demonstrated distinct responsibilities and packaging tests.
3. v0.5: portable contracts from Core, adapters and capability negotiation; native Claude support first, other providers only after conformance.
4. v0.6+: durable execution and richer integrations where evidence justifies them. No public release dates or parity promises.

## Release gates
Official Claude CLI strict validation, repository validator, fixtures for each new skill, real runtime trials with positive and negative controls, task evidence tied to exact commit, independent QA/security, backwards compatibility, install test from packaged artifact, license and secret scan. Report PASS/FAIL/BLOCKED/INCONCLUSIVE accurately. Do not merge existing drafts or widen their scope through this strategy.
