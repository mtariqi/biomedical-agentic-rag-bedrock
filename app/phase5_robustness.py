"""Phase 5 robustness analyses; evaluation labels are never silently altered.

All variants use a shared semantic index and query embeddings. Parameter sweeps
are descriptive sensitivity checks, not tuned held-out performance estimates.
"""
from __future__ import annotations

from collections import defaultdict
from .evidence_retrieval import BM25Retriever
from .hybrid_retrieval import SemanticRetriever, reciprocal_rank_fusion
from .retrieval_benchmark import rank_metrics, validate_judgments

EGFR_QUERY = "EGFR signaling and resistance to targeted therapy in TNBC"
BORDERLINE_PMID = "28653902"
CUTOFFS = (1, 3, 5, 10)
RRF_CONSTANTS = (10, 30, 60, 100)
CANDIDATE_POOLS = (5, 10, 20, 40)


def label_scenarios(judgments: list[dict]) -> dict[str, dict]:
    """Strict EGFR case is unjudged for recall, rather than falsely 0."""
    baseline = [{"query": j["query"], "relevant_pmids": list(j["relevant_pmids"])}
                for j in judgments]
    strict = [{"query": j["query"], "relevant_pmids": [
        p for p in j["relevant_pmids"] if not (
            j["query"] == EGFR_QUERY and str(p) == BORDERLINE_PMID
        )
    ]} for j in judgments]
    excluded = [j["query"] for j in strict if not j["relevant_pmids"]]
    strict = [j for j in strict if j["relevant_pmids"]]
    return {
        "original_broad_rtk": {
            "judgments": baseline, "excluded_no_positive_queries": [],
            "interpretation": "Original provisional AI-assisted labels; EGFR-specificity unresolved",
        },
        "strict_egfr": {
            "judgments": strict, "excluded_no_positive_queries": excluded,
            "interpretation": "PMID 28653902 not EGFR-specific in abstract; no-positive queries excluded from recall/nDCG aggregation",
        },
    }


def _score_rankings(judgments: list[dict], rankings: dict[str, list[dict]],
                    cutoffs: tuple[int, ...]) -> dict:
    if not judgments:
        return {"queries": 0, "per_cutoff": {}, "per_query": []}
    rows = []
    for j in judgments:
        relevant = {str(p) for p in j["relevant_pmids"]}
        query = j["query"]
        row = {"query": query, "relevant_pmids": sorted(relevant),
               "retrieved_pmids": [str(h["pmid"]) for h in rankings[query]],
               "cutoffs": {str(k): rank_metrics(rankings[query], relevant, k)
                           for k in cutoffs}}
        rows.append(row)
    means = {}
    for k in cutoffs:
        metrics = [r["cutoffs"][str(k)] for r in rows]
        means[str(k)] = {
            metric: sum(r[metric] for r in metrics) / len(metrics)
            for metric in ("recall_at_k", "precision_at_k",
                           "reciprocal_rank_at_k", "ndcg_at_k")
        }
    return {"queries": len(rows), "per_cutoff": means, "per_query": rows}


def run_robustness(
    records: list[dict], judgments: list[dict], encoder,
    cutoffs: tuple[int, ...] = CUTOFFS,
    constants: tuple[int, ...] = RRF_CONSTANTS,
    candidate_pools: tuple[int, ...] = CANDIDATE_POOLS,
) -> dict:
    validate_judgments(judgments, {str(r["pmid"]) for r in records})
    if not cutoffs or any(k < 1 for k in cutoffs):
        raise ValueError("cutoffs must be positive")
    if not constants or any(c < 1 for c in constants):
        raise ValueError("RRF constants must be positive")
    if not candidate_pools or any(n < 1 for n in candidate_pools):
        raise ValueError("candidate pools must be positive")

    max_k = max(cutoffs)
    max_candidates = max(max_k, max(candidate_pools))
    bm25 = BM25Retriever(records)
    semantic = SemanticRetriever(records, encoder)
    # Encode each query once, and reuse all candidate rankings in every variant.
    queries = [j["query"] for j in judgments]
    lexical_lists = {q: bm25.search(q, max_candidates) for q in queries}
    semantic_lists = {q: semantic.search(q, max_candidates) for q in queries}
    for q in queries:
        for hit in lexical_lists[q]:
            hit["retriever"] = "bm25"
        for hit in semantic_lists[q]:
            hit["retriever"] = "semantic"

    def fuse(q: str, constant: int, pool: int) -> list[dict]:
        return reciprocal_rank_fusion(
            [lexical_lists[q][:pool], semantic_lists[q][:pool]],
            k=constant, limit=max_k,
        )

    # Note: max_k may exceed pool; this is intentional and transparent.
    base_pool = 20
    base_constant = 60
    rankings = {
        "bm25": {q: lexical_lists[q][:max_k] for q in queries},
        "semantic": {q: semantic_lists[q][:max_k] for q in queries},
        "hybrid_rrf_baseline": {
            q: fuse(q, base_constant, base_pool) for q in queries
        },
    }
    scenarios = label_scenarios(judgments)
    evaluation = {}
    for scenario_name, scenario in scenarios.items():
        evaluation[scenario_name] = {
            "interpretation": scenario["interpretation"],
            "excluded_no_positive_queries": scenario["excluded_no_positive_queries"],
            "methods": {
                name: _score_rankings(scenario["judgments"], method_rankings, cutoffs)
                for name, method_rankings in rankings.items()
            },
        }

    sensitivity = []
    for constant in constants:
        for pool in candidate_pools:
            fused = {q: fuse(q, constant, pool) for q in queries}
            for scenario_name, scenario in scenarios.items():
                scored = _score_rankings(scenario["judgments"], fused, cutoffs)
                sensitivity.append({
                    "scenario": scenario_name, "rrf_constant": constant,
                    "candidate_pool": pool, "queries": scored["queries"],
                    "per_cutoff": scored["per_cutoff"],
                    "is_original_configuration": constant == 60 and pool == 20,
                })
    return {
        "corpus_size": len(records), "query_count": len(queries),
        "cutoffs": list(cutoffs), "rrf_constants": list(constants),
        "candidate_pools": list(candidate_pools),
        "baseline_rrf_constant": base_constant,
        "baseline_candidate_pool": base_pool,
        "audit": {
            "pmid": BORDERLINE_PMID, "query": EGFR_QUERY,
            "finding": "TNBC RTK-inhibitor resistance/NF-kappa-B review; abstract does not name EGFR",
            "original_label": 1,
            "strict_egfr_label": "not established from abstract",
            "adjudication": "expert/full-text verification required",
        },
        "evaluation": evaluation, "rrf_sensitivity": sensitivity,
        "caution": "AI-assisted labels, small corpus and five queries; descriptive sensitivity, not external validation",
    }
