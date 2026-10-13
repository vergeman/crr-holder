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

* Implement metadata, summaries, and holdings drill-down endpoints.
* Build report and portfolio filters, summary metrics, rankings, the holdings matrix, and contract details.
* Route TanStack Query hooks through a shared data-access interface, initially backed by Orval-generated HTTP calls.
* Verify filtering, pagination, and aggregate reconciliation; keep OPT and OBL separate.
* Leave a map placeholder until the tabular data flow works.

Output: a usable explorer backed by the API. See [API design](../api.md) and [frontend design](../web.md).

## Sprint 4 - Add the Map

* Show source and sink footprints using settlement-point coordinates.
* Connect map selections to the shared filters and holdings views.
* Reconcile geographic summaries with tabular totals.

Output: geographic exploration integrated with the existing explorer.

## Sprint 5 - Compare SQLite Access Modes

* Add browser SQLite via WASM, then a VFS approach, behind the shared data-access interface.
* Add a toggle between API and browser access modes with equivalent results.
* Benchmark query latency and frontend bandwidth across the same interactions.

Output: a benchmark suite and measured comparison of the access modes. See [engineering questions](../index.md#engineering-question).

