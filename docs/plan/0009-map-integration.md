# 0009 - Sprint 4: Map Integration

Type: feat
Branch: feat/0009-map-integration

## Goal

* Replace the map placeholder with selectable source and sink footprints.

* Reconcile geographic endpoint MWh with the filtered portfolio and holdings.

## Context

* Expand Sprint 4 in [the outline](0001-init-outline.md#sprint-4---add-the-map),
  after the completed Sprint 3 explorer and before access-mode work in Sprint 5.

* `settlement_points` already stores nullable longitude and latitude; monthly
  holdings already supply contractual MWh. Use these without dataset changes.

* `CRRExplorer` owns shared filters, while the provider and hooks isolate HTTP.
  Extend the existing `/api/summary` contract as sketched in [API design](../api.md).

* Endpoint participation differs from ranking semantics: a same-endpoint holding
  contributes once as a source and once as a sink; rankings count that point once.

## Geographic summary contract

Extend `GET /api/summary` with `geographicFootprint`:

```text
geographicFootprint: [{
  settlementPoint,
  longitude,
  latitude,
  sourceMwh,
  sinkMwh
}]
```

* Add `api/geography.py` with `get_geographic_footprint`; call it from
  `api/queries.py` after resolving the report. Add its response model and field
  in `api/main.py`; retain the existing operation ID and shared parameters.

* Reuse `holdings_filter` for the report, holder, and inclusive source OR sink
  predicate. Filter holdings before endpoint aggregation, so a selected point
  retains its counterpart endpoints. Do not restrict output to the selected node.

* Sum `peak_wd_mwh + peak_we_mwh + off_peak_mwh` across delivery months and both
  hedge types independently by source and by sink. Combine those groups by point
  with zero for the absent role; sort by settlement-point identifier ascending.
  Do not net roles, reverse pairs, or reuse deduplicated point-ranking totals.

* Left join coordinates after aggregation. Return every participating point,
  including zero-MWh points and points with either coordinate null. Keep nullable
  coordinates and unrounded numeric MWh; no top-k cutoff or map pagination.

* Return an empty list for an empty portfolio. Each source-role sum and each
  sink-role sum must independently equal `summary.totalMwh`. Their combined sum
  is twice that total, including same-endpoint holdings.

* Do not store endpoint aggregates, additional coordinate representations,
  geographic classifications, or duplicate combined totals.

## Map and shared selection

* Add `web/src/components/map/Map.jsx`; replace the placeholder in
  `web/src/main.jsx` and update map and floating-panel styles in `web/src/style.css`.
  Pass the existing summary query state, selected point, MWh formatter, and
  `changeSettlementPoint` callback. Keep provider/hooks unchanged: the existing summary
  request carries the map data. Regenerate Orval through the development flow.

* Add `maplibre-gl` and its package CSS using the existing npm manifests. Use
  MapLibre directly, with OpenFreeMap's Positron style and visible attribution;
  add no React map wrapper, geographic asset, or geocoding service. Basemap tiles
  require network access; holdings continue to use the local API.

* Fit the initial MapLibre bounds to coordinate-bearing points in the report's
  market summary. Retain the camera and report-wide marker size scale across
  holder/point changes; refit on report change or Reset view. Use `useSummary`
  and its existing cache for report-wide data. Clean up map and markers on unmount.

* Keep the title/report header above a map filling the remaining viewport.
  Float Explore Holdings, Summary, Discover, map information, holdings, and
  contract details over the map. Give panels native collapsible headings and
  independent scrolling; keep controls and attribution reachable on narrow screens.

* Draw one circle per point with both coordinates. Circle area is proportional
  to `sourceMwh + sinkMwh`, with a minimum visible radius for zero totals.
  Keep the size scale fixed to the report-wide footprint across portfolio changes.
  Color continuously from source-dominant through balanced to sink-dominant
  using the relative source/sink shares; use balanced color when both are zero.
  Draw smaller circles after larger ones so they remain reachable.

* Show a legend explaining role colors, circle area, and the fact that endpoint
  MWh counts both ends and is not the portfolio total. On hover or keyboard focus,
  show the identifier and separate source and sink MWh; never infer portfolio
  MWh by adding marker totals.

* Use native buttons as MapLibre markers with Enter/Space activation
  and a visible focus/selected outline. Keep a small `MarkerButton` component
  in `web/src/components/map/MarkerButton.jsx`: React renders its events and
  attributes through a portal into a MapLibre marker host. Extract `Legend.jsx`
  and `MapControls.jsx` into the same directory. Use `MapStatus.jsx` for separate
  basemap and data error/loading messages. Use `MapPointDetails.jsx` for empty or
  unmapped portfolios and hover/focus details; retain state, named retry handlers,
  and camera fitting in `Map.jsx`. Name the initial Texas coordinates and
  document report-bound fitting. Marker selection calls `changeSettlementPoint`,
  retaining report and holder and following the existing point-filter behavior:
  refresh summary/holdings, reset source pages/expansions, and close contract details.
  Selecting the current marker keeps its selection. Provide a native Clear point
  button using `changePoint('')`; retain the existing dropdown for every point.

* Use MapLibre navigation controls for zoom and native keyboard/touch panning;
  provide a Reset view button restoring report bounds. Add no path lines,
  clustering, spatial selection, draggable panels, or saved viewport preferences.

* Report the count and separate source/sink MWh of points missing either
  coordinate, computed from the response. Keep them in tabular/filter totals;
  do not position them at invented coordinates. If no points can be placed,
  show an explicit no-coordinate state and retain this coverage explanation.

* Show loading, empty, and retryable error states in the map region. Retry uses
  the existing summary query. Do not display an old portfolio's markers while a
  different portfolio loads; keep report-extent loading/error handling local.

* Keep holdings hide/resize and drawer behavior intact. Fit the map and controls
  within the viewport below the header on desktop and narrow screens.

## Approach and commit groups

1. **`docs(plan): define Sprint 4 map integration`** — add this
   sequential plan and link it from Sprint 4 in the outline.
2. **`feat(api): add geographic endpoint participation`** — add the query,
   summary model integration, and `api/tests/test_geography.py`, reusing the
   in-memory fixture with coordinate assignments local to these tests.
3. **`feat(web): connect geographic footprint to portfolio filters`** — add
   the MapLibre component, floating panels, shared-selection wiring, and styles;
   regenerate the client and verify the geographic-to-contract exploration flow.

## Scope control

* Use the smallest implementation satisfying the closed acceptance and validation
  lists. Resolve routine choices within this scope without confirmation.

* Add only the files and response fields specified here and the requested
  MapLibre dependency. Use read-only SQLite and existing stored coordinates
  and monthly MWh columns.
  Leave schema, ingestion, ranking semantics, and holdings contracts unchanged.

* Keep handwritten code outside replaceable `web/src/generated/` output.
  Group imports and separate phases with blank lines and brief comments about
  purpose where useful. Use natural wording rather than literal phase prefixes.
  Explain SQL intermediate results and comparisons; keep fixture setup,
  execution, and assertions distinct.

* Before adding unplanned stored data, files, dependencies, or substantial
  verification, explain why, request a scope decision, and wait for the reply.
  Existing authorization covers work specified here.

* Inspect `docker-compose.yml` and run `docker compose ps` before starting
  services. Reuse running services without restarting or recreating containers
  unless a required change or observed failure makes it necessary.

* Leave WASM/VFS, access-mode comparisons, map path drill-down, export, and
  pagination optimization outside this sprint. Keep the offset pagination
  benchmark in outline section 4.1 as separate work. Do not push.

## Refactor and formatting tasks

* [x] Extract portfolio, holdings, and map components into their directories;
  add map/holdings index exports and clarify shared state/handler names.

* [x] Replace the contract drawer with a responsive modal and compact tables.

* [x] Run Prettier on components, `main.jsx`, and data hooks/provider;
  keep formatting commits separate and adjacent to map/holdings refactors.

## Validation and tests

* API fixtures check report/filter isolation, both endpoint roles including
  same-endpoint holdings, deterministic complete output, nullable coordinates,
  and empty results. Reconcile each role independently with summary MWh so
  geographic coverage cannot silently change portfolio accounting.

* Run `docker compose exec -T api python -m unittest discover -s tests -v`.

* Compare geographic source and sink sums independently with read-only SQL and
  full source/sink matrix totals under market, holder, point, and combined filters.
  Include mapped and unmapped contributions; record geographic query time for
  these filter shapes as required by the outline.

* Check desktop and narrow-screen browser rendering, role/size legend, marker
  hover/focus and keyboard selection, pan/zoom/reset, floating-panel collapse,
  holdings hide/resize, coverage and request states,
  and shared filter clearing. Follow a marker selection through source/sink
  expansion to contract details and confirm matching portfolio totals.

* Confirm automatic Orval regeneration exposes the new summary field and leaves
  handwritten provider/hooks intact, with generated output remaining ignored.

* Run `git diff --check`. Report required checks as terse outcome bullets;
  include only required measurements and material limitations or failures.

## Acceptance

* [x] Summary returns complete, deterministically ordered endpoint participation
  under the existing report and portfolio filters without changing ranking totals.

* [x] Each geographic role, including unmapped points, reconciles with portfolio
  and matrix MWh; same-endpoint holdings participate once in each role.

* [x] A MapLibre map fills the viewport below the header with collapsible
  floating panels and reachable controls on desktop and narrow screens.

* [x] The map shows coordinate-bearing points with explained roles and sizes,
  identifies missing-coordinate coverage, and supports keyboard selection/zoom.

* [x] Map selection and clearing drive the existing filters and full holdings
  drill-down; loading, empty, error/retry, and narrow layouts work.

* [x] Portfolio, holdings, and map components are grouped by feature with
  map/holdings directory exports.

* [x] Contract details use a desktop/mobile modal with labeled context, tables,
  keyboard focus wrapping, Escape/Close, and focus return to the selected cell.

* [x] Components, entry point, and data hooks/provider pass Prettier checks.

* [x] Required API, SQL, browser, generation, and diff checks complete.

## Validation results

* API suite: 18 tests passed.

* Independent SQL and complete source/sink matrix reconciliation: market,
  holder, point, and combined filters passed, including unmapped inventory.

* Geographic query times: market 9,262.7ms; holder 5.6ms; point 5,189.7ms;
  combined 2.3ms. Broad geographic aggregation remains a local latency limitation.

* MapLibre: basemap style/tiles, native Enter/Space selection, hover/focus,
  pan/zoom/reset, retained camera, and contract-cell reconciliation passed.

* Floating panels: collapse, scrolling bounds, holdings hide/show and
  pointer/keyboard resize, header clearance, and desktop/narrow layout passed.

* Geographic loading, empty, missing-coordinate, error, and retry states passed.

* Dataset coverage: 1,002 participating market points; 11 lack complete coordinates.
  Report-change browser coverage is limited by the dataset's single report;
  API fixtures verify separate reports.

* Orval regenerated the geographic summary field automatically; generated output
  remains ignored and handwritten provider/hooks remain unchanged.

* Refactor builds and modal desktop/mobile, table, and keyboard checks: passed.

* Prettier checks for components, entry point, and data hooks/provider: passed.

* `git diff --check`: passed.
