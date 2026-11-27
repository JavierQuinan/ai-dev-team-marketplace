# Frontend engineering patterns

Load only when frontend scope warrants it. Detect stack and versions from repository manifests and lockfiles; do not infer from file names alone. Follow existing routing, state and component conventions.

## Framework-neutral
- Reuse existing primitives and design tokens; separate view state from server state.
- Explicit loading/empty/error/success/permission states; prevent duplicate submission and stale response races.
- Semantic controls, keyboard navigation, focus restoration, accessible names and reduced motion; test rather than claim compliance.
- Responsive layout with content-driven breakpoints; verify representative narrow/wide viewports.
- Avoid leaking sensitive data to client logs or storage; authorization remains server-side.
- Measure rendering/network performance before optimizing; no new dependency without justification and approval where required.

## Evidence-driven framework notes
React/Next.js: inspect server/client component boundaries, hooks and existing cache strategy. Angular: inspect standalone/module conventions, signals/RxJS and existing DI/state. Vue/Nuxt: inspect composables, SSR and store conventions. Svelte/SvelteKit: inspect load/actions and reactivity conventions. Only apply rules for versions actually present.

## Handoff
Consume accepted design and API contracts. Report actual lint/typecheck/build/test and browser checks separately; missing checks are NOT RUN.
