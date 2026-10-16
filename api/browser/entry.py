"""Browser service exports; route validation remains on the server."""

from services.metadata import get_metadata
from services.summary.summary import get_summary
from services.crr_holdings.source_holdings import get_source_holdings
from services.crr_holdings.sink_holdings import get_sink_holdings
from services.crr_holdings.contract_holdings import get_contract_holdings


def metadata(db, report_id=None, account_holder=None):
    return get_metadata(db, report_id, account_holder)


def summary(db, report_id=None, account_holder=None, settlement_point=None):
    return get_summary(db, report_id, account_holder, settlement_point)


def sources(
    db, report_id=None, account_holder=None, settlement_point=None, limit=20, offset=0,
):
    return get_source_holdings(db, report_id, account_holder, settlement_point, limit, offset)


def sinks(db, source, report_id=None, account_holder=None, settlement_point=None):
    return get_sink_holdings(db, source, report_id, account_holder, settlement_point)


def contracts(
    db, source, sink, month, hedge_type, report_id=None,
    account_holder=None, settlement_point=None,
):
    return get_contract_holdings(
        db, source, sink, month, hedge_type, report_id, account_holder, settlement_point,
    )
