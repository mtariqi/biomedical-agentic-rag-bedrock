"""Export reviewable PMID evidence rows from the existing QC corpus."""
import argparse
import csv
import json
from pathlib import Path

from app.evidence_retrieval import BM25Retriever, load_evidence
from app.evidence_export import evidence_rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--corpus", type=Path, default=None)
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--output", type=Path, default=Path("reports/evidence/tnbc_kinase_evidence.csv"))
    args = parser.parse_args()
    hits = BM25Retriever(load_evidence(args.corpus)).search(args.query, k=args.k)
    rows = evidence_rows(hits)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["pmid", "url", "title", "year", "journal", "rank",
              "detected_terms_not_verified_entities", "verbatim_abstract_excerpts",
              "evidence_status", "study_design", "causal_support"]
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(row[key], ensure_ascii=False)
                             if isinstance(row[key], list) else row[key] for key in fields})
    print(f"Exported {len(rows)} unverified evidence candidates to {args.output}")


if __name__ == "__main__":
    main()
