"""Run multi-cutoff and RRF sensitivity benchmark with explicit EGFR audit."""
import argparse
import json
from pathlib import Path

from app.evidence_retrieval import load_evidence
from app.hybrid_retrieval import DEFAULT_MODEL, load_sentence_encoder
from app.phase5_robustness import run_robustness
from app.retrieval_benchmark import validate_judgments


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--judgments", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, default=None)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--output", type=Path, default=Path(
        "reports/evaluation/phase5_robustness.json"))
    args = parser.parse_args()
    records = load_evidence(args.corpus)
    judgments = json.loads(args.judgments.read_text(encoding="utf-8"))
    validate_judgments(judgments, {r["pmid"] for r in records})
    result = run_robustness(records, judgments, load_sentence_encoder(args.model))
    result["embedding_model"] = args.model
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for scenario, payload in result["evaluation"].items():
        print(f"\n{scenario}: {len(payload['methods']['bm25']['per_query'])} queries")
        if payload["excluded_no_positive_queries"]:
            print("  Excluded (no strict positive labels):",
                  payload["excluded_no_positive_queries"])
        for name, metrics in payload["methods"].items():
            print(f"  {name}:")
            for k in result["cutoffs"]:
                m = metrics["per_cutoff"][str(k)]
                print(f"    @{k}: recall={m['recall_at_k']:.3f} "
                      f"precision={m['precision_at_k']:.3f} "
                      f"MRR={m['reciprocal_rank_at_k']:.3f} "
                      f"nDCG={m['ndcg_at_k']:.3f}")
    print(f"\nSaved {len(result['rrf_sensitivity'])} RRF sensitivity rows to {args.output}")


if __name__ == "__main__":
    main()
