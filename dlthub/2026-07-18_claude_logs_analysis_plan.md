# Analysis Plan: claude_logs

## Connection
pipeline: claude_logs
dataset: (current default dataset via `pipeline.dataset()`)
destination: duckdb

## Profile Summary
| table | rows | key columns | notes |
|-------|------|-------------|-------|
| logs | 9,720 | type, timestamp, message__model, message__usage__*, source_project, source_session | temporal: timestamp (TIMESTAMPTZ, UTC); heterogeneous event `type`; excludes omarlopesino |
| logs__message__content | ~5.5k | type, name (tool name when type='tool_use') | tool calls live here; `name` = tool |

Corpus spans **2026-06-21 → 2026-07-18** (~4 weeks). Event types: assistant (4,583), user (2,672), plus mode/attachment/system/etc. Models: sonnet-5, haiku-4-5, fable-5, opus-4-8, sonnet-4-6. Cache reads dominate token volume (~323M vs 1.18M fresh input).

## Questions
1. [x] How does my Claude Code activity trend day by day? → Chart 1
2. [x] Which models do I use most? → Chart 2
3. [x] How are tokens consumed across models (input/output/cache)? → Chart 3
4. [x] Which tools does Claude call most often? → Chart 4
5. [x] Which projects do I use Claude Code in most? → Chart 5
6. [x] What time of day am I most active? → Chart 6
7. [x] How many distinct sessions do I run per day? → Chart 7
8. [x] How does daily token consumption trend over time? → Chart 8

## Data Gaps
(none — usage report fully answerable from the loaded schema)

## Chart 1: Daily Activity — User Prompts vs Assistant Responses
question: How does my Claude Code activity trend day by day?
type: line (multi-series)
x: timestamp (daily)
y: count(*) by type
source: logs

```sql
SELECT
    DATE_TRUNC('day', timestamp)::DATE AS day,
    type,
    COUNT(*) AS messages
FROM logs
WHERE type IN ('user', 'assistant') AND timestamp IS NOT NULL
GROUP BY 1, 2
ORDER BY 1
```

```altair
alt.Chart(df).mark_line(point=True).encode(
    x="day:T",
    y="messages:Q",
    color=alt.Color("type:N", title="Message type"),
    tooltip=["day:T", "type:N", "messages:Q"]
).properties(title="Daily Activity — User Prompts vs Assistant Responses", width="container")
```

## Chart 2: Model Usage
question: Which models do I use most?
type: bar
x: message__model
y: count(*)
source: logs

```sql
SELECT
    message__model AS model,
    COUNT(*) AS responses
FROM logs
WHERE message__model IS NOT NULL
GROUP BY 1
ORDER BY responses DESC
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("responses:Q", title="Assistant responses"),
    y=alt.Y("model:N", sort="-x", title="Model"),
    tooltip=["model:N", "responses:Q"]
).properties(title="Assistant Responses by Model", width="container")
```

## Chart 3: Token Consumption by Model
question: How are tokens consumed across models (input/output/cache)?
type: stacked bar
x: message__model
y: sum(tokens) by token category
source: logs

```sql
SELECT model, category, SUM(tokens) AS tokens FROM (
    SELECT message__model AS model, 'input' AS category, message__usage__input_tokens AS tokens FROM logs
    UNION ALL
    SELECT message__model, 'output', message__usage__output_tokens FROM logs
    UNION ALL
    SELECT message__model, 'cache_read', message__usage__cache_read_input_tokens FROM logs
    UNION ALL
    SELECT message__model, 'cache_creation', message__usage__cache_creation_input_tokens FROM logs
) t
WHERE model IS NOT NULL AND tokens IS NOT NULL
GROUP BY 1, 2
ORDER BY 1
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("model:N", sort="-y", title="Model"),
    y=alt.Y("tokens:Q", title="Tokens", stack=True),
    color=alt.Color("category:N", title="Token type"),
    tooltip=["model:N", "category:N", "tokens:Q"]
).properties(title="Token Consumption by Model (input / output / cache)", width="container")
```

## Chart 4: Top Tools Called
question: Which tools does Claude call most often?
type: horizontal bar
x: count(*)
y: name
source: logs__message__content

```sql
SELECT
    name AS tool,
    COUNT(*) AS calls
FROM logs__message__content
WHERE type = 'tool_use' AND name IS NOT NULL
GROUP BY 1
ORDER BY calls DESC
LIMIT 15
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("calls:Q", title="Tool calls"),
    y=alt.Y("tool:N", sort="-x", title="Tool"),
    tooltip=["tool:N", "calls:Q"]
).properties(title="Top 15 Tools Called by Claude", width="container")
```

## Chart 5: Activity by Project
question: Which projects do I use Claude Code in most?
type: horizontal bar
x: count(*)
y: source_project
source: logs

```sql
SELECT
    source_project AS project,
    COUNT(*) AS assistant_responses
FROM logs
WHERE type = 'assistant'
GROUP BY 1
ORDER BY assistant_responses DESC
LIMIT 12
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("assistant_responses:Q", title="Assistant responses"),
    y=alt.Y("project:N", sort="-x", title="Project"),
    tooltip=["project:N", "assistant_responses:Q"]
).properties(title="Top Projects by Claude Code Activity", width="container")
```

## Chart 6: Activity by Hour of Day
question: What time of day am I most active?
type: bar
x: hour of day (UTC)
y: count of user prompts
source: logs

```sql
SELECT
    EXTRACT(HOUR FROM timestamp)::INT AS hour_utc,
    COUNT(*) AS prompts
FROM logs
WHERE type = 'user' AND timestamp IS NOT NULL
GROUP BY 1
ORDER BY 1
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("hour_utc:O", title="Hour of day (UTC)"),
    y=alt.Y("prompts:Q", title="User prompts"),
    tooltip=["hour_utc:O", "prompts:Q"]
).properties(title="When I Use Claude Code (Prompts by Hour, UTC)", width="container")
```

## Chart 7: Sessions Per Day
question: How many distinct sessions do I run per day?
type: line
x: timestamp (daily)
y: count(distinct source_session)
source: logs

```sql
SELECT
    DATE_TRUNC('day', timestamp)::DATE AS day,
    COUNT(DISTINCT source_session) AS sessions
FROM logs
WHERE timestamp IS NOT NULL
GROUP BY 1
ORDER BY 1
```

```altair
alt.Chart(df).mark_area(line=True, opacity=0.4).encode(
    x="day:T",
    y=alt.Y("sessions:Q", title="Distinct sessions"),
    tooltip=["day:T", "sessions:Q"]
).properties(title="Distinct Sessions Per Day", width="container")
```

## Chart 8: Daily Token Consumption Trend
question: How does daily token consumption trend over time?
type: stacked area
x: timestamp (daily)
y: sum(tokens) by category
source: logs

```sql
SELECT day, category, SUM(tokens) AS tokens FROM (
    SELECT DATE_TRUNC('day', timestamp)::DATE AS day, 'input' AS category, message__usage__input_tokens AS tokens FROM logs
    UNION ALL
    SELECT DATE_TRUNC('day', timestamp)::DATE, 'output', message__usage__output_tokens FROM logs
    UNION ALL
    SELECT DATE_TRUNC('day', timestamp)::DATE, 'cache_read', message__usage__cache_read_input_tokens FROM logs
    UNION ALL
    SELECT DATE_TRUNC('day', timestamp)::DATE, 'cache_creation', message__usage__cache_creation_input_tokens FROM logs
) t
WHERE day IS NOT NULL AND tokens IS NOT NULL
GROUP BY 1, 2
ORDER BY 1
```

```altair
alt.Chart(df).mark_area().encode(
    x="day:T",
    y=alt.Y("tokens:Q", title="Tokens", stack=True),
    color=alt.Color("category:N", title="Token type"),
    tooltip=["day:T", "category:N", "tokens:Q"]
).properties(title="Daily Token Consumption by Type", width="container")
```
