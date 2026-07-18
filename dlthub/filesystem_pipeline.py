"""dlt filesystem pipeline: load local Claude session logs (JSONL) into DuckDB.

Reads every ~/.claude/projects/**/*.jsonl session transcript, parses each line
into a record, injects source-file provenance, and lets dlt normalize the
heterogeneous events into DuckDB.

bucket_url is read from .dlt/config.toml under [sources.filesystem].
file_glob is set inline so the pattern lives next to the code that depends on it.
"""

import json
from typing import Iterator

import dlt
from dlt.sources import TDataItems
from dlt.sources.filesystem import FileItemDict, filesystem

# Project folders (first path segment of relative_path) to skip entirely.
EXCLUDE_PROJECTS = {"-home-omi-proyectos-omarlopesino"}


@dlt.transformer
def read_jsonl_with_source(items: Iterator[FileItemDict]) -> Iterator[TDataItems]:
    """Parse each JSONL file line-by-line and stamp every record with its origin.

    Adds three columns that plain read_jsonl drops, so every row is traceable
    back to its file/session/project even when the JSON line itself omits
    session_id (e.g. file-history-snapshot events):
      - source_file:    the .jsonl filename (also the Claude session UUID)
      - source_session: filename without extension (the session id)
      - source_project: the project folder Claude derived from the cwd
    """
    for file_obj in items:
        relative_path = file_obj["relative_path"]  # e.g. "-home-omi-proj/<uuid>.jsonl"
        file_name = file_obj["file_name"]
        source_project = relative_path.split("/")[0]
        source_session = file_name.rsplit(".", 1)[0]

        records = []
        with file_obj.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                record["source_file"] = file_name
                record["source_session"] = source_session
                record["source_project"] = source_project
                records.append(record)
        yield records


def load_logs() -> None:
    """Load Claude JSONL session logs into DuckDB (dataset: claude_logs, table: logs)."""
    pipeline = dlt.pipeline(
        pipeline_name="claude_logs",
        destination="duckdb",
        dataset_name="claude_logs",
        dev_mode=True,  # fresh dataset on every run during dev
    )

    files = filesystem(file_glob="**/*.jsonl").add_filter(
        lambda item: item["relative_path"].split("/")[0] not in EXCLUDE_PROJECTS
    )
    reader = (files | read_jsonl_with_source()).with_name("logs")

    load_info = pipeline.run(reader, write_disposition="replace")
    print(load_info)
    print(pipeline.last_trace.last_normalize_info)


if __name__ == "__main__":
    load_logs()
