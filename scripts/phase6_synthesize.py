"""Run Phase 6 auditable TNBC evidence synthesis with existing hybrid retrieval."""
import argparse
import csv
import json
from pathlib import Path

from app.evidence_retrieval import load_evidence
from app.hybrid_retrieval import DEFAULT_MODEL, HybridRetriever, load_sentence_encoder
from app.evidence_synthesis import synthesize_evidence, summarize_mentions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--candidate-k", type=int, default=20)
    parser.add_argument("--max-sentences", type=int, default=4)
    parser.add_argument("--corpus", type=Path, default=None)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--output", type=Path, default=Path("reports/evidence/phase6_synthesis.json"))
    args = parser.parse_args()
    records = load_evidence(args.corpus)
    if not records:
        raise ValueError("No valid PubMed abstracts in QC corpus")
    retriever = HybridRetriever(records, load_sentence_encoder(args.model))
    result = retriever.search(args.query, k=args.k, candidate_k=args.candidate_k)
    report = synthesize_evidence(result["hits"], args.query, args.max_sentences)
    report["retrieval_method"] = result["retrieval_method"]
    report["retrieval_configuration"] = {
        "embedding_model": args.model, "rrf_constant": 60,
        "candidate_pool": max(args.k, args.candidate_k),
        "top_k": args.k,
    }
    report["entity_mention_index"] = summarize_mentions(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    csv_path = args.output.with_suffix(".csv")
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        fields = ["evidence_id", "pmid", "url", "sentence_index",
                  "verbatim_excerpt", "entities_mentioned",
                  "experimental_language_detected", "relationship_status",
                  "causal_support", "evidence_status"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in report["evidence"]:
            writer.writerow({
                key: json.dumps(row[key], ensure_ascii=False)
                if isinstance(row[key], (dict, list)) else row[key]
                for key in fields
            })
    print(f"Sources: {report['source_count']}; reviewable sentences: "
          f"{report['evidence_sentence_count']}")
    print(f"JSON: {args.output}\nCSV: {csv_path}")
    print("Evidence status: requires human review; no causal claims asserted")


if __name__ == "__main__":
    main()
