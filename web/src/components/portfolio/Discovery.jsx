// The directory suffix is useful in source data but adds noise to rankings.
function accountDisplayName(name) {
  return name?.replace(/\s*\(CRRAH\)$/, "") || "";
}

function RankingTable({
  id,
  title,
  rows,
  identifierKey,
  onSelect,
  onClear,
  selected,
  mwhNumber,
  loading,
  pointTotals = false,
}) {
  const explanation =
    "Ranked by contractual MWh for the current filters." +
    (pointTotals
      ? " Each holding counts toward its source and sink; identical endpoints " +
        "count once. Do not add settlement-point totals to calculate portfolio MWh."
      : "");

  // Native buttons share the dropdown handlers and expose tooltip descriptions.
  return (
    <div className="ranking-list" aria-labelledby={`${id}-heading`}>
      <div className="ranking-heading">
        <h3
          id={`${id}-heading`}
          tabIndex={0}
          aria-describedby={`${id}-tooltip`}
        >
          {title}
        </h3>
        <span className="ranking-tooltip" id={`${id}-tooltip`} role="tooltip">
          {explanation}
        </span>
        <button
          type="button"
          className="ranking-clear control-icon"
          disabled={loading || !selected}
          aria-label={`Clear ${title} filter`}
          title={`Clear ${title} filter`}
          onClick={onClear}
        >
          <span aria-hidden="true">×</span>
        </button>
      </div>
      {rows.length === 0 ? (
        <p>No holdings match these filters.</p>
      ) : (
        <div className="ranking-scroll">
          <table className="ranking-table" aria-busy={loading}>
            <thead>
              <tr>
                <th scope="col">{pointTotals ? "Settlement Point" : "Code"}</th>
                {!pointTotals && <th scope="col">Account Holder</th>}
                <th scope="col">Total MWh</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr
                  key={row[identifierKey]}
                  onClick={() => {
                    if (!loading) onSelect(row[identifierKey]);
                  }}
                  className={
                    selected === row[identifierKey]
                      ? "ranking-selected"
                      : undefined
                  }
                >
                  <td>
                    <button
                      type="button"
                      className="ranking-identity"
                      disabled={loading}
                      aria-pressed={selected === row[identifierKey]}
                    >
                      {row[identifierKey]}
                    </button>
                  </td>
                  {!pointTotals && <td>{accountDisplayName(row.legalName)}</td>}
                  <td className="ranking-mwh">
                    {mwhNumber.format(row.totalMwh)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default function Discovery({
  summary,
  mwhNumber,
  accountHolder,
  settlementPoint,
  onHolderSelect,
  onPointSelect,
  onHolderClear,
  loading,
}) {
  // Both rankings belong to the same currently selected portfolio.
  return (
    <section aria-labelledby="discover-heading">
      <details open>
        <summary>
          <h2 id="discover-heading">Discover</h2>
        </summary>
        <div className="discovery-lists">
          <RankingTable
            mwhNumber={mwhNumber}
            loading={loading}
            id="top-accounts"
            title="Top Accounts"
            rows={summary.topAccountHolders}
            identifierKey="accountHolder"
            onSelect={onHolderSelect}
            onClear={onHolderClear}
            selected={accountHolder}
          />
          <RankingTable
            mwhNumber={mwhNumber}
            loading={loading}
            id="top-points"
            title="Top Settlement Points"
            rows={summary.topSettlementPoints}
            identifierKey="settlementPoint"
            onSelect={onPointSelect}
            onClear={() => onPointSelect("")}
            selected={settlementPoint}
            pointTotals
          />
        </div>
      </details>
    </section>
  );
}
