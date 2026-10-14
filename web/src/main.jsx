// Imports
import { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useMetadata, useSummary } from './data/hooks';
import SourceHoldings from './SourceHoldings';
import ContractDrawer from './ContractDrawer';
import './style.css';

// Preparation
const queryClient = new QueryClient();
// MWh display rounds up; calculations retain their original precision.
const mwhNumber = new Intl.NumberFormat('en-US', {
  maximumFractionDigits: 0, roundingMode: 'ceil',
});
const boundPanelHeight = (height) => Math.max(200, Math.min(window.innerHeight * 0.8, height));

function PortfolioSummary({ summary }) {
  const metrics = [
    ['Total Contractual MWh', mwhNumber.format(summary.totalMwh)],
    ['Account Holders', summary.accountHolderCount],
    ['Settlement Points', summary.settlementPointCount],
    ['Source-Sink Pairs', summary.directedPathCount],
  ];

  // Output: inventory values and percentages use the same unrounded API totals.
  return (
    <section aria-labelledby="summary-heading">
      <h2 id="summary-heading">Portfolio Summary</h2>
      <p>Contractual inventory across the report’s delivery horizon.</p>
      <dl>
        {metrics.map(([label, value]) => (
          <div key={label}><dt>{label}</dt><dd>{value}</dd></div>
        ))}
      </dl>
      {['OPT', 'OBL'].map((type) => {
        const mwh = summary.hedgeTypeMwh[type];
        const percent = summary.totalMwh === 0 ? 0 : 100 * mwh / summary.totalMwh;
        return (
          <div className="hedge" key={type}>
            <div className="hedge-label">
              <span>{type === 'OPT' ? 'Options' : 'Obligations'} ({type})</span>
              <span>{mwhNumber.format(mwh)} MWh · {percent.toFixed(1)}%</span>
            </div>
            <div className="bar" aria-hidden="true">
              <div className={type.toLowerCase()} style={{ width: `${percent}%` }} />
            </div>
          </div>
        );
      })}
      {summary.accountHolderCount === 0 && <p>No holdings match these filters.</p>}
    </section>
  );
}

function RankingList({ id, title, rows, identifierKey, onSelect, onClear,
                       filtered, pointTotals = false }) {
  const explanation = 'Ranked by contractual MWh for the current filters.' +
    (pointTotals ? ' Each holding counts toward its source and sink; identical endpoints ' +
      'count once. Do not add settlement-point totals to calculate portfolio MWh.' : '');

  // Output: native buttons share the dropdown handlers and expose tooltip descriptions.
  return (
    <div className="ranking-list" aria-labelledby={`${id}-heading`}>
      <div className="ranking-heading">
        <h3 id={`${id}-heading`} tabIndex={0}
          aria-describedby={`${id}-tooltip`}>{title}</h3>
        <span className="ranking-tooltip" id={`${id}-tooltip`} role="tooltip">
          {explanation}
        </span>
        <button type="button" className="ranking-clear" disabled={!filtered}
          aria-label={`Clear ${title} filter`} onClick={onClear}>Clear</button>
      </div>
      {rows.length === 0 ? <p>No holdings match these filters.</p> : (
        <ol>
          {rows.map((row, index) => (
            <li key={row[identifierKey]}>
              <button type="button" className="ranking-row"
                onClick={() => onSelect(row[identifierKey])}>
                <span className="ranking-rank">{index + 1}</span>
                <span className="ranking-identity">
                  <strong>{row[identifierKey]}</strong>
                  {row.legalName && <span>{row.legalName}</span>}
                </span>
                <span className="ranking-mwh">{mwhNumber.format(row.totalMwh)} MWh</span>
              </button>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

function Discovery({ summary, accountHolder, settlementPoint,
                     onHolderSelect, onPointSelect, onHolderClear }) {
  // Output: both lists belong to the same currently selected portfolio.
  return (
    <section aria-labelledby="discover-heading">
      <h2 id="discover-heading">Discover</h2>
      <div className="discovery-lists">
        <RankingList id="top-accounts" title="Top Accounts"
          rows={summary.topAccountHolders} identifierKey="accountHolder"
          onSelect={onHolderSelect} onClear={onHolderClear} filtered={!!accountHolder} />
        <RankingList id="top-points" title="Top Settlement Points"
          rows={summary.topSettlementPoints} identifierKey="settlementPoint"
          onSelect={onPointSelect} onClear={() => onPointSelect('')}
          filtered={!!settlementPoint} pointTotals />
      </div>
    </section>
  );
}

function CRRExplorer() {
  // Preparation: keep independent holder choices available as points refresh.
  const [reportId, setReportId] = useState(null);
  const [accountHolder, setAccountHolder] = useState('');
  const [settlementPoint, setSettlementPoint] = useState('');
  const [selection, setSelection] = useState(null);
  const cellButton = useRef(null);
  const [panelVisible, setPanelVisible] = useState(true);
  const [panelHeight, setPanelHeight] = useState(() => boundPanelHeight(window.innerHeight * 0.35));
  const [viewportHeight, setViewportHeight] = useState(window.innerHeight);
  const resizeStart = useRef(null);
  const reportMetadata = useMetadata(reportId);
  const metadata = useMetadata(reportId, accountHolder);
  const summary = useSummary(reportId, accountHolder, settlementPoint);

  useEffect(() => {
    if (reportId === null && reportMetadata.data) {
      setReportId(reportMetadata.data.reportId);
    }
  }, [reportId, reportMetadata.data]);

  useEffect(() => {
    // Transformation: retain the chosen size while reapplying viewport bounds.
    function resizeViewport() {
      setViewportHeight(window.innerHeight);
      setPanelHeight((height) => boundPanelHeight(height));
    }
    window.addEventListener('resize', resizeViewport);
    return () => window.removeEventListener('resize', resizeViewport);
  }, []);

  function changeReport(value) {
    setSelection(null);
    setReportId(Number(value));
    setAccountHolder('');
    setSettlementPoint('');
  }

  function changeHolder(value) {
    setSelection(null);
    // Transformation: reset the old point before both requests start.
    setAccountHolder(value);
    setSettlementPoint('');
  }

  function clearFilters() {
    setSelection(null);
    setAccountHolder('');
    setSettlementPoint('');
  }

  function changePoint(value) {
    setSelection(null);
    setSettlementPoint(value);
  }

  function clearHolder() {
    setSelection(null);
    setAccountHolder('');
  }

  function selectCell(cell, button) {
    cellButton.current = button;
    setSelection(cell);
  }

  function closeDetails() {
    setSelection(null);
    if (cellButton.current?.isConnected) cellButton.current.focus({ preventScroll: true });
  }

  function togglePanel() {
    if (panelVisible) setSelection(null);
    setPanelVisible(!panelVisible);
  }

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

  // Output
  return (
    <main>
      <header>
        <div>
          <h1>ERCOT CRR Holdings Explorer</h1>
          <p>Outstanding contractual holdings</p>
        </div>
        <label>Report
          <select value={reportId ?? ''} disabled={!reportMetadata.data}
            onChange={(event) => changeReport(event.target.value)}>
            {!reportMetadata.data && <option value="">Loading reports...</option>}
            {reportMetadata.data?.reports.map((report) => (
              <option key={report.reportId} value={report.reportId}>
                {report.publicationDate}
              </option>
            ))}
          </select>
        </label>
      </header>
      {reportMetadata.isError && <p role="alert">Unable to load report filters.</p>}
      <div className="workspace">
        <aside>
          <section aria-labelledby="filters-heading">
            <h2 id="filters-heading">Explore Holdings</h2>
            <label>Account Holder
              <select value={accountHolder} disabled={!reportMetadata.data}
                onChange={(event) => changeHolder(event.target.value)}>
                <option value="">All Account Holders</option>
                {reportMetadata.data?.accountHolders.map((holder) => (
                  <option key={holder.accountHolder} value={holder.accountHolder}>
                    {holder.accountHolder}{holder.legalName ? ` — ${holder.legalName}` : ''}
                  </option>
                ))}
              </select>
            </label>
            <label>Settlement Point
              <select value={settlementPoint} disabled={!metadata.data || metadata.isError}
                onChange={(event) => changePoint(event.target.value)}>
                <option value="">
                  {metadata.isError ? 'Unable to load settlement points' :
                    !metadata.data ? 'Loading settlement points...' : 'All Settlement Points'}
                </option>
                {!metadata.isError && metadata.data?.settlementPoints.map((point) => (
                  <option key={point} value={point}>{point}</option>
                ))}
              </select>
            </label>
            {metadata.isError && <p role="alert">Unable to load settlement points.</p>}
            <button onClick={clearFilters}>Clear Filters</button>
          </section>
          {summary.isError ? <p role="alert">Unable to load portfolio summary.</p> :
            !summary.data ? <p role="status">Loading portfolio summary...</p> :
              <>
                <PortfolioSummary summary={summary.data} />
                <Discovery summary={summary.data} accountHolder={accountHolder}
                  settlementPoint={settlementPoint} onHolderSelect={changeHolder}
                  onPointSelect={changePoint} onHolderClear={clearHolder} />
              </>}
        </aside>
        <section className="map-placeholder" aria-labelledby="map-heading">
          <h2 id="map-heading">Geographic Footprint</h2>
          <p>Map coming in Sprint 4.</p>
        </section>
      </div>
      <section className="holdings-panel" aria-labelledby="holdings-heading">
        <div className="holdings-panel-header">
          <h2 id="holdings-heading">CRR Holdings</h2>
          <button type="button" onClick={togglePanel} aria-expanded={panelVisible}
            aria-controls="holdings-content">{panelVisible ? 'Hide' : 'Show'} holdings</button>
        </div>
        <div hidden={!panelVisible}>
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
              onCellSelect={selectCell} onSourceCollapse={(source) => {
                if (selection?.source === source) setSelection(null);
              }} />
          </div>
        </div>
      </section>
      {selection && <ContractDrawer
        key={`${selection.source}/${selection.sink}/${selection.deliveryMonth}/${selection.hedgeType}`}
        reportId={reportId} accountHolder={accountHolder} settlementPoint={settlementPoint}
        selection={selection} mwhNumber={mwhNumber} onClose={closeDetails} />}
    </main>
  );
}

createRoot(document.getElementById('root')).render(
  <QueryClientProvider client={queryClient}><CRRExplorer /></QueryClientProvider>,
);
