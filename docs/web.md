# Frontend Design

Goal: to have something beyond filtering Excel or pandas - move naturally
between the market, individual portfolios, geographic positions, ordered source-sink pairs,
and actual contracts. Real exploration

Top down we get birds eye overview to detailed inventory


## Initial Full Page

* Discover shows Top Accounts and Top Settlement Points side by side,
  stacking on narrow screens. Both lists remain visible; there is no toggle.
* Point rankings count holdings where the point is source or sink. An A-to-B
  holding contributes to both A and B, so point totals must not be added to
  obtain portfolio MWh. Same-endpoint holdings count once for that point.

* Market or ""portfolio" summary
* e-charts are now subsumed by the filters

* workspace ~ 65%; CRR drawer on bottom
* Sidebar left ~ 40%, map ~ 60%


## Account Holder , SP Selection

* Initially shows "all" - default (null) is "market-wide"
*  everything below is a deeper, filtered dive.
  * selection by toggle in map drives everything below
  * Profile gets enriched

* selector methods; the selectors, the map onClick node, each k in the
  top k in portfolio and map

* when select a node, it's valid for source
  * map view: settlement point source OR sink - want to see both
  * map markers: show source vs sink



```text
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ERCOT CRR HOLDINGS EXPLORER                                                                     │
│ Outstanding CRR holdings                                                [ Report: Oct 2026 ▼ ] │
├───────────────────────────────────────┬─────────────────────────────────────────────────────────┤
│                                       │                                                         │
│ EXPLORE HOLDINGS                      │ GEOGRAPHIC FOOTPRINT                                    │
│                                       │                                                         │
│ Account Holder                        │ ┌─────────────────────────────────────────────────────┐ │
│ [ Exxon                       ▼ ]     │ │                                                     │ │
│                                       │ │                       TEXAS                         │ │
│ Settlement Point                      │ │                                                     │ │
│ [ All Settlement Points        ▼ ]     │ │          ◉       ●        ◉                        │ │
│                                       │ │     ●         ◉           ●                         │ │
│ [ Clear Filters ]                     │ │               ◉            ◉                       │ │
│                                       │ │                                                     │ │
├───────────────────────────────────────┤ │        ●       ◉         ●                        │ │
│                                       │ │             ●      ◉                                │ │
│ PORTFOLIO SUMMARY                     │ │                                                     │ │
│                                       │ │                                                     │ │
│ Total Contractual MWh       2.1B      │ │                                                     │ │
│ Account Holders              376      │ │                                                     │ │
│ Settlement Points          2,100      │ │                                                     │ │
│ Source-Sink Pairs         18,400      │ │                                 [ + ] [ − ]         │ │
│                                       │ └─────────────────────────────────────────────────────┘ │
│ Options       ████████████  68%       │                                                         │
│ Obligations   ██████        32%       │ ● Source-dominant   ● Balanced   ● Sink-dominant         │
│                                       │ Circle area ∝ total endpoint MWh                        │
│                                       │                                                         │
├───────────────────────────────────────┤                                                         │
│                                       │                                                         │
│ DISCOVER                              │                                                         │
│                                       │                                                         │
│ TOP ACCOUNTS       TOP SETTLEMENTS    │                                                         │
│                                       │                                                         │
│ 1. XLUREP  107M    1. HB_NORTH   …    │                                                         │
│ 2. XNRGLD   89M    2. HB_HOUSTON …    │                                                         │
│ 3. XMEA1    86M    3. …               │                                                         │
│ …                 …                   │                                                         │
│ 10. …             10. …               │                                                         │
│                                       │                                                         │
├───────────────────────────────────────┴─────────────────────────────────────────────────────────┤
│                                      ⋮ Drag to resize                                          │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ FORWARD CRR HOLDINGS                                                                [ ▾ Hide ] │
│ Contractual MWh                                                                                 │
│                                                                                                 │
│                                   OCT 2026              NOV 2026              DEC 2026         │
│ Source → Sink                  OPT       OBL          OPT       OBL          OPT       OBL      │
│ ─────────────────────────────────────────────────────────────────────────────────────────────── │
│ ▾ HB_HOUSTON                  12.5M      3.2M        11.8M      3.4M        10.9M      2.9M     │
│     ↳ HB_NORTH                 4.1M      1.2M         3.8M      1.1M         3.5M      1.0M     │
│     ↳ LZ_HOUSTON               3.2M      0.8M         3.0M      0.9M         2.8M      0.7M     │
│     ↳ NODE_A                   0.5M      0.1M         0.6M      0.1M         0.4M      0.1M     │
│ ▸ HB_NORTH                     9.4M      2.1M         8.7M      2.0M         8.2M      1.8M     │
│ ▸ LZ_SOUTH                     7.2M      1.8M         7.0M      1.6M         6.8M      1.5M     │
│ ...                                                                                             │
│                                                                                                 │
│ [ Show more sources ]                                                       Scroll months →     │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘


```


## CRR Holdings Component

* Separate options (OPT) and obligations (OBL)
  * recall the option delta thought experiment; but time considerations and
    scope creep, treat this more of an inventory then a "risk" sheet.
  * Don't net "opposing" sides out either, show totals for same instrument
  * NB: All this is because OPT's don't net out, they are effectively $0 strike
    call options on spreads, so "opposing" side payoffs are like a straddle.

* Default / initial view:  market "wide" totals

* onClick cell: (Source - Sink, OPT/OBL) -> trigger Sidebar
  * ? can I click a source only? Lets say no for now. A side panel could end up
    showing 500+ entities x ~1000 SP's x every CRR record which is not a "detail panel"

* source->sink sorted by size (aggregate opt/obl)

```text

┌───────────────────────────────────────────────────────────────────────────────────────┐
│ CRR HOLDINGS                                                                          │
│                                                                                       │
│ Possible Filter: [ Settlement point...        ]                                       │
│                                                                                       │
│ Contractual MWh                                                                       │
│                                                                                       │
│                           OCT 2026             NOV 2026             DEC 2026         │
│ Source → Sink          OPT       OBL         OPT       OBL         OPT       OBL      │
│ ───────────────────────────────────────────────────────────────────────────────────── │
│ ▾ HB_HOUSTON           12.5M      3.2M        11.8M      3.4M        10.9M      2.9M │
│    ↳ HB_NORTH           4.1M      1.2M         3.8M      1.1M         3.5M      1.0M │
│    ↳ LZ_HOUSTON         3.2M      0.8M         3.0M      0.9M         2.8M      0.7M │
│    ↳ NODE_X             0.5M      0.1M         0.6M      0.1M         0.4M      0.1M │
│ ▸ HB_NORTH              9.4M      2.1M         8.7M      2.0M         8.2M      1.8M │
│ ▸ LZ_SOUTH              7.2M      1.8M         7.0M      1.6M         6.8M      1.5M │
│ ▸ NODE_Y                1.1M      0.3M         1.0M      0.3M         0.9M      0.2M │
│ ...                                                                                   │
│                                                                                       │
│ [Show more sources]                                               Scroll months →     │
└───────────────────────────────────────────────────────────────────────────────────────┘
```



## Detail Sidebar / Drawer

* Example shows everything at source x sink x instrument x time period
* For an individual account holder, this will have been selected prior to click
  on the "Account Holder" Panel



```text
┌───────────────────────────────────────────────────┐
│ CRR HOLDINGS DETAILS                            ✕ │
│                                                   │
│ HB_HOUSTON → POINT_A                              │
│ October 2026 · Options                            │
│                                                   │
│                                      MWh          │
│ ───────────────────────────────────────────────── │
│                                                   │
│ ▾ XMEA1                              120,000       │
│                                                   │
│     ▾ PeakWD                         80,000       │
│         ├─ CRR 101 · Segment 1                    │
│         │  100 MW · Oct 1–15         20,000       │
│         │                                         │
│         └─ CRR 102 · Segment 1                    │
│            200 MW · Oct 16–31        60,000       │
│                                                   │
│     ▸ PeakWE                         25,000       │
│                                                   │
│     ▸ Off-peak                       15,000       │
│                                                   │
│ ▸ XDARBY                           90,000         │
│ ▸ XNRGLD                           30,000         │
│ ───────────────────────────────────────────────── │
│ TOTAL                               120,000       │
│                                                   │
└───────────────────────────────────────────────────┘

```

* MW or MWh - if we break out peak/offpeak, etc we could label as MW if grouped as such.



---

# Component Model

* `/api/summary` needs to handle both sidebar top summaries *and* the map.


```text
App
└── CRRExplorer
    │   [State]
    │   ├── reportId
    │   ├── accountHolder
    │   └── settlementPoint
    │
    ├── Header                        /api/metadata
    │   └── ReportSelector
    │
    ├── Overview                      /api/summary
    │   │
    │   ├── Sidebar                          40%
    │   │   │
    │   │   ├── Filters
    │   │   │   ├── AccountHolderSelector
    │   │   │   └── SettlementPointSelector
    │   │   │
    │   │   ├── PortfolioSummary
    │   │   │   ├── SummaryMetrics
    │   │   │   └── HedgeType
    │   │   │
    │   │   └── Rankings
    │   │       ├── TopAccountHolders        clickable
    │   │       └── TopSettlementPoints      clickable
    │   │
    │   └── Map                              60%
    │        └── SettlementMarkers           clickable
    │
    └── ForwardHoldings                     bottom panel
        │                                   Collapsible / Resizable
        │
        ├── HoldingsMatrix
        │   ├── SourceRow                   /api/holdings/sources
        │   ├── Pagination                  offset / nextOffset
        │   └── SinkRow                     /api/holdings/sources/{source}/sinks
        │
        └── ContractDrawer                  /api/holdings/contracts
            └── AccountHolderGroup
                └── TimeOfUseGroup
                    └── ContractRow

```
