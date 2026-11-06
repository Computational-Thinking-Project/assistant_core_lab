#!/usr/bin/env python3
"""Apply SQL migrations in order and remember which ones ran.

python scripts/migrate.py assistant.db
"""

import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


db_path = sys.argv[1] if len(sys.argv) > 1 else "assistant.db"
folder = Path(__file__).resolve().parents[1] / "sql" / "migrations"

con = sqlite3.connect(db_path)

try:
    con.execute(
        "CREATE TABLE IF NOT EXISTS schema_version "
        "(name TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    con.commit()

    done = {
        row[0]
        for row in con.execute("SELECT name FROM schema_version")
    }

    for f in sorted(folder.glob("*.sql")):
        if f.name in done:
            print(f"skip  {f.name}")
            continue

        sql = f.read_text(encoding="utf-8")
        applied_at = datetime.now(timezone.utc).isoformat()

        name_sql, time_sql = con.execute(
            "SELECT quote(?), quote(?)",
            (f.name, applied_at),
        ).fetchone()

        script = (
            "BEGIN IMMEDIATE;\n"
            + sql
            + "\nINSERT INTO schema_version (name, applied_at) "
            + f"VALUES ({name_sql}, {time_sql});\n"
            + "COMMIT;\n"
        )

        try:
            con.executescript(script)
        except Exception:
            con.rollback()
            raise

        print(f"apply {f.name}")

finally:
    con.close()


