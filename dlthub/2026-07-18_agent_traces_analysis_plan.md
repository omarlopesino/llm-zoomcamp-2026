# Analysis Plan: agent_traces

## Connection
pipeline: agent_traces
dataset: (current default dataset via `pipeline.dataset()`)
destination: duckdb

## Profile Summary
| table | rows | key columns | notes |
|-------|------|-------------|-------|
| logs | 20,000 | type, timestamp, session_id, message__model, message__stop_reason, usage__input_tokens, usage__output_tokens, git_branch | 2,476 sessions; span 2026-01-01 → 01-02 (synthetic, uniform) |
| logs__message__content | 19,668 | type, name (tool when type='tool_use') | tool calls |

Source: `/logs` endpoint of the test traces API (20k of 1M available). Models evenly split across haiku-4-5, fable-5, opus-4-8, sonnet-5. Tokens: ~330M input, ~26M output. Branches: dev, fix/pagination, main, feat/standalone-in-process.

## Questions
1. [x] How do messages split between user and assistant? → Chart 1
2. [x] Which models appear most? → Chart 2
3. [x] How are tokens consumed across models? → Chart 3
4. [x] Which tools are called most? → Chart 4
5. [x] How is activity distributed across git branches? → Chart 5
6. [x] What are the assistant stop reasons? → Chart 6
7. [x] How many messages per session (distribution)? → Chart 7
8. [x] How does log volume trend over time (hourly)? → Chart 8

## Data Gaps
(none)

## Chart 1: Messages by Type
question: How do messages split between user and assistant?
type: bar
source: logs

```sql
SELECT type, COUNT(*) AS messages
FROM logs
GROUP BY 1
ORDER BY messages DESC
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("messages:Q", title="Messages"),
    y=alt.Y("type:N", sort="-x", title="Type"),
    tooltip=["type:N", "messages:Q"]
).properties(title="Messages by Type", width="container")
```

## Chart 2: Responses by Model
question: Which models appear most?
type: bar
source: logs

```sql
SELECT message__model AS model, COUNT(*) AS responses
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
question: How are tokens consumed across models?
type: stacked bar
source: logs

```sql
SELECT model, category, SUM(tokens) AS tokens FROM (
    SELECT message__model AS model, 'input' AS category, usage__input_tokens AS tokens FROM logs
    UNION ALL
    SELECT message__model, 'output', usage__output_tokens FROM logs
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
).properties(title="Token Consumption by Model (input / output)", width="container")
```

## Chart 4: Top Tools Called
question: Which tools are called most?
type: horizontal bar
source: logs__message__content

```sql
SELECT name AS tool, COUNT(*) AS calls
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
).properties(title="Top Tools Called", width="container")
```

## Chart 5: Activity by Git Branch
question: How is activity distributed across git branches?
type: horizontal bar
source: logs

```sql
SELECT git_branch AS branch, COUNT(*) AS messages
FROM logs
WHERE git_branch IS NOT NULL
GROUP BY 1
ORDER BY messages DESC
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("messages:Q", title="Messages"),
    y=alt.Y("branch:N", sort="-x", title="Git branch"),
    tooltip=["branch:N", "messages:Q"]
).properties(title="Activity by Git Branch", width="container")
```

## Chart 6: Assistant Stop Reasons
question: What are the assistant stop reasons?
type: bar
source: logs

```sql
SELECT message__stop_reason AS stop_reason, COUNT(*) AS responses
FROM logs
WHERE message__stop_reason IS NOT NULL
GROUP BY 1
ORDER BY responses DESC
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("stop_reason:N", title="Stop reason"),
    y=alt.Y("responses:Q", title="Assistant responses"),
    tooltip=["stop_reason:N", "responses:Q"]
).properties(title="Assistant Stop Reasons", width="container")
```

## Chart 7: Messages Per Session (Distribution)
question: How many messages per session?
type: bar (histogram)
source: logs

```sql
SELECT messages_in_session, COUNT(*) AS sessions FROM (
    SELECT session_id, COUNT(*) AS messages_in_session
    FROM logs
    WHERE session_id IS NOT NULL
    GROUP BY 1
) t
GROUP BY 1
ORDER BY 1
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("messages_in_session:O", title="Messages in session"),
    y=alt.Y("sessions:Q", title="Number of sessions"),
    tooltip=["messages_in_session:O", "sessions:Q"]
).properties(title="Distribution of Messages per Session", width="container")
```

## Chart 8: Log Volume Over Time (Hourly)
question: How does log volume trend over time?
type: line
source: logs

```sql
SELECT DATE_TRUNC('hour', timestamp) AS hour, COUNT(*) AS logs
FROM logs
WHERE timestamp IS NOT NULL
GROUP BY 1
ORDER BY 1
```

```altair
alt.Chart(df).mark_line(point=True).encode(
    x="hour:T",
    y=alt.Y("logs:Q", title="Logs"),
    tooltip=["hour:T", "logs:Q"]
).properties(title="Log Volume Over Time (Hourly)", width="container")
```
