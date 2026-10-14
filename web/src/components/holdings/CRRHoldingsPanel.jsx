import { useRef, useState } from "react";
import SourceHoldings from "./SourceHoldings";

// The ref saves the starting height and pointer Y for each drag. Pointer movement
// updates height state, which updates the holdings content's CSS height style.
// The ref and resize handlers ultimately control the panel's CSS height.
const boundCRRHoldingsPanelHeight = (height) =>
  Math.max(200, Math.min(window.innerHeight * 0.8, height));

export default function CRRHoldingsPanel({
  reportId,
  accountHolder,
  accountHolderName,
  settlementPoint,
  mwhNumber,
  crrHoldingsPanelVisible,
  onToggle,
  onCellSelect,
  onSourceCollapse,
  selection,
}) {
  const resizeStart = useRef(null);
  const [crrHoldingsPanelHeight, setCRRHoldingsPanelHeight] = useState(() =>
    boundCRRHoldingsPanelHeight(window.innerHeight * 0.45)
  );

  function startResize(event) {
    if (event.button !== 0) return;
    resizeStart.current = { y: event.clientY, height: crrHoldingsPanelHeight };
    event.currentTarget.setPointerCapture(event.pointerId);
    event.preventDefault();
  }

  function moveResize(event) {
    if (!resizeStart.current) return;
    setCRRHoldingsPanelHeight(
      boundCRRHoldingsPanelHeight(
        resizeStart.current.height + resizeStart.current.y - event.clientY
      )
    );
  }

  function finishResize(event) {
    resizeStart.current = null;
    event.currentTarget.releasePointerCapture(event.pointerId);
  }

  // Cancellation or lost capture also ends the drag.
  function cancelResize() {
    resizeStart.current = null;
  }

  function keyboardResize(event) {
    if (event.key !== "ArrowUp" && event.key !== "ArrowDown") return;
    event.preventDefault();
    setCRRHoldingsPanelHeight((height) =>
      boundCRRHoldingsPanelHeight(height + (event.key === "ArrowUp" ? 20 : -20))
    );
  }

  return (
    <section className="holdings-panel" aria-labelledby="holdings-heading">
      {/* Pointer handlers resize the panel from its top-edge grab strip. */}
      <div
        className="holdings-resize"
        hidden={!crrHoldingsPanelVisible}
        role="separator"
        tabIndex={0}
        aria-label="Resize holdings panel"
        aria-orientation="horizontal"
        aria-valuemin={200}
        aria-valuemax={Math.round(window.innerHeight * 0.8)}
        aria-valuenow={Math.round(crrHoldingsPanelHeight)}
        aria-valuetext={`${Math.round(crrHoldingsPanelHeight)} pixels`}
        onPointerDown={startResize}
        onPointerMove={moveResize}
        onPointerUp={finishResize}
        onPointerCancel={cancelResize}
        onLostPointerCapture={cancelResize}
        onKeyDown={keyboardResize}
      >
        <span aria-hidden="true" />
      </div>
      <div className="holdings-panel-header">
        <h2 id="holdings-heading">
          <button
            type="button"
            className="holdings-toggle"
            aria-label={
              crrHoldingsPanelVisible ? "Hide holdings" : "Show holdings"
            }
            title={crrHoldingsPanelVisible ? "Hide holdings" : "Show holdings"}
            onClick={onToggle}
            aria-expanded={crrHoldingsPanelVisible}
            aria-controls="holdings-content"
          >
            <svg
              className="control-caret"
              viewBox="0 0 16 16"
              aria-hidden="true"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="m4 6 4 4 4-4" />
            </svg>
            <span>
              CRR Holdings
              {accountHolder && (
                <span>
                  {" · "}
                  {accountHolderName?.replace(/\s*\(CRRAH\)$/, "") ||
                    accountHolder}
                </span>
              )}
              {settlementPoint && <span> · {settlementPoint}</span>}
            </span>
          </button>
        </h2>
      </div>
      <div className="holdings-panel-body" hidden={!crrHoldingsPanelVisible}>
        <div
          id="holdings-content"
          className="holdings-content"
          style={{ height: crrHoldingsPanelHeight }}
        >
          <SourceHoldings
            key={`${reportId}/${accountHolder}/${settlementPoint}`}
            reportId={reportId}
            accountHolder={accountHolder}
            settlementPoint={settlementPoint}
            mwhNumber={mwhNumber}
            visible={crrHoldingsPanelVisible}
            selection={selection}
            onCellSelect={onCellSelect}
            onSourceCollapse={onSourceCollapse}
          />
        </div>
      </div>
    </section>
  );
}
