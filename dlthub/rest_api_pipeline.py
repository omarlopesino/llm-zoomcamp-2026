"""dlt REST API pipeline: load agent-trace logs from the test traces API into DuckDB.

Source: https://test-agent-traces-api-xt2e7ottma-ew.a.run.app  (no auth — public)
Endpoint: GET /logs?offset=&limit=  → returns Claude Code transcript-format logs.
Pagination: offset-based (limit max 1000, response carries total/next_offset).

We cap the load at MAX_LOGS rows via the offset paginator's maximum_offset.
"""

from typing import Any

import dlt
from dlt.hub import run
from dlt.sources.rest_api import RESTAPIConfig, rest_api_resources

BASE_URL = "https://test-agent-traces-api-xt2e7ottma-ew.a.run.app"
PAGE_LIMIT = 1000  # API max rows per request


@dlt.source(name="agent_traces")
def agent_traces_source(max_logs: int = 20000) -> Any:
    """Load agent-trace logs from the test traces API.

    Args:
        max_logs: Total number of logs to load. Rounded down to the paginator's
            page boundary via maximum_offset. Defaults to 20,000.
    """
    config: RESTAPIConfig = {
        "client": {
            "base_url": BASE_URL,
            # Offset pagination: increment `offset` by `limit` until maximum_offset.
            "paginator": {
                "type": "offset",
                "limit": PAGE_LIMIT,
                "offset": 0,
                "offset_param": "offset",
                "limit_param": "limit",
                "maximum_offset": max_logs,
                "total_path": "total",
            },
        },
        "resources": [
            {
                "name": "logs",
                "primary_key": "index",
                "write_disposition": "replace",
                "endpoint": {
                    "path": "/logs",
                    "data_selector": "logs",
                },
            },
        ],
    }
    yield from rest_api_resources(config)


@run.pipeline("agent_traces")
def ingest_agent_traces() -> None:
    """dltHub Platform job: load 20k agent-trace logs into DuckDB.

    Runs on the runtime with a stable dataset (no dev_mode). Note: DuckDB storage
    on the runtime is ephemeral — data does not persist between runs.
    """
    pipeline = dlt.pipeline(
        pipeline_name="agent_traces",
        destination="warehouse",  # named: duckdb (dev) / motherduck (prod)
        dataset_name="agent_traces_data",
    )
    load_info = pipeline.run(agent_traces_source(max_logs=20000))
    print(load_info)


def load_logs() -> None:
    """Local dev run: load 20k agent-trace logs into DuckDB (fresh dataset each run)."""
    pipeline = dlt.pipeline(
        pipeline_name="agent_traces",
        destination="warehouse",  # named: duckdb (dev) / motherduck (prod)
        dataset_name="agent_traces_data",
        dev_mode=True,  # fresh dataset on every run during dev
    )

    load_info = pipeline.run(agent_traces_source(max_logs=20000))
    print(load_info)
    print(pipeline.last_trace.last_normalize_info)


if __name__ == "__main__":
    load_logs()
