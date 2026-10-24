# Frontend Architecture — AI Agent Onboarding

This document orients AI coding agents working in `frontend/`. All facts were
extracted from the codebase; verify against source when the code and this
document disagree. Also read the repository-level `AGENTS.md` first — its
rules (never commit, run quality gates, no summary files, etc.) always apply.

## Stack (verified from `frontend/package.json`)

- **Vue 3.5** with Composition API and `<script setup>` syntax
- **TypeScript 6** (`tsconfig.json`, `strict: true`, path alias `@/*` → `./src/*`)
- **Vite 8** build tool, ESM modules (`"type": "module"`)
- **Pinia 3** state management
- **Vue Router 5** (`createWebHistory`) with auth navigation guards
- **vue3-gettext 4** for i18n (English, Hungarian)
- **Bootstrap 5.3** CSS (plus Popper.js); chart.js 4 via vue-chartjs
- **Vitest 4** + jsdom for tests; ESLint 10 + Prettier; Knip for dead-code detection
- Node.js 24+

## Where things live

```text
frontend/
├── index.html              # Vite entry
├── vite.config.js          # Build, dev proxy, Vitest config
├── eslint.config.js        # ESLint (flat config)
├── knip.config.js          # Unused file/export detection
├── tsconfig.json           # Strict TS, @/* alias
├── public/                 # Static assets copied verbatim
└── src/
    ├── main.ts             # App bootstrap (see below)
    ├── App.vue
    ├── pages/              # Route-level components (one per route)
    ├── components/
    │   ├── auth/           # PasswordResetForm, RecoveryCodeDisplay
    │   ├── charts/         # BarChart, PieChart (chart.js wrappers)
    │   ├── data/           # VueDataTable, TableCell, EditableCell, UndoCorrectionCell, ...
    │   └── layout/         # BreadcrumbNavigation, PageHeader, LoadingState, ErrorState
    ├── composables/        # Reusable Composition-API functions
    ├── stores/             # Pinia stores (one file per store)
    ├── router/index.ts     # Route table + auth guard
    ├── js/
    │   ├── api.ts          # Barrel re-exporting js/api/*
    │   ├── api/            # request.ts (transport), auth.ts, transactions.ts, processing.ts
    │   ├── themes/         # Theme definitions + picker
    │   └── ...             # csrfToken, dateUtils, gettext, logger, resultsTransform, routeUtils
    ├── directives/popover.ts
    ├── config/             # auth-config.ts, highlight-config.ts
    ├── types/              # api.ts, auth.ts, column.ts, index.ts (AppError)
    ├── locales/            # en.po, hu.po, messages.pot, translations.json
    └── css/                # main.css, auth.css (imported after Bootstrap)
```

Tests live in `frontend/test/` (Vitest, `test/**/*.{test,spec}.?(c|m)[jt]s?(x)`,
`test/setup.ts` global setup).

## Application bootstrap (`src/main.ts`)

Order matters and is deliberate:

1. `createApp(App)`, install Pinia
2. Eagerly initialize the categories store
   (`useCategoriesStore().loadCategories()` — fire-and-forget, errors logged)
3. Install vue3-gettext, then the router
4. Register the global `v-popover` directive; Bootstrap is assigned to
   `globalThis.bootstrap` for popover support
5. Mount to `#app`

Custom CSS is imported after Bootstrap's stylesheet so overrides win.

## Routing and authentication (`src/router/index.ts`)

Routes are flat; each maps to a component in `src/pages/`. Route `meta`
drives access control:

| Meta flag | Meaning |
|---|---|
| `requiresAuth: true` | Redirect unauthenticated users to `/login` with `?redirect=<fullPath>` |
| `requiresGuest: true` | Redirect authenticated users to `/` |
| `public: true` | No auth requirements |

Key authenticated routes: `/` (Index), `/import`, `/settings`, `/results`
(Categories), `/results/accounts/:accountId/...` drilldowns,
`/transactions`, `/pivot`, `/statistics`. Auth pages: `/login`,
`/register`, `/forgot-password`, `/logout`. Catch-all `/:pathMatch(.*)*`
renders NotFound.

A single global `router.beforeEach` guard:

- Restores the session from cookies on first navigation
  (`authStore.initialize()` — runs even for public routes)
- Enforces `requiresAuth` / `requiresGuest`

Pages never re-initialize the auth store themselves.

## API layer (`src/js/api/`)

All backend communication goes through this layer. Backend is a separate
Flask app exposing REST API v2; the frontend never renders server-side
templates.

- **`request.ts`** — the single transport:
  - Base URL: `import.meta.env.VITE_API_BASE_URL ?? '/api/v2'`
  - Always sends cookies (`credentials: 'include'`)
  - Attaches `X-CSRF-Token` from `js/csrfToken.ts` to POST/PUT/DELETE/PATCH
  - On a 403 "invalid csrf token", mints a fresh token from
    `GET /auth/csrf-token` and retries the request exactly once
  - Throws `AppError` (from `types/index.ts`) on failure; parses
    `error` / `message` / `detail` from JSON error bodies
  - Exposes `request<T>()`, `postData<T>()`, `getApiUrl()`
- **`auth.ts`** — register, login, logout, getMe, fetchCsrfToken,
  resetPassword, deleteAccount, updateUsername, changePassword,
  exportMyData, updateSharingPreference
- **`transactions.ts`** — fetchTransactionsByResult, fetchAllTransactions,
  updateTransaction, undoTransaction, fetchAggregatedTransactions,
  fetchMonthCategories, fetchCategoryMonthTransactions
- **`processing.ts`** — createTransaction (multipart upload),
  recalculateStatistics, fetchCategories, fetchCostOfLivingCategories,
  fetchAllCsvProfiles, fetchProcessingResults, fetchProcessingResultMetadata
- **`api.ts`** — barrel that re-exports the three domain modules; import
  from `'../js/api'` (this is the single import path used app-wide)

Rules for agents:

- New endpoints go in the matching domain module and are re-exported by the
  `api.ts` barrel
- Never call `fetch()` directly from components, pages, or stores — always
  go through the API layer so CSRF and error handling stay consistent
- API request/response shapes are typed in `src/types/api.ts` and
  `src/types/auth.ts`; keep them in sync with backend Pydantic contracts
- Dates crossing the API boundary are ISO 8601 strings

## State management (`src/stores/`)

All stores use Pinia's setup (function) syntax, not options syntax.

| Store | Responsibility |
|---|---|
| `auth` | User session, login/logout/register, recovery code state; ensures a CSRF cookie exists |
| `dataset` | Cached fetch of the user's complete transaction dataset + result metadata, keyed by `resultId`. Categories, Transactions, and Pivot pages share it so navigation between them is render-only |
| `categories` | Category definitions loaded at bootstrap; maps `category_id` to display names |
| `pivot` | Pivot selections and chart preferences (persisted) |
| `statistical` | Statistical algorithm/direction preferences, persisted via `usePersistentRef` |
| `form` | Import-form state, validation error codes; no navigation side effects |
| `feedback` | Global success/error/info/warning message queue (id, type, timestamp, autoDismiss) |
| `locale` | Current gettext locale, persisted |
| `theme` | Theme id, persisted to localStorage; applies CSS custom properties |

Conventions:

- UI preferences persist through `usePersistentRef` (localStorage-backed,
  JSON-serialized, validated on read) — not ad-hoc `localStorage` calls
- Cross-store communication happens through store methods, not direct
  mutation of foreign state (e.g. auth store calls dataset store on logout)
- The CSRF token is delivered by the backend as a readable cookie
  (set on login/register/getMe//auth/csrf-token, cleared on logout);
  `js/csrfToken.ts` reads it from `document.cookie` and the API client
  echoes it in the X-CSRF-Token header, retrying once on a 403 with
  `code: CSRF_TOKEN_INVALID`

### Dataset scaling ceiling (watch item)

The `dataset` store holds the complete transaction list per result
scope in reactive memory — potentially tens of thousands of rows —
because VueDataTable paginates client-side and the pages share the
cache. This is a deliberate ceiling: it keeps navigation between
Categories, Transactions, and Pivot render-only and avoids a
server-pagination surface. The store logs a debug message once a
dataset exceeds 20 000 rows so real-world sizes become observable
before the ceiling hurts.

Break-glass plan when evidence shows real users exceed the ceiling:
switch to server-side pagination on `/api/v2/transactions`
(offset/limit are already supported) plus windowed (virtualized)
rendering in VueDataTable, dropping the full-list cache in favor of
page caches. Do not attempt that refactor without evidence — the
current design is correct for the observed data sizes.

## Composables (`src/composables/`)

Pages compose these instead of duplicating logic:

### Async error/loading patterns (sanctioned — pick by use case)

```text
Page-load data          → useApiData (data/isLoading/error; page renders
                           ErrorState; no toast; optional onError hook)
User-triggered command  → useAsyncAction (store error + rethrow; page
                           decides presentation and catches at the call site)
Inline/cell errors      → rethrow from the API wrapper (see
                           useTransactionCorrections); the owning cell
                           displays it
```

Do not add a fourth pattern; the `dataset` store owns caching, so no
client-side query library is introduced.

Two auth store actions deliberately bypass `useAsyncAction` — do not
"normalize" them back:

- `logoutUser` clears local state in a `finally` regardless of the
  outcome: a failed logout request must still drop the local user
  (the session cookie may be gone either way), so there is no error
  path for `run` to manage.
- `initialize` treats a failed `getMe` as "not authenticated", not an
  error: swallowing it is the intended contract, and a stale shared
  `error` ref would make every guard-triggered boot look broken.

### Inventory

- `useApiData` — fetching only: loading/error state, errors stored and
  rendered by the page
- `useAsyncAction` — wraps async handlers: clears prior error, sets loading,
  stores and re-throws errors, so pages only handle the success path
  (used by Settings and the auth store)
- `useDrilldownData` + `useAggregatedGroups` — drilldown pages
  (MonthCategoriesList, CategoryMonthsList) rendering
  `AggregatedTransactionsResponse` groups with totals and highlighting
- `useTableSorting`, `useTableFiltering`, `useTablePagination`,
  `useTableHighlight` — state/behavior composables backing VueDataTable
- `useTransactionCorrections` — category/merchant/notice corrections shared
  by transaction table pages; rethrows so editable cells display errors
- `useFormWithNavigation` — form submission UX: translates messages, shows
  feedback, navigates to results (the form store keeps only state and the
  API call)
- `useRouteParams` — type-safe route parameter extraction
- `useResultQuery` — navigation queries carrying the optional `resultId`
  filter
- `useBreadcrumbs`, `usePageTitle` — navigation chrome
- `usePersistentRef` — localStorage-persisted refs

## Components

- **`components/data/VueDataTable.vue`** — the custom data grid (no
  DataTables.net/jQuery). Sorting, pagination, global search, row
  highlighting, Bootstrap 5 styling. Custom cells render Vue
  components or escaped plain text (`formatValue`); there is no
  v-html rendering in the table. Sorting/filtering/pagination/highlight
  state lives in `composables/useTable{Sorting,Filtering,Pagination,Highlight}.ts`
- **Extending cell rendering:** prefer a scoped `#cell-<key>` slot on
  VueDataTable (slot props: `value`, `row`, `index`) over growing the
  `component`/`componentProps` indirection; the slot wins over every
  built-in rendering. Do not add new per-capability flags to
  `types/column.ts` when a slot can express the cell. Existing
  `component`-based columns keep working unchanged
- **`components/data/`** also provides `EditableCell`, `UndoCorrectionCell`,
  `TableLink`, `TableLinkWithPopover`, `TableCell`, `ToggleFilterButton`,
  and `tableAggregates.ts`
- **`components/charts/`** — `BarChart` / `PieChart` wrappers over
  vue-chartjs; use these rather than chart.js directly
- **`components/layout/`** — `PageHeader`, `BreadcrumbNavigation`,
  `LoadingState`, `ErrorState`
- **`components/auth/`** — `PasswordResetForm`, `RecoveryCodeDisplay`

## i18n and theming

- vue3-gettext with `defaultLanguage: 'en'`, `availableLanguages: en, hu`.
  Catalogs in `src/locales/` (`en.po`, `hu.po`, `messages.pot`,
  compiled `translations.json`). Translatable strings go through gettext
  functions; run the extraction/compile scripts (see `package.json`
  `gettext-extract` / `gettext-compile`, or `make lang` from the repo root)
  and translate manually — do not machine-edit `.po` translations blindly
- Themes are TypeScript modules in `src/js/themes/` (baltic-blue,
  corporate, earth-tones, green-dream, soft-pastel). The theme store applies
  them and persists the choice to localStorage

## Build, dev, and deployment modes

- Dev server: port 3000, proxies `/api/v2` to `http://localhost:5000`
  (`vite.config.js`). Run via `make frontend` or `npm run dev` in `frontend/`
- Production build: `vite build` → `frontend/dist/` (terser minify,
  `js/[name].js` and `css/[name].[ext]` outputs). `npm run build:prod` sets
  `VITE_API_BASE_URL=/api/v2`. Sourcemaps are omitted by default; build
  with `VITE_SOURCEMAPS=true` to include them (the backend catch-all
  refuses to serve `.map` files regardless)
- Integrated mode: the backend serves the frontend from
  `src/whatsthedamage/view/static/dist/` via a catch-all route, and sets
  the CSP on every SPA response (`SPA_CSP` in
  `src/whatsthedamage/api/middleware.py`): `default-src 'self';
  script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self'
  data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'`
- Standalone mode: host `dist/` separately; set `VITE_API_BASE_URL` and
  enable CORS on the backend. The CSP then comes from the static host,
  not Flask — configure the same policy there (host header or a
  `<meta http-equiv="Content-Security-Policy">` tag in the hosted
  `index.html`, with `connect-src` extended to the API origin, e.g.
  `connect-src 'self' https://api.example.com`)

## Testing and quality gates

Every change must pass, from `frontend/`:

```bash
npm run lint          # ESLint (.ts, .js, .vue)
npm run type-check    # tsc --noEmit
npm run knip          # unused files/exports detection
npm run test          # Vitest (jsdom, test/ directory)
```

Or from the repo root: `make frontend-test` / `make test` (full stack).
Fix all errors; address warnings unless the user approves otherwise.
Place new tests in `frontend/test/` mirroring the source layout
(`test/composables/`, `test/pages/` exist for this).

## Conventions that reviewers will enforce

- Vue 3 Composition API with `<script setup lang="ts">`; never options API
  for new components
- Strict TypeScript; avoid `any`
- Never use `null` for optional values — use `undefined`
- Prefer functions over classes; async/await for asynchrony; no callbacks
- ES2022 features; Node built-ins (`node:` prefix) over new dependencies —
  ask before adding any npm package
- No comments unless absolutely necessary; self-documenting names
- Do not add DataTables.net/jQuery; use `VueDataTable.vue` and the existing
  chart components
- Bootstrap 5 via native HTML elements + Bootstrap classes directly; do not
  create wrapper components for Bootstrap elements; theme colors go through
  semantic CSS variables (e.g. `bg-surface-primary`, `text-on-primary`)
- Security: never log passwords, session tokens, CSRF tokens, or recovery
  codes; the API layer handles CSRF automatically — do not bypass it
- Keep date exchange in ISO 8601 (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)

## Typical data flow (reference for new pages)

```text
Route (guarded) → Page component (pages/)
    → API module (js/api/*) → request.ts (CSRF + errors) → REST API v2
    → typed response (types/api.ts)
    → Pinia store (stores/) or composable (composables/)
    → VueDataTable / charts / layout components
```

For example, `pages/Categories.vue` combines `useApiData`, `useDatasetStore`,
`useStatisticalStore`, `useCategoriesStore`, `useFeedbackStore`, and
`useGettext`, renders `VueDataTable` with `Column` definitions, and builds
drilldown links with `js/routeUtils` helpers.
