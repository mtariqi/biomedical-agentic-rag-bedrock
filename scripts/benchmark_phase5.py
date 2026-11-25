"""Compare three retrieval strategies with externally curated relevance labels.

Run as python -m scripts.benchmark_phase5 ...
"""
import argparse
import json
from pathlib import Path

from app.evidence_retrieval import load_evidence
from app.hybrid_retrieval import DEFAULT_MODEL, load_sentence_encoder
from app.retrieval_benchmark import benchmark


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--judgments", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, default=None)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--candidate-k", type=int, default=20)
    parser.add_argument("--output", type=Path, default=Path("reports/evaluation/phase5_comparison.json"))
    args = parser.parse_args()
    records = load_evidence(args.corpus)
    judgments = json.loads(args.judgments.read_text(encoding="utf-8"))
    # Validate before loading a potentially large model.
    from app.retrieval_benchmark import validate_judgments
    validate_judgments(judgments, {r["pmid"] for r in records})
    report = benchmark(records, judgments, load_sentence_encoder(args.model),
                       k=args.k, candidate_k=args.candidate_k)
    report["embedding_model"] = args.model
    report["corpus_size"] = len(records)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({name: {k: v for k, v in metrics.items() if k != "per_query"}
                      for name, metrics in report["retrieval_methods"].items()}, indent=2))


if __name__ == "__main__":
    main()
