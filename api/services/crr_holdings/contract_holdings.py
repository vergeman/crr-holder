"""GET /api/holdings/contracts supplies the contract-details modal opened
from a CRR Holdings sink's monthly OPT/OBL cell. Show matching contract
segments grouped by account holder and time of use, with MW, hours, and MWh.
"""

from services.helpers import resolve_report
from sql import load_sql
from timing import timed


def _query_contract_segments(db, report_id, account_holder, settlement_point,
                            source, sink, month, hedge_type):
    """Return ordered segments with columns:

    account_holder, legal_name, time_of_use, crr_id, segment_id, crr_type,
    start_date, end_date, mw, hours, month_mwh.
    """
    parameters = {
        "report_id": report_id,
        "account_holder": account_holder or None,
        "settlement_point": settlement_point or None,
        "source": source,
        "sink": sink,
        "month": month,
        "hedge_type": hedge_type,
    }
    statement = "crr_holdings/contract_segments.sql"
    if account_holder:
        statement = "crr_holdings/contract_segments_account.sql"
    return db.execute(load_sql(statement), parameters).fetchall()


def _group_contract_segments(segments):
    """Group ordered segments by holder and time of use, summing their MWh."""
    holders = {}
    for holder, name, tou, crr_id, segment_id, crr_type, start, end, mw, hours, mwh in segments:
        group = holders.setdefault(holder, {
            "accountHolder": holder, "legalName": name, "totalMwh": 0,
            "timeOfUseGroups": {},
        })
        tou_group = group['timeOfUseGroups'].setdefault(tou, {
            "timeOfUse": tou, "hours": hours, "totalMwh": 0, "contracts": [],
        })
        tou_group['contracts'].append({
            "crrId": crr_id, "segmentId": segment_id, "crrType": crr_type,
            "startDate": start, "endDate": end, "mw": mw, "monthMwh": mwh,
        })
        tou_group['totalMwh'] += mwh
        group['totalMwh'] += mwh

    # Time-of-use groups have a fixed display order within each holder.
    for group in holders.values():
        groups = group['timeOfUseGroups']
        group['timeOfUseGroups'] = [groups[tou] for tou in
                                    ('PeakWD', 'PeakWE', 'Off-peak') if tou in groups]
    return sorted(holders.values(), key=lambda group:
                  (-group['totalMwh'], group['accountHolder']))


@timed
def get_contract_holdings(db, source, sink, month, hedge_type, report_id=None,
                         account_holder=None, settlement_point=None):
    """Build modal contents for the selected source, sink, month, and hedge type.

    Return contract segments grouped by account holder and time of use,
    including contract identifiers, MW, hours, and calculated monthly MWh.
    Include modal, holder, and time-of-use MWh totals; rank holders by total MWh.
    """
    report_id = resolve_report(db, report_id)
    segments = _query_contract_segments(
        db, report_id, account_holder, settlement_point, source, sink, month, hedge_type)

    account_holders = _group_contract_segments(segments)
    total_mwh = sum(holder['totalMwh'] for holder in account_holders)

    return {"reportId": report_id, "source": source, "sink": sink,
            "deliveryMonth": month, "hedgeType": hedge_type,
            "totalMwh": total_mwh, "accountHolders": account_holders}
