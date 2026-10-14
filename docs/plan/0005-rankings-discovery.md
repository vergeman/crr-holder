# 0005 - Sprint 3.2: Rankings and Discovery

Type: feat
Branch: feat/0005-rankings-discovery

## Goal

* Add top-ten holder and settlement-point rankings to the portfolio summary.
* Connect discovery list clicks to the existing shared filters.
* Display holder identifiers and available legal names.

## Context

* Implement Sprint 3.2 in [the outline](0001-init-outline.md#32---rankings-and-discovery).
* Build on Sprint 3.1's summary, metadata, filters, and provider boundary, now
  merged into master. See [its detailed plan](0004-filters-portfolio-summary.md).
* Use existing monthly holdings and holder directories without changing storage.
* Leave holdings drill-down, map implementation, and access-mode comparisons to
  later sprint groups.

## Implementation limits

* Group ranking SQL in `api/rankings.py`, with `get_top_account_holders` and
  `get_top_settlement_points` query functions.
* Keep `api/queries.py` as the summary orchestration point and `api/main.py` as
  the endpoint/response contract.
* Put ranking tests in `api/tests/test_rankings.py` and shared fixture setup in
  `api/tests/fixtures.py`; retain metric and metadata tests in
  `api/tests/test_summary.py`.
* Extend `web/src/main.jsx` and `web/src/style.css`; retain the existing
  `web/src/data/` provider and hooks as the request boundary.
* Use existing dependencies, read-only SQLite, and handwritten JavaScript.
* Add no endpoint, request parameter, pagination, search, chart library, index,
  stored aggregate, schema change, or separate ranking query hook.
* Return at most ten rows per list, with no configurable limit or Show More.
* Keep automatically generated Orval output ignored under `web/src/generated/`.

## Ranking contract

Extend `/api/summary` without changing its operation name, existing fields,
parameters, latest-report default, or single-report behavior.

| Field | Row shape |
|---|---|
| `topAccountHolders` | `{ accountHolder, legalName, totalMwh }` |
| `topSettlementPoints` | `{ settlementPoint, totalMwh }` |

* Both lists use the same matching holdings as the summary: report, optional
  holder, and inclusive source-or-sink point filter.
* Sum the three prepared monthly MWh columns over the whole delivery horizon
  and both OPT/OBL. Do not net reversed source-sink pairs.
* Holder totals group by identifier. Join the existing directory for legal names;
  keep identifiers when names are null.
* Point totals sum holdings matching that point as source or sink. Count a
  same-endpoint holding once for that point. Different endpoints each receive
  the holding's MWh in their separate point groups.
* Expand source contributions plus sink contributions where sink differs from
  source. Do not deduplicate contributions from separate months or holders.
* Order unrounded MWh descending, then identifier ascending. Apply the ten-row
  limit after grouping and ordering. Empty results return two empty arrays.
* Point groups overlap, so their summed totals do not reconcile to portfolio MWh.
  Holder groups partition holdings, but the top-ten subset can omit holders.
  Add no percentages or Other aggregate.

## Discovery behavior

* Add Discover beneath the summary with Top Accounts and Top Settlement Points
  visible side by side. Stack the lists on narrow screens; there is no toggle.
  Both lists come from the same summary response.
* Display rank, identifier, formatted MWh, and holder legal name when available.
  Use native row buttons, descriptive list headings, and existing number
  formatting. A small shared ranking-list component may render both lists.
* Attach an information tooltip to each list subheading instead of a separate
  information icon or visible explanatory text. Both tooltips say: "Ranked by
  contractual MWh for the current filters." The Top Settlement Points tooltip also explains: "Each holding
  counts toward its source and sink; identical endpoints count once. Do not add
  settlement-point totals to calculate portfolio MWh."
* Make tooltip information available on hover and keyboard focus, with an
  accessible description on each keyboard-focusable subheading. Use existing
  dependencies.
  A 100 MWh A-to-B holding contributes 100 to A and 100 to B while the portfolio
  contains 100 MWh; A-to-A contributes only 100 to A.
* Holder clicks reuse the holder-change handler: retain report, select holder,
  immediately clear point, then fetch point metadata and summary in parallel.
* Clicking a row in Top Settlement Points selects that settlement-point
  identifier, retains report and holder, replaces the settlement-point filter,
  and fetches only summary.
* Each list heading has a Clear button, disabled when its filter is inactive.
  Clearing Top Accounts removes only the holder filter, retaining report and
  settlement point; fetch metadata and summary through the existing hooks.
  Clearing Top Settlement Points removes only the point filter, retaining report
  and holder; fetch only summary. This differs from choosing a holder, which
  continues to clear the point immediately.
* Values describe holdings before the click. Replacing an existing point can
  admit additional holdings; a holder click clears the previous point. Those
  transitions need not preserve the displayed ranking total.
* With no point filter, a settlement-point ranking click produces its ranked MWh
  as the new summary total. From the unfiltered market, a holder click produces its ranked MWh.
* Use the existing filter state for dropdowns, clicks, report changes, and Clear
  Filters. Keep existing loading/error behavior; do not show an older portfolio's
  rankings as the newly selected portfolio. Show an empty-list message when empty.

## Approach

### Commit group 1 - Plan documentation

* Commit this plan independently after the Sprint 3.2 outline and discovery
  layout documentation.

### Commit group 2 - Shared test fixture

* Extract the existing fixture into `api/tests/fixtures.py` and update summary
  tests to reuse it without changing their metric and metadata assertions.
* Keep this extraction separate from the ranking implementation.

### Commit group 3 - Ranking API and fixture checks

* Add separate holder and point aggregate queries in `api/rankings.py`; do not
  enlarge the existing metrics SQL into one combined ranking query.
* Have `get_summary` call the ranking functions with its connection, resolved
  report, and active filters, then attach their results to the response. Use the
  same bound predicate semantics through `holdings_filter` in `api/filters.py`,
  imported by both summary and rankings. No generic query framework.
* Add named FastAPI ranking-row models and both arrays to `Summary`.
* Label imports, preparation, filtered holdings, endpoint contributions,
  aggregation, and output with brief purpose-oriented comments.
* Add ranking tests in `api/tests/test_rankings.py` using the already extracted
  eight-row fixture in `api/tests/fixtures.py`.
* Update summary tests to use the shared fixture and assert their existing metric
  fields without requiring the response to contain only those fields. Assert the
  ranking arrays through `get_summary` in the separate ranking test file.

### Commit group 4 - Discovery UI and generated contract

* Let the existing development process regenerate the Orval response types.
  Do not edit or commit generated output.
* Read rankings through the existing provider and summary hook.
* Implement the two visible lists and row clicks. Use a small shared list
  component where their rendering is the same; keep filter state in the explorer.
* Record the specified validation results and query times in this plan.

### Commit group 5 - Independent filter clearing and subheading tooltips

* Add separate Clear buttons for Top Accounts and Top Settlement Points. Keep
  each disabled while its own filter is inactive; clear only that filter.
* Keep holder-selection behavior unchanged. Holder clearing uses the holder
  state setter directly so the selected settlement point is retained.
* Remove information icons. Show the existing explanations when the subheading
  is hovered or keyboard-focused, retaining an accessible description.
* Verify both independent clears, retained report/dropdown selections, disabled
  buttons, request behavior, and subheading hover/focus tooltips in the browser.
  Reuse running services; no repeat API suite or SQL reconciliation is needed
  for these UI-only changes.

## Scope control

* Use the smallest implementation satisfying the acceptance criteria.
* Treat acceptance and verification as closed lists.
* Before adding unplanned stored data, files, dependencies, or substantial
  verification, explain why, explicitly prompt for a scope decision, and wait.
  Existing authorization covers work specified here.
* Resolve routine implementation choices without asking for confirmation.
* Inspect Compose configuration and `docker compose ps` before starting services;
  reuse running development services.

## Validation and tests

* Use the shared in-memory fixture to check that rankings match the summary's
  filters and report, count identical endpoints once, and apply deterministic
  ordering and the ten-row limit. Keep existing metric and metadata coverage.
* Run `python -m unittest discover -s tests -v` in the API container.
* Compare market, holder, point, and combined rankings with independent
  read-only SQL to confirm real-data totals and ordering; record summary times.
* Check browser layout, filter selection/clearing, request behavior, tooltips,
  and loading/error/empty states so discovery stays aligned with the portfolio.
* Confirm Orval regenerates the ranking contract and generated output stays
  ignored, with provider and hooks outside it.

## Acceptance

* [x] Summary returns both ranking arrays for the active report and filters.
* [x] Rankings use contractual MWh, deterministic ties, and a ten-row limit;
  same-endpoint holdings count once per point.
* [x] Holder identifiers and available legal names display correctly.
* [x] Both ranking lists are visible side by side, stacking on narrow screens;
  row clicks update shared filters with the specified reset/request behavior.
* [x] Heading tooltips explain current-filter ranking context and overlapping
  settlement-point totals, with hover and keyboard-focus access.
* [x] Loading, errors, and empty results reflect the selected portfolio.
* [x] Summary and ranking tests use the shared in-memory fixture, with ranking
  tests in their own file and existing metric/metadata assertions retained.
* [x] The specified fixture, reconciliation, timing, and browser checks pass;
  generated output remains replaceable and ignored.
* [x] No new dependencies, storage changes, endpoints, holdings views, or map
  implementation are introduced.
* [x] Each ranking Clear button removes only its own filter, retains the other
  filter and report, and is disabled when its filter is inactive.
* [x] Tooltips appear on subheading hover and keyboard focus without information
  icons; the group 5 browser checks pass.

## Validation results

* API tests: 5 passed, including the shared-filter refactor.
* Rankings: all four filter cases matched independent SQL.
* Summary timings: market 6.58s; holder 1.57ms; point 4.59s; combined 3.40ms.
* Browser checks passed: layout, filter clicks/clears, tooltips, and loading/error/empty states.
* Report reset checked with browser-only metadata; the dataset has one report.
* Orval types regenerated; generated output remains ignored.
