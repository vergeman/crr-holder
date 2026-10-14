# 0007 - Sprint 3.4: Sink Expansion

Type: feat
Branch: feat/0007-sink-expansion

## Goal

* Load all matching sinks when a source is expanded in the holdings matrix.
* Show sink OPT/OBL totals and monthly cells beneath their parent source.
* Reconcile sink contributions with the source under the same report and filters.

## Context

* Expand Sprint 3.4 in [the outline](0001-init-outline.md#34---sink-expansion).
* Sprint 3.3 provides source pagination, continuous months, and separate hedge totals.
* Sink rows represent ordered Source-Sink Pairs; reversed pairs remain separate.
* Contract details and panel hide/resize remain Sprint 3.5 work.

## Endpoint and aggregation

Add `GET /api/holdings/sources/{source}/sinks`, operation ID `getSinkHoldings`.

| Parameter | Behavior |
|---|---|
| `source` | Required path identifier; restrict holdings to this source. |
| `report_id` | Optional; resolve the latest publication when omitted. |
| `account_holder` | Optional; retain the shared holder predicate. |
| `settlement_point` | Optional; retain the inclusive source OR sink predicate. |

Return this response shape; MWh fields are numeric, unrounded values:

```text
{
  reportId,
  source,
  deliveryMonths: ["2026-10-01", ...],
  sinks: [{
    sink,
    totalOptMwh,
    totalOblMwh,
    months: [{ deliveryMonth, OPT, OBL }, ...]
  }, ...]
}
```

* Resolve the report with `resolve_report` and reuse `holdings_filter` from
  `api/filters.py`. Add a bound source predicate alongside the shared filters.
* A selected point matching the source retains all its matching sinks. Otherwise,
  only holdings whose sink matches the point remain. Same-endpoint holdings
  contribute once; do not net reversed pairs.
* Obtain the same continuous, report-wide `deliveryMonths` as the source endpoint,
  independent of holder, point, and source. Extract the existing timeline query
  into a small helper in `api/holdings.py` for these two endpoints.
* Sum `peak_wd_mwh + peak_we_mwh + off_peak_mwh` by sink, delivery month,
  and hedge type. Return every matching sink and every header month, using zero
  for missing OPT/OBL contributions. Do not add pagination or a cutoff.
* Return `totalOptMwh` and `totalOblMwh` across the full filtered delivery horizon.
  Sort sinks by their unrounded sum descending, then sink identifier ascending.
  Do not return an additional combined total or store aggregates.
* No matching holdings returns `sinks: []` with the selected report's timeline.
  Expansion introduces no new holdings range or month selection.

## Matrix behavior

* Add a native expand/collapse button beside each source identifier, with
  `aria-expanded` and an accessible label identifying the source.
* Fetch sinks only when that source is expanded. Allow multiple sources to remain
  expanded; place each source's sinks immediately beneath it in response order.
* Use a small `SinkHoldings` component in `web/src/SinkHoldings.jsx` to own the
  per-source query and render child table rows. Keep source pagination in
  `SourceHoldings.jsx`; do not introduce a general tree-table abstraction.
* Align sink rows with the existing Total MWh and delivery-month OPT/OBL columns.
  Indent sink identifiers under their source and retain the sticky label column.
  Use the existing whole-number ceiling formatter for displayed MWh only.
* Keep source totals and monthly cells visible and unchanged while expanded,
  collapsed, loading, or failed. Reconcile using unrounded values; individually
  rounded displayed sink cells can sum differently from the displayed parent.
* Show loading, empty, and error states beneath the affected source. On failure,
  show "Unable to load sinks." followed by a native text button labeled "Retry",
  using the existing button styling. Use no error icon. Keep the message and
  button visible near the source label when months are scrolled horizontally.
  Retry requests sinks for that source; other rows and expansions remain usable.
* Add `getSinkHoldings` to `web/src/data/provider.js`: this wrapper calls Orval's
  generated HTTP function and unwraps its response. Add `useSinkHoldings` in
  `web/src/data/hooks.js` using TanStack `useQuery` to call the provider wrapper.
  Keep these edits outside generated code so Orval cannot overwrite them.
  Key requests by report, holder, point, and source; pass the cancellation signal
  through the provider and use the existing stale-time policy.
* Collapse hides sink rows; reopening may reuse TanStack's cached response under
  that same key. Do not prefetch collapsed sources or add persistent storage.
* Report or portfolio-filter changes reset expansions through the existing keyed
  matrix mount. Late responses must not appear under a different selection.
* Appending source pages retains existing expansions and horizontal scrolling.
  Expansion/collapse must not invoke the first-holdings jump again.
* Keep source and sink MWh cells display-only; contract clicks arrive in Sprint 3.5.
  Limit CSS to expansion controls, child indentation, and readable request states.

## Approach and commit groups

1. **`docs(plan): define Sprint 3.4 sink expansion`** — add this plan and its
   outline link. Align design docs only where this contract clarifies existing text.
2. **`feat(api): add source sink holdings`** — add `get_sink_holdings` and the
   shared timeline helper in `api/holdings.py`; add response models and the route
   in `api/main.py`, retaining the existing read-only connection pattern.
   Add `api/tests/test_sinks.py`, reusing the in-memory fixture from
   `api/tests/fixtures.py`; keep extra sink rows local to these tests.
3. **`feat(web): expand source holdings into sinks`** — extend
   `web/src/data/provider.js` and `web/src/data/hooks.js`; add `SinkHoldings.jsx`
   and source expansion controls in `SourceHoldings.jsx`, with minimal styles in
   `web/src/style.css`. Regenerate Orval through the existing development flow.

## Scope control

* Use the smallest implementation satisfying the closed acceptance and validation
  lists; resolve routine choices within this scope without confirmation.
* Use existing dependencies, prepared monthly columns, and read-only SQLite.
  Add no schema changes, indexes, stored totals, pagination, or general frameworks.
* Keep generated Orval output ignored in `web/src/generated/`; keep handwritten
  provider, hooks, and UI outside it.
* Leave contracts, maps, panel resizing, broader CSS work, and access-mode
  comparisons outside this sprint.
* Before adding unplanned stored data, files, dependencies, or substantial
  verification, explain why, request a scope decision, and wait for the reply.
  Existing authorization covers work specified here.
* Inspect Compose configuration and `docker compose ps` before starting services;
  reuse running development services as required by `AGENTS.md`.

## Validation and tests

* Use the shared fixture to check report/filter consistency, complete months,
  deterministic ordering, and sink-to-source OPT/OBL reconciliation. Check that
  all sinks are returned, including beyond the source page size.
* Run `docker compose exec -T api python -m unittest discover -s tests -v`.
* Compare an expanded source with independent read-only SQL and its parent totals
  for market, holder, point, and combined filters. Record endpoint times for those
  cases; full benchmarking remains later work.
* Check browser expansion/collapse, independent source states, retry, filter
  resets, cached reopening, and preserved expansions/scrolling on Show more.
  Confirm generated Orval output updates and remains ignored.

## Acceptance

* [x] The sink endpoint retains the report and shared filters plus the source.
* [x] Every matching sink is returned, ordered by combined MWh and identifier.
* [x] Sink rows contain separate OPT/OBL totals and complete zero-filled months.
* [x] Unrounded sink totals and monthly cells reconcile with their parent source.
* [x] Expanding a source loads aligned sink rows; collapsing leaves totals unchanged.
* [x] Loading, empty, and retryable errors remain local to the expanded source.
* [x] Filter changes reset expansions; Show more retains expansions and scrolling.
* [x] Provider, hooks, and generated code retain their existing boundaries.
* [x] Required API, SQL reconciliation/timing, and browser checks pass.

## Validation results

* API suite: 12 tests passed.
* Independent SQL and parent reconciliation: all four filter cases passed.
* Endpoint timings: market 2.66s; holder 0.14s; point 0.44s; combined 0.14s.
* Browser: expansion, cache reuse, local states/retry, paging/scroll, and filter
  resets passed; report reset used a browser-only second-report selection.
* Orval regenerated automatically; generated output remains ignored.
