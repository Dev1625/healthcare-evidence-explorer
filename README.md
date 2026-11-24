# Healthcare Evidence Explorer

A small tool for a question that comes up when reading about healthcare workflows: where did this observation come from? Search a set of evidence records, filter by topic, and open the source details behind each record.

This is a portfolio demo built with AI assistance. The organizations, source documents, and observations in `data/` are fictional. The demo uses two CSV files so the raw data and cleaning steps are easy to inspect.

## Run it

Use Python 3.11 or newer. From the repo root, run:

```sh
python -m venv .venv
# macOS / Linux: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:8000`. Search for `refill` and inspect its source to see how the UI handles an unavailable publication date. Search for `Forest County` and select **Referrals** to filter by publisher and topic together.

## Pandas walkthrough

Run `python walkthrough.py` to see the raw labels, cleaned record count, joined sources, and grouped topics. The actual transformations live in [evidence.py](evidence.py).

| Step | What the code does |
| --- | --- |
| Read | Load separate observation and source tables as strings so IDs keep their format. |
| Normalize | Strip whitespace and case-fold record IDs, source IDs, topics, and statuses. Two differently formatted copies of `ev-02` now match. |
| Deduplicate | Drop identical normalized rows. Fail when the same record ID has conflicting content. |
| Join | Left-join source details on `source_id` and validate the many-to-one relationship. Unmatched observations stay visible. |
| Keep missing values | Parse dates to ISO format. Missing values reach the UI as JSON `null` and display as `Not recorded`. |

## API and frontend

`app.py` loads the cleaned data at startup. `GET /api/evidence` returns `records`, `topics`, and a dataset `summary`. The optional `q` parameter searches titles, observations, publishers, and document IDs. The optional `topic` parameter filters a normalized topic. Search matches literal text.

```text
GET /api/evidence?topic=medication+access&q=refill
```

The frontend in `static/` uses the Fetch API and renders the result list and source metadata. It needs no Node build or API keys.

Run `python -m unittest discover -s tests -v` to check the cleanup rules and hit the API over a local HTTP connection.

## Trade-offs

The demo loads a fixed dataset into memory and is intended to run locally. A larger version would need persistent storage and pagination. The source details expose provenance and missing fields, with evidence strength left to the reader.
