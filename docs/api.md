# API Plan

## Analytical / Component Level Endpoints

* Summary and Map

| Method | Endpoint        | Purpose                                                              | Parameters                                           |
|--------|-----------------|----------------------------------------------------------------------|------------------------------------------------------|
| GET    | `/api/metadata` | Reports, account holders, settlement points controls                 | `report_id?`, `account_holder?`                      |
| GET    | `/api/summary`  | Metrics, OPT/OBL, top-k rankings - collection of analystical queries | `report_id?`, `account_holder?`, `settlement_point?` |


* `/api/metadata`:
  * reports, account holders (list), settlement points (list)


* `/api/summary`:
  * Metrics: overall summary given filters: totalMwh, num account, num settlement points, num directedPath
  * HedgeTypeMix - maybe interesting per company
  * Top AccountHolders
  * Top SettlementPoints
  * Map update: Geographic Footprint (sp, sourceMwh, sinkMwh)
    * each node is source and sink circular marker



## Record / REST-Y drill-down endpoints

* For Detail CRR view holdings
* Only sources are paginated, using `limit?` and `offset?`; sinks and contracts
  return all matching rows initially.

| Method | Endpoint                               | Purpose                                                        | Parameters                                                               |
|--------|----------------------------------------|----------------------------------------------------------------|--------------------------------------------------------------------------|
| GET    | `/api/holdings/sources`                | CRR holdings matrix:  aggregate sources x month                | `report_id?`, `account_holder?`, `settlement_point?`, `limit?`, `offset?` |
| GET    | `/api/holdings/sources/{source}/sinks` | onClick expand source to show aggregate sinks                  | `source`, `report_id?`, `account_holder?`, `settlement_point?`           |
| GET    | `/api/holdings/contracts`              | onClick sink - expand to individual CRR records - no aggregate | `report_id?`, `source`, `sink`, `month`, `hedge_type`, `account_holder?`, `settlement_point?` |


## Parameters

* top down * `account_holder` and `settlement_point` drive everything;
* empty values focus on "entire market" view
  * `settlement_point`: inclusive source OR sink for summary and all holdings
    endpoints; count a matching holding once even when both endpoints match.


* remember OPT/OBL x TOU
* Source pagination: `limit` defaults to 20 (1–100); `offset` defaults to zero
  and must be nonnegative. It counts sources to skip in the sorted filtered list.
* The sources response returns `nextOffset` or null when no sources remain.
  Query `limit + 1` source identifiers once, return `limit`, and use the extra
  identifier to determine whether another page exists. Each source includes all
  delivery-month cells; pagination never splits a source row.
* Reset the offset to zero when report, holder, or settlement-point filters change.
  See [Sprint 3.3 contract](plan/0006-source-holdings-matrix.md).

* endpoints vs map:
  * if we show an aggregate MWh,it wil just be dominated by the hubs and loading zones, kind of obvious.
  * more interesting is to see the source-sink pairs, particularly by account holder. Sinks are also sources so not necessarily "losing" anything, this is just a way to look at it
  * better if we can reconcile it with tabular data below
  * simple first, simple better. stop overthinking everything.

query: measure its execution time.
aggregation: write a reconciliation test.
endpoint: verify pagination and filtering.
frontend interaction: verify the corresponding results.

* Avoiding canonical REST resources:
  1. not updating any records
  2. access is predominantely column-wise aggregation

