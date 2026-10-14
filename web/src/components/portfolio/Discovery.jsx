function RankingList({ id, title, rows, identifierKey, onSelect, onClear,
                       filtered, mwhNumber, pointTotals = false }) {
  const explanation = 'Ranked by contractual MWh for the current filters.' +
    (pointTotals ? ' Each holding counts toward its source and sink; identical endpoints ' +
      'count once. Do not add settlement-point totals to calculate portfolio MWh.' : '');

  // Native buttons share the dropdown handlers and expose tooltip descriptions.
  return (
    <div className="ranking-list" aria-labelledby={`${id}-heading`}>
      <div className="ranking-heading">
        <h3 id={`${id}-heading`} tabIndex={0}
          aria-describedby={`${id}-tooltip`}>{title}</h3>
        <span className="ranking-tooltip" id={`${id}-tooltip`} role="tooltip">
          {explanation}
        </span>
        <button type="button" className="ranking-clear" disabled={!filtered}
          aria-label={`Clear ${title} filter`} onClick={onClear}>Clear</button>
      </div>
      {rows.length === 0 ? <p>No holdings match these filters.</p> : (
        <ol>
          {rows.map((row, index) => (
            <li key={row[identifierKey]}>
              <button type="button" className="ranking-row"
                onClick={() => onSelect(row[identifierKey])}>
                <span className="ranking-rank">{index + 1}</span>
                <span className="ranking-identity">
                  <strong>{row[identifierKey]}</strong>
                  {row.legalName && <span>{row.legalName}</span>}
                </span>
                <span className="ranking-mwh">{mwhNumber.format(row.totalMwh)} MWh</span>
              </button>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

export default function Discovery({ summary, mwhNumber, accountHolder, settlementPoint,
                     onHolderSelect, onPointSelect, onHolderClear }) {
  // Both lists belong to the same currently selected portfolio.
  return (
    <section aria-labelledby="discover-heading">
      <details open><summary><h2 id="discover-heading">Discover</h2></summary>
        <div className="discovery-lists">
          <RankingList mwhNumber={mwhNumber} id="top-accounts" title="Top Accounts"
            rows={summary.topAccountHolders} identifierKey="accountHolder"
            onSelect={onHolderSelect} onClear={onHolderClear} filtered={!!accountHolder} />
          <RankingList mwhNumber={mwhNumber} id="top-points" title="Top Settlement Points"
            rows={summary.topSettlementPoints} identifierKey="settlementPoint"
            onSelect={onPointSelect} onClear={() => onPointSelect('')}
            filtered={!!settlementPoint} pointTotals />
        </div>
      </details>
    </section>
  );
}

