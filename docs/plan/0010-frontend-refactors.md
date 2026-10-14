# 0010 - Frontend Refactors

Type: refactor
Branch: refactor/0010-frontend-refactors

## Goal

* Improve holdings resizing, source expansion, and contract-modal presentation.

* Compress portfolio controls, improve discovery readability, and clarify map
  interactions and marker encoding.

## Context

* Sprint 4.1 refines the existing holdings components after map integration.

* The holdings drawer is implemented by `CRRHoldingsPanel`.

## Approach and commit groups

Implement in this order; keep panel controls, source expansion, and modal
presentation in separate commits. Separate portfolio loading behavior from
layout changes. Use the review points before starting the next stage.

### 1. Shared control styling and lightweight UI evaluation

* Investigate a lightweight UI library with icon support for cleaner dropdowns,
  buttons, and disclosure carets. Compare accessibility, styling flexibility,
  React compatibility, icon coverage, and dependency cost with improving
  existing controls. Evaluate an icon library separately from a full component
  framework; prefer consistent sizing, spacing, borders, and focus styles when
  those solve the problem.

* Present a concise recommendation and concrete control examples for a scope
  decision before adding a dependency or building shared control abstractions.

* Group the visual control changes below under one consistent treatment:
  dropdowns, action buttons, borderless disclosure carets, and icon buttons,
  including hover, focus, disabled, and expanded states.

* Include modal close, holdings hide/show, discovery clear, and Clear Filters
  in this shared treatment. Choose consistent icons and retain accessible
  names and tooltips for icon-only controls. Keep visible "Clear Filters" text
  because it affects the whole portfolio.

* Review prompt: present styled control examples and the library recommendation.
  Ask which approach and icon treatment to use; wait for a decision before
  adding dependencies, shared modules, or applying the chosen treatment.

* Agreed treatment: native controls, inline SVG carets, and IBM Plex Sans.
  Keep controls compact, with centered carets and consistent focus styling.

### 2. Portfolio filters and summary

* Keep filters beside the page title in the header on desktop; wrap on narrow
  screens. Center the title, leave space before filters, and cap selector widths.
  Remove the Explore Holdings disclosure and redundant header caption.

* Join Portfolio Summary and Discover in one scrolling pane. Keep the summary
  compact: MWh and OPT/OBL on the left, counts on the right. Move count labels
  toward their values without moving the counts.

* Remove the summary caption and colored breakdown bars. Display OPT/OBL as
  numeric MWh values followed by a separator and raw percentage; omit MWh units.

* Retain previous summary data during filter changes and show Updating beside
  the filters. Disable selection while replacement data is pending. Cached
  current-selection data remains usable during background refreshes.

* Derive loading from TanStack query state; document the distinction between
  pending results and previous-selection placeholder data.

* Keep existing component boundaries.

### 3. Discovery tables

* Widen `Discovery` and its two ranking columns. Keep Top Accounts and Top
  Settlement Points headings on one line; stack tables on narrow screens.

* Use separate Code, Account Holder, and Total MWh columns in Top Accounts.
  Keep names on one line, strip the trailing `(CRRAH)` display suffix, and
  right-align totals. Keep the table compact with horizontal overflow.

* For settlement points, place the name and Total MWh on the same row. Retain
  filter selection through keyboard-accessible, visually unboxed controls.

* Make the entire ranking row clickable, including totals; retain keyboard
  activation, loading guards, and subtle hover and selected states.

* Use back arrows for clearing and ellipses with full-name hover titles.
  Keep ten-row rankings; pagination and custom selectors remain follow-ups.

* Review prompt: show the portfolio and discovery layouts on desktop and narrow
  screens. Ask for feedback on widths, density, hierarchy, and selection styling
  before proceeding to holdings changes.

### 4. Holdings panel controls

* Start `CRRHoldingsPanel` minimized by default, with its expand control reachable.

* In `web/src/components/holdings/CRRHoldingsPanel.jsx`, move the resize handle
  to the pane's actual top edge, retaining pointer and keyboard resizing.

* Make the holdings title a keyboard-accessible expand/collapse control with
  a left caret and expanded state. Append active account-holder and point
  filters; use the full holder name without trailing `(CRRAH)`, falling back
  to its code.

* Sit flush with the workspace bottom and contain matrix scrolling, keeping
  controls reachable on desktop and narrow screens.

* Start expanded content at 45% viewport height. Compact rows and carets;
  distinguish normal-weight totals with blue tint and a divider.

* Keep a visible, draggable horizontal scrollbar at the matrix bottom.
  Freeze Source and both Total MWh columns during horizontal scrolling.

* Freeze the date and OPT/OBL header rows during vertical scrolling; reduce
  their font and padding. Remove the redundant Contractual MWh caption.

* Keep loading, error, and empty sink labels frozen beside the source columns.

### 5. Source expansion

* In `web/src/components/holdings/SourceHoldings.jsx`, make any cell in a source
  row expand its sinks, including the source-name cell and horizontally scrolled
  value cells. Users must not need to scroll back to the source name to expand.

* Use a borderless caret for expansion state and retain keyboard activation.

* Source-name clicks expand sinks. Map navigation from those clicks is deferred
  unless a usability issue warrants it; preserve the current map camera.

### 6. Contract modal presentation

* In `web/src/components/holdings/ContractDetailsModal.jsx`, place the full
  account-holder entity name above its short code. Make the full name darker
  and more prominent; show the code alone when no full name is available.

* Reduce the gap between the account-holder heading and its TOU groups, and
  rebalance spacing between PeakWD, PeakWE, and off-peak expansions.

* Replace the modal's Close text with a conventional close icon and an
  accessible name, retaining Escape dismissal and focus return.

* Update related styles in `web/src/style.css` within each commit group.

* Review prompt: show edge resizing, horizontal scrolling, source expansion,
  and the revised modal; include the source-point map navigation findings.
  Ask for feedback on control placement, name emphasis, and TOU spacing before
  proceeding to map changes.

### 7. Map controls and presentation

* Show `MapPointDetails` as a floating hover panel near the active marker,
  also available on keyboard focus. Offset the panel from its marker and disable
  pointer interception so it does not obscure the marker or cause hover flicker.

* Use three aligned detail rows: bold SP name, Source MWh, and Sink MWh.
  Remove the former map loading/error/retry/empty-state panel.

* Remove Clear point from `MapControls`. Clear the settlement-point filter on
  map-background clicks; marker clicks select without immediately clearing,
  and floating-panel or control clicks do not clear it. Completing a map drag
  must retain the selected point; only a plain background click clears it.

* Place an accessible reset-view icon button beside the MapLibre +/− controls.

* Omit the attribution control for the current personal-project version.

* Move the legend between filters and Report as a bottom-aligned, 180px header
  gradient with Source, Balanced, and Sink labels below and space before Report.
  Omit disclosure and description. Use blue–dark-blue–red for source-dominant,
  balanced, and sink-dominant points.

* In `Map` and `MarkerButton`, scale circle area against the largest located
  point in the current filtered portfolio, with diameters clamped to 8–56 px.
  Zero-MWh points remain 8 px. Keep report-wide points for camera bounds only
  and retain a clear selected-point outline when marker sizes change.

* Retain exact source/sink MWh in point details. Marker sizes rescale with
  filters, with minimum-size circles outside proportional scaling.

* Review prompt: demonstrate market and filtered circles, hover/focus details,
  and the revised map controls. Ask for feedback on the proposed color direction,
  size tradeoff, legend readability, and panel placement; wait for review before
  marking visual acceptance complete.

### 8. Split comparison workspace

* Keep Portfolio/Discover left (680px default, resizable); map and holdings
  share the right. Preserve independent scrolling and holdings height resizing.

* Keep rankings side by side on desktop; stack panes on narrow screens.
  Resize the map with its pane and fit report bounds without sidebar padding.

## Delivery-month decision

* Keep expired delivery months for now. Contracts retain their full start-to-end
  expansion without a report-date cutoff; totals and drill-downs stay unchanged.

## Scope control

* Work within the listed holdings, portfolio, and map components, `main.jsx`,
  and their styles. Evaluate a lightweight library first; adding a dependency
  or shared control modules requires the scope decision above.

* Keep data queries, totals, sorting, and pagination unchanged. Preserve map
  camera position on filter changes and the existing report-wide reset bounds.

* Treat acceptance and validation as closed lists. Ask before adding unplanned
  files, dependencies, stored data, or substantial verification.

* Resolve routine implementation choices within this scope without confirmation.

* Keep formatting-only changes in separate commits after the related refactor.

## Acceptance

* [x] A lightweight UI recommendation with icon support and control examples
  has been reviewed; dropdowns, buttons, carets, close, hide/show, clear, and
  Clear Filters use the agreed style and accessible names; Clear Filters
  retains visible text.

* [x] The pane resizes from its top edge with pointer and keyboard controls.

* [x] Holdings hide/show controls use accessible icons.

* [x] `CRRHoldingsPanel` starts minimized and can be expanded from its control.

* [x] Holdings sits flush with the workspace bottom, with compact rows,
  distinct normal-weight totals, and a larger default expansion height.

* [x] A visible draggable scrollbar reaches all holdings columns; Source and
  totals stay frozen, with compact sticky date/OPT/OBL headers and sink states.

* [x] The clickable holdings title shows active filters using the full holder
  name without the trailing `(CRRAH)` suffix.

* [x] Any source-row cell expands its sinks without scrolling back to the source
  name; the borderless caret retains keyboard expansion and collapse.

* [x] Source-click map navigation was investigated and deferred after review;
  clicks expand sinks without moving the map camera.

* [x] Account-holder full names appear above short codes with stronger emphasis.

* [x] TOU groups sit closer to their account-holder heading with consistent
  spacing between expansions.

* [x] The modal uses an accessible close icon; Close and Escape return focus to
  the selected holdings cell.

* [x] Filters and actions run horizontally on desktop; the visually joined
  summary has the requested two-column grouping and fits narrow screens.

* [x] Discovery uses wider tables with single-line desktop headings, separate
  code and long-name columns, aligned totals, and mouse/keyboard selection.

* [x] Compact rankings use back arrows and name ellipses; portfolio and holdings
  remain visible together in resizable panes that stack on narrow screens.

* [x] Point details appear on hover/focus; map-background clicks clear point
  selection while drags, marker, panel, and control interactions do not clear it.
  The hover panel does not obscure markers or intercept pointer events.

* [x] Hover details use aligned rows; the old map status box is removed.

* [x] Reset view sits beside +/−; attribution is omitted for now. The header
  gradient matches the blue–dark-blue–red marker colors.

* [x] Filtered circles use the current portfolio's size scale and remain
  visible within 8–56 px with a clear selection outline.

* [x] The control decision and each staged visual review have been completed
  with user feedback reflected in the implementation.

## Validation

* Check resizing, title toggling, filter labels, scrollbar dragging, frozen
  headers/totals/sink states, source expansion after scrolling, and modal
  presentation on desktop and narrow screens so controls remain usable.

* Check keyboard resizing, source activation, and modal dismissal/focus return
  to retain keyboard access after replacing text controls.

* Check portfolio and discovery layouts on desktop and narrow screens, including
  mouse and keyboard selection, to verify readable tables and reachable filters.

* Check pane resizing, independent scrolling, and adjacent holdings updates.

* Check marker hover/focus, background clearing, and reset alongside floating
  panels; compare market and filtered marker sizes and legend colors to verify
  readable encoding without accidental selection clearing, hover flicker, or
  camera movement; verify dragging retains selection.

* Run `docker compose exec -T web npx vite build --outDir /tmp/0010-web-build`.

* Run `git diff --check`.
