// Imports
import { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useMetadata, useSummary } from './data/hooks';
import SourceHoldings from './SourceHoldings';
import './style.css';

// Preparation
const queryClient = new QueryClient();
const number = new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 });

function PortfolioSummary({ summary }) {
  const metrics = [
    ['Total Contractual MWh', number.format(summary.totalMwh)],
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
              <span>{number.format(mwh)} MWh · {percent.toFixed(1)}%</span>
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
                <span className="ranking-mwh">{number.format(row.totalMwh)} MWh</span>
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
  const reportMetadata = useMetadata(reportId);
  const metadata = useMetadata(reportId, accountHolder);
  const summary = useSummary(reportId, accountHolder, settlementPoint);

  useEffect(() => {
    if (reportId === null && reportMetadata.data) {
      setReportId(reportMetadata.data.reportId);
    }
  }, [reportId, reportMetadata.data]);

  function changeReport(value) {
    setReportId(Number(value));
    setAccountHolder('');
    setSettlementPoint('');
  }

  function changeHolder(value) {
    // Transformation: reset the old point before both requests start.
    setAccountHolder(value);
    setSettlementPoint('');
  }

  function clearFilters() {
    setAccountHolder('');
    setSettlementPoint('');
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
                onChange={(event) => setSettlementPoint(event.target.value)}>
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
                  onPointSelect={setSettlementPoint} onHolderClear={() => setAccountHolder('')} />
              </>}
        </aside>
        <section className="map-placeholder" aria-labelledby="map-heading">
          <h2 id="map-heading">Geographic Footprint</h2>
          <p>Map coming in Sprint 4.</p>
        </section>
      </div>
      <SourceHoldings key={`${reportId}/${accountHolder}/${settlementPoint}`}
        reportId={reportId} accountHolder={accountHolder}
        settlementPoint={settlementPoint} number={number} />
    </main>
  );
}

createRoot(document.getElementById('root')).render(
  <QueryClientProvider client={queryClient}><CRRExplorer /></QueryClientProvider>,
);
