"""Serve the existing dataset and shared service SQL for the WASM experiment."""

import os
from pathlib import Path
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import FileResponse


router = APIRouter()
SQL_DIRECTORY = Path(__file__).parent / "sql"


@router.api_route("/api/database", methods=["GET", "HEAD"], include_in_schema=False)
def database_download():
    return FileResponse(
        os.environ["DB_FILE"],
        media_type="application/vnd.sqlite3",
        headers={"Cache-Control": "no-store"},
    )


@router.get("/api/source-sql/{statement}", include_in_schema=False)
def source_statement(
    statement: Literal[
        "resolve_report",
        "delivery_months",
        "source_portfolio_bounds",
        "source_portfolio_bounds_account",
        "source_portfolio_bounds_point",
        "ranked_sources",
        "ranked_sources_account",
        "ranked_sources_point",
        "ranked_sources_point_account",
        "source_month_cells",
        "source_month_cells_account",
        "ranked_sinks",
        "ranked_sinks_account",
        "sink_month_cells",
        "sink_month_cells_account",
        "contract_segments",
        "contract_segments_account",
    ],
):
    directory = SQL_DIRECTORY if statement == "resolve_report" else SQL_DIRECTORY / "crr_holdings"
    return FileResponse(directory / f"{statement}.sql", media_type="text/plain")


@router.get("/api/metadata-sql/{statement}", include_in_schema=False)
def metadata_statement(
    statement: Literal[
        "reports",
        "report_account_holders",
        "settlement_point_choices",
        "settlement_point_choices_account",
    ],
):
    return FileResponse(SQL_DIRECTORY / "metadata" / f"{statement}.sql", media_type="text/plain")


@router.get("/api/summary-sql/{statement}", include_in_schema=False)
def summary_statement(
    statement: Literal[
        "portfolio_metrics",
        "portfolio_metrics_account",
        "portfolio_metrics_point",
        "portfolio_metrics_point_account",
        "top_account_holders",
        "top_account_holders_account",
        "top_account_holders_point",
        "top_account_holders_point_account",
        "settlement_point_totals",
        "settlement_point_totals_account",
        "settlement_point_totals_point",
        "settlement_point_totals_point_account",
    ],
):
    return FileResponse(SQL_DIRECTORY / "summary" / f"{statement}.sql", media_type="text/plain")
