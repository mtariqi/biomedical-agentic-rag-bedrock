"""Export non-destructive relation-quality triage and review priority."""
import argparse
import csv
import json
from pathlib import Path

from app.relation_quality import triage_candidates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path,
                        default=Path("reports/evidence/phase6_2_relationships.json"))
    parser.add_argument("--output", type=Path,
                        default=Path("reports/evidence/phase6_3_1_quality.json"))
    args = parser.parse_args()
    original = json.loads(args.input.read_text(encoding="utf-8"))
    report = triage_candidates(original)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    csv_path = args.output.with_suffix(".csv")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "candidate_id", "pmid", "entity_a", "entity_b", "predicate_cue",
            "quality_review_priority", "quality_flags", "verbatim_excerpt",
        ])
        writer.writeheader()
        for c in report["candidates"]:
            writer.writerow({
                "candidate_id": c["candidate_id"], "pmid": c["pmid"],
                "entity_a": c["entity_a"], "entity_b": c["entity_b"],
                "predicate_cue": c["predicate_cue"],
                "quality_review_priority": c["quality_review_priority"],
                "quality_flags": ";".join(c["quality_flags"]),
                "verbatim_excerpt": c["verbatim_excerpt"],
            })
    print(f"Candidates retained: {report['candidate_count']}")
    print(f"Flagged for review: {report['flagged_candidate_count']}")
    print(f"JSON: {args.output}\nCSV: {csv_path}")
    print("No annotation templates or expert labels were modified.")


if __name__ == "__main__":
    main()
