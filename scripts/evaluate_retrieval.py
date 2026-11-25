"""Evaluate PMID retrieval with manually curated query relevance judgments.

Usage:
  python scripts/evaluate_retrieval.py --judgments data/processed/relevance_judgments.json
JSON format:
  [{"query": "SRC TNBC resistance", "relevant_pmids": ["39390250"]}]
No default relevance labels are fabricated.
"""
import argparse
import json
from pathlib import Path

from app.evidence_retrieval import BM25Retriever, load_evidence


def evaluate(judgments: list[dict], retriever: BM25Retriever, k: int = 5) -> dict:
    if not judgments:
        raise ValueError("At least one judged query is required")
    rows = []
    for item in judgments:
        query = str(item["query"])
        relevant = {str(p) for p in item["relevant_pmids"]}
        if not relevant:
            raise ValueError(f"No relevance labels for query: {query}")
        hits = retriever.search(query, k)
        retrieved = [hit["pmid"] for hit in hits]
        positions = [i for i, pmid in enumerate(retrieved, 1) if pmid in relevant]
        rows.append({
            "query": query,
            "relevant_pmids": sorted(relevant),
            "retrieved_pmids": retrieved,
            "recall_at_k": len(positions) / len(relevant),
            "precision_at_k": len(positions) / k,
            "reciprocal_rank_at_k": 1 / min(positions) if positions else 0.0,
        })
    return {
        "k": k,
        "queries": len(rows),
        "mean_recall_at_k": sum(r["recall_at_k"] for r in rows) / len(rows),
        "mean_precision_at_k": sum(r["precision_at_k"] for r in rows) / len(rows),
        "mrr_at_k": sum(r["reciprocal_rank_at_k"] for r in rows) / len(rows),
        "per_query": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--judgments", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, default=None)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--output", type=Path, default=Path("reports/evaluation/bm25_metrics.json"))
    args = parser.parse_args()
    judgments = json.loads(args.judgments.read_text(encoding="utf-8"))
    result = evaluate(judgments, BM25Retriever(load_evidence(args.corpus)), args.k)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
