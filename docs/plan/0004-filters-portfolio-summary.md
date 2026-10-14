# 0004 - Sprint 3.1: Filters and Portfolio Summary

Type: feat
Branch: feat/0004-filters-portfolio-summary

## Goal

* Replace the account-holder list demo with report and portfolio filters.
* Display four portfolio metrics and an OPT/OBL split from the prepared SQLite data.
* Route TanStack Query through a handwritten provider wrapper importing an
  automatically updated Orval HTTP client.

## Context

* Sprint 2 provides FastAPI, SQLite, React, Vite, and Docker Compose connectivity.
  TanStack Query and Orval are installed but not configured.
* Implement group 3.1 in [the sprint outline](0001-init-outline.md#31---filters-and-portfolio-summary).
* Use existing `reports`, `account_holders`, `settlement_points`, and
  `crr_monthly_holdings` tables.
  Monthly contractual MWh is already prepared in three TOU columns.
* Rankings, holdings drill-down, and map implementation follow in later groups.

## Implementation limits

* Work in `api/` and `web/`; adjust Compose only as needed for development startup.
* Keep Python `sqlite3`, read-only database access, and the existing database mount.
  Do not change ingestion, schema, indexes, or stored fields.
* Keep handwritten frontend code in JavaScript. Orval may emit TypeScript client
  code and types under `web/src/generated/`; do not migrate the application.
* Use existing dependencies and Node built-ins for generation automation.
  Do not add a chart library, router, ORM, or test framework.
* Implement only metadata and summary operations in the shared access wrapper.
  Do not create future provider implementations or a generic provider registry.
* Use native selectors and minimal CSS for the header, filters, summary, and map
  placeholder. No search widgets, account profile, TOU chart, or holdings panel.

## API and Filter Contract

* `GET /api/metadata` accepts optional `report_id` and `account_holder`.
  The account-holder parameter narrows settlement-point dropdown choices only.
* `GET /api/summary` accepts optional `report_id`, `account_holder`, and
  `settlement_point`. Omitted or empty portfolio filters mean all holders/points.
* Resolve an omitted report to the latest `publication_date`, breaking ties with
  descending `report_id`. Every query operates on exactly one report.
* Combine active filters with AND. Settlement-point matching is
  `(source = settlement_point OR sink = settlement_point)` in a single predicate;
  a holding matching both ends contributes once.
* Use the whole delivery horizon present in the selected report. This group has
  no delivery-month filter, hedge-type filter, TOU filter, or pagination.
* Define explicit FastAPI response models and stable operation names so OpenAPI
  generation produces named metadata and summary operations.

### Metadata response

| Field | Shape | Meaning |
|---|---|---|
| `reportId` | integer | Resolved report used for account-holder dropdown choices and summaries. |
| `reports` | array of `{ reportId, publicationDate }` | All reports, latest first; dates retain ISO format. |
| `accountHolders` | array of `{ accountHolder, legalName }` | Holders present in the selected report; legal name may be null. |
| `settlementPoints` | array of strings | Unique points used as sources or sinks in the selected report, narrowed to the selected holder when provided. |

* Order holder dropdown choices by identifier and point dropdown choices
  alphabetically. Include an All choice in each UI dropdown.
* Obtain report-specific holder dropdown choices from monthly holdings, joining
  the existing holder directory for legal names. Do not return unused holders.
* Obtain relevant point identifiers from sources and sinks in monthly holdings
  for the selected report and optional holder; join `settlement_points` for the
  directory identifiers. Use an inclusive union: source, sink, or both qualify,
  and each point appears once. Do not return unused directory points.
* With no holder selected, show all points used in the report. With holder X
  selected, show only points used by X. The selected point does not narrow its
  own dropdown or the account-holder dropdown.
* Holder dropdown choices depend only on report, so users can switch accounts
  while a point is selected. Point dropdown choices depend on report and holder.
* Do not return email domains, coordinates, or other enrichment in this group.

### Summary response and display

| Field | Display label | Calculation over matching monthly holdings |
|---|---|---|
| `totalMwh` | Total Contractual MWh | Sum `peak_wd_mwh + peak_we_mwh + off_peak_mwh` across all matching rows. |
| `accountHolderCount` | Account Holders | Count distinct account-holder identifiers. |
| `settlementPointCount` | Settlement Points | Count the distinct union of source and sink identifiers. |
| `directedPathCount` | Directed Paths | Count distinct ordered `(source, sink)` pairs. |
| `hedgeTypeMwh.OPT` | Options | Sum contractual MWh for OPT rows. |
| `hedgeTypeMwh.OBL` | Obligations | Sum contractual MWh for OBL rows. |

* Return `reportId` alongside these fields to identify the resolved snapshot.
* Counts describe matching holdings, not the available dropdown choices. Under a
  settlement-point filter, point count includes its matching counterparties.
* Count each holder, point, and directed pair once across delivery months, TOU,
  and hedge types. A reversed path is a different directed path; do not net it.
* Always return both hedge-type keys. An absent type or empty result has zero MWh;
  an empty result also has zero counts and zero total MWh.
* Derive percentages in the UI as `100 * typeMwh / totalMwh`, or zero when total
  is zero. Do not add separately returned percentages or TOU totals.
* Display total MWh and both hedge-type MWh with consistent number formatting;
  show each hedge type's percentage to one decimal place and a simple CSS bar.
  Rounding affects display only, not API values or reconciliation.
* Identify the summary as contractual inventory across the report's delivery
  horizon; do not label it energy delivered, risk, or net exposure.

## Approach

### Commit group 1 - Metadata and summary API

* Replace temporary `/api/account-holders` with metadata and summary endpoints in
  `api/main.py`; put the query functions in `api/queries.py`.
* Preserve opening the database read-only and closing it per request.
* Resolve the report before querying report-specific metadata or summary values.
* Sum prepared monthly MWh columns rather than recalculating TOU hours or summing
  MW across months. Use distinct result sets for point and directed-pair counts.
* Keep SQL readable with brief comments identifying filtered holdings, distinct
  sets, and aggregate results. Do not add cached or materialized results.

### Commit group 2 - Generated HTTP client and query boundary

* Add `web/orval.config.js` targeting the running API's OpenAPI schema and writing
  HTTP functions and associated types only under `web/src/generated/`.
* Generate plain HTTP operations; maintain TanStack hooks by hand outside that
  directory. Do not generate a second set of query hooks.
* Add a small Node development script under `web/scripts/` and wire it into
  `npm run dev`. Use built-in fetch to poll `http://api:8000/openapi.json` at a
  short fixed interval, retaining the last successful schema in memory.
* Wait for the API, generate once before starting Vite, then regenerate whenever
  schema contents change, including after an API reload. Serialize generation;
  only accept the changed schema after successful generation. Expose errors in
  development output and retry on a later poll. Stop child processes on shutdown.
* Do not write a separate OpenAPI snapshot or add a file-watcher dependency.
* Keep generated imports available at startup and allow Vite to pick up regenerated
  files. Document generation/startup behavior briefly in the existing README.
* Add `web/src/data/provider.js`: import generated HTTP functions, unwrap their
  responses, and expose only `getMetadata` and `getSummary` for this group.
* At the exported provider selection, add a brief comment: "Swap the HTTP provider
  here for browser SQLite or VFS in Sprint 5."
* Add `web/src/data/hooks.js` with handwritten TanStack Query hooks invoking that
  provider. Include resolved report and active portfolio filters in query keys;
  omit empty filters from HTTP requests. Metadata keys include report and holder;
  summary keys include report, holder, and settlement point.
* Add a QueryClient provider at the React entry point. Components consume hooks
  and do not import generated HTTP functions directly.

### Commit group 3 - Filters and portfolio summary UI

* Replace the demo view with a header/report selector, filter controls, portfolio
  summary, OPT/OBL mix, and a map placeholder; extract components only as needed
  for these distinct sections.
* Own `reportId`, `accountHolder`, and `settlementPoint` in the explorer component.
  Initialize report selection from metadata's resolved latest report before
  enabling the summary query.
* Show report publication dates in the report selector and holder identifiers
  with legal names where available. Default holder/point selections to All.
* On report change, clear holder and point filters and load metadata for the new
  report. Clear Filters resets holder and point while retaining the report.
* On account-holder change, update the holder and reset settlement point to All
  together, before requests start. This also prevents an incompatible old point
  from being submitted with the new holder; do not wait for metadata to clear it.
* Fetch metadata for the new report/holder and summary for the new filters in
  parallel. The summary does not wait for settlement-point dropdown data.
* Immediately show the selected holder. While its point choices load, disable
  the point dropdown and show "Loading settlement points..." rather than the
  previous holder's choices. Populate and enable it when metadata arrives.
* On settlement-point change, fetch only the summary; metadata does not depend
  on that selection. Keep the report's account-holder dropdown available.
* Let TanStack Query reuse cached data under the matching query keys; do not add
  a separate cache. Cached choices can populate the dropdown immediately.
* Show brief loading and request-error text. If metadata fails, keep the point
  dropdown disabled with an error while allowing the independent summary to load.
  Do not show an older portfolio's totals as the selected portfolio's totals
  while the next summary is loading.
* Show zero metrics and an empty-holdings message for a successful empty result.

## Scope control

* Use the smallest implementation satisfying the acceptance criteria.
* Treat acceptance criteria and verification below as closed lists.
* Before adding unplanned stored data, files, dependencies, or substantial
  verification steps, explain why, explicitly prompt the user for a scope decision,
  and wait for their reply. Existing authorization covers the requested work.
* Resolve routine implementation choices within this scope without prompting.
* Leave ingestion and later sprint features unchanged.

## Validation and Tests

* Add `api/tests/test_summary.py` using standard-library unittest. Define fixture
  rows as Python literals in that same file, not in a separate fixture file.
* In the test class's `setUp`, create a fresh `sqlite3.connect(":memory:")` database,
  load `db/crr/sql/schema.sql`, and insert the rows specified below. Close the
  connection in `tearDown`. Each test gets an isolated database; no `.sqlite`
  fixture file is created, copied, or committed, and the prepared database is not
  modified. Query functions receive this connection directly.
* Populate only `reports`, `account_holders`, `settlement_points`, and
  `crr_monthly_holdings`. Leave raw holdings and TOU tables empty: these unit tests
  exercise queries over already prepared monthly data, not dataset preparation.
* Separate setup, execution, and assertions. No HTTP test-client dependency is
  required. Assert independently specified totals and counts for market,
  holder-only, point-only, combined, and empty filters.
* Assert latest-report resolution and explicit-report isolation. Assert holder
  dropdown choices contain the selected report's holders, retain a holder without
  a legal name, and stay unchanged under account-holder filtering of metadata.
* Assert point dropdown choices contain the report's used points with no holder
  selected, narrow to the holder's used points when selected, exclude unused
  directory points, and include points used as source only, sink only, or both
  exactly once.
* Run `python -m unittest discover -s api/tests -v` in the API container once.
* Against the prepared database, compare market, one holder, one point, and their
  combination through `/api/summary` with independent raw-holdings SQL joined to
  `tou_hours`. Compare all four metrics and both hedge-type totals; use the existing
  MWh tolerance `1e-6 + 1e-10 * abs(expected)`. Reuse that holder/point for the UI check.
* Measure and record representative metadata/summary query times in the
  implementation report; add no timing fields, persisted logs, or benchmark suite.
* Start Compose through the documented command. Manually check default report,
  each filter, combined filters, clear filters, empty results, and OPT/OBL display.
  When switching accounts with a point selected, verify the immediate reset,
  loading dropdown, narrowed choices, and parallel metadata/summary requests in
  browser network tools. Returning to a holder may reuse its cached choices.
* Temporarily change an API response schema and verify automatic regeneration and
  that the handwritten wrapper/hooks remain unchanged. Restore the schema and
  verify regeneration back to the intended contract. Run no unrelated test suite.

### Exact unit-test fixture

Keep this data inline in `api/tests/test_summary.py`:

* Two reports: `(1, "2026-09-01")` and `(2, "2026-10-01")`.
* Three holders: `X` and `Z` with legal names, and `Y` with a null legal name.
* Five settlement points: `A`, `B`, `C`, `D`, and `E`; enrichment fields may be null.
  `E` is a directory entry without holdings.
* Eight monthly holdings rows, specified below. MWh columns are explicit fixture
  values. Fill the schema's required MW columns with zero; these summary queries
  do not read MW. Do not derive expected assertions by rerunning aggregate logic.

| Report | Holder | Source | Sink | Delivery month | Hedge | PeakWD MWh | PeakWE MWh | Off-peak MWh |
|---|---|---|---|---|---|---:|---:|---:|
| 1 | X | A | B | 2026-10-01 | OPT | 10 | 0 | 0 |
| 1 | Z | D | A | 2026-10-01 | OBL | 20 | 0 | 0 |
| 2 | X | A | B | 2026-10-01 | OPT | 8 | 2 | 0 |
| 2 | X | A | B | 2026-11-01 | OPT | 10 | 5 | 5 |
| 2 | X | B | A | 2026-10-01 | OBL | 0 | 30 | 0 |
| 2 | X | A | A | 2026-10-01 | OPT | 0 | 0 | 40 |
| 2 | Y | C | D | 2026-10-01 | OBL | 50 | 0 | 0 |
| 2 | Y | C | A | 2026-10-01 | OPT | 20 | 20 | 20 |

For report 2, market totals are 210 MWh (130 OPT, 80 OBL), two holders,
four points, and five directed paths. Holder X has 100 MWh (70 OPT, 30 OBL),
one holder, two points, and three directed paths. Point A matches 160 MWh;
the A-to-A row contributes its 40 MWh once. Holder X with point A has 100 MWh;
holder X with point C has zero. Report 1 totals 30 MWh and must stay separate.
Report 2's point dropdown contains A/B/C/D, X's contains A/B, and Y's contains
A/C/D. Report 1's contains A/B/D. No dropdown includes E.

## Acceptance

* [x] Metadata defaults to the latest publication, offers report-specific holders,
  and returns unique source-or-sink points for the report and optional holder.
* [x] Account changes immediately reset the point and fetch metadata/summary in
  parallel; the point dropdown shows loading then relevant choices, and holder
  choices remain available independently of the selected point.
* [x] Summary returns the four defined metrics and both hedge-type MWh totals for
  one snapshot, with accurate source-or-sink filtering and no double counting.
* [x] The UI displays the metrics and OPT/OBL MWh/percentages under shared filters;
  clear filters retains the report, and empty results display zero totals.
* [x] Generated code stays under `web/src/generated/` and updates automatically on
  startup/schema changes without overwriting handwritten wrapper or hook code.
* [x] TanStack hooks call the provider wrapper, whose selection includes the
  provider-swap comment; components do not call generated HTTP functions directly.
* [x] The finite fixture, real-data reconciliation, query timings, and manual
  interaction/generation checks above are completed.
* [x] No schema changes, new dependencies, rankings, holdings views, or map logic
  are introduced.

## Implementation Validation

* Fixture tests passed in the API container with
  `python -m unittest discover -s tests -v` (three tests with filter subcases).
  The container mounts `api/` at `/app` and the schema at `/data/sql/schema.sql`.
* Market, XNRGLD, HB_NORTH, and their combined API summaries reconciled with
  independent raw-contract/TOU calculations for all specified metrics.
* Browser interaction checks passed for latest-report initialization, individual
  and combined filters, immediate point reset, narrowed dropdowns, loading,
  parallel requests, cached choices, clear filters, report reset, empty results,
  and OPT/OBL values/percentages. No application runtime exceptions were observed.
  The prepared dataset contains one report; cross-report isolation is covered by
  the two-report unit fixture.
* Temporary response-field changes and restoration regenerated the HTTP client
  automatically; provider and hooks remained byte-for-byte unchanged.
* The existing development environment remains running. Modern
  `docker compose up -d --remove-orphans` succeeded; legacy `docker-compose` hit
  a `ContainerConfig` compatibility error with the installed Docker Engine.
* Representative local query timings after using direct active-filter predicates:

| Query | Execution time |
|---|---:|
| Market summary | 3,121.7 ms |
| XNRGLD summary | 0.5 ms |
| HB_NORTH summary | 2,104.5 ms |
| XNRGLD + HB_NORTH summary | 0.5 ms |
| Market metadata | 1,292.4 ms |
| XNRGLD metadata | 489.1 ms |

Broad report queries remain noticeably slower than account-specific summaries;
no dataset indexes or schema were changed. These are representative measurements,
not a benchmark suite.
