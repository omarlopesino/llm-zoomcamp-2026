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
    # Agent Traces Usage Report

    20,000 agent-trace logs pulled from the `/logs` endpoint of the
    test traces API, loaded into DuckDB via a dlt `rest_api` pipeline.
    """)
    return


@app.cell
def _(dlt):
    pipeline = dlt.attach(
        "agent_traces",
        destination="warehouse",  # duckdb (dev) / motherduck (prod)
        dataset_name="agent_traces_data",
    )
    dataset = pipeline.dataset()
    return (dataset,)


@app.cell
def _(mo):
    mo.md("""
    ## Messages & models
    """)
    return


@app.cell
def _(dataset):
    df_chart1 = dataset("""
        SELECT type, COUNT(*) AS messages
        FROM logs
        GROUP BY 1
        ORDER BY messages DESC
    """).df()
    return (df_chart1,)


@app.cell
def _(alt, df_chart1):
    _chart = alt.Chart(df_chart1).mark_bar().encode(
        x=alt.X("messages:Q", title="Messages"),
        y=alt.Y("type:N", sort="-x", title="Type"),
        tooltip=["type:N", "messages:Q"],
    ).properties(title="Messages by Type", width="container")
    _chart
    return


@app.cell
def _(dataset):
    df_chart2 = dataset("""
        SELECT message__model AS model, COUNT(*) AS responses
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
    df_chart6 = dataset("""
        SELECT message__stop_reason AS stop_reason, COUNT(*) AS responses
        FROM logs
        WHERE message__stop_reason IS NOT NULL
        GROUP BY 1
        ORDER BY responses DESC
    """).df()
    return (df_chart6,)


@app.cell
def _(alt, df_chart6):
    _chart = alt.Chart(df_chart6).mark_bar().encode(
        x=alt.X("stop_reason:N", title="Stop reason"),
        y=alt.Y("responses:Q", title="Assistant responses"),
        tooltip=["stop_reason:N", "responses:Q"],
    ).properties(title="Assistant Stop Reasons", width="container")
    _chart
    return


@app.cell
def _(mo):
    mo.md("""
    ## Tokens
    """)
    return


@app.cell
def _(dataset):
    df_chart3 = dataset("""
        SELECT model, category, SUM(tokens) AS tokens FROM (
            SELECT message__model AS model, 'input' AS category, usage__input_tokens AS tokens FROM logs
            UNION ALL
            SELECT message__model, 'output', usage__output_tokens FROM logs
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
        title="Token Consumption by Model (input / output)",
        width="container",
    )
    _chart
    return


@app.cell
def _(mo):
    mo.md("""
    ## Tools, branches & sessions
    """)
    return


@app.cell
def _(dataset):
    df_chart4 = dataset("""
        SELECT name AS tool, COUNT(*) AS calls
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
    ).properties(title="Top Tools Called", width="container")
    _chart
    return


@app.cell
def _(dataset):
    df_chart5 = dataset("""
        SELECT git_branch AS branch, COUNT(*) AS messages
        FROM logs
        WHERE git_branch IS NOT NULL
        GROUP BY 1
        ORDER BY messages DESC
    """).df()
    return (df_chart5,)


@app.cell
def _(alt, df_chart5):
    _chart = alt.Chart(df_chart5).mark_bar().encode(
        x=alt.X("messages:Q", title="Messages"),
        y=alt.Y("branch:N", sort="-x", title="Git branch"),
        tooltip=["branch:N", "messages:Q"],
    ).properties(title="Activity by Git Branch", width="container")
    _chart
    return


@app.cell
def _(dataset):
    df_chart7 = dataset("""
        SELECT messages_in_session, COUNT(*) AS sessions FROM (
            SELECT session_id, COUNT(*) AS messages_in_session
            FROM logs
            WHERE session_id IS NOT NULL
            GROUP BY 1
        ) t
        GROUP BY 1
        ORDER BY 1
    """).df()
    return (df_chart7,)


@app.cell
def _(alt, df_chart7):
    _chart = alt.Chart(df_chart7).mark_bar().encode(
        x=alt.X("messages_in_session:O", title="Messages in session"),
        y=alt.Y("sessions:Q", title="Number of sessions"),
        tooltip=["messages_in_session:O", "sessions:Q"],
    ).properties(title="Distribution of Messages per Session", width="container")
    _chart
    return


@app.cell
def _(mo):
    mo.md("""
    ## Volume over time
    """)
    return


@app.cell
def _(dataset):
    df_chart8 = dataset("""
        SELECT DATE_TRUNC('hour', timestamp) AS hour, COUNT(*) AS logs
        FROM logs
        WHERE timestamp IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """).df()
    return (df_chart8,)


@app.cell
def _(alt, df_chart8):
    _chart = alt.Chart(df_chart8).mark_line(point=True).encode(
        x="hour:T",
        y=alt.Y("logs:Q", title="Logs"),
        tooltip=["hour:T", "logs:Q"],
    ).properties(title="Log Volume Over Time (Hourly)", width="container")
    _chart
    return


if __name__ == "__main__":
    app.run()
