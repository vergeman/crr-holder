# Imports
import sqlite3
from contextlib import closing

from fastapi import FastAPI, Query
from pydantic import BaseModel

from queries import get_metadata, get_summary
from holdings import get_source_holdings


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
    totalMwh: float
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
