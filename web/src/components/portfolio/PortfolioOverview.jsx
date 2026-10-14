import PortfolioSummary from "./PortfolioSummary";
import Discovery from "./Discovery";

export default function PortfolioOverview({
  summary,
  mwhNumber,
  accountHolder,
  settlementPoint,
  onHolderSelect,
  onPointSelect,
  onHolderClear,
  loading,
}) {
  if (summary.isError) {
    return <p role="alert">Unable to load portfolio.</p>;
  }
  if (!summary.data) {
    return (
      <p className="portfolio-loading" role="status">
        Loading portfolio...
      </p>
    );
  }

  return (
    <div className="portfolio-overview" aria-busy={loading}>
      <div className="portfolio-scroll">
        <PortfolioSummary summary={summary.data} mwhNumber={mwhNumber} />
        <Discovery
          summary={summary.data}
          mwhNumber={mwhNumber}
          accountHolder={accountHolder}
          settlementPoint={settlementPoint}
          onHolderSelect={onHolderSelect}
          onPointSelect={onPointSelect}
          onHolderClear={onHolderClear}
          loading={loading}
        />
      </div>
    </div>
  );
}
