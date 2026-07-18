"""Agent traces — ingest 20k logs from the test traces API and explore them."""

from rest_api_pipeline import ingest_agent_traces
import agent_traces_dashboard

__all__: list[str] = ["ingest_agent_traces", "agent_traces_dashboard"]
