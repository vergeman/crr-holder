from typing import Literal

from pydantic import BaseModel


# Response models also define the generated HTTP contract.
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


class GeographicPoint(BaseModel):
    settlementPoint: str
    longitude: float | None
    latitude: float | None
    sourceMwh: float
    sinkMwh: float


class Summary(BaseModel):
    reportId: int
    totalMwh: float
    accountHolderCount: int
    settlementPointCount: int
    directedPathCount: int
    hedgeTypeMwh: HedgeTypeMwh
    topAccountHolders: list[RankedAccountHolder]
    topSettlementPoints: list[RankedSettlementPoint]
    geographicFootprint: list[GeographicPoint]


# Source matrix response contract.
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


# Original contract fields are stored once in the response hierarchy.
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
