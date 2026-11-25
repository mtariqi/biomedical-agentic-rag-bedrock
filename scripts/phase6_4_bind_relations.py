"""Run Phase 6.4 conservative binding with PMID/abstract provenance checks."""
import argparse
import csv
import json
from pathlib import Path

from app.biomedical_relation_binding import extract_bound_relations
from app.evidence_retrieval import load_evidence


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path,
                        default=Path("reports/evidence/phase6_synthesis.json"))
    parser.add_argument("--corpus", type=Path, default=None)
    parser.add_argument("--output", type=Path,
                        default=Path("reports/evidence/phase6_4_bound_relations.json"))
    args = parser.parse_args()
    synthesis = json.loads(args.input.read_text(encoding="utf-8"))
    corpus = {str(r["pmid"]): r["abstract"] for r in load_evidence(args.corpus)}
    for item in synthesis.get("evidence", []):
        pmid = str(item.get("pmid") or "")
        excerpt = str(item.get("verbatim_excerpt") or "")
        if pmid not in corpus or not excerpt or excerpt not in corpus[pmid]:
            raise ValueError(f"Source provenance failed for PMID {pmid}")
    report = extract_bound_relations(synthesis)
    report["provenance_check"] = {
        "status": "passed",
        "checked_excerpts": len(synthesis.get("evidence", [])),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    csv_path = args.output.with_suffix(".csv")
    fields = [
        "candidate_id", "pmid", "evidence_id", "subject", "predicate",
        "object", "rule", "text_span", "evidence_qualification",
        "contexts_mentioned", "tnbc_specific", "context_verified",
        "relation_status", "verbatim_excerpt",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in report["candidates"]:
            writer.writerow({
                key: json.dumps(row[key], ensure_ascii=False)
                if isinstance(row[key], (dict, list)) else row[key]
                for key in fields
            })
    print(f"Provenance PASS: {report['provenance_check']['checked_excerpts']} excerpts")
    print(f"Textually bound candidates (unverified): {report['candidate_count']}")
    print(f"JSON: {args.output}\nCSV: {csv_path}")
    print("Original Phase 6.2 and Phase 6.3 outputs were not modified.")


if __name__ == "__main__":
    main()
