"""Run this from the repo to see what each data cleanup step buys you."""

import pandas as pd

from evidence import DATA, load_evidence, search


def main():
    raw = pd.read_csv(DATA / "evidence.csv", dtype="string")
    print("1. Inspect the raw IDs and topics")
    print(raw[["record_id", "topic"]].to_string(index=False))

    evidence, summary = load_evidence()
    print("\n2. Normalize IDs, drop repeats, and attach sources")
    print(f"{summary['input_rows']} input rows -> {len(evidence)} records")
    print(evidence[["record_id", "source_ref", "published"]].to_string(index=False))

    print("\n3. Count topics without ignoring missing labels")
    print(evidence.groupby("topic", dropna=False).size().to_string())

    print("\n4. Look up an observation and trace its source")
    for record in search(evidence, "refill"):
        print(f"{record['title']} | {record['publisher']} | {record['source_ref']}")


if __name__ == "__main__":
    main()
