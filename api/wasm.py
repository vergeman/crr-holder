"""Serve the read-only dataset for browser query providers."""

import os

from fastapi import APIRouter
from fastapi.responses import FileResponse


router = APIRouter()


@router.api_route("/api/database", methods=["GET", "HEAD"], include_in_schema=False)
def database_download():
    return FileResponse(
        os.environ["DB_FILE"],
        media_type="application/vnd.sqlite3",
        headers={"Cache-Control": "no-store"},
    )
