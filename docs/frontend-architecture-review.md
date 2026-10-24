# Frontend Architecture Review — Findings and Remediation Plan

Working document derived from an evidence-based architecture review of
`frontend/`. Each finding has a stable ID, code-level evidence, a suggested
solution, and acceptance criteria. It is meant to be **manually fine-tuned**:
edit statuses, reorder phases, or drop findings before handing a phase to an
AI agent.

Companion document: `docs/frontend-architecture.md` (frontend orientation).
Repository rules in `AGENTS.md` apply to all work here (never commit, run
all quality gates, English only, no new dependencies without asking).

## How agents should use this document

- Work **one phase at a time, one finding at a time** unless a finding
  explicitly groups related ones. Do not mix phases in one change set.
- Before starting a finding, re-read the referenced source files: the
  evidence below was verified at review time (2026-10-22) but may have moved.
- After each finding, run the quality gates and satisfy the acceptance
  criteria before moving on.
- Lines prefixed with `SUGGESTION:` are proposals, not decisions. If the
  chosen approach conflicts with code reality, stop and flag it rather than
  improvising a different architecture.
- Lines prefixed with `DECISION:` are what the AI agents should follow.

## Quality gates (after every finding)

```bash
# Frontend findings (from frontend/)
npm run lint
npm run type-check
npm run knip
npm run test
# Or from repo root
make frontend-test

# Backend findings (S2 backend part, S5b backend part, E3 backend half)
pytest
tox -e lint
tox -e type
# Or from repo root
make backend-test
make lint
```

## Status legend

| Status | Meaning |
|---|---|
| `todo` | Not started |
| `in-progress` | Assigned/being worked |
| `blocked` | Waiting on a decision or another finding |
| `done` | Implemented and gates pass |
| `rejected` | Reviewed and deliberately not done (record why) |

## Phase overview

| Phase | Theme | Findings | Risk profile |
|---|---|---|---|
| 1 | Security quick wins | S1, S2, S3, S4 | Small, contained, high value |
| 2 | Delivery and delivery safety | E1, S5 (frontend 5a + backend verification/gaps) | Mechanical, no behavior change |
| 3 | Error handling and observability | M2, E3 (backend + frontend) | Small frontend + backend coordination |
| 4 | Data grid decomposition | M1, E2 | Largest refactor, enables the rest |
| 5 | Consistency and contracts | M3, M4, M5, M6, E4, E5 | Cleanup + documentation |

Findings with backend work (S2 backend part, S5 backend part,
E3 backend half) can be assigned to a backend-focused agent
independently of the frontend halves. S2 and E3 both require lockstep
frontend/backend shipping.

---

# Phase 1 — Security quick wins

## S1: CSV/TSV formula injection in table exports

- **Priority:** High (top finding)
- **Category:** Security
- **Status:** `todo`
- **Evidence:**
  - `frontend/src/js/tableExport.ts` — `exportCsv` (quote escaping only) and
    `exportExcel` (raw `row.join('\t')`, no escaping at all)
  - `getExportValue` returns raw string values from user-imported
    transaction data (descriptions, merchant names from CSV files)
- **Risk:** A cell beginning with `=`, `+`, `-`, or `@` executes as a
  formula when the exported file is opened in Excel/Sheets (e.g.
  `=HYPERLINK(...)`, `=cmd|...`). Tab/newline characters in values also
  corrupt the TSV output. Imported bank CSVs are semi-trusted at best.
- **Acceptance criteria:**
  - CSV/XLS export functionality is deleted.
  - `npm run knip` clean, all gates pass
- **DECISION:** The CSV/XLS export is an incomplete feature, it was never used. Drop the whole feature completely. Users can use export/takeaway provided by GDPR guardrail to save their data.
  - Blast-radius:
    - VueDataTable - showExport/csvText/excelText props, exportCSV/exportExcel functions
    - buttons block, includeInExport in  types/column.ts, useAggregatedGroups.ts, PivotTable.vue, CategoryMonthTransactions.vue
    - delete frontend/src/js/tableExport.ts, test/tableExport.test.ts, export tests in VueDataTable.test.ts,
    - re-extract gettext strings

## S2: CSRF token persisted in localStorage

- **Priority:** High
- **Category:** Security
- **Status:** `todo`
- **Evidence:**
  - `frontend/src/js/csrfToken.ts` — module-level variable backed by
    `localStorage` under key `csrfToken`
- **Risk:** localStorage is readable by any XSS payload; the token outlives
  the page load it was minted for. The comment justifies persistence as
  avoiding token re-minting, but `authStore.initialize()` and the request
  retry path already self-heal stale/missing tokens.
- **DECISION (revised 2026-10-22): Option 1 — deliver the token as a
  readable cookie instead of response bodies (backend change).**
  Rationale: the backend rotates the stored hash on every mint
  (`AuthSessionService.refresh_csrf_token` — each newly issued token
  invalidates the previous one), so per-tab in-memory tokens would
  ping-pong 403 → retry → mint in multi-tab use. The earlier "no
  cross-tab benefit" claim was wrong; cookie delivery keeps cross-tab
  sharing (cookies are shared across all tabs of the origin by
  construction) while eliminating localStorage entirely, and ties the
  token's lifetime to the session's.
  1. Backend: on every response that currently carries `csrf_token` in
     the body (login, register, getMe, `/auth/csrf-token`), set it as a
     cookie instead: `Set-Cookie: csrf_token=<token>; Secure;
     SameSite=Strict; Path=/api/v2` — deliberately **not** HttpOnly (the
     frontend must read it). Remove the body field (breaking change,
     shipped in lockstep with the frontend — same constraint as E3).
     Logout clears the cookie (`Max-Age=0`). In standalone
     (cross-origin) deployments the cookie must be `SameSite=None;
     Secure` — the session cookie already requires the same relaxation
     there, so this adds no new exposure.
  2. Frontend: `csrfToken.ts` shrinks to a cookie reader
     (`getCsrfToken()` parses `document.cookie`); delete `setCsrfToken`,
     the module variable, and all localStorage code. The auth store
     stops managing tokens (no more `setCsrfToken` calls). The 403
     retry in `request.ts` stays: `GET /auth/csrf-token` refreshes the
     cookie and the request retries once — rotation is instantly
     visible to every tab via the cookie, so no mint ping-pong.
  3. Trust note (document in the code): the cookie is not HttpOnly, so
     XSS can read it — but an XSS payload can already drive requests as
     the user in-page, so this adds no new capability. The win is that
     the token no longer persists beyond the session (the actual
     localStorage problem).
- **Acceptance criteria:**
  - No `localStorage` reference remains in `csrfToken.ts`; the module
    is a cookie reader only
  - Backend tests assert the `Set-Cookie` attributes (Secure,
    SameSite, Path, not HttpOnly) on mint/login/register/getMe, and
    that logout clears the cookie
  - Frontend test: token read from the cookie; a 403 CSRF retry
    refreshes the cookie and the retried request succeeds
  - Multi-tab: a rotation in one tab is immediately usable by the
    other tab (manual or e2e check) — no mint ping-pong
  - Backend and frontend ship in lockstep (same constraint as E3)
  - All gates pass on both sides


## S3: Dead `v-html` render path in the data grid

- **Priority:** Medium
- **Category:** Security + maintainability
- **Status:** `todo`
- **Evidence:**
  - `frontend/src/types/column.ts` — `renderHtml?: (…) => string`
  - `frontend/src/components/data/TableCell.vue:59` — `v-html` rendering
  - `frontend/src/components/data/VueDataTable.vue` — security note and
    export handling for `renderHtml` in `frontend/src/js/tableExport.ts`
  - Grep at review time found **zero page-level consumers** of
    `renderHtml`; only infrastructure references exist
- **Risk:** Retained attack surface (arbitrary HTML injection) with no
  active benefit. The `component`/`componentProps` mechanism covers every
  actual use case.
- **DECISION:** Remove the `renderHtml` path entirely:
  `types/column.ts`, `TableCell.vue` (v-html branch),
  `tableExport.ts` (`getExportValue` HTML-strip branch), and the
  VueDataTable security note. Knip and type-check will confirm no
  consumers break.
- **Acceptance criteria:**
  - No `v-html` remains outside `pages/Privacy.vue` and `pages/Legal.vue`
    (those render static content and are out of scope)
  - `npm run knip` clean; tests pass
- **Alternative (if a consumer is found during work):** keep the field but
  sanitize its output and raise `vue/no-v-html` from `warn` to `error`
  with targeted inline disables.

## S4: Popover directive renders HTML by default

- **Priority:** Medium
- **Category:** Security
- **Status:** `todo`
- **Evidence:**
  - `frontend/src/directives/popover.ts` — `html: options.html !== false`
  - `frontend/src/components/data/TableLinkWithPopover.vue` — passes
    `html: true` with `popoverContent` derived from imported transaction
    data (`frontend/src/pages/Categories.vue` via `getCellDetailsString`)
- **Risk:** Imported CSV data reaches Bootstrap popover HTML rendering.
  Bootstrap's sanitizer allowlist is permissive; the actual content here
  appears to be plain-text details.
- **DECISION:**
  1. Default `html` to `false` in the directive (opt-in per use).
  2. Change `TableLinkWithPopover` to not pass `html: true`.
  3. Change the `<br>` html tag join to `\n` and add `white-space: pre-line` CSS to the popover content class.
- **Acceptance criteria:**
  - Directive test covers text-only content path
  - Manual check (or screenshot test) that the Categories month-cell
    popover still displays its details correctly

---

# Phase 2 — Delivery and delivery safety

## E1: No route-level code splitting

- **Priority:** Medium (compounds with growth)
- **Category:** Extendability / performance
- **Status:** `todo`
- **Evidence:**
  - `frontend/src/router/index.ts` — all 17+ pages statically imported
  - Build output at review time: a single ~556 KB `dist/js/main.js` plus
    a ~2.6 MB sourcemap
- **DECISION:**
  1. Convert data-heavy/authenticated pages to lazy imports:
     `component: () => import('../pages/Categories.vue')`.
  2. Keep the Index (landing) and auth pages eager so first paint and
     login are fast.
  3. Consider a named chunk per route group if output filenames become
     unreadable.
- **Acceptance criteria:**
  - `npm run build` produces multiple `js/` chunks
  - All routes still resolve; router tests pass
  - No page's first navigation shows a blank screen without a loading
    indicator (use route-level loading state if needed)

## S5: Sourcemaps shipped to production; existing CSP unverified against a real build

- **Priority:** Medium
- **Category:** Security
- **Status:** `todo`
- **Correction (backend review, 2026-10-22):** The original finding said
  "add CSP for integrated mode". That is **already implemented** — the
  backend registers an `after_request` hook
  (`src/whatsthedamage/api/middleware.py` → `register_security_headers`,
  wired in `create_app` in `src/whatsthedamage/app.py`) that sets on every
  response:
  - Non-API (SPA) responses: `SPA_CSP` = `default-src 'self';
    script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self'
    data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';
    base-uri 'self'; form-action 'self'`
  - `/api/*` responses: `API_CSP` = `default-src 'none';
    frame-ancestors 'none'` plus `Cache-Control: no-store`
  - Plus `X-Content-Type-Options`, `X-Frame-Options: DENY`,
    `Referrer-Policy`, config-gated HSTS
  - Covered by `tests/api/v2/test_api_middleware.py`

  The remaining work is verification and gap-closing, not implementation.
- **Evidence:**
  - `frontend/vite.config.js` — `sourcemap: true` with no prod/dev
    distinction; `.map` files land in `frontend/dist/`
  - `src/whatsthedamage/controllers/frontend_routes.py` — the catch-all
    serves **any file that exists** under the static dist folder (the
    `file_path.exists()` branch has no extension filter), so `.map`
    files would be served once synced there
  - `src/whatsthedamage/view/static/dist/` is currently empty and no
    Make target populates it (the sync is manual) — so the existing
    `SPA_CSP` has never demonstrably run against a real build
- **SUGGESTION:**
  1. (S5a, frontend) Gate sourcemaps behind an env flag so production
     `dist/` has no `.map` files at all.
  2. (S5b-1, backend) Defense-in-depth: explicitly 404 requests for
     `*.map` in the frontend catch-all route so a stray map file can
     never be served, regardless of how dist gets populated.
  3. (S5b-2, backend) Verify `SPA_CSP` against a real production build:
     build the frontend, sync to `view/static/dist/`, and exercise
     login, import, tables, and charts under the header. Note
     `script-src 'self'` forbids inline scripts — fine with Vite's
     default build, but unverified. `style-src 'unsafe-inline'` is
     genuinely required (Vue inline style bindings + theme custom
     properties); do not attempt to tighten it without nonces (low
     value — leave it).
  4. (Docs) Standalone mode still has no CSP (the header comes from the
     static host, not Flask) — document the recommended CSP meta tag
     or host-header configuration in `docs/frontend-architecture.md`.
- **Acceptance criteria:**
  - Production `dist/` does not expose `.map` files (or this is explicitly
    approved and documented as intended)
  - Backend catch-all returns 404 for `.map` requests (test)
  - Built app verified working under `SPA_CSP` in integrated mode

---

# Phase 3 — Error handling and observability

## M2: No global Vue error handler

- **Priority:** Medium
- **Category:** Maintainability / observability
- **Status:** `todo`
- **Evidence:**
  - No `app.config.errorHandler`, `onErrorCaptured`, or
    `unhandledrejection` listener anywhere in `src/`
  - `frontend/src/js/logger.ts` is only a console wrapper; errors reach
    end users' consoles but nothing else
- **SUGGESTION:**
  1. In `main.ts`, set `app.config.errorHandler` and register a
     `window.addEventListener('unhandledrejection', …)`, both routed
     through `logger` (console-only — see backend review below).
  2. Never log payloads containing sensitive data; log component stack and
     message only.
- **Acceptance criteria:**
  - A deliberately thrown error in a page is captured by the handler
    (unit test mounting an app with a failing component)
  - Quality gates pass
- **Backend review (2026-10-22): no endpoint needed.** The backend already
  has server-side observability: `src/whatsthedamage/api/error_handlers.py`
  → `handle_generic_exception` logs unexpected `/api/*` exceptions with
  request context (path, method, user agent, remote addr — no sensitive
  payload) and returns a generic 500. Recommendation: the frontend handler
  logs to console only — **do not add a client-error ingestion
  endpoint**. This is a self-hosted, GDPR-conscious app with a retention
  policy; a reporting endpoint would create a new personal-data surface
  (stack traces can contain user data) for little operational gain.
- **DECISION:** the frontend handler logs to console only

### M2-B: Backend "proper fix" for the 8160b33 catch-all logging

- **Status:** `rejected` (independent of the frontend work; pure backend)
- **Evidence:** Commit 8160b33 added ad-hoc `logger.exception(...)` calls
  inside bare `except Exception:` blocks in
  `src/whatsthedamage/api/v2/auth/endpoints.py` (login, logout,
  update_me, change_password, export), `api/v2/endpoints/reference.py`,
  and `controllers/routes.py` — the commit message itself says "needs
  proper fix". Those catch-alls swallow unexpected exceptions **before**
  the central `handle_generic_exception` ever sees them, which is why
  the logging had to be bolted on endpoint-by-endpoint.
- **SUGGESTION:** Narrow each bare `except Exception` to the expected
  exception types (the specific auth/validation errors the endpoint
  already handles) and let genuinely unexpected errors propagate to
  `handle_generic_exception`. Then delete the ad-hoc
  `logger.exception` lines. One logging site, one format, all
  endpoints — including future ones.
- **Acceptance criteria:**
  - No ad-hoc `logger.exception` in per-endpoint catch-all blocks remains;
    unexpected exceptions surface via `handle_generic_exception`
  - `tests/api/v2/test_auth_error_logging.py` updated to assert the
    central handler logs instead of per-endpoint blocks
  - Backend gates pass (`pytest`, `tox -e lint`, `tox -e type`)
- **DECISION:** will be treated as a separate backend work item (out of scope)

## E3: CSRF failure detection depends on English error copy

- **Priority:** Medium
- **Category:** Extendability / robustness (frontend + backend)
- **Status:** `todo`
- **Evidence:**
  - `frontend/src/js/api/request.ts` — `isInvalidCsrfTokenError` matches
    `/invalid csrf token/i` against the parsed error **message string**
  - Backend: the target string is produced at
    `src/whatsthedamage/api/auth_decorators.py:133`:
    `jsonify({'error': 'Invalid CSRF token'}), 403` — **no `code`
    field**
  - The code infrastructure already exists and is in active use:
    `_create_error_response(message, status_code, error_code,
    retry_after)` in `api/v2/auth/endpoints.py` (used with
    `AUTHENTICATION_FAILED`, `VALIDATION_ERROR`) and
    `rate_limit_response` in `api/middleware.py` already emitting
    `code: 'RATE_LIMIT_EXCEEDED'`
- **Risk:** A backend message change silently breaks the automatic CSRF
  retry, surfacing as confusing 403s for users.
- **DECISION:**
  1. Backend: add `code` to all four 403 responses in the `require_csrf`
     decorator (it guards auth + transactions, corrections, statistics,
     and processing results endpoints):

     | Current message (`auth_decorators.py`) | Suggested `code` |
     |---|---|
     | `CSRF token requires authenticated session` | `CSRF_SESSION_REQUIRED` |
     | `CSRF token required for state-changing requests` | `CSRF_TOKEN_MISSING` |
     | `Session has no CSRF token` | `CSRF_TOKEN_NOT_SET` |
     | `Invalid CSRF token` | `CSRF_TOKEN_INVALID` |

     Keep the messages unchanged (frontend compatibility).
     Implementation: `_create_error_response` is auth-blueprint-local
     but the decorator is app-wide — hoist the helper to a shared
     module (e.g. `api/helpers.py`, next to the error handlers) and
     reuse it from both places; `rate_limit_response` in
     `middleware.py` hand-rolls the same shape and should adopt it too
     (DRY).
  2. Frontend: match on `code`, remove regex on message.
  3. Update the API types (`src/types/`) for the error shape.
- **Acceptance criteria:**
  - Backend tests assert `code` presence on all 403 CSRF paths (extend
    the existing `tests/api/v2/` middleware coverage) so the frontend
    retry contract cannot regress silently
  - Retry path covered by a frontend unit test using the `code` field
  - Backend gates pass (`pytest`, `tox -e lint`, `tox -e type`) and
    frontend gates pass
  - Backend and frontend ship at the same time to avoid backward compatibility issues.

---

# Phase 4 — Data grid decomposition

## M1: VueDataTable is a god component (893 lines)

- **Priority:** High (enabling refactor for E2 and future grid features)
- **Category:** Maintainability
- **Status:** `todo` — **largest single work item; do not mix with other
  findings. Split into reviewable milestones.**

- **Evidence:**
  - `frontend/src/components/data/VueDataTable.vue` — sorting,
    pagination, global search, column filters, row highlighting,
    aggregate rows, CSV/Excel export, Bootstrap styling, all in one
    component
  - Every new column capability currently must stay in sync across
    VueDataTable, TableCell
- **DECISION:**
  1. Extract `useTableSorting` composable (sort state + comparator)
  2. Extract `useTableFiltering` (global search + per-column filters)
  3. Extract `useTablePagination`
  4. Extract `useTableHighlight` (row highlighting config handling)
  - Keep each extraction behavior-preserving: existing
    `VueDataTable.test.ts` must pass unchanged after every milestone.
- **Target state:** VueDataTable is orchestration + template; each
  composable has its own test file.
- **Acceptance criteria:**
  - VueDataTable drops to a fraction of its current size (no fixed
    number; reviewable templates + wiring)
  - No public behavior change; existing tests pass without modification
    (add new tests per composable)
- **Dependencies:** S1, S3 (removing `renderHtml`) should land first to avoid
  migrating a dead code path.

## E2: Column API grows by flag accumulation

- **Priority:** Medium
- **Category:** Extendability
- **Status:** `todo`
- **Evidence:**
  - `frontend/src/types/column.ts` — `renderHtml`, `component`,
    `componentProps`, `filterChoices`, class/classFn, aggregate config;
    each new capability touches three files (see M1)
- **DECISION:**
  1. After M1, prefer Vue **slots** for new cell-rendering needs
     (`#cell-<key>` scoped slots) instead of extending the
     `component`/`componentProps` indirection.
  2. Document the chosen extension pattern in
     `docs/frontend-architecture.md` so agents stop inventing new ones.
  3. Do not break existing `component` usage; slot support is additive.
- **Acceptance criteria:**
  - A documented, tested slot-based example renders a custom cell
  - Existing `component`-based columns unchanged

---

# Phase 5 — Consistency and contracts

## M3: Convention drift (localStorage and null usage)

- **Priority:** Low
- **Category:** Maintainability
- **Status:** `todo`
- **Evidence:**
  - `frontend/src/pages/Index.vue` — raw `localStorage`
    get/set/remove for the selected result, bypassing `usePersistentRef`
  - `null` used pervasively (`routeUtils.extractResultId`, `useApiData`
    return type, `dataset` metadata) despite the "never use null"
    convention in the onboarding doc
- **DECISION:**
  1. Migrate Index.vue to `usePersistentRef`.
  2. Compare to updated rules outlined in bullet point "Nullability rule:" in `AGENTS.md` and ask users confirmation before move on.
- **Acceptance criteria:**
  - No raw `localStorage` outside `usePersistentRef.ts` and
    `csrfToken.ts` (and none in csrfToken.ts after S2)

## M4: Inconsistent async error/loading patterns across composables and stores

- **Priority:** Low (cost of change is small; only a handful of consumers)
- **Category:** Maintainability
- **Status:** `todo` (split into M4a/M4b/M4c below; can be worked separately)
- **Evidence (verified 2026-10-22, deeper than the first pass):**
  The problem is not two overlapping composables — it is **five**
  coexisting async error/loading conventions:

  | Pattern | Where | Loading | Error semantics | Presentation |
  |---|---|---|---|---|
  | `useApiData` | Categories, PivotTable, `useDrilldownData` | own `isLoading` | stores, swallows (no rethrow) | feedback toast **and** `error` ref (double-reported); needs an injected i18n `t` |
  | `useAsyncAction` | Settings.vue only (5 instances) | own `isLoading` per instance | stores, swallows, returns `T \| undefined` | page reads `error` ref |
  | `useTransactionCorrections` | Transactions, CategoryMonthTransactions | none (cells own it) | **rethrows** | success toast; error displayed inline by `EditableCell`/`UndoCorrectionCell` |
  | `withLoading` in `stores/auth.ts` | auth store actions | `isLoading` | stores, **rethrows** | `authStore.error` |
  | Hand-rolled try/catch | Login.vue, form store + `useFormWithNavigation` | page-local | mixed | varies |

- **Why it matters:**
  - `useAsyncAction` swallows errors and returns `undefined`, so callers
    cannot distinguish "succeeded with no result" from "failed", and the
    `T | undefined` return forces checks even for actions that always
    return a value
  - `useApiData` swallows errors, so a failed refetch silently leaves
    stale data with no way for the caller to react; it also mixes three
    concerns (fetching, i18n via `t`/`errorMessageKey`, presentation via
    the feedback store) while pages already render errors via
    `ErrorState` — the toast is a redundant second channel
  - Settings.vue instantiates `useAsyncAction` five times → five
    independent loading/error pairs
  - Agents (and humans) must guess which contract applies

- **Recommendation (rationale):** Do **not** merge the two composables —
  they serve distinct concerns; merging produces a configuration-driven
  blob. Sharpen each contract instead, retire the redundant
  store-internal wrapper, and document three sanctioned patterns:

  ```text
  Page-load data          → useApiData (data/isLoading/error; page renders ErrorState; no toast)
  User-triggered command  → useAsyncAction (store error + rethrow; page decides presentation)
  Inline/cell errors      → rethrow from the API wrapper; owning cell displays it
  ```

  No new dependencies (no TanStack Query etc.): the `dataset` store
  already owns caching, and AGENTS.md requires approval for npm additions.

### M4a: Fix `useAsyncAction` contract (store + rethrow)

- **Status:** `todo`
- **DECISION:** store the error message as today, then **rethrow** (the
  semantics `withLoading` in the auth store already has). Return type
  becomes an honest `Promise<T>`. Update Settings.vue accordingly — its
  five instances can share one instance where "an operation is running"
  should be a single state.
- **Acceptance criteria:**
  - M2 should land first, or M2 should land together with M4a
  - Composable unit tests: error stored AND rethrown; loading resets in
    `finally`
  - Settings.vue compiles and its tests pass; no caller treats
    `undefined` as "failure" anymore
  - Settings.vue should catch rethrown errors from click handlers at the call site

### M4b: Decouple `useApiData` (fetching only, single error channel)

- **Status:** `todo`
- **DECISION:**
  1. Remove the feedback-store push and the `t`/`errorMessageKey`
     coupling. Return `data`, `isLoading`, `error`; pages already render
     `ErrorState` — the toast is duplicate reporting.
  2. Keep an optional `onError?: (err: unknown) => void` hook for pages
     that need a side effect on failure.
  3. Update consumers: Categories.vue, PivotTable.vue,
     `useDrilldownData.ts` (and through it MonthCategoriesList,
     CategoryMonthsList, CategoryMonthTransactions). Verify nothing
     depended on the toast.
- **Acceptance criteria:**
  - `useApiData` is unit-testable with a plain `fetchFn`, no Pinia or
     gettext setup
  - No double error reporting remains on the touched pages; gates pass

### M4c: Auth store adopts `useAsyncAction`; document the three patterns

- **Status:** `todo` (depends on M4a)
- **DECISION:**
  1. Replace the auth store's internal `withLoading` with
     `useAsyncAction` once its contract matches (store + rethrow) —
     one pattern retires.
  2. `useTransactionCorrections` stays as-is: its rethrow-for-inline
     contract is correct for editable cells. Document it as the third
     sanctioned pattern (see the rule box above), not as drift.
  3. Document the decision rule in `docs/frontend-architecture.md`
     (composables section).
- **Acceptance criteria:**
  - No `withLoading` wrapper remains in `stores/auth.ts`; auth tests pass
  - Onboarding doc names the rule and the three patterns

## M5: API types hand-duplicated from backend Pydantic

- **Priority:** Low (drift risk grows with API churn)
- **Category:** Maintainability
- **Status:** `todo`
- **Evidence:**
  - `frontend/src/types/api.ts`, `frontend/src/types/auth.ts` mirror
    backend Pydantic models with no sync mechanism
- **SUGGESTION:** Add a contract test: the backend generates a JSON schema
  (or fixtures) for its API models; the frontend test asserts its types
  against a checked-in fixture. Cheaper than code generation, catches
  drift at gate time. Exact mechanism is an open design decision —
  prototype in a scratch branch before committing to it.
- **Acceptance criteria:**
  - A failing backend change breaks a frontend test (demonstrate once)

## M6: `exportExcel` writes TSV with an .xlsx extension

- **Priority:** Low
- **Category:** Maintainability / correctness
- **Status:** `rejected` subsumed by S1
- **Evidence:**
  - `frontend/src/js/tableExport.ts` — `.xlsx` filename with TSV content
    and `application/vnd.ms-excel` MIME; values are not escaped (also
    covered by S1)
- **DECISION:**
  1. S1 already removes this feature.
- **Acceptance criteria:**
  - `tableExport` functionality is removed, callers are updated.

## E4: Locale change re-mounts the entire Layout

- **Priority:** Low
- **Category:** Extendability / UX
- **Status:** `todo` (verify before changing)
- **Evidence:**
  - `frontend/src/App.vue` — `<Layout :key="currentLocale">` forces a
    full subtree remount on language switch, discarding table state,
    scroll position, and popover instances
- **DECISION:**
  1. First verify whether dropping the `:key` works: vue3-gettext is
     reactive, but some texts may not re-render if components captured
     translated strings at setup time.
  2. If strings are captured, fix those components to compute them
     reactively rather than remounting the world.
- **Acceptance criteria:**
  - Language switch updates all visible text without a Layout remount
    (or the remount is documented as a deliberate workaround with the
    reason)

## E5: Full dataset held reactively in memory, no ceiling documented

- **Priority:** Low (today) / watch item
- **Category:** Extendability / scaling
- **Status:** `todo` (documentation task first)
- **Evidence:**
  - `frontend/src/stores/dataset.ts` — complete transaction list per
    resultId cached in reactive arrays; the module doc itself notes
    "potentially tens of thousands of rows"
- **DECISION:**
  1. Document the scaling ceiling and the intended break-glass plan
     (server-side pagination + windowed rendering) in
     `docs/frontend-architecture.md`.
  2. Optional: add a lightweight size log (`logger.debug`) when a dataset
     exceeds a threshold so real-world sizes become observable before
     the ceiling is hit.
- **Acceptance criteria:**
  - Onboarding doc records the ceiling and the planned evolution
  - No premature pagination refactor without evidence it is needed

---

# Notes and open decisions

- **Backend review (2026-10-22) folded in.** S5b is now
  verification/gap-closing (the CSP already exists — see S5). **S2
  now includes a backend change** (deliver the CSRF token as a readable
  cookie — see S2). E3 needs a small backend change (CSRF `code`
  fields — see E3). M2's console-only decision is recorded — no
  backend endpoint needed; the 8160b33 "proper fix" is tracked as
  **M2-B**. Sequence the backend work items separately; split agents
  per side of the API boundary where convenient.
- **S2 cookie flags recorded** (see S2): session cookies are Secure +
  HttpOnly + SameSite=Lax by default; the CSRF mint rotation is the
  reason cookie delivery was chosen over per-tab in-memory tokens.
- Remaining audit caveat (a human should sanity-check):
  - Runtime memory for E5 was not measured; the ceiling is theoretical.
- Findings intentionally **not** scheduled: none rejected at review time; M6 (subsumed by S1) and M2-B (out of scope) were rejected during planning — see their sections
  Record any rejection here with a reason.
