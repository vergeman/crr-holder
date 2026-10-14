# 0008 - Sprint 3.5: Contract Details and Completed Workspace

Type: feat
Branch: feat/0008-contract-details-workspace

## Goal

* Open contract details from a sink's delivery-month OPT or OBL cell.
* Show original contract fields and selected-month MWh grouped by holder and TOU.
* Finish holdings panel hide/resize behavior while preserving matrix navigation.

## Context

* Expand Sprint 3.5 in [the outline](0001-init-outline.md#35---contract-details-and-completed-workspace).
* Sprint 3.4 supplies sink cells under the report and shared portfolio filters.
* Monthly aggregates omit contract identity; read `crr_holdings` and `tou_hours`
  to explain cells without changing the prepared dataset.
* Follow [frontend](../web.md), [data](../data.md), and [API](../api.md) designs;
  leave the map placeholder until Sprint 4.

## Endpoint and calculation

Add `GET /api/holdings/contracts`, operation ID `getContractHoldings`.

| Parameter | Behavior |
|---|---|
| `source`, `sink` | Required; select the exact ordered pair. |
| `month` | Required first-of-month ISO date (`YYYY-MM-01`), matching a matrix header. |
| `hedge_type` | Required `OPT` or `OBL`; never combine instruments. |
| `report_id` | Optional; resolve the latest publication when omitted. |
| `account_holder`, `settlement_point` | Optional; retain shared portfolio filters. |

Return numeric, unrounded MW and MWh in this response shape:

```text
{
  reportId,
  source,
  sink,
  deliveryMonth,
  hedgeType,
  totalMwh,
  accountHolders: [{
    accountHolder,
    legalName,
    totalMwh,
    timeOfUseGroups: [{
      timeOfUse,
      hours,
      totalMwh,
      contracts: [{ crrId, segmentId, crrType, startDate, endDate, mw, monthMwh }]
    }]
  }]
}
```

* Add `get_contract_holdings` in `api/holdings.py`. Reuse `resolve_report` and
  `holdings_filter`; apply bound pair, month, and hedge predicates. Keep the
  inclusive source OR sink predicate so same-endpoint holdings appear once.
* Join original holdings to `tou_hours` on matching TOU and selected delivery
  month, with `delivery_month BETWEEN start_date AND end_date`, exactly as in
  `db/crr/sql/monthly_holdings.sql`. Compute each contribution as `mw * hours`.
  Do not introduce daily proration or reinterpret the prepared calculation.
* Select records for one report only. Contract identity within that report is
  `(crr_id, segment_id)`; retain distinct segments and reversed pairs separately.
* Return all matching contracts without pagination, cutoff, or zero-contribution
  suppression. Return an empty holder list and zero total when none match.
* Group once in the response hierarchy: common report/pair/month/hedge fields
  belong to the envelope, holder and TOU fields to their groups. Display each
  record with that context rather than repeating common fields in every row.
* Use the existing holder directory for nullable legal names. Sort holders by
  selected-month MWh descending, then holder identifier ascending. Order TOU
  groups as `PeakWD`, `PeakWE`, `Off-peak`; omit groups with no matching records.
  Sort contracts within each TOU by `monthMwh` descending, then CRR ID and segment
  ID ascending. Compute cell and group totals from the full returned records.
* Add response models and the read-only route in `api/main.py`. Reject invalid
  month or hedge parameters with the usual FastAPI validation response; add no
  separate identifier lookup or speculative input formats.

## Contract drawer

* Add `web/src/ContractDrawer.jsx`. Keep selected-cell state in `CRRExplorer`
  in `web/src/main.jsx`; pass the selection callback through `SourceHoldings.jsx`
  to `SinkHoldings.jsx`. Selection contains source, sink, delivery month, and
  hedge type; use the current report and portfolio filters for the request.
* Make sink monthly cells native buttons with accessible labels identifying
  the pair, month, and hedge type. Keep zero cells selectable; source cells and
  full-horizon Total MWh cells remain display-only because they lack cell context.
* Show a right-side drawer with the ordered pair, month, instrument, full cell
  total, and independently expandable holder and TOU groups. Initially collapse
  holder groups; initially collapse TOU groups when a holder is opened.
  Holder headers always show their subtotals; TOU headers show theirs whenever
  the parent holder is open, even if that TOU is collapsed. Keep the full total
  visible independently of expansion. Do not derive totals from visible rows.
* Show CRR ID, segment ID, CRR type, and the selected month as `MMM YYYY` with
  smaller, lighter labels above values. Keep original start/end dates in the API
  response; omit the date range from the displayed contract row.
* Display original MW and actual selected-month TOU hours in separate columns.
  Return hours once per TOU group. Label the right-aligned selected-month MWh
  value `Total MW x {TOU}`; retain the existing ceiling formatter for MWh display
  only and preserve MW precision. Reconcile using unrounded response values.
* Align each holder total at the bottom right beside its name block and leave
  20px of space above the first TOU group.
* Add `getContractHoldings` to `web/src/data/provider.js` and `useContractHoldings`
  to `web/src/data/hooks.js`, following existing unwrap, cancellation, enabled,
  and stale-time behavior. Key by report, holder, point, source, sink, month,
  and hedge type. Fetch only for an open selection; use TanStack's existing cache.
* Show loading, empty, and retryable error states inside the drawer. On failure,
  show "Unable to load contracts." and a native Retry button. A different cell
  resets group expansion and cannot display the previous cell's response.
* Close through a visible Close button or Escape, returning focus to the clicked
  cell when it remains mounted. Report, holder, or point changes close details.
  Source collapse also closes details for that source. Opening or closing details
  leaves source pages, other expansions, and horizontal scroll in place.
* Use a labeled nonmodal complementary panel so filters and matrix remain usable;
  provide its own vertical scrolling. On narrow screens, fit the drawer to the
  viewport width. Use existing dependencies and native controls.

## Holdings panel hide and resize

* Keep panel visibility and height state outside the portfolio-keyed matrix in
  `CRRExplorer`, so report/filter changes reset matrix data but retain panel size.
  Keep `SourceHoldings` mounted when hidden to retain pages, expansions, and scroll.
* Keep a panel header with Hide/Show available when the content is hidden.
  Hiding the panel also closes contract details; showing it restores the matrix
  without invoking the first-holdings jump again.
* Add a horizontal resize handle above the panel content. Use native pointer
  events and pointer capture to adjust its visible height, with an initial height
  of `35vh`, a minimum of 200px, and a maximum of `80vh`; reapply bounds on viewport
  changes. Scroll the panel vertically instead of stretching the page with rows.
* Make the handle focusable with `role="separator"`, horizontal orientation,
  and an accessible name. Up/Down arrows increase/decrease height by 20px within
  the same bounds; expose the current size with ARIA value attributes.
* Preserve horizontal month scrolling and sticky identifiers. Limit CSS changes
  to panel sizing/overflow, the handle, clickable cells, and the drawer; retain
  the existing overview and map placeholder layout. Add no saved preferences.

## Approach and commit groups

1. **`docs(plan): define Sprint 3.5 contract details and workspace`** — add this
   plan and link it from the outline and design docs.
2. **`feat(api): expose selected-month contract details`** — implement the query,
   response models, and route in `api/holdings.py` and `api/main.py`. Add
   `api/tests/test_contracts.py`, using the shared in-memory schema fixture with
   original contracts and matching TOU/monthly rows local to these tests.
3. **`feat(web): drill into grouped contract details`** — add the drawer and
   provider/hook integration; wire sink-cell selection through the existing
   components. Regenerate Orval through the existing development flow.
4. **`feat(web): finish holdings panel controls`** — implement hide/show and
   pointer/keyboard resizing in `web/src/main.jsx`, `SourceHoldings.jsx`, and
   `web/src/style.css`; add viewport metadata in `web/index.html` so mobile
   sizing uses the device width. Verify the complete drill-down flow.

## Scope control

* Use the smallest implementation satisfying the closed acceptance and validation
  lists; resolve routine choices within this scope without confirmation.
* Use existing dependencies and read-only SQLite. Add no schema changes, indexes,
  stored aggregates, duplicate record representations, or general tree framework.
* Keep handwritten provider/hooks outside replaceable, ignored Orval output in
  `web/src/generated/`. Label imports and distinct implementation/test phases
  with brief purpose comments as required by `AGENTS.md`.
* Leave pagination changes, daily TOU calculations, ingestion, export, maps,
  broader visual redesign, and access-mode benchmarks outside this sprint.
* Before adding unplanned stored data, files, dependencies, or substantial
  verification, explain why, request a scope decision, and wait for the reply.
  Existing authorization covers work specified here.
* Inspect Compose configuration and `docker compose ps` before starting services;
  reuse running development services as required by `AGENTS.md`.

## Validation and tests

* API fixtures check report/filter isolation, exact pair/month/instrument
  selection, original fields and segment identity, deterministic grouping/order,
  and empty results. Reconcile contract contributions and both subtotal levels
  with prepared sink cells to establish a trustworthy final drill-down.
* Check invalid month/hedge parameters through the route to verify the public
  input contract. Keep fixture values and assertion mechanics in test code.
* Run `docker compose exec -T api python -m unittest discover -s tests -v`.
* Compare the detail response and clicked sink cell with independent read-only
  SQL for market, holder, point, and combined filters. Record query execution
  time for each; full access-mode benchmarking remains Sprint 5.
* For one market-wide cell with many contracts, record contract count, query and
  endpoint time, response bytes, and whether drawer rendering remains usable.
  Report any observed limitation; request a scope decision before pagination or
  another performance mechanism rather than imposing a speculative threshold.
* Check browser cell selection, grouping/collapse with unchanged totals, request
  states/retry, selection changes, close/focus behavior, and filter resets.
  Check hide/show and pointer/keyboard resize on desktop and a narrow viewport,
  including retained pages, expansions, scrolling, and first-holdings positioning.
* Confirm automatic Orval regeneration includes the new endpoint and leaves
  handwritten provider/hooks intact; generated output remains ignored.

## Acceptance

* [x] The endpoint returns all contracts for the selected cell under its report
  and shared filters, with original fields and unrounded selected-month MWh.
* [x] Holder/TOU grouping and deterministic ordering follow this contract;
  each TOU group returns its actual selected-month hours.
* [x] Contract contributions, TOU subtotals, holder subtotals, and the full total
  reconcile with the clicked sink cell without schema changes.
* [x] Sink monthly cells open the correctly labeled drawer; group collapse changes
  visibility only, with totals retained at each visible group header. Contract
  rows use lighter labels, abbreviated months, separate MW/TOU-hours columns,
  and right-aligned totals; holder totals align beside names with TOU spacing.
* [x] Loading, empty, retry, close/focus, and selection/filter changes work without
  showing details from another cell or portfolio.
* [x] Hide/show and bounded pointer/keyboard resize preserve matrix navigation.
* [x] Provider, hooks, and generated code retain their existing boundaries.
* [x] Required API, SQL reconciliation/timing, browser, and large-cell practicality
  checks complete, with any material performance limitation reported.

## Validation results

* API suite: 16 tests passed.
* Independent SQL, contract subtotals, and sink-cell reconciliation: market,
  holder, point, and combined filters passed.
* Query timings: market 21.4ms; holder 5.4ms; point 12.3ms; combined 6.1ms.
* Market cell: 1,234 contracts; 176,496 response bytes; endpoint 44.3ms.
  Full drawer rendering and group interaction remained usable locally.
* Browser: drawer selection, totals, disclosure, loading/empty/error/retry,
  late-response isolation, close/focus, and source/filter resets passed.
* Panel: hide/show, desktop pointer/keyboard and narrow touch/keyboard resizing,
  viewport bounds, retained pages/scroll/expansions, and hidden-filter positioning
  passed. Report reset used a browser-only selection because the dataset has
  one report.
* Orval regenerated automatically; generated output remains ignored and
  handwritten provider/hooks remain outside it.
* Presentation refinements: API hours/calculation checks and desktop/narrow
  browser layout checks passed; final label and column edits passed diff checks.
