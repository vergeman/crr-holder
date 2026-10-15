import os
import sqlite3
from contextlib import closing, contextmanager


@contextmanager
def open_database():
    with closing(sqlite3.connect(f"file:{os.environ['DB_FILE']}?mode=ro", uri=True)) as db:
        yield db
