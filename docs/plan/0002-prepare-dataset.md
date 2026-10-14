# 0002 - Prepare Dataset

Type: feat Branch: feat/0002-prepare-dataset Status: planned

## Goal

* Build a SQLite dataset from four supplied files in a Docker container.
* Store contracts and monthly holdings for the explorer, with settlement-point
  coordinates and account enrichment.

## Context

* Implements Sprint 1 of `0001-init-outline.md`; follows `docs/data.md` and
  `docs/api.md`.
* Use `data/CRROwnershipofRecord10012026.zip`,
  `data/List_of_Market_Participants_in_ERCOT_Region_20261011.xlsx`,
  `data/CRR-Time-of-Use-Hours_2026-2029_UPD.xlsx`, and `data/topology.json`.

## Implementation limits

* This is a one-shot importer for the four supplied files. Support their current
  formats and observed values; let unexpected formats fail plainly.
* Optimize for short, readable code and easy inspection. Use plain functions
  without reusable ingestion abstractions or support for hypothetical inputs.
* Retain original inputs in `data/`. Store each field once in ordinary columns;
  no JSON copies or extra audit/location metadata.
* Use only the six tables listed below, defining their columns in `sql/schema.sql`.
  Settlement points contain only `settlement_point`, `longitude`, `latitude`,
  `point_type`, `load_zone`, and `capacity_mw`. Additional columns require discussion.
* Use one Python entry point, one input-reader helper, and the four SQL files.
  Do not introduce further helper modules, dependencies, or generated artifacts.
* Do NOT touch: API/frontend implementation, application Docker setup, automated
  fetching, or browser SQLite benchmarks.

## Approach

* Work in `db/crr/`; entry point: `prepare_dataset.py`; output: `crr.sqlite`.
* Load SQL relative to the script and bind input query parameters.

### 1. Container and schema — commit group 1

* Use the official `python:3.12-slim-bookworm` image with its pinned digest and
  pinned `openpyxl` dependency; verify `import sqlite3` at image build time.
* Document image build and one-shot execution commands. Mount `data/` read-only
  and `db/crr/` for output; run with the host user's UID/GID.
* Define `reports`, `crr_holdings`, `account_holders`, `tou_hours`,
  `settlement_points`, and `crr_monthly_holdings` in `sql/schema.sql`;
  keep lookup indexes in `sql/indexes.sql`.
* Keep report identity separate from delivery dates. Record input filenames,
  known publication dates, and hashes in `reports`. Enforce raw
  uniqueness with the `(report_id, crr_id, segment_id)` primary key.

### 2. Import inputs — commit group 2

* Stream the holdings CSV directly from the ZIP. Store CRR/segment IDs as
  INTEGER, inclusive delivery dates as ISO date text, and MW as REAL. Store the
  remaining source fields directly in their columns and normalize TOU names.
* Import the CRRAH sheet as account short name, legal name, and email domain.
  Retain unmatched accounts with null enrichment.
* Import the published monthly TOU hours, mapping `OffPeak` to `Off-peak`.
  Use the workbook's hours, including daylight-saving months.
* Read `settlement_points.features` and match `properties.sp_id` to holdings
  sources/sinks. Interpret Point coordinates as `[longitude, latitude]` and
  store point type, load zone, and capacity in the six settlement-point columns.
* Give every source/sink a settlement-point row; retain null coordinates for
  missing locations. Hub/load-zone coordinates are representative approximations.

### 3. Materialize and verify — commit group 3

* Expand the supplied whole-month contracts across their inclusive delivery
  months using `sql/monthly_holdings.sql`.
* Aggregate by report, account, source, sink, month, and hedge type into PeakWD,
  PeakWE, and Off-peak MW/MWh columns. Multiply MW by published monthly hours;
  keep OPT and OBL separate and contracts available for drill-down.
* Use `sql/validate.sql` for only the checks and counts listed below.
* Build into a temporary database and replace `crr.sqlite` after validation.
  Ignore generated databases in Git and Docker build contexts.

## Validation and tests

* Implement only these checks:
  1. Raw row count matches the CSV.
  2. Required monthly TOU hours exist.
  3. Monthly MW/MWh reconcile by report, hedge type, delivery month, and TOU,
     allowing `1e-6 + 1e-10 * abs(expected)` tolerance.
* Report missing account enrichment and coordinates as counts.
* Use one small fixture for monthly expansion and TOU mapping, with explicit
  expected rows. Do not add a malformed-input matrix or speculative edge cases.
* Run the complete import once. Additional full builds require a concrete
  failure or unresolved concern; a comparison database is not a normal output.

## Acceptance

* [ ] Documented Docker commands generate `db/crr/crr.sqlite` from the four inputs
      without manual ZIP extraction, with output owned by the host user.
* [ ] The script loads separate schema, materialization, index, and validation SQL.
* [ ] Contract fields are stored once in parsed columns; original inputs remain
      on disk and no JSON copies are stored in the database.
* [ ] Raw counts, required TOU hours, and monthly MW/MWh totals reconcile.
* [ ] OPT/OBL and TOU blocks remain separate, with contracts available for drill-down.
* [ ] Every source/sink has a settlement-point row with the six retained columns;
      missing enrichment and coordinates remain null and are counted.
