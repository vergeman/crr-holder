"""Prepare the dataset from the four supplied ERCOT files."""
import argparse
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import tempfile

from import_inputs import load_inputs

SQL_DIR = Path(__file__).resolve().parent / "sql"


def read_sql(name):
    return (SQL_DIR / name).read_text()


def build_dataset(data_dir, output):
    # Prepare a temporary output beside the final database.
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{output.name}.", suffix=".tmp", dir=output.parent)
    os.close(fd)
    try:
        with closing(sqlite3.connect(temporary)) as db:
            # Create tables and import the four supplied files.
            db.executescript(read_sql("schema.sql"))
            print("Importing inputs...", flush=True)
            count = load_inputs(db, Path(data_dir))

            # Expand contracts into months, then create lookup indexes.
            print("Materializing monthly holdings...", flush=True)
            db.executescript(read_sql("monthly_holdings.sql"))
            print("Materializing summary holdings...", flush=True)
            db.executescript(read_sql("summary_holdings.sql"))
            db.executescript(read_sql("indexes.sql"))

            # Validate the temporary database before publishing it.
            print("Comparing counts, TOU coverage and MW/MWh...", flush=True)
            results = dict(db.execute(read_sql("validate.sql"), {"raw_count": count}))
            errors = {key: value for key, value in results.items() if key.endswith("_errors") and value}
            if errors:
                raise ValueError(f"Dataset comparisons failed: {errors}")

        # Publish the completed database after all comparisons pass.
        os.replace(temporary, output)
        return results
    finally:
        Path(temporary).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output", type=Path, default=Path("db/crr/crr.sqlite"))
    args = parser.parse_args()
    for key, value in build_dataset(args.data_dir, args.output).items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
