"""Auditable comparative evaluation for PMID retrieval.

Judgments must be expert-authored; no synthetic labels or pseudo-ground-truth.
"""
from __future__ import annotations

import math
from collections.abc import Callable

from .evidence_retrieval import BM25Retriever
from .hybrid_retrieval import HybridRetriever, SemanticRetriever


def validate_judgments(judgments: list[dict], corpus_pmids: set[str]) -> None:
    if not isinstance(judgments, list) or not judgments:
        raise ValueError("Provide a nonempty list of expert-curated judgments")
    seen = set()
    for item in judgments:
        if not isinstance(item, dict):
            raise ValueError("Each judgment must be an object")
        query = item.get("query")
        labels = item.get("relevant_pmids")
        if not isinstance(query, str) or not query.strip() or query in seen:
            raise ValueError("Judgment queries must be unique nonempty strings")
        seen.add(query)
        if not isinstance(labels, list) or not labels:
            raise ValueError(f"Query {query!r} needs nonempty relevant_pmids")
        if any(not str(p).isdigit() for p in labels):
            raise ValueError(f"Query {query!r} contains invalid PMID")
        if len({str(p) for p in labels}) != len(labels):
            raise ValueError(f"Query {query!r} has duplicate relevance labels")
        unknown = {str(p) for p in labels} - corpus_pmids
        if unknown:
            raise ValueError(
                f"Judged PMID(s) not in QC corpus for {query!r}: {sorted(unknown)}"
            )


def rank_metrics(hits: list[dict], relevant: set[str], k: int) -> dict:
    if k < 1 or not relevant:
        raise ValueError("k and relevant PMIDs must be nonempty")
    ranked = [str(hit["pmid"]) for hit in hits[:k]]
    if len(set(ranked)) != len(ranked):
        raise ValueError("Retrieved PMID list contains duplicates")
    indicators = [int(p in relevant) for p in ranked]
    hits_count = sum(indicators)
    rr = next((1 / i for i, value in enumerate(indicators, 1) if value), 0.0)
    dcg = sum(value / math.log2(i + 1) for i, value in enumerate(indicators, 1))
    ideal = sum(1 / math.log2(i + 1) for i in range(1, min(k, len(relevant)) + 1))
    return {
        "recall_at_k": hits_count / len(relevant),
        "precision_at_k": hits_count / k,
        "reciprocal_rank_at_k": rr,
        "ndcg_at_k": dcg / ideal,
    }


def benchmark(
    records: list[dict], judgments: list[dict], encoder, k: int = 5,
    candidate_k: int = 20
) -> dict:
    if k < 1 or candidate_k < 1:
        raise ValueError("k and candidate_k must be positive")
    validate_judgments(judgments, {r["pmid"] for r in records})
    lexical = BM25Retriever(records)
    semantic = SemanticRetriever(records, encoder)
    hybrid = HybridRetriever.__new__(HybridRetriever)
    hybrid.lexical, hybrid.semantic = lexical, semantic
    methods: dict[str, Callable[[str], list[dict]]] = {
        "bm25": lambda q: lexical.search(q, k),
        "semantic": lambda q: semantic.search(q, k),
        "hybrid_rrf": lambda q: hybrid.search(q, k=k, candidate_k=candidate_k)["hits"],
    }
    output = {}
    for name, search in methods.items():
        rows = []
        for item in judgments:
            query = item["query"]
            relevant = {str(p) for p in item["relevant_pmids"]}
            hits = search(query)
            metrics = rank_metrics(hits, relevant, k)
            rows.append({
                "query": query, "relevant_pmids": sorted(relevant),
                "retrieved_pmids": [str(h["pmid"]) for h in hits],
                **metrics,
            })
        output[name] = {
            "queries": len(rows),
            "mean_recall_at_k": sum(r["recall_at_k"] for r in rows) / len(rows),
            "mean_precision_at_k": sum(r["precision_at_k"] for r in rows) / len(rows),
            "mrr_at_k": sum(r["reciprocal_rank_at_k"] for r in rows) / len(rows),
            "mean_ndcg_at_k": sum(r["ndcg_at_k"] for r in rows) / len(rows),
            "per_query": rows,
        }
    return {
        "k": k, "candidate_k": max(k, candidate_k),
        "judgment_status": "expert_curated_required",
        "retrieval_methods": output,
    }
