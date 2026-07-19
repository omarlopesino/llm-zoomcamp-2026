# Q1

It creates only one span at https://logfire-eu.pydantic.dev/omarlopesino/starter-project?q=trace_id%3D%27019f76fdf317de5a0333064da116c0ff%27+and+span_id%3D%27e6f0e645093ea00b%27&spanId=e6f0e645093ea00b&traceId=019f76fdf317de5a0333064da116c0ff&env=-clear-&since=2026-07-18T20%3A19%3A44.374318Z&until=2026-07-18T21%3A19%3A44.374318Z

# Q2

Twenty two, so let's fill it with 24

duck> SELECT COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'agent_traces';┌──────────────┐
│ count_star() │
│    int64     │
├──────────────┤
│           22 │
└──────────────┘


# Q3

1500-3000


SELECT trace_id,
       count(*)                                   AS llm_calls,
       sum(attributes__gen_ai_usage_input_tokens) AS total_input_tokens
FROM logfire_data.records
WHERE attributes__gen_ai_usage_input_tokens IS NOT NULL
GROUP BY trace_id;



┌──────────────────────────────────┬───────────┬────────────────────┐
│             trace_id             │ LLM calls │ total_input_tokens │
├──────────────────────────────────┼───────────┼────────────────────┤
│ 019f77c0d6e9f818c41cd3897b37daa0 │ 2         │ 1623               │
└──────────────────────────────────┴───────────┴────────────────────┘
