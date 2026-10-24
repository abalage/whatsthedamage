# Backend Performance Plan

Status: proposal, not implemented. This document lists recommended backend
changes to improve the performance of the transaction-heavy views
(Categories, Transactions, Pivot Table), including changes that require
backend refactors. Nothing described here has been applied to the backend.

## Context

The three main views all need the user's transaction data:

- **Categories** (`/results`) builds an account x category x month matrix
  client-side, including per-cell popover detail lines.
- **Transactions** (`/transactions`) renders a row-level table with sorting,
  filtering, and inline corrections.
- **Pivot Table** (`/pivot`) transforms the flat transaction list into an
  account/category/month aggregation for the chart and table views.

Until recently, each page refetched the complete dataset on every navigation.
The frontend now shares a cached dataset between the pages
(`frontend/src/stores/dataset.ts`), which makes navigating between them
render-only. The costs listed below therefore apply primarily to the **first
load of a scope** (cold cache, page reload, or after cache invalidation), and
to users whose datasets exceed the fetch-all safety cap.

## Findings from the current code

These observations were verified against the code at the time of writing:

1. `/api/v2/transactions/aggregate`
   (`src/whatsthedamage/api/v2/endpoints/transactions.py`, function
   `aggregate_transactions`) loads up to **10,000 rows as ORM entities** and
   groups them **in Python** via `statistical_service.group_transactions`.
   The 10,000-row limit is hard-coded, so datasets larger than that are
   silently aggregated from a truncated subset - a performance problem and a
   correctness bug.
2. `/api/v2/transactions` list queries use **OFFSET pagination** ordered by
   `created_at` (`src/whatsthedamage/models/repositories/transaction_repository.py`,
   `find_by_user_with_filters` and friends). Deep OFFSET pages re-scan and
   discard rows, so each later page of a paged fetch-all gets slower.
3. Database indexes are **single-column only**
   (`src/whatsthedamage/models/database/transaction.py`):
   `user_id`, `date`, `account`, `result_id`, `created_at`, and the unique
   `(user_id, deduplication_hash)`. Filtered queries on
   `user_id + result_id + account/category/month` cannot use one composite
   index and pay extra row lookups.
4. The list endpoint serializes **every column** of each transaction
   (`_transaction_to_dict`), including `original_*` correction snapshots,
   `deduplication_hash`, and audit timestamps that the tables never render.
5. No response compression (gzip/brotli) is configured anywhere in the Flask
   stack.

## Recommendations

| # | Recommendation | Why / Impact | Effort |
|---|----------------|--------------|--------|
| P0 | SQL `GROUP BY` matrix endpoint for Categories/Pivot | Removes ~95% of transferred bytes and all client-side aggregation for the two matrix views; fixes the 10k truncation bug | Medium |
| P1 | Keyset pagination for fetch-all | Each page stops re-scanning; enables parallel range fetching (4-8x lower total latency) | Small-Medium |
| P2 | Payload slimming for the transactions list | ~30-50% smaller JSON, less browser parse cost | Small |
| P3 | Response compression (gzip/brotli) | 50k-row JSON compresses 5-10x; near-zero code | Trivial |
| P4 | Server-side pagination/filtering for the Transactions table | Page load becomes O(pageSize) instead of O(dataset); the only real fix for that page at large scale | Medium |
| P5 | Composite database indexes | Faster every filtered query path; matters most on SQLite | Small (Alembic migration) |
| P6 | Cache or precompute statistical highlights | One fewer round trip per Categories visit; less CPU on repeats | Small-Medium |
| P7 | ETag/304 support per result scope | Free revalidation for reloads and revisits | Small |
| P8 | SQLite/infrastructure hardening (WAL, PostgreSQL option), SQL-side aggregation everywhere | Headroom for scale | Larger |

### P0 - SQL GROUP BY matrix endpoint

Add a matrix-capable aggregation endpoint (or extend the existing aggregate
endpoint) that performs the grouping in SQL:

```sql
SELECT account, category_id, substr(date, 1, 7) AS month, SUM(amount)
FROM transactions
WHERE user_id = :user_id [AND result_id = :result_id]
GROUP BY account, category_id, month;
```

- Returns hundreds of cells instead of tens of thousands of rows; ORM
  hydration of full entity lists disappears from this path.
- Fixes the silent 10k truncation in the current aggregate endpoint.
- Include per-cell transaction counts (or ids) so the frontend can lazily
  fetch popover detail lines on hover instead of shipping them with the
  matrix.
- The existing Python-side `group_transactions` path can remain for the
  drilldown views.

### P1 - Keyset pagination for fetch-all

Replace OFFSET with a cursor for the fetch-all path used by the frontend:

```sql
WHERE user_id = :user_id AND id > :cursor ORDER BY id LIMIT :page_size
```

- Add a composite index on `(user_id, id)`.
- Expose the cursor in the API response so the client can chain pages.
- With stable id cursors the frontend can also partition the id space and
  fetch ranges **in parallel** (4-8 concurrent requests), replacing 25
  sequential round trips for a 50k-row dataset.

### P2 - Payload slimming

The list endpoint currently returns every column. Add a `fields` query
parameter (or a table-specific projection) so the transaction views download
only the fields they render. Correction snapshot fields (`original_*`) are
only needed when edit mode is active; audit columns are never rendered.

### P3 - Response compression

Enable gzip or brotli at the WSGI server / reverse proxy layer. Transaction
JSON is highly repetitive and compresses 5-10x. This benefits every endpoint
without any application code.

### P4 - Server-side pagination for the Transactions table

The endpoint already supports `limit`, `offset`, and `sort_by`/`sort_order`.
Wire the frontend table to request pages on demand and move the client-side
filters (corrected-only, category) to query parameters. The page then loads
O(pageSize) rows regardless of dataset size. This is the only approach that
keeps the Transactions page fast when a user has far more rows than the
fetch-all cap.

### P5 - Composite indexes

Add covering composites for the hot query shapes:

- `(user_id, result_id, created_at)` for the default listing order
- `(user_id, category_id)`, `(user_id, account)`, `(user_id, date)` for the
  filter combinations used by the drilldown and aggregate endpoints

Verify with `EXPLAIN QUERY PLAN` on realistic data sizes before and after.

### P6 - Highlights caching

Categories issues an extra `recalculate-statistics` request on every mount to
compute outlier/pareto highlights. Cache the computed highlights per
`(user, result, algorithms, direction)` and invalidate on correction, or fold
them into the P0 matrix response so the page needs a single round trip.

### P7 - ETag/304 support

Compute a cheap validator per result scope (for example a hash of the
transaction count and `max(updated_at)`) and honor
`If-None-Match`/`If-Modified-Since`. Complements the frontend dataset cache
for reloads and session revisits.

### P8 - Infrastructure and structural work

- Enable SQLite WAL mode (and `synchronous=NORMAL`) if not already.
- For multi-user production deployments, consider PostgreSQL via the existing
  `WHATSTHEDAMAGE_DATABASE_URI` configuration switch.
- Migrate remaining Python-side aggregation patterns (full ORM list hydration
  followed by in-memory grouping) to SQL aggregates; P0 covers the hottest
  instance of this pattern.

## Suggested order

1. **P3 + P2 + P1** - cheap, no frontend changes required, and they make the
   existing fetch-all path several times faster.
2. **P0** - structurally cheap Categories/Pivot loads; also fixes the 10k
   aggregation truncation.
3. **P4** - when the Transactions page is slow at real dataset sizes.
4. **P5-P8** - alongside or after, based on profiling.

## Caveats

- The impact estimates are derived from the code paths and frontend render
  benchmarks, not from profiling a production dataset. Validate with
  `EXPLAIN QUERY PLAN` and real payload sizes before committing to the
  larger refactors (P0, P4, P8).
- The frontend dataset cache already removes the repeated-fetch cost of
  navigating between the three views; the backend work above primarily
  improves first-load latency and correctness at scale.
