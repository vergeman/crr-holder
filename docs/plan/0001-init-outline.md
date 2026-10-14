# 0001 - Project and Sprint Outline

Build an ERCOT CRR holdings explorer, then compare API access with browser SQLite.
Use this outline to sequence the detailed implementation plans.

## Sprint 1 - Prepare the Dataset

* Parse the available holdings, account-holder, and TOU data into SQLite raw tables.
* Prepare monthly holdings and settlement-point coordinates for exploration.
* Keep ingestion minimal; automated fetching and a general ETL pipeline are outside the initial scope.

Output: a reproducible SQLite dataset. See [data design](../data.md).

## Sprint 2 - Establish the Stack

* Set up project directories, dependencies, Dockerfiles, and Docker Compose.
* Connect FastAPI to SQLite and scaffold React with TanStack Query and Orval.
* Run a hello-world request from the web app through the API.

Output: a working local development stack.

## Sprint 3 - Build the Explorer

Build the following groups in order, each ending with a working UI flow.
Leave a map placeholder until Sprint 4.

### 3.1 - Filters and Portfolio Summary

Detailed plan: [0004 - Filters and Portfolio Summary](0004-filters-portfolio-summary.md).

* Implement `/api/metadata` and the metrics and OPT/OBL mix in `/api/summary`.
* Build report, account-holder, and settlement-point selectors, clear filters,
  and portfolio summary metrics.
* Narrow settlement-point dropdown choices to the report and selected holder's
  sources or sinks (inclusive union, unique points). On holder change, clear the
  point immediately and refresh dropdown metadata and summary in parallel.
* Default to the latest report by publication date; never combine report snapshots.
* Apply settlement-point filtering as source OR sink across summaries and holdings.
  Include each matching holding once, including when both endpoints match.
* Use contractual MWh for summaries and matrix cells. Keep OPT and OBL separate
  and do not net opposing ordered source-sink pairs.
* Establish TanStack Query and Orval generation. Write generated HTTP client
  code and types only under `web/src/generated/`; treat that directory as
  replaceable output, with no handwritten wrapper or hook code inside it.
* Automatically regenerate the client from the API's OpenAPI schema during
  development startup and when the API schema changes.
* Keep the handwritten data-access wrapper outside `web/src/generated/`. Import
  generated HTTP calls into that wrapper and route TanStack Query hooks through
  it, so regeneration cannot overwrite the wrapper or hooks.
* Add a brief comment at the wrapper's provider selection identifying it as the
  place to swap HTTP for browser SQLite or VFS providers in Sprint 5.
* Verify that an API schema change updates generated output automatically while
  leaving the handwritten wrapper and hooks unchanged.
* Verify market, account-holder, settlement-point, and combined filters against
  dataset totals, including a holding whose source and sink both match.

Output: selecting a portfolio updates trustworthy totals; clearing filters
returns to the market view for the selected report.

### 3.2 - Rankings and Discovery

Detailed plan: [0005 - Rankings and Discovery](0005-rankings-discovery.md).

* Add top-ten account-holder and settlement-point rankings by contractual MWh
  under the current filters to `/api/summary`.
* Show both discovery lists side by side, stacking on narrow screens, and connect
  ranking clicks to the shared filters.
* Display holder identifiers and available legal names from the existing directory.
* Verify holder clicks clear the settlement-point filter and settlement-point
  clicks retain the holder; each updates the corresponding filtered summary.

Output: users can discover holders and settlement points through rankings.

### 3.3 - Source Holdings Matrix

Detailed plan: [0006 - Source Holdings Matrix](0006-source-holdings-matrix.md).

* Implement `/api/holdings/sources` and the source-by-delivery-month matrix.
* Display separate OPT and OBL columns with horizontal month scrolling.
* Initially show a fixed number of complete source rows; provide "show more
  sources." Define the initial count in the detailed implementation plan.
* Page sources only using `limit` and `offset`, returning `nextOffset`; each
  returned source includes all its delivery-month cells.
* Sort sources by total contractual MWh across delivery months and both hedge
  types, descending; use the source identifier to break ties.
* Verify source pagination without duplicates or omissions and reconcile all
  source cells with the filtered summary, separately for OPT and OBL.

Output: users can explore a portfolio's sources across delivery months.

### 3.4 - Sink Expansion

Detailed plan: [0007 - Sink Expansion](0007-sink-expansion.md).

* Implement `/api/holdings/sources/{source}/sinks` and load sinks on expansion.
* Return all matching sinks for an expanded source without pagination or cutoff;
  include all delivery-month cells and retain the shared filters.
* Sort sinks by total contractual MWh across delivery months and both hedge
  types, descending; use the sink identifier to break ties.
* Verify expansion under the shared filters and reconcile sink cells with their
  parent source cells, separately for OPT and OBL.

Output: expanding a source explains its totals through Source-Sink Pairs.

### 3.5 - Contract Details and Completed Workspace

Detailed plan: [0008 - Contract Details and Completed Workspace](0008-contract-details-workspace.md).

* Implement `/api/holdings/contracts` and open details from a sink/month/hedge-type
  cell, retaining the report and portfolio filters.
* Return all contracts matching that cell without pagination initially.
* Show original contract fields, including MW and TOU, alongside each contract's
  MWh contribution to the selected delivery month.
* Group contracts by account holder and TOU. Sort account-holder groups by total
  MWh descending and contract rows within each TOU group by selected-month MWh
  descending; break ties with account-holder identifier or CRR ID and segment ID.
* Show the full cell total and account-holder/TOU subtotals regardless of whether
  their groups are expanded. Expansion changes visibility, not totals.
* Finish the holdings panel's hide and resize behavior.
* Reconcile contract contributions and group subtotals with the clicked cell;
  verify that collapsing groups leaves totals unchanged.
* Check a market-wide cell with many contracts to assess whether an unpaginated
  detail response is practical before considering any pagination change.

Output: users can move from market totals to individual contracts and reconcile
numbers throughout the drill-down.

Measure representative query execution times as queries are implemented.
Use the prepared dataset without adding stored fields or changing its schema.
Full access-mode benchmarking belongs to Sprint 5. Map endpoint MWh counts source
and sink participation separately; adding those endpoint totals counts each path
at both ends and is not the portfolio's contractual MWh total.

Output: a usable explorer backed by the API. See [API design](../api.md) and
[frontend design](../web.md). These groups refine the earlier design sketches;
only source lists require pagination initially.

## Sprint 4 - Add the Map

Detailed plan: [0009 - Map Integration](0009-map-integration.md).

### Map Integration

* Show source and sink footprints using settlement-point coordinates.
* Connect map selections to the shared filters and holdings views.
* Reconcile geographic summaries with tabular totals.

Output: geographic exploration integrated with the existing explorer.

### 4.1 - Frontend Refactors

Implementation details, commit groups, acceptance, and validation:
[0010 - Frontend Refactors](0010-frontend-refactors.md).

* Establish consistent dropdowns, buttons, disclosure carets, and action icons;
  evaluate lightweight UI and icon libraries before choosing the approach.

* Compress Explore Holdings into horizontal filters and a visually joined,
  two-column portfolio summary.

* Widen discovery into readable account-holder and settlement-point tables,
  emphasizing full names, aligned totals, and clear selection states.

* Improve holdings edge resizing, source-cell expansion, and contract-modal
  hierarchy and spacing; move the holdings pane closer to the bottom edge.

* Refine map hover details, background-click clearing, grouped map controls,
  compact legend, red/blue encoding, and visible filtered-circle scaling.

* Work in that order, prompting for the control-system decision and staged
  visual feedback on portfolio/discovery, holdings/modal, and map changes.

Output: a more compact, consistent explorer, with implementation decisions and
visual feedback captured through staged reviews.

### 4.2 - Offset Pagination Benchmark

* TODO: once the explorer flow is wired, measure first-page and later-page
  source endpoint latency under market, holder, point, and combined filters.

* Assess aggregation cost and increasing offsets before deciding whether
  keyset (cursor) pagination would improve performance.

## Sprint 5 - Compare SQLite Access Modes

* Add browser SQLite via WASM, then a VFS approach, behind the shared data-access interface.
* Add a toggle between API and browser access modes with equivalent results.
* Benchmark query latency and frontend bandwidth across the same interactions.

Output: a benchmark suite and measured comparison of the access modes. See [engineering questions](../index.md#engineering-question).

