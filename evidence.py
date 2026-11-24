"""Prepare the small evidence table used by the app and walkthrough."""

from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent / "data"


def load_evidence(data_dir=DATA):
    rows = pd.read_csv(data_dir / "evidence.csv", dtype="string")
    sources = pd.read_csv(data_dir / "sources.csv", dtype="string")

    for column in rows.columns:
        rows[column] = rows[column].str.strip().replace("", pd.NA)
    for column in ("record_id", "source_id", "topic", "status"):
        rows[column] = rows[column].str.casefold()
    sources["source_id"] = sources["source_id"].str.strip().str.casefold()

    if rows["record_id"].isna().any() or sources["source_id"].isna().any():
        raise ValueError("Evidence record IDs and source table IDs are required")

    before = len(rows)
    rows = rows.drop_duplicates()
    if rows["record_id"].duplicated().any():
        raise ValueError("Conflicting evidence rows share a record ID")

    # Keep unmatched records visible so a broken join is easy to spot.
    evidence = rows.merge(sources, on="source_id", how="left", validate="many_to_one")
    evidence["published"] = pd.to_datetime(
        evidence["published"], format="%Y-%m-%d", errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    evidence = evidence.sort_values("record_id").reset_index(drop=True)
    return evidence, {"input_rows": before, "duplicates": before - len(evidence)}


def search(evidence, query="", topic=""):
    if topic:
        evidence = evidence.loc[evidence["topic"].eq(topic.casefold())]
    if evidence.empty:
        return []
    if query.strip():
        query = query.strip().casefold()
        fields = evidence[["title", "observation", "publisher", "source_ref"]]
        matches = fields.fillna("").apply(
            lambda column: column.str.casefold().str.contains(query, regex=False)
        )
        evidence = evidence.loc[matches.any(axis=1)]
    # Pandas missing values become JSON null rather than guessed values.
    return evidence.astype(object).where(evidence.notna(), None).to_dict("records")
