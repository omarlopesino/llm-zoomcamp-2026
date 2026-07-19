"""Pull observability data from Pydantic Logfire into DuckDB with dlt.

Logfire exposes a read-only Query API (`GET /v1/query`) that runs SQL against
your project's data (the `records` table holds spans/logs). It requires a
**read** token as a Bearer credential.

The API answers in a *columnar* shape (each column carries a `values` array),
so we transpose it into row dicts before yielding them to dlt.

Docs: https://logfire.pydantic.dev/docs/how-to-guides/query-api/
Context: https://dlthub.com/context/source/logfire
"""

import os
from typing import Any, Iterator

import dlt
import requests
from dotenv import load_dotenv

# Reuse the read token already stored in .env (LOGFIRE_READ_TOKEN) by exposing
# it under dlt's config convention for `[sources.logfire] read_token`, so the
# source below can pick it up via `dlt.secrets.value`.
load_dotenv()
if os.environ.get("LOGFIRE_READ_TOKEN") and not os.environ.get(
    "SOURCES__LOGFIRE__READ_TOKEN"
):
    os.environ["SOURCES__LOGFIRE__READ_TOKEN"] = os.environ["LOGFIRE_READ_TOKEN"]

# EU region endpoint (matches the project URL in questions.md). Use
# https://logfire-us.pydantic.dev/v1/query for US-region projects.
LOGFIRE_QUERY_URL = "https://logfire-eu.pydantic.dev/v1/query"


def _rows_from_columnar(payload: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Transpose Logfire's columnar JSON response into row dicts."""
    columns = payload.get("columns", [])
    if not columns:
        return
    names = [col["name"] for col in columns]
    value_lists = [col["values"] for col in columns]
    for row in zip(*value_lists):
        yield dict(zip(names, row))


@dlt.resource(name="records", write_disposition="append", primary_key="span_id")
def records(
    read_token: str = dlt.secrets.value,
    start_timestamp: dlt.sources.incremental[str] = dlt.sources.incremental(
        "start_timestamp", initial_value="1970-01-01T00:00:00Z"
    ),
) -> Iterator[dict[str, Any]]:
    """Query the Logfire `records` table (spans + logs) incrementally.

    Uses `start_timestamp` as an incremental cursor so re-runs only fetch spans
    newer than the last one already loaded.
    """
    sql = (
        "SELECT * FROM records "
        f"WHERE start_timestamp > '{start_timestamp.last_value}' "
        "ORDER BY start_timestamp"
    )
    response = requests.get(
        LOGFIRE_QUERY_URL,
        headers={
            "Authorization": f"Bearer {read_token}",
            "Accept": "application/json",
        },
        params={"sql": sql},
        timeout=60,
    )
    response.raise_for_status()
    yield from _rows_from_columnar(response.json())


@dlt.source(name="logfire")
def logfire_source(read_token: str = dlt.secrets.value):
    return records(read_token=read_token)


def get_data() -> None:
    pipeline = dlt.pipeline(
        pipeline_name="logfire_pipeline",
        destination="duckdb",
        dataset_name="logfire_data",
    )
    load_info = pipeline.run(logfire_source())
    print(load_info)
    # Show what landed
    with pipeline.sql_client() as client:
        n = client.execute_sql("SELECT count(*) FROM records")[0][0]
        print(f"\nrecords loaded into DuckDB: {n}")


if __name__ == "__main__":
    get_data()
