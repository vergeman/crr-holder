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
        <div className="portfolio-summary-columns">
          <dl className="portfolio-inventory">
            <div className="portfolio-total">
              <dt>Total Contractual MWh</dt>
              <dd>{mwhNumber.format(summary.totalMwh)}</dd>
            </div>
            {["OPT", "OBL"].map((type) => {
              const mwh = summary.hedgeTypeMwh[type];
              const percent =
                summary.totalMwh === 0 ? 0 : (100 * mwh) / summary.totalMwh;
              return (
                <div className="portfolio-hedge" key={type}>
                  <dt>
                    {type === "OPT" ? "Options" : "Obligations"} ({type})
                  </dt>
                  <dd>
                    {mwhNumber.format(mwh)} · {percent.toFixed(1)}%
                  </dd>
                </div>
              );
            })}
          </dl>
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
