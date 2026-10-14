import PortfolioSummary from './components/portfolio/PortfolioSummary';
import PortfolioFilters from './components/portfolio/PortfolioFilters';
import Discovery from './components/portfolio/Discovery';
import { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useMetadata, useSummary } from './data/hooks';
import HoldingsPanel, { boundPanelHeight } from './components/holdings/HoldingsPanel';
import ContractDrawer from './ContractDrawer';
import './style.css';

const queryClient = new QueryClient();
// MWh display rounds up; calculations retain their original precision.
const mwhNumber = new Intl.NumberFormat('en-US', {
  maximumFractionDigits: 0, roundingMode: 'ceil',
});

function CRRExplorer() {
  // keep independent holder choices available as points refresh.
  const [reportId, setReportId] = useState(null);
  const [accountHolder, setAccountHolder] = useState('');
  const [settlementPoint, setSettlementPoint] = useState('');
  const [selection, setSelection] = useState(null);
  const cellButton = useRef(null);
  const [panelVisible, setPanelVisible] = useState(true);
  const [panelHeight, setPanelHeight] = useState(() => boundPanelHeight(window.innerHeight * 0.35));
  const [viewportHeight, setViewportHeight] = useState(window.innerHeight);
  const reportMetadata = useMetadata(reportId);
  const metadata = useMetadata(reportId, accountHolder);
  const summary = useSummary(reportId, accountHolder, settlementPoint);

  useEffect(() => {
    if (reportId === null && reportMetadata.data) {
      setReportId(reportMetadata.data.reportId);
    }
  }, [reportId, reportMetadata.data]);

  useEffect(() => {
    // retain the chosen size while reapplying viewport bounds.
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
    // reset the old point before both requests start.
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
          <PortfolioFilters reportMetadata={reportMetadata} metadata={metadata}
            accountHolder={accountHolder} settlementPoint={settlementPoint}
            onHolderSelect={changeHolder} onPointSelect={changePoint} onClear={clearFilters} />
          {summary.isError ? <p role="alert">Unable to load portfolio summary.</p> :
            !summary.data ? <p role="status">Loading portfolio summary...</p> :
              <>
                <PortfolioSummary summary={summary.data} mwhNumber={mwhNumber} />
                <Discovery summary={summary.data} mwhNumber={mwhNumber} accountHolder={accountHolder}
                  settlementPoint={settlementPoint} onHolderSelect={changeHolder}
                  onPointSelect={changePoint} onHolderClear={clearHolder} />
              </>}
        </aside>
        <section className="map-placeholder" aria-labelledby="map-heading">
          <h2 id="map-heading">Geographic Footprint</h2>
          <p>Map coming in Sprint 4.</p>
        </section>
      </div>
      <HoldingsPanel reportId={reportId} accountHolder={accountHolder}
        settlementPoint={settlementPoint} mwhNumber={mwhNumber}
        panelVisible={panelVisible} panelHeight={panelHeight}
        viewportHeight={viewportHeight} setPanelHeight={setPanelHeight}
        onToggle={togglePanel} onCellSelect={selectCell}
        onSourceCollapse={(source) => {
          if (selection?.source === source) setSelection(null);
        }} />
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
