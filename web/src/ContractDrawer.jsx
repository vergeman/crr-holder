// Imports
import { useEffect, useRef } from 'react';
import { useContractHoldings } from './data/hooks';

export default function ContractDrawer({ reportId, accountHolder, settlementPoint,
  selection, mwhNumber, onClose }) {
  // Preparation: the parent remounts this drawer for each selected cell.
  const query = useContractHoldings(reportId, accountHolder, settlementPoint, selection);
  const closeButton = useRef(null);
  const month = new Date(`${selection.deliveryMonth}T00:00:00Z`).toLocaleDateString(
    'en-US', { month: 'long', year: 'numeric', timeZone: 'UTC' });

  useEffect(() => { closeButton.current.focus(); }, []);
  useEffect(() => {
    function escape(event) {
      if (event.key === 'Escape') {
        event.preventDefault();
        onClose();
      }
    }
    document.addEventListener('keydown', escape);
    return () => document.removeEventListener('keydown', escape);
  }, [onClose]);

  // Output: native disclosure changes visibility, never response subtotals.
  return <aside className="contract-drawer" aria-labelledby="contract-heading">
    <div className="contract-header">
      <h2 id="contract-heading">CRR Holdings Details</h2>
      <button type="button" ref={closeButton} onClick={onClose}>Close</button>
    </div>
    <p><strong>{selection.source} → {selection.sink}</strong><br />
      {month} · {selection.hedgeType === 'OPT' ? 'Options' : 'Obligations'}
      {' '}({selection.hedgeType})</p>
    {query.isError ? <div role="alert">Unable to load contracts.{' '}
      <button type="button" disabled={query.isFetching}
        onClick={() => query.refetch()}>Retry</button>
    </div> : !query.data ? <p role="status">Loading contracts...</p> : <>
      <p className="contract-total">Selected-month total:{' '}
        <strong>{mwhNumber.format(query.data.totalMwh)} MWh</strong></p>
      {query.data.accountHolders.length === 0 ? <p>No contracts match this cell.</p> :
        query.data.accountHolders.map((holder) => <details key={holder.accountHolder}
          className="contract-holder">
          <summary><span>{holder.accountHolder}
            {holder.legalName && <small>{holder.legalName}</small>}</span>
            <strong>{mwhNumber.format(holder.totalMwh)} MWh</strong></summary>
          {holder.timeOfUseGroups.map((group) => <details key={group.timeOfUse}
            className="contract-tou">
            <summary><span>{group.timeOfUse}</span>
              <strong>{mwhNumber.format(group.totalMwh)} MWh</strong></summary>
            <ul>{group.contracts.map((contract) =>
              <li key={`${contract.crrId}/${contract.segmentId}`}>
                <strong>CRR {contract.crrId} · Segment {contract.segmentId}</strong>
                <span>{contract.crrType} · {contract.mw} MW</span>
                <span>{contract.startDate}–{contract.endDate}</span>
                <span>Selected-month contribution:{' '}
                  {mwhNumber.format(contract.monthMwh)} MWh</span>
              </li>)}</ul>
          </details>)}
        </details>)}
    </>}
  </aside>;
}
