export default function PortfolioSummary({ summary, mwhNumber }) {
  const metrics = [
    ["Account Holders", summary.accountHolderCount],
    ["Settlement Points", summary.settlementPointCount],
    ["Source-Sink Pairs", summary.directedPathCount],
  ];

  // Inventory values and percentages use the same unrounded API totals.
  return (
    <section className="portfolio-summary" aria-labelledby="summary-heading">
      <details open>
        <summary>
          <h2 id="summary-heading">Portfolio Summary</h2>
        </summary>
        <p>Contractual inventory across the report’s delivery horizon.</p>
        <div className="portfolio-summary-columns">
          <div>
            <dl className="portfolio-total">
              <div>
                <dt>Total Contractual MWh</dt>
                <dd>{mwhNumber.format(summary.totalMwh)}</dd>
              </div>
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
          </div>
          <dl>
            {metrics.map(([label, value]) => (
              <div key={label}>
                <dt>{label}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
        </div>
        {summary.accountHolderCount === 0 && (
          <p>No holdings match these filters.</p>
        )}
      </details>
    </section>
  );
}
