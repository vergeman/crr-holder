# Imports
import sqlite3
from contextlib import closing

from fastapi import FastAPI
from pydantic import BaseModel

from queries import get_metadata, get_summary


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
