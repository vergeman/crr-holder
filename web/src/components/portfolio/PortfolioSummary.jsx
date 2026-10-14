export default function PortfolioSummary({ summary, mwhNumber }) {
  const metrics = [
    ["Total Contractual MWh", mwhNumber.format(summary.totalMwh)],
    ["Account Holders", summary.accountHolderCount],
    ["Settlement Points", summary.settlementPointCount],
    ["Source-Sink Pairs", summary.directedPathCount],
  ];

  // Inventory values and percentages use the same unrounded API totals.
  return (
    <section aria-labelledby="summary-heading">
      <details open>
        <summary>
          <h2 id="summary-heading">Portfolio Summary</h2>
        </summary>
        <p>Contractual inventory across the report’s delivery horizon.</p>
        <dl>
          {metrics.map(([label, value]) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
        {["OPT", "OBL"].map((type) => {
          const mwh = summary.hedgeTypeMwh[type];
          const percent =
            summary.totalMwh === 0 ? 0 : (100 * mwh) / summary.totalMwh;
          return (
            <div className="hedge" key={type}>
              <div className="hedge-label">
                <span>
                  {type === "OPT" ? "Options" : "Obligations"} ({type})
                </span>
                <span>
                  {mwhNumber.format(mwh)} MWh · {percent.toFixed(1)}%
                </span>
              </div>
              <div className="bar" aria-hidden="true">
                <div
                  className={type.toLowerCase()}
                  style={{ width: `${percent}%` }}
                />
              </div>
            </div>
          );
        })}
        {summary.accountHolderCount === 0 && (
          <p>No holdings match these filters.</p>
        )}
      </details>
    </section>
  );
}
