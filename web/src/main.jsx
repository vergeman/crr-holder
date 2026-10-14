import PortfolioSummary from "./components/portfolio/PortfolioSummary";
import PortfolioFilters from "./components/portfolio/PortfolioFilters";
import Discovery from "./components/portfolio/Discovery";
import { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useMetadata, useSummary } from "./data/hooks";
import CRRHoldingsPanel, {
  boundCRRHoldingsPanelHeight,
  ContractDetailsModal,
} from "./components/holdings";
import Map from "./components/map";
import "./style.css";

const queryClient = new QueryClient();
// MWh display rounds up; calculations retain their original precision.
const mwhNumber = new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 0,
  roundingMode: "ceil",
});

function CRRExplorer() {
  // Keep independent holder choices available as points refresh.
  const [reportId, setReportId] = useState(null);
  const [accountHolder, setAccountHolder] = useState("");
  const [settlementPoint, setSettlementPoint] = useState("");
  const [selection, setSelection] = useState(null);
  const cellButton = useRef(null);
  const [crrHoldingsPanelVisible, setCRRHoldingsPanelVisible] = useState(true);
  const [crrHoldingsPanelHeight, setCRRHoldingsPanelHeight] = useState(() =>
    boundCRRHoldingsPanelHeight(window.innerHeight * 0.35)
  );
  const [viewportHeight, setViewportHeight] = useState(window.innerHeight);
  const reportMetadata = useMetadata(reportId);
  const metadata = useMetadata(reportId, accountHolder);
  const summary = useSummary(reportId, accountHolder, settlementPoint);
  const isoSummary = useSummary(reportId, "", "");

  useEffect(() => {
    if (reportId === null && reportMetadata.data) {
      setReportId(reportMetadata.data.reportId);
    }
  }, [reportId, reportMetadata.data]);

  useEffect(() => {
    // Retain the chosen size while reapplying viewport bounds.
    function resizeViewport() {
      setViewportHeight(window.innerHeight);
      setCRRHoldingsPanelHeight((height) => boundCRRHoldingsPanelHeight(height));
    }
    window.addEventListener("resize", resizeViewport);
    return () => window.removeEventListener("resize", resizeViewport);
  }, []);

  function changeReport(value) {
    setSelection(null);
    setReportId(Number(value));
    setAccountHolder("");
    setSettlementPoint("");
  }

  function changeAccountHolder(value) {
    setSelection(null);
    // Reset the old point before both requests start.
    setAccountHolder(value);
    setSettlementPoint("");
  }

  function clearFilters() {
    setSelection(null);
    setAccountHolder("");
    setSettlementPoint("");
  }

  function changeSettlementPoint(value) {
    setSelection(null);
    setSettlementPoint(value);
  }

  function clearAccountHolder() {
    setSelection(null);
    setAccountHolder("");
  }

  function selectCell(cell, button) {
    cellButton.current = button;
    setSelection(cell);
  }

  function closeContractDetails() {
    setSelection(null);
    if (cellButton.current?.isConnected)
      cellButton.current.focus({ preventScroll: true });
  }

  function toggleCRRHoldingsPanel() {
    if (crrHoldingsPanelVisible) setSelection(null);
    setCRRHoldingsPanelVisible(!crrHoldingsPanelVisible);
  }

  return (
    <main>
      <header>
        <div>
          <h1>ERCOT CRR Holdings Explorer</h1>
          <p>Outstanding contractual holdings</p>
        </div>
        <label>
          Report
          <select
            value={reportId ?? ""}
            disabled={!reportMetadata.data}
            onChange={(event) => changeReport(event.target.value)}
          >
            {!reportMetadata.data && (
              <option value="">Loading reports...</option>
            )}
            {reportMetadata.data?.reports.map((report) => (
              <option key={report.reportId} value={report.reportId}>
                {report.publicationDate}
              </option>
            ))}
          </select>
        </label>
      </header>
      {reportMetadata.isError && (
        <p role="alert">Unable to load report filters.</p>
      )}
      <div
        className="workspace"
        style={{
          "--holdings-space": crrHoldingsPanelVisible ? `${crrHoldingsPanelHeight + 200}px` : "140px",
        }}
      >
        <aside>
          <PortfolioFilters
            reportMetadata={reportMetadata}
            metadata={metadata}
            accountHolder={accountHolder}
            settlementPoint={settlementPoint}
            onHolderSelect={changeAccountHolder}
            onPointSelect={changeSettlementPoint}
            onClear={clearFilters}
          />
          {summary.isError ? (
            <p role="alert">Unable to load portfolio summary.</p>
          ) : !summary.data ? (
            <p role="status">Loading portfolio summary...</p>
          ) : (
            <>
              <PortfolioSummary summary={summary.data} mwhNumber={mwhNumber} />
              <Discovery
                summary={summary.data}
                mwhNumber={mwhNumber}
                accountHolder={accountHolder}
                settlementPoint={settlementPoint}
                onHolderSelect={changeAccountHolder}
                onPointSelect={changeSettlementPoint}
                onHolderClear={clearAccountHolder}
              />
            </>
          )}
        </aside>
        <Map
          key={reportId}
          summary={summary}
          isoSummary={isoSummary}
          selectedPoint={settlementPoint}
          onPointSelect={changeSettlementPoint}
          mwhNumber={mwhNumber}
        />
        <CRRHoldingsPanel
          reportId={reportId}
          accountHolder={accountHolder}
          settlementPoint={settlementPoint}
          mwhNumber={mwhNumber}
          crrHoldingsPanelVisible={crrHoldingsPanelVisible}
          crrHoldingsPanelHeight={crrHoldingsPanelHeight}
          viewportHeight={viewportHeight}
          setCRRHoldingsPanelHeight={setCRRHoldingsPanelHeight}
          onToggle={toggleCRRHoldingsPanel}
          selection={selection}
          onCellSelect={selectCell}
          onSourceCollapse={(source) => {
            if (selection?.source === source) setSelection(null);
          }}
        />
        {selection && (
          <ContractDetailsModal
            key={`${selection.source}/${selection.sink}/${selection.deliveryMonth}/${selection.hedgeType}`}
            reportId={reportId}
            accountHolder={accountHolder}
            settlementPoint={settlementPoint}
            selection={selection}
            mwhNumber={mwhNumber}
            onClose={closeContractDetails}
          />
        )}
      </div>
    </main>
  );
}

createRoot(document.getElementById("root")).render(
  <QueryClientProvider client={queryClient}>
    <CRRExplorer />
  </QueryClientProvider>
);
