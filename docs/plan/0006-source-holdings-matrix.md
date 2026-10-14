# 0006 - Sprint 3.3: Source Holdings Matrix

Type: feat
Branch: feat/0006-source-holdings-matrix

## Goal

* Add a filtered source-by-delivery-month holdings endpoint.
* Show contractual MWh in separate OPT and OBL columns for each month.
* Load complete source rows in pages through Show more sources.

## Context

* Expand Sprint 3.3 in [the outline](0001-init-outline.md#33---source-holdings-matrix).
* Build on the shared filters, summary, discovery, and HTTP provider boundary.
* Use prepared monthly holdings; source groups partition the filtered portfolio.
* Leave sink expansion to Sprint 3.4 and contract details to Sprint 3.5.

## Endpoint and aggregation

Add `GET /api/holdings/sources`, operation ID `getSourceHoldings`.

| Parameter | Behavior |
|---|---|
| `report_id` | Optional; resolve the latest publication when omitted. |
| `account_holder` | Optional; use the existing holder predicate. |
| `settlement_point` | Optional; use the existing inclusive source OR sink predicate. |
| `limit` | Default 20; accept integers from 1 to 100. |
| `offset` | Optional nonnegative integer source offset; start at zero when omitted. |

Return this response shape:

```text
{
  reportId,
  deliveryMonths: ["2026-10-01", ...],
  holdingsRange: { firstMonth, lastMonth } | null,
  sources: [{
    source,
    totalOptMwh,
    totalOblMwh,
    months: [{ deliveryMonth, OPT, OBL }, ...]
  }, ...],
  nextOffset: integer | null
}
```

* Resolve one report using `resolve_report`; reuse `api/filters.py` for holdings.
* Build `deliveryMonths` as a continuous monthly timeline from the earliest to
  latest delivery month in the selected report, including intervening months
  without holdings. Keep this header independent of holder/point filters and pages.
* Return `holdingsRange` as the first and last months with nonzero contractual
  MWh in the entire filtered portfolio, across all sources rather than the current
  page. Use the same month date format as `deliveryMonths`; return null when
  there are no nonzero contributions. Calculate these bounds without storing them.
* Sum `peak_wd_mwh + peak_we_mwh + off_peak_mwh`, grouped by source,
  delivery month, and hedge type. Keep OPT and OBL separate; retain reversed
  pairs as separate holdings and count same-endpoint holdings once.
* Return per-source `totalOptMwh` and `totalOblMwh` from SQL, summing each type
  across the full filtered delivery horizon. Order sources in SQL by their sum;
  return only the separate totals, with no stored aggregates.
* Rank sources by unrounded total MWh across all months and both hedge types,
  descending, then source identifier ascending.
* Page the ranked source identifiers before returning their monthly aggregates.
  Every source includes every header month, with zero for missing contributions.
  The displayed totals use `totalOptMwh` and `totalOblMwh`; their sum equals
  the sum of all monthly OPT and OBL cells.
* In one query, fetch `limit + 1` ranked sources (21 for a 20-source page),
  but return only the first `limit`. If the extra source exists, set `nextOffset`
  to the current offset plus `limit`; otherwise return null. No separate request
  is needed to check for another page.
* Use offset pagination for these immutable report snapshots and deterministic
  ordering. The offset counts sources to skip in the sorted, filtered list; reset it to
  zero when the report or portfolio filters change.
* Empty matches return an empty source array and `nextOffset: null`, retaining the
  selected report's month header. Do not return portfolio totals for just a page.

## Matrix behavior

* Add a CRR Holdings panel below the existing overview and map placeholder.
  Label values Contractual MWh; show source identifiers and chronological months
  with separate OPT and OBL subcolumns. Place Total OPT and Total OBL immediately
  after Source, before the monthly columns; label the group Total MWh.
  Keep Source sticky; totals scroll with the month columns.
* Initially request 20 sources. Show more sources appends another 20 complete
  rows; hide the button when `nextOffset` is null and disable it while loading.
* Use horizontal scrolling for months and keep source labels visible with a
  sticky first column. Reuse existing numeric formatting; zero remains visible.
* Above the matrix, show the filtered holdings range, for example
  "Holdings: Jan–Mar 2029", and a native "Jump to first holdings" button.
  The range identifies the endpoints; months between them may contain zeros.
  Hide the range and jump button when `holdingsRange` is null.
* Once the first page for a report/filter selection renders, scroll horizontally
  to the first month in `holdingsRange`. The jump button returns to that month.
  Keep earlier and later report months accessible; do not skip zero months.
  Appending pages must preserve the user's horizontal scroll position.
* Drive requests from the same resolved report, holder, and point as the summary.
  Report or portfolio-filter changes start again at the first source page.
* Keep pagination data isolated by query key so late responses cannot append
  rows from a previous selection. Pass the request cancellation signal through
  the provider as for existing queries.
* Show initial loading, empty, and error states in the holdings panel. A failed
  additional page retains loaded rows and provides a retry through Show more.
* Source rows and cells are display-only in this sprint; add no expansion or
  detail interaction before their endpoints exist.
* Limit styling to a usable matrix and scrolling. Panel hide/resize and the
  broader panel sizing, typography, and scroll-jump pass remain later work.

## Approach and commit groups

1. **Plan and design alignment** — add this plan and link it from the outline.
   Correct `docs/api.md` to specify pagination for sources only, with the shared
   point filter retained by later drill-down endpoints. Keep Sprint 3.4/3.5 scope.
2. **Holdings API and tests** — put source aggregation and pagination in
   `api/holdings.py`; add response models and the route in `api/main.py`.
   Put tests in `api/tests/test_holdings.py`, reusing
   `api/tests/fixtures.py`. Keep additional pagination rows local to these tests.
3. **Source matrix UI** — add `getSourceHoldings` to
   `web/src/data/provider.js` and a `useInfiniteQuery` hook in
   `web/src/data/hooks.js`. Build the matrix in
   `web/src/SourceHoldings.jsx`, mount it from `web/src/main.jsx`, and add its
   styles to `web/src/style.css`. Regenerate Orval through the existing dev flow.
4. **Source hedge totals follow-up** — one separate commit updating this plan,
   SQL/response model, tests, and the matrix totals columns. Verify totals against
   monthly cells and summary across filters/pages, then check column placement,
   formatting, paging, and first-month positioning in the browser.

## Scope control

* Use the smallest implementation satisfying the acceptance criteria; treat
  acceptance and validation requirements as closed lists.
* Use existing dependencies, read-only SQLite, and prepared monthly columns.
  Add no schema changes, indexes, stored aggregates, or pagination framework.
* Keep generated code ignored under `web/src/generated/`; handwritten provider,
  hooks, and components stay outside it.
* Add no sink endpoint, contract endpoint, map implementation, sorting controls,
  month filters, exports, or access-mode comparison.
* Before adding unplanned stored data, files, dependencies, or substantial
  verification, explain why, request a scope decision, and wait for the reply.
  Existing authorization covers work specified here; resolve routine choices
  within this scope without confirmation.
* Inspect Compose configuration and `docker compose ps` before starting services;
  reuse the running development environment as required by `AGENTS.md`.

## Validation and tests

* Use the shared in-memory fixture to check report/filter consistency, complete
  continuous months, portfolio-wide holdings bounds, monthly OPT/OBL cells,
  and reconciliation with summary totals. Check pagination
  and tied ordering so traversing pages neither loses nor repeats sources.
* Run `python -m unittest discover -s tests -v` in the API container.
* Compare all source pages with independent read-only SQL and summary OPT/OBL
  totals for market, holder, point, and combined filters. Record endpoint times
  for these four cases; full benchmarking remains Sprint 5.
* Check browser first-holdings positioning, the range/jump control, preserved
  scrolling on Show more, filter resets, and loading/error/empty behavior to confirm rows always belong to the active portfolio. Confirm Orval
  regenerates the endpoint contract while generated output remains ignored.

## Acceptance

* [x] The endpoint uses the selected report and shared holder/point filters.
* [x] Every returned source has all report months, separate OPT/OBL MWh, and a
  complete total; missing cells are zero.
* [x] Per-source OPT/OBL query totals reconcile with monthly cells and summary;
  the matrix shows them before the monthly columns.
* [x] The timeline includes every month in the report span, including gaps;
  holdings bounds reflect the entire filtered portfolio across pages.
* [x] Initial/filter loads scroll to first holdings; the range and jump button
  expose its dates, and additional pages preserve horizontal scroll position.
* [x] Sources sort by total MWh descending with identifier ties; pagination
  returns complete rows without duplicates or omissions.
* [x] All source pages reconcile with filtered summary totals for OPT and OBL.
* [x] The matrix starts with 20 sources, appends pages, scrolls months, and resets
  pagination when report or portfolio filters change.
* [x] Loading, empty, and error states support the specified initial/page behavior.
* [x] Provider, TanStack Query, and generated Orval contract follow existing boundaries.
* [x] Required API, SQL reconciliation/timing, and browser checks pass.
* [x] Storage and later sprint features remain outside this implementation.

## Validation results

* API tests: 9 passed; pagination parameter validation passed.
* Independent SQL and summary reconciliation: all four filter cases passed.
* First-page timings: market 2.24s; holder 0.19s; point 1.83s; combined 0.15s.
* Browser: paging, positioning, scrolling, filter resets, and request states passed.
* Orval regenerated automatically; generated output remains ignored.
* Source totals follow-up: API reconciliation and browser column/scroll checks passed.
