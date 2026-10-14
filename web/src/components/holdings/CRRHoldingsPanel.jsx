import { useRef } from "react";
import SourceHoldings from "./SourceHoldings";

export const boundCRRHoldingsPanelHeight = (height) =>
  Math.max(200, Math.min(window.innerHeight * 0.8, height));

export default function CRRHoldingsPanel({
  reportId,
  accountHolder,
  settlementPoint,
  mwhNumber,
  crrHoldingsPanelVisible,
  crrHoldingsPanelHeight,
  viewportHeight,
  setCRRHoldingsPanelHeight,
  onToggle,
  onCellSelect,
  onSourceCollapse,
  selection,
}) {
  const resizeStart = useRef(null);

  function startResize(event) {
    if (event.button !== 0) return;
    resizeStart.current = { y: event.clientY, height: crrHoldingsPanelHeight };
    event.currentTarget.setPointerCapture(event.pointerId);
    event.preventDefault();
  }

  function moveResize(event) {
    if (resizeStart.current) {
      setCRRHoldingsPanelHeight(
        boundCRRHoldingsPanelHeight(
          resizeStart.current.height + resizeStart.current.y - event.clientY
        )
      );
    }
  }

  function keyboardResize(event) {
    if (event.key === "ArrowUp" || event.key === "ArrowDown") {
      event.preventDefault();
      setCRRHoldingsPanelHeight((height) =>
        boundCRRHoldingsPanelHeight(
          height + (event.key === "ArrowUp" ? 20 : -20)
        )
      );
    }
  }

  return (
    <section className="holdings-panel" aria-labelledby="holdings-heading">
      <div className="holdings-panel-header">
        <h2 id="holdings-heading">CRR Holdings</h2>
        <button
          type="button"
          className="control-icon holdings-toggle"
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
        </button>
      </div>
      <div className="holdings-panel-body" hidden={!crrHoldingsPanelVisible}>
        <div
          className="holdings-resize"
          role="separator"
          tabIndex={0}
          aria-label="Resize holdings panel"
          aria-orientation="horizontal"
          aria-valuemin={200}
          aria-valuemax={Math.round(viewportHeight * 0.8)}
          aria-valuenow={Math.round(crrHoldingsPanelHeight)}
          aria-valuetext={`${Math.round(crrHoldingsPanelHeight)} pixels`}
          onPointerDown={startResize}
          onPointerMove={moveResize}
          onPointerUp={(event) => {
            resizeStart.current = null;
            event.currentTarget.releasePointerCapture(event.pointerId);
          }}
          onPointerCancel={() => {
            resizeStart.current = null;
          }}
          onLostPointerCapture={() => {
            resizeStart.current = null;
          }}
          onKeyDown={keyboardResize}
        >
          ⋮ Drag to resize
        </div>
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
