# Delivery evidence

Release readiness is a recommendation, not an action. Capture intended version, exact source SHA and tested revision, changed scope, required checks and actual results, review findings and dispositions, migration and rollback plan where applicable, artifact identity/digest when available, dependency and security gates, and human approvals still pending.

GO requires current evidence for all mandatory gates and no unresolved required findings. CONDITIONAL GO is only for explicitly permitted optional residual risks with owner and rationale; never for missing required checks. NO-GO for failed, blocked, stale or unexecuted mandatory checks. Do not manufacture release evidence from static evals.

Deployment planning records target environment, artifact, prerequisite approvals, preflight, rollout, health checks, abort thresholds, rollback and verification owner. Do not deploy, merge, publish or mutate production. Actual deployment status may be reported only from external observed evidence tied to the artifact and environment; otherwise label planned/not executed/unknown.

If a CI failure is involved, use ci-failure-diagnosis.md and preserve original failure evidence.
