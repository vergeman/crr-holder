import { useEffect, useRef } from "react";
import { useContractHoldings } from "../../data/hooks";

export default function ContractDetailsModal({
  reportId,
  accountHolder,
  settlementPoint,
  selection,
  mwhNumber,
  onClose,
}) {
  const query = useContractHoldings(
    reportId,
    accountHolder,
    settlementPoint,
    selection
  );
  const dialog = useRef(null);
  const month = new Date(
    `${selection.deliveryMonth}T00:00:00Z`
  ).toLocaleDateString("en-US", {
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  });

  // Native modal dialogs keep keyboard focus inside and block background input.
  useEffect(() => {
    const modal = dialog.current;
    modal.showModal();
    return () => modal.close();
  }, []);

  function closeModal() {
    dialog.current.close();
    onClose();
  }

  function keepFocusInside(event) {
    if (event.key !== "Tab") return;
    const controls = [
      ...dialog.current.querySelectorAll("button, summary, [tabindex]"),
    ].filter((control) => !control.disabled && control.checkVisibility());
    const first = controls[0];
    const last = controls[controls.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  // Native disclosure changes visibility, never response subtotals.
  return (
    <dialog
      ref={dialog}
      id="contract-details"
      className="contract-details-modal"
      aria-labelledby="contract-heading"
      onKeyDown={keepFocusInside}
      onCancel={(event) => {
        event.preventDefault();
        closeModal();
      }}
    >
      <div className="contract-header">
        <h2 id="contract-heading">CRR Contract Details</h2>
        <button type="button" autoFocus onClick={closeModal}>
          Close
        </button>
      </div>
      <dl className="contract-selection">
        <div>
          <dt>Source</dt>
          <dd>{selection.source}</dd>
        </div>
        <div>
          <dt>Sink</dt>
          <dd>{selection.sink}</dd>
        </div>
        <div>
          <dt>Contract month</dt>
          <dd>{month}</dd>
        </div>
        <div>
          <dt>Hedge type</dt>
          <dd>
            {selection.hedgeType} (
            {selection.hedgeType === "OPT" ? "Options" : "Obligations"})
          </dd>
        </div>
      </dl>
      <div className="contract-body">
        {query.isError ? (
          <div role="alert">
            Unable to load contracts.{" "}
            <button
              type="button"
              disabled={query.isFetching}
              onClick={() => query.refetch()}
            >
              Retry
            </button>
          </div>
        ) : !query.data ? (
          <p role="status">Loading contracts...</p>
        ) : (
          <>
            <h3 className="contract-total">
              <span>Total</span>
              <strong>{mwhNumber.format(query.data.totalMwh)} MWh</strong>
            </h3>
            {query.data.accountHolders.length === 0 ? (
              <p>No contracts match this cell.</p>
            ) : (
              query.data.accountHolders.map((holder) => (
                <details key={holder.accountHolder} className="contract-holder">
                  <summary>
                    <span className="contract-holder-heading">
                      <span>
                        {holder.accountHolder}
                        {holder.legalName && <small>{holder.legalName}</small>}
                      </span>
                      <strong>{mwhNumber.format(holder.totalMwh)} MWh</strong>
                    </span>
                  </summary>
                  {holder.timeOfUseGroups.map((group) => (
                    <details key={group.timeOfUse} className="contract-tou">
                      <summary>
                        <span>{group.timeOfUse}</span>
                        <strong>{mwhNumber.format(group.totalMwh)} MWh</strong>
                      </summary>
                      <div
                        className="contract-table-scroll"
                        tabIndex={0}
                        role="region"
                        aria-label={`${holder.accountHolder} ${group.timeOfUse} contracts`}
                      >
                        <table className="contract-table">
                          <thead>
                            <tr>
                              <th scope="col">CRR</th>
                              <th scope="col">Segment</th>
                              <th scope="col">Type</th>
                              <th scope="col">Month</th>
                              <th scope="col">MW</th>
                              <th scope="col">{group.timeOfUse} hours</th>
                              <th scope="col">Total MW x hours (MWh)</th>
                            </tr>
                          </thead>
                          <tbody>
                            {group.contracts.map((contract) => (
                              <tr
                                key={`${contract.crrId}/${contract.segmentId}`}
                              >
                                <td>{contract.crrId}</td>
                                <td>{contract.segmentId}</td>
                                <td>{contract.crrType}</td>
                                <td>{month}</td>
                                <td>{contract.mw}</td>
                                <td>{group.hours}</td>
                                <td>{mwhNumber.format(contract.monthMwh)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </details>
                  ))}
                </details>
              ))
            )}
          </>
        )}
      </div>
    </dialog>
  );
}
