# Q1. First trace

> The console exporter prints every finished span as a dictionary. Count the spans in the console output - each one is a separate ReadableSpan entry. How many spans does the trace produce?

It produces three spans: for rag, search and llm respectively. 

# Q2. Capturing metrics as span attributes

> Now re-run the query. How many input tokens do we see?

After running again the rag the total we seee that there are 7000 input tokens spent.

# Q3. Span timing

> For a typical query, roughly how long does the LLM call take?

After several runs it has been seen that it takes around 3 miliseconds, SO the answer is *Over 2000ms*. Example:

```json
{
    ...
    "start_time": "2026-07-18T16:28:40.805364Z",
    "end_time": "2026-07-18T16:28:43.143009Z",
    ...
}
```

That's the average, ocasionally there are lower than 2 seconds calls.

# Q4. Saving traces to SQLite

> Re-run the query from Q1. Which span names appear in the spans table?

There appear three:

```bash
sqlite> select * from spans;
╭────────┬─────────────────────┬─────────────────────┬──────────────┬───────────────┬──────╮
│  name  │     start_time      │      end_time       │ input_tokens │ output_tokens │ cost │
╞════════╪═════════════════════╪═════════════════════╪══════════════╪═══════════════╪══════╡
│ search │ 1784392740993625147 │ 1784392740995159831 │ NULL         │ NULL          │ NULL │
│ llm    │ 1784392741007035865 │ 1784392743896215278 │         7111 │           114 │ NULL │
│ rag    │ 1784392740993573127 │ 1784392743908150585 │ NULL         │ NULL          │ NULL │
╰────────┴─────────────────────┴─────────────────────┴──────────────┴───────────────┴──────╯
```

# Q5. Querying trace data

> Using SQL (or pandas), compute the total duration for each span name excluding rag. Which span type takes the most total time?

Querying several times , the most costful call is calling *llm*:

```bash
sqlite> SELECT name, (end_time - start_time) /  pow(10, 9) time_spent FROM spans where name in ('llm', 'search') ORDER BY time_spent DESC;
╭────────┬─────────────╮
│  name  │ time_spent  │
╞════════╪═════════════╡
│ llm    │ 4.092374174 │
│ llm    │ 2.889179413 │
│ llm    │ 2.486619404 │
│ llm    │ 1.912431709 │
│ search │ 0.001568076 │
│ search │ 0.001534684 │
│ search │ 0.001478244 │
│ search │ 0.001476576 │
╰────────┴─────────────╯
```

It makes sense as search is done with minsearch text search in RAM with small data, which will go lightning speed. llm calls are doing an HTTP API call which
most of the times is slower, plus the current cost of obtaining a generated repsonse from a LLM.

# Q6. Token stability across runs

> How much do the input tokens vary across 4 runs of the same query?

They are practically identical, 7111 tokens. The results can be seen in FifthExercise.ipynb

