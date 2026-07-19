"""Run ad-hoc SQL against the Logfire DuckDB database.

Usage:
    uv run python query.py                          # opens an interactive prompt
    uv run python query.py "SELECT * FROM records"  # runs one query and prints it
"""

import sys

import duckdb

DB_PATH = ".dlt/data/dev/logfire_pipeline.duckdb"


def connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(DB_PATH, read_only=True)
    con.execute("SET search_path='logfire_data'")
    return con


def main() -> None:
    con = connect()

    if len(sys.argv) > 1:
        con.sql(" ".join(sys.argv[1:])).show()
        return

    print("Connected to logfire_data (read-only). Type SQL, or 'tables', or 'quit'.")
    while True:
        try:
            sql = input("duck> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not sql or sql.lower() in {"quit", "exit"}:
            break
        if sql.lower() == "tables":
            con.sql(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='logfire_data' ORDER BY table_name"
            ).show()
            continue
        try:
            con.sql(sql).show()
        except Exception as e:  # keep the REPL alive on bad SQL
            print(f"error: {e}")


if __name__ == "__main__":
    main()
