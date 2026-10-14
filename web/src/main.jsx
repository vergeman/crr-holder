import {
  PortfolioOverview,
  PortfolioPanel,
  ReportSelector,
} from "./components/portfolio";
import PortfolioFilters from "./components/portfolio/PortfolioFilters";
import { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useMetadata, useSummary } from "./data/hooks";
import CRRHoldingsPanel, { ContractDetailsModal } from "./components/holdings";
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
  // Remember the holdings button that opened the modal so focus can return to it.
  const cellButton = useRef(null);
  const [crrHoldingsPanelVisible, setCRRHoldingsPanelVisible] = useState(false);
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
      // Reuse default metadata when switching to the resolved report ID.
      queryClient.setQueryData(
        ["metadata", reportMetadata.data.reportId, ""],
        reportMetadata.data
      );
      setReportId(reportMetadata.data.reportId);
    }
  }, [reportId, reportMetadata.data]);

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
    // Keep the originating DOM element alongside the selected contract cell.
    cellButton.current = button;
    setSelection(cell);
  }

  function closeContractDetails() {
    setSelection(null);
    // Restore focus if the originating button still exists, without scrolling.
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
        <ReportSelector
          reportMetadata={reportMetadata}
          reportId={reportId}
          onReportSelect={changeReport}
        />
      </header>
      {reportMetadata.isError && (
        <p role="alert">Unable to load report filters.</p>
      )}
      <div className="workspace">
        <PortfolioPanel>
          <PortfolioOverview
            summary={summary}
            mwhNumber={mwhNumber}
            accountHolder={accountHolder}
            settlementPoint={settlementPoint}
            onHolderSelect={changeAccountHolder}
            onPointSelect={changeSettlementPoint}
            onHolderClear={clearAccountHolder}
            loading={portfolioLoading}
          />
        </PortfolioPanel>
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
