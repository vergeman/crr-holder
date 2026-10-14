export default function PortfolioFilters({
  reportMetadata,
  metadata,
  accountHolder,
  settlementPoint,
  onHolderSelect,
  onPointSelect,
  onClear,
  loading,
}) {
  return (
    <section
      className="portfolio-filters"
      aria-label="Portfolio filters"
      aria-busy={loading}
    >
      <div className="portfolio-filter-controls">
        <label>
          Account Holder
          <select
            value={accountHolder}
            disabled={loading || !reportMetadata.data}
            onChange={(event) => onHolderSelect(event.target.value)}
          >
            <option value="">All Account Holders</option>
            {reportMetadata.data?.accountHolders.map((holder) => (
              <option key={holder.accountHolder} value={holder.accountHolder}>
                {holder.accountHolder}
                {holder.legalName ? ` — ${holder.legalName}` : ""}
              </option>
            ))}
          </select>
        </label>
        <label>
          Settlement Point
          <select
            value={settlementPoint}
            disabled={loading || !metadata.data || metadata.isError}
            onChange={(event) => onPointSelect(event.target.value)}
          >
            <option value="">
              {metadata.isError
                ? "Unable to load settlement points"
                : !metadata.data
                ? "Loading settlement points..."
                : "All Settlement Points"}
            </option>
            {!metadata.isError &&
              metadata.data?.settlementPoints.map((point) => (
                <option key={point} value={point}>
                  {point}
                </option>
              ))}
          </select>
        </label>
        {metadata.isError && (
          <p role="alert">Unable to load settlement points.</p>
        )}
        <button disabled={loading} onClick={onClear}>
          Clear Filters
        </button>
        <span className="portfolio-filter-status" role="status">
          {loading ? "Updating…" : ""}
        </span>
      </div>
    </section>
  );
}
