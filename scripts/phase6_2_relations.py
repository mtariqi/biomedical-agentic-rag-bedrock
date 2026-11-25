"""Extract auditable candidate relationships from Phase 6 JSON."""
import argparse
import csv
import json
from pathlib import Path

from app.evidence_retrieval import load_evidence
from app.relationship_extraction import extract_relationship_candidates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("reports/evidence/phase6_synthesis.json"))
    parser.add_argument("--corpus", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=Path("reports/evidence/phase6_2_relationships.json"))
    args = parser.parse_args()
    report = json.loads(args.input.read_text(encoding="utf-8"))
    corpus = {str(r["pmid"]): r["abstract"] for r in load_evidence(args.corpus)}
    # Reject altered or fabricated evidence before generating relationships.
    for item in report.get("evidence", []):
        pmid = str(item.get("pmid") or "")
        excerpt = str(item.get("verbatim_excerpt") or "")
        if pmid not in corpus or not excerpt or excerpt not in corpus[pmid]:
            raise ValueError(f"Source provenance failed for PMID {pmid}")
    output = extract_relationship_candidates(report)
    output["provenance_check"] = {
        "status": "passed", "checked_excerpts": len(report.get("evidence", []))
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    csv_path = args.output.with_suffix(".csv")
    fields = [
        "candidate_id", "pmid", "url", "evidence_id", "verbatim_excerpt",
        "entity_a", "entity_a_category", "entity_b", "entity_b_category",
        "predicate_cue", "direction", "relation_status", "causal_support",
        "verification_status", "context_class", "context_cues",
        "experimental_models_mentioned", "negation_cue_detected",
        "hedging_cue_detected", "study_design_verified",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in output["candidates"]:
            writer.writerow({
                key: json.dumps(item[key], ensure_ascii=False)
                if isinstance(item[key], (list, dict)) else item[key]
                for key in fields
            })
    print(f"Provenance PASS: {output['provenance_check']['checked_excerpts']} excerpts")
    print(f"Unverified relation candidates: {output['candidate_count']}")
    print(f"JSON: {args.output}\nCSV: {csv_path}")


if __name__ == "__main__":
    main()
