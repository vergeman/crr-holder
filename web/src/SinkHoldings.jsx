// Imports
import { useSinkHoldings } from './data/hooks';

export default function SinkHoldings({ reportId, accountHolder, settlementPoint,
  source, deliveryMonths, mwhNumber, onCellSelect }) {
  const query = useSinkHoldings(reportId, accountHolder, settlementPoint, source);

  // Output: request states stay in the sticky label cell beside this source.
  if (!query.data || query.isError || query.data.sinks.length === 0) {
    return <tr className="sink-state">
      <th scope="row">
        {query.isError ? <div role="alert">Unable to load sinks.{' '}
          <button type="button" disabled={query.isFetching}
            onClick={() => query.refetch()}>Retry</button>
        </div> : !query.data ? <span role="status">Loading sinks...</span> :
          <span>No sinks match these filters.</span>}
      </th>
      <td colSpan={2 + deliveryMonths.length * 2} />
    </tr>;
  }

  // Output: every sink aligns with the parent's totals and complete month header.
  return query.data.sinks.map((row) => <tr className="sink-row" key={row.sink}>
    <th scope="row">↳ {row.sink}</th>
    <td>{mwhNumber.format(row.totalOptMwh)}</td>
    <td>{mwhNumber.format(row.totalOblMwh)}</td>
    {row.months.flatMap((month) => ['OPT', 'OBL'].map((type) =>
      <td key={`${month.deliveryMonth}/${type}`}>
        <button type="button" className="contract-cell"
          aria-label={`${source} to ${row.sink}, ${month.deliveryMonth}, ${type} contract details`}
          onClick={(event) => onCellSelect({ source, sink: row.sink,
            deliveryMonth: month.deliveryMonth, hedgeType: type }, event.currentTarget)}>
          {mwhNumber.format(month[type])}
        </button>
      </td>))}
  </tr>);
}
