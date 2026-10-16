"""Load shared SQL statements as plain text."""

from functools import cache
from pathlib import Path


@cache
def load_sql(name):
    return (Path(__file__).parent / name).read_text()
