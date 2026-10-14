"""Prepare the dataset from the four supplied ERCOT files."""
import argparse
from pathlib import Path

SQL_DIR = Path(__file__).resolve().parent / "sql"


def read_sql(name):
    return (SQL_DIR / name).read_text()


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output", type=Path, default=Path("db/crr/crr.sqlite"))
    return parser.parse_args()


if __name__ == "__main__":
    arguments()
    raise SystemExit("Input import and monthly materialization follow in the next commit groups")
