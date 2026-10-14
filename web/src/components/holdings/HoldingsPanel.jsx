import { useRef } from 'react';
import SourceHoldings from '../../SourceHoldings';

export const boundPanelHeight = (height) => Math.max(200, Math.min(window.innerHeight * 0.8, height));

export default function HoldingsPanel({ reportId, accountHolder, settlementPoint,
  mwhNumber, panelVisible, panelHeight, viewportHeight, setPanelHeight,
  onToggle, onCellSelect, onSourceCollapse }) {
  const resizeStart = useRef(null);

  function startResize(event) {
    if (event.button !== 0) return;
    resizeStart.current = { y: event.clientY, height: panelHeight };
    event.currentTarget.setPointerCapture(event.pointerId);
    event.preventDefault();
  }

  function moveResize(event) {
    if (resizeStart.current) {
      setPanelHeight(boundPanelHeight(
        resizeStart.current.height + resizeStart.current.y - event.clientY));
    }
  }

  function keyboardResize(event) {
    if (event.key === 'ArrowUp' || event.key === 'ArrowDown') {
      event.preventDefault();
      setPanelHeight((height) => boundPanelHeight(height + (event.key === 'ArrowUp' ? 20 : -20)));
    }
  }

  return (
    <section className="holdings-panel" aria-labelledby="holdings-heading">
      <div className="holdings-panel-header">
        <h2 id="holdings-heading">CRR Holdings</h2>
        <button type="button" onClick={onToggle} aria-expanded={panelVisible}
          aria-controls="holdings-content">{panelVisible ? 'Hide' : 'Show'} holdings</button>
      </div>
      <div className="holdings-panel-body" hidden={!panelVisible}>
        <div className="holdings-resize" role="separator" tabIndex={0}
          aria-label="Resize holdings panel" aria-orientation="horizontal"
          aria-valuemin={200} aria-valuemax={Math.round(viewportHeight * 0.8)}
          aria-valuenow={Math.round(panelHeight)} aria-valuetext={`${Math.round(panelHeight)} pixels`}
          onPointerDown={startResize} onPointerMove={moveResize}
          onPointerUp={(event) => {
            resizeStart.current = null;
            event.currentTarget.releasePointerCapture(event.pointerId);
          }}
          onPointerCancel={() => { resizeStart.current = null; }}
          onLostPointerCapture={() => { resizeStart.current = null; }}
          onKeyDown={keyboardResize}>⋮ Drag to resize</div>
        <div id="holdings-content" className="holdings-content" style={{ height: panelHeight }}>
          <SourceHoldings key={`${reportId}/${accountHolder}/${settlementPoint}`}
            reportId={reportId} accountHolder={accountHolder}
            settlementPoint={settlementPoint} mwhNumber={mwhNumber} visible={panelVisible}
            onCellSelect={onCellSelect} onSourceCollapse={onSourceCollapse} />
        </div>
      </div>
    </section>
  );
}
