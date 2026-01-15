# Voice2Machine Frontend (Tauri 2 + React 19)

AI agent instructions for the desktop GUI in `apps/frontend/`.

This app is **local-first**. The React UI talks to the Python daemon through **Tauri IPC** (React → Rust → Unix socket → Python). Keep UI logic thin; push heavy logic down to the daemon.

## Non-Negotiables (Repo Rules)

- Local-first: do not introduce network calls or telemetry unless explicitly requested.
- Docs as code: if a change affects behavior, update documentation (Spanish) under `docs/docs/es/`.
- Code comments should be in **Latin American Spanish**.
- Never add secrets (API keys, tokens) to the repo.

## Tech Stack (Current)

- React `19.1.x`, Vite `7.x`, TypeScript `5.8.x`
- Tauri `2.x`
- Tailwind CSS `4.1.x`
- State: Zustand (`src/stores/*`)
- Forms/validation: React Hook Form + Zod (`src/schemas/*`)
- Tests: Vitest + Testing Library (`happy-dom`)

## Development Prerequisites

- Node.js 20+.
- Rust (stable toolchain) for `npm run tauri dev` / `npm run tauri build`.
- Linux system deps (Ubuntu example): `libwebkit2gtk-4.1-dev`.
- For realistic UI behavior, run the Python daemon (the UI will otherwise show `disconnected`).

## Package Manager

- Use `npm` by default.
- Ask first before running `npm install` or changing dependencies.
- Do not regenerate or switch lockfiles (there may be more than one in-repo).

## Fast Commands (Prefer File-Scoped)

Run commands from `apps/frontend/`.

### Validate quickly (preferred)

- Typecheck: `npx tsc -p tsconfig.json --noEmit`
- Lint (whole app): `npx eslint .`
- Lint (single file): `npx eslint src/path/to/file.tsx --fix`
- Tests (watch): `npm test`
- Tests (single file, CI-style): `npx vitest run src/path/to/test.spec.tsx`

### Dev / Build

- Web dev (fastest): `npm run dev`
- Desktop dev: `npm run tauri dev`
- Web build: `npm run build`

Only run these when explicitly requested (slow / environment-dependent):

- Desktop build: `npm run tauri build`

## Project Map (Where Things Live)

- Entry: `src/main.tsx`
- App shell + navigation: `src/App.tsx`
- UI components: `src/components/`
- Hooks: `src/hooks/`
- State stores (Zustand): `src/stores/`
- Schemas (Zod): `src/schemas/` (e.g., config validation)
- Types: `src/types.ts`, `src/types/ipc.ts`
- Styling: `src/styles/` + Tailwind config
- Tauri bridge (Rust): `src-tauri/` (IPC, socket, permissions)

## Code Standards

### Formatting

Follow `.prettierrc`:

- Semicolons enabled
- Double quotes (`singleQuote: false`)
- `printWidth: 80`

If you need an auto-fix, use `npx eslint ... --fix` (do not assume Prettier is installed).

### TypeScript / React

- Prefer function components + hooks.
- Avoid `any`; type public APIs and exported helpers.
- Use the `@` alias for imports from `src/` when it improves readability.
- Keep hooks pure: no side effects during render.
- Keep component props small; push cross-cutting state into stores.

## Key Architecture Patterns (Copy These)

### 1) Backend communication: store-first

- Tauri commands are invoked from stores (example: `src/stores/backendStore.ts`).
- UI components should call store actions instead of calling `invoke(...)` directly.

When adding/modifying a command:

- Update the call site in `src/stores/backendStore.ts`.
- Keep TS types aligned with `src/types/ipc.ts` (mirrors Rust structs).
- If the Rust side changes, update `src-tauri/src/lib.rs` accordingly.

### 2) State updates: events + polling fallback

- `src/components/BackendInitializer.tsx` subscribes to `v2m://state-update` and falls back to polling `get_status`.
- Don’t add additional poll loops in random components.

### 3) Config UX: Zod schema is the source of truth

- Validate config forms with `src/schemas/config.ts` and `react-hook-form`.
- Treat `GeminiConfig.api_key` as sensitive:
  - Never log it.
  - Never add default real keys.
  - Prefer masking in UI when displayed.

## Testing Guidelines

- Add/extend tests whenever you fix a bug or add behavior.
- Prefer Testing Library queries by role/label/text; use `data-testid` only when needed.
- Keep tests small and deterministic; mock Tauri `invoke`/events at the boundary.
- Great places to add unit tests:
  - Pure helpers in `src/utils.ts`
  - Hooks with isolated logic (mock external deps)

## UX & Accessibility

- Keyboard-first flows must work (navigation, modals, shortcuts).
- Ensure focus management for dialogs/modals.
- Use semantic HTML; add descriptive alt text for images/icons when applicable.

## Git / PR Expectations

- Small, focused diffs; no drive-by refactors.
- Do not change lockfiles unless necessary and explicitly requested.
- If behavior changes, update docs (Spanish) and keep `README.md`/`LEEME.md` in sync when relevant.

## Boundaries

### Always do

- Read the nearest AGENTS.md (this file) + repo root rules.
- Run fast checks (typecheck + targeted tests) for changed areas.
- Keep changes consistent with existing patterns and naming.

### Ask first

- Installing/upgrading deps (`npm install`, new packages) or changing lockfiles.
- Running slow commands (`npm run tauri build`) or doing cross-app refactors.
- Changing Rust code in `src-tauri/` (unless the task explicitly involves IPC).
- Deleting/renaming files or changing app permissions.

### Never do

- Commit secrets, API keys, tokens, or private URLs.
- Add analytics/telemetry/network calls that violate local-first.
- Weaken security checks in the IPC bridge / permissions.

## Common Pitfalls (Avoid)

- Don’t call `invoke(...)` directly from components; route through stores.
- Don’t add extra polling loops; use `BackendInitializer`.
- Don’t log or persist secrets (e.g., `GeminiConfig.api_key`).
- Don’t introduce network requests or telemetry by default.

## If Something Seems Off

- UI shows “disconnected”: confirm the Python daemon is running and the IPC bridge is healthy.
- IPC changes failing: verify command names match between `invoke("...")` and the Rust command handlers.
