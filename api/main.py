# Imports
import sqlite3
from contextlib import closing
from datetime import date
from typing import Annotated, Literal

from fastapi import FastAPI, Query
from pydantic import AfterValidator, BaseModel

from queries import get_metadata, get_summary
from holdings import get_source_holdings, get_sink_holdings, get_contract_holdings


# Preparation: response models also define the generated HTTP contract.
class Report(BaseModel):
    reportId: int
    publicationDate: str


class AccountHolder(BaseModel):
    accountHolder: str
    legalName: str | None


class Metadata(BaseModel):
    reportId: int
    reports: list[Report]
    accountHolders: list[AccountHolder]
    settlementPoints: list[str]


class HedgeTypeMwh(BaseModel):
    OPT: float
    OBL: float


class RankedAccountHolder(BaseModel):
    accountHolder: str
    legalName: str | None
    totalMwh: float


class RankedSettlementPoint(BaseModel):
    settlementPoint: str
    totalMwh: float


class Summary(BaseModel):
    reportId: int
    totalMwh: float
    accountHolderCount: int
    settlementPointCount: int
    directedPathCount: int
    hedgeTypeMwh: HedgeTypeMwh
    topAccountHolders: list[RankedAccountHolder]
    topSettlementPoints: list[RankedSettlementPoint]


# Preparation: source matrix response contract.
class HoldingsMonth(HedgeTypeMwh):
    deliveryMonth: str


class SourceHolding(BaseModel):
    source: str
    totalOptMwh: float
    totalOblMwh: float
    months: list[HoldingsMonth]


class HoldingsRange(BaseModel):
    firstMonth: str
    lastMonth: str


class SourceHoldings(BaseModel):
    reportId: int
    deliveryMonths: list[str]
    holdingsRange: HoldingsRange | None
    sources: list[SourceHolding]
    nextOffset: int | None


class SinkHolding(BaseModel):
    sink: str
    totalOptMwh: float
    totalOblMwh: float
    months: list[HoldingsMonth]


class SinkHoldings(BaseModel):
    reportId: int
    source: str
    deliveryMonths: list[str]
    sinks: list[SinkHolding]


# Preparation: original contract fields are stored once in the response hierarchy.
class Contract(BaseModel):
    crrId: int
    segmentId: int
    crrType: str
    startDate: str
    endDate: str
    mw: float
    monthMwh: float


class TimeOfUseGroup(BaseModel):
    timeOfUse: str
    hours: int
    totalMwh: float
    contracts: list[Contract]


class ContractAccountHolder(BaseModel):
    accountHolder: str
    legalName: str | None
    totalMwh: float
    timeOfUseGroups: list[TimeOfUseGroup]


class ContractHoldings(BaseModel):
    reportId: int
    source: str
    sink: str
    deliveryMonth: str
    hedgeType: Literal['OPT', 'OBL']
    totalMwh: float
    accountHolders: list[ContractAccountHolder]


def validate_delivery_month(value):
    # Validation: accept only real first-of-month ISO dates.
    parsed = date.fromisoformat(value)
    if parsed.day != 1 or parsed.isoformat() != value:
        raise ValueError('Use a first-of-month ISO date (YYYY-MM-01).')
    return value


app = FastAPI()


# Output: keep each request on the existing read-only dataset.
@app.get("/api/metadata", response_model=Metadata, operation_id="getMetadata")
def metadata(report_id: int | None = None, account_holder: str | None = None):
    with closing(sqlite3.connect("file:/data/crr.sqlite?mode=ro", uri=True)) as db:
        return get_metadata(db, report_id, account_holder)


@app.get("/api/summary", response_model=Summary, operation_id="getSummary")
def summary(report_id: int | None = None, account_holder: str | None = None,
            settlement_point: str | None = None):
    with closing(sqlite3.connect("file:/data/crr.sqlite?mode=ro", uri=True)) as db:
        return get_summary(db, report_id, account_holder, settlement_point)


# Output
@app.get("/api/holdings/sources", response_model=SourceHoldings,
         operation_id="getSourceHoldings")
def source_holdings(report_id: int | None = None,
                    account_holder: str | None = None,
                    settlement_point: str | None = None,
                    limit: int = Query(20, ge=1, le=100),
                    offset: int = Query(0, ge=0)):
    with closing(sqlite3.connect("file:/data/crr.sqlite?mode=ro", uri=True)) as db:
        return get_source_holdings(db, report_id, account_holder,
                                   settlement_point, limit, offset)


# Output: expanded sources use the same read-only report and portfolio filters.
@app.get("/api/holdings/sources/{source}/sinks", response_model=SinkHoldings,
         operation_id="getSinkHoldings")
def sink_holdings(source: str, report_id: int | None = None,
                  account_holder: str | None = None,
                  settlement_point: str | None = None):
    with closing(sqlite3.connect("file:/data/crr.sqlite?mode=ro", uri=True)) as db:
        return get_sink_holdings(db, source, report_id, account_holder, settlement_point)


# Output: cell details retain one report and the same portfolio selection.
@app.get("/api/holdings/contracts", response_model=ContractHoldings,
         operation_id="getContractHoldings")
def contract_holdings(source: str, sink: str,
                      month: Annotated[str, Query(pattern=r'^\d{4}-\d{2}-01$'),
                                       AfterValidator(validate_delivery_month)],
                      hedge_type: Literal['OPT', 'OBL'],
                      report_id: int | None = None,
                      account_holder: str | None = None,
                      settlement_point: str | None = None):
    with closing(sqlite3.connect("file:/data/crr.sqlite?mode=ro", uri=True)) as db:
        return get_contract_holdings(db, source, sink, month, hedge_type,
                                     report_id, account_holder, settlement_point)
