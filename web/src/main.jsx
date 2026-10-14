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
import Map, { Legend } from "./components/map";
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
  const [portfolioWidth, setPortfolioWidth] = useState(680);
  const portfolioResizeStart = useRef(null);
  const [crrHoldingsPanelVisible, setCRRHoldingsPanelVisible] = useState(false);
  const [crrHoldingsPanelHeight, setCRRHoldingsPanelHeight] = useState(() =>
    boundCRRHoldingsPanelHeight(window.innerHeight * 0.45)
  );
  const [viewportHeight, setViewportHeight] = useState(window.innerHeight);
  const reportMetadata = useMetadata(reportId);
  const metadata = useMetadata(reportId, accountHolder);
  const summary = useSummary(reportId, accountHolder, settlementPoint);
  const isoSummary = useSummary(reportId, "", "");
  // Derived from TanStack-managed query state: isPending means no result yet.
  // isPlaceholderData means the previous selection is shown as a placeholder
  // while the request for the current selection is in flight. Cached results
  // for the current selection remain usable during background refreshes.
  const portfolioLoading =
    summary.isPending ||
    summary.isPlaceholderData ||
    metadata.isPending ||
    reportMetadata.isPending;

  useEffect(() => {
    if (reportId === null && reportMetadata.data) {
      setReportId(reportMetadata.data.reportId);
    }
  }, [reportId, reportMetadata.data]);

  useEffect(() => {
    // Retain the chosen size while reapplying viewport bounds.
    function resizeViewport() {
      setViewportHeight(window.innerHeight);
      setCRRHoldingsPanelHeight((height) =>
        boundCRRHoldingsPanelHeight(height)
      );
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
        <div className="explorer-heading">
          <h1>ERCOT CRR Holdings Explorer</h1>
        </div>
        <PortfolioFilters
          reportMetadata={reportMetadata}
          metadata={metadata}
          accountHolder={accountHolder}
          settlementPoint={settlementPoint}
          onHolderSelect={changeAccountHolder}
          onPointSelect={changeSettlementPoint}
          onClear={clearFilters}
          loading={portfolioLoading}
        />
        <Legend />
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
          "--portfolio-width": `${portfolioWidth}px`,
        }}
      >
        <aside>
          {!summary.data && !summary.isError && (
            <p role="status">Loading portfolio...</p>
          )}
          <div
            className="portfolio-overview"
            hidden={!summary.data && !summary.isError}
            aria-busy={portfolioLoading}
          >
            <div className="portfolio-scroll">
              {summary.isError ? (
                <p role="alert">Unable to load portfolio summary.</p>
              ) : !summary.data ? (
                <p role="status">Loading portfolio summary...</p>
              ) : (
                <PortfolioSummary
                  summary={summary.data}
                  mwhNumber={mwhNumber}
                />
              )}
              {summary.data && (
                <Discovery
                  summary={summary.data}
                  mwhNumber={mwhNumber}
                  accountHolder={accountHolder}
                  settlementPoint={settlementPoint}
                  onHolderSelect={changeAccountHolder}
                  onPointSelect={changeSettlementPoint}
                  onHolderClear={clearAccountHolder}
                  loading={portfolioLoading}
                />
              )}
            </div>
          </div>
        </aside>
        <div
          className="portfolio-resize"
          role="separator"
          tabIndex={0}
          aria-label="Resize portfolio pane"
          aria-orientation="vertical"
          aria-valuemin={320}
          aria-valuemax={Math.max(320, window.innerWidth - 500)}
          aria-valuenow={portfolioWidth}
          onPointerDown={(event) => {
            if (event.button !== 0) return;
            portfolioResizeStart.current = {
              x: event.clientX,
              width: portfolioWidth,
            };
            event.currentTarget.setPointerCapture(event.pointerId);
            event.preventDefault();
          }}
          onPointerMove={(event) => {
            if (!portfolioResizeStart.current) return;
            setPortfolioWidth(
              Math.max(
                320,
                Math.min(
                  window.innerWidth - 500,
                  portfolioResizeStart.current.width +
                    event.clientX -
                    portfolioResizeStart.current.x
                )
              )
            );
          }}
          onPointerUp={() => {
            portfolioResizeStart.current = null;
          }}
          onPointerCancel={() => {
            portfolioResizeStart.current = null;
          }}
          onLostPointerCapture={() => {
            portfolioResizeStart.current = null;
          }}
          onKeyDown={(event) => {
            if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
            event.preventDefault();
            setPortfolioWidth((width) =>
              Math.max(
                320,
                Math.min(
                  window.innerWidth - 500,
                  width + (event.key === "ArrowRight" ? 20 : -20)
                )
              )
            );
          }}
        />
        <div className="map-holdings-workspace">
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
            accountHolderName={
              reportMetadata.data?.accountHolders.find(
                (holder) => holder.accountHolder === accountHolder
              )?.legalName
            }
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
        </div>
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
