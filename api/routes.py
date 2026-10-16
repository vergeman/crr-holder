from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Query
from pydantic import AfterValidator

from database import open_database
from models import Metadata, Summary, SourceHoldings, SinkHoldings, ContractHoldings
from services.crr_holdings import get_source_holdings, get_sink_holdings, get_contract_holdings
from services.metadata import get_metadata
from services.summary import get_summary


def validate_delivery_month(value):
    # Accept only real first-of-month ISO dates.
    parsed = date.fromisoformat(value)
    if parsed.day != 1 or parsed.isoformat() != value:
        raise ValueError('Use a first-of-month ISO date (YYYY-MM-01).')
    return value


router = APIRouter()


# Keep each request on the existing read-only dataset.
@router.get("/api/metadata", response_model=Metadata, operation_id="getMetadata")
def metadata(report_id: int | None = None, account_holder: str | None = None):
    with open_database() as db:
        return get_metadata(db, report_id, account_holder)


@router.get("/api/summary", response_model=Summary, operation_id="getSummary")
def summary(report_id: int | None = None, account_holder: str | None = None,
            settlement_point: str | None = None):
    with open_database() as db:
        return get_summary(db, report_id, account_holder, settlement_point)


@router.get("/api/holdings/sources", response_model=SourceHoldings,
         operation_id="getSourceHoldings")
def source_holdings(report_id: int | None = None,
                    account_holder: str | None = None,
                    settlement_point: str | None = None,
                    limit: int = Query(20, ge=1, le=100),
                    offset: int = Query(0, ge=0)):
    with open_database() as db:
        return get_source_holdings(db, report_id, account_holder,
                                   settlement_point, limit, offset)


# Expanded sources use the same read-only report and portfolio filters.
@router.get("/api/holdings/sources/{source}/sinks", response_model=SinkHoldings,
         operation_id="getSinkHoldings")
def sink_holdings(source: str, report_id: int | None = None,
                  account_holder: str | None = None,
                  settlement_point: str | None = None):
    with open_database() as db:
        return get_sink_holdings(db, source, report_id, account_holder, settlement_point)


# Cell details retain one report and the same portfolio selection.
@router.get("/api/holdings/contracts", response_model=ContractHoldings,
         operation_id="getContractHoldings")
def contract_holdings(source: str, sink: str,
                      month: Annotated[str, Query(pattern=r'^\d{4}-\d{2}-01$'),
                                       AfterValidator(validate_delivery_month)],
                      hedge_type: Literal['OPT', 'OBL'],
                      report_id: int | None = None,
                      account_holder: str | None = None,
                      settlement_point: str | None = None):
    with open_database() as db:
        return get_contract_holdings(db, source, sink, month, hedge_type,
                                     report_id, account_holder, settlement_point)
