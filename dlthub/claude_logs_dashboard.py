import marimo

__generated_with = "0.23.13"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import altair as alt
    import dlt

    return alt, dlt, mo


@app.cell
def _(mo):
    mo.md("""
    # Claude Code Usage Report

    Detailed usage across all local Claude Code sessions
    (`~/.claude/projects/**/*.jsonl`, omarlopesino excluded),
    spanning **2026-06-21 → 2026-07-18**.
    """)
    return


@app.cell
def _(dlt):
    pipeline = dlt.attach("claude_logs")
    dataset = pipeline.dataset()
    return (dataset,)


@app.cell
def _(mo):
    mo.md("""
    ## Activity over time
    """)
    return


@app.cell
def _(dataset):
    df_chart1 = dataset("""
        SELECT
            DATE_TRUNC('day', timestamp)::DATE AS day,
            type,
            COUNT(*) AS messages
        FROM logs
        WHERE type IN ('user', 'assistant') AND timestamp IS NOT NULL
        GROUP BY 1, 2
        ORDER BY 1
    """).df()
    return (df_chart1,)


@app.cell
def _(alt, df_chart1):
    _chart = alt.Chart(df_chart1).mark_line(point=True).encode(
        x="day:T",
        y="messages:Q",
        color=alt.Color("type:N", title="Message type"),
        tooltip=["day:T", "type:N", "messages:Q"],
    ).properties(
        title="Daily Activity — User Prompts vs Assistant Responses",
        width="container",
    )
    _chart
    return


@app.cell
def _(dataset):
    df_chart7 = dataset("""
        SELECT
            DATE_TRUNC('day', timestamp)::DATE AS day,
            COUNT(DISTINCT source_session) AS sessions
        FROM logs
        WHERE timestamp IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """).df()
    return (df_chart7,)


@app.cell
def _(alt, df_chart7):
    _chart = alt.Chart(df_chart7).mark_area(line=True, opacity=0.4).encode(
        x="day:T",
        y=alt.Y("sessions:Q", title="Distinct sessions"),
        tooltip=["day:T", "sessions:Q"],
    ).properties(title="Distinct Sessions Per Day", width="container")
    _chart
    return


@app.cell
def _(dataset):
    df_chart6 = dataset("""
        SELECT
            EXTRACT(HOUR FROM timestamp)::INT AS hour_utc,
            COUNT(*) AS prompts
        FROM logs
        WHERE type = 'user' AND timestamp IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """).df()
    return (df_chart6,)


@app.cell
def _(alt, df_chart6):
    _chart = alt.Chart(df_chart6).mark_bar().encode(
        x=alt.X("hour_utc:O", title="Hour of day (UTC)"),
        y=alt.Y("prompts:Q", title="User prompts"),
        tooltip=["hour_utc:O", "prompts:Q"],
    ).properties(
        title="When I Use Claude Code (Prompts by Hour, UTC)",
        width="container",
    )
    _chart
    return


@app.cell
def _(mo):
    mo.md("""
    ## Models & tokens
    """)
    return


@app.cell
def _(dataset):
    df_chart2 = dataset("""
        SELECT
            message__model AS model,
            COUNT(*) AS responses
        FROM logs
        WHERE message__model IS NOT NULL
        GROUP BY 1
        ORDER BY responses DESC
    """).df()
    return (df_chart2,)


@app.cell
def _(alt, df_chart2):
    _chart = alt.Chart(df_chart2).mark_bar().encode(
        x=alt.X("responses:Q", title="Assistant responses"),
        y=alt.Y("model:N", sort="-x", title="Model"),
        tooltip=["model:N", "responses:Q"],
    ).properties(title="Assistant Responses by Model", width="container")
    _chart
    return


@app.cell
def _(dataset):
    df_chart3 = dataset("""
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
    """).df()
    return (df_chart3,)


@app.cell
def _(alt, df_chart3):
    _chart = alt.Chart(df_chart3).mark_bar().encode(
        x=alt.X("model:N", sort="-y", title="Model"),
        y=alt.Y("tokens:Q", title="Tokens", stack=True),
        color=alt.Color("category:N", title="Token type"),
        tooltip=["model:N", "category:N", "tokens:Q"],
    ).properties(
        title="Token Consumption by Model (input / output / cache)",
        width="container",
    )
    _chart
    return


@app.cell
def _(dataset):
    df_chart8 = dataset("""
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
    """).df()
    return (df_chart8,)


@app.cell
def _(alt, df_chart8):
    _chart = alt.Chart(df_chart8).mark_area().encode(
        x="day:T",
        y=alt.Y("tokens:Q", title="Tokens", stack=True),
        color=alt.Color("category:N", title="Token type"),
        tooltip=["day:T", "category:N", "tokens:Q"],
    ).properties(title="Daily Token Consumption by Type", width="container")
    _chart
    return


@app.cell
def _(mo):
    mo.md("""
    ## Tools & projects
    """)
    return


@app.cell
def _(dataset):
    df_chart4 = dataset("""
        SELECT
            name AS tool,
            COUNT(*) AS calls
        FROM logs__message__content
        WHERE type = 'tool_use' AND name IS NOT NULL
        GROUP BY 1
        ORDER BY calls DESC
        LIMIT 15
    """).df()
    return (df_chart4,)


@app.cell
def _(alt, df_chart4):
    _chart = alt.Chart(df_chart4).mark_bar().encode(
        x=alt.X("calls:Q", title="Tool calls"),
        y=alt.Y("tool:N", sort="-x", title="Tool"),
        tooltip=["tool:N", "calls:Q"],
    ).properties(title="Top 15 Tools Called by Claude", width="container")
    _chart
    return


@app.cell
def _(dataset):
    df_chart5 = dataset("""
        SELECT
            source_project AS project,
            COUNT(*) AS assistant_responses
        FROM logs
        WHERE type = 'assistant'
        GROUP BY 1
        ORDER BY assistant_responses DESC
        LIMIT 12
    """).df()
    return (df_chart5,)


@app.cell
def _(alt, df_chart5):
    _chart = alt.Chart(df_chart5).mark_bar().encode(
        x=alt.X("assistant_responses:Q", title="Assistant responses"),
        y=alt.Y("project:N", sort="-x", title="Project"),
        tooltip=["project:N", "assistant_responses:Q"],
    ).properties(title="Top Projects by Claude Code Activity", width="container")
    _chart
    return


if __name__ == "__main__":
    app.run()
