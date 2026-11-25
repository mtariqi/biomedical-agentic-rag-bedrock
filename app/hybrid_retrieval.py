"""Phase 4: PMID-grounded BM25 + real sentence embedding retrieval with RRF.

The semantic model is optional and loaded only when hybrid search is requested.
This module never uses the demo SHA embeddings or invents scientific claims.
"""
from __future__ import annotations

from typing import Protocol
import numpy as np

from .evidence_retrieval import BM25Retriever, load_evidence

DEFAULT_MODEL = "pritamdeka/S-PubMedBert-MS-MARCO"


class Encoder(Protocol):
    def encode(self, sentences, **kwargs): ...


def load_sentence_encoder(model_name: str = DEFAULT_MODEL) -> Encoder:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "Real semantic retrieval requires sentence-transformers. "
            "Install: pip install -r requirements-semantic.txt"
        ) from exc
    return SentenceTransformer(model_name)


def _normalized_vectors(vectors, count: int) -> np.ndarray:
    array = np.asarray(vectors, dtype=np.float32)
    if array.ndim != 2 or array.shape[0] != count:
        raise ValueError("Encoder returned invalid vector dimensions")
    if not np.isfinite(array).all():
        raise ValueError("Encoder returned non-finite vectors")
    norms = np.linalg.norm(array, axis=1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError("Encoder returned zero-length vectors")
    return array / norms


class SemanticRetriever:
    """In-memory cosine search over the existing QC abstracts; no FAISS rebuild."""

    def __init__(self, records: list[dict], encoder: Encoder):
        self.records = records
        self.encoder = encoder
        self.vectors = None
        if records:
            texts = [
                f"{r['title']}. {r['abstract']}" for r in records
            ]
            self.vectors = _normalized_vectors(
                encoder.encode(texts, show_progress_bar=False), len(records)
            )

    def search(self, query: str, k: int = 5) -> list[dict]:
        if k < 1:
            raise ValueError("k must be positive")
        if not query.strip() or not self.records:
            return []
        query_vector = _normalized_vectors(
            self.encoder.encode([query], show_progress_bar=False), 1
        )
        if query_vector.shape[1] != self.vectors.shape[1]:
            raise ValueError("Query and document embedding dimensions differ")
        scores = self.vectors @ query_vector[0]
        order = sorted(
            range(len(self.records)),
            key=lambda i: (-float(scores[i]), self.records[i]["pmid"]),
        )
        return [
            {"rank": rank, "score": round(float(scores[i]), 6), **self.records[i]}
            for rank, i in enumerate(order[:k], start=1)
        ]


def reciprocal_rank_fusion(
    rankings: list[list[dict]], k: int = 60, limit: int = 5
) -> list[dict]:
    """Deduplicate by PMID and combine ranked lists (not raw incomparable scores)."""
    if k < 1 or limit < 1:
        raise ValueError("k and limit must be positive")
    fused: dict[str, dict] = {}
    for ranking in rankings:
        seen_in_ranking = set()
        for rank, hit in enumerate(ranking, start=1):
            pmid = str(hit.get("pmid") or "")
            if not pmid.isdigit() or pmid in seen_in_ranking:
                continue
            seen_in_ranking.add(pmid)
            if pmid not in fused:
                fused[pmid] = {
                    key: value for key, value in hit.items()
                    if key not in ("rank", "score")
                }
                fused[pmid]["fusion_score"] = 0.0
                fused[pmid]["retrievers"] = []
            fused[pmid]["fusion_score"] += 1 / (k + rank)
            if hit.get("retriever") and hit["retriever"] not in fused[pmid]["retrievers"]:
                fused[pmid]["retrievers"].append(hit["retriever"])
    ordered = sorted(
        fused.values(), key=lambda hit: (-hit["fusion_score"], hit["pmid"])
    )
    return [
        {"rank": rank, **{**hit, "fusion_score": round(hit["fusion_score"], 8)}}
        for rank, hit in enumerate(ordered[:limit], start=1)
    ]


class HybridRetriever:
    def __init__(self, records: list[dict], encoder: Encoder):
        self.lexical = BM25Retriever(records)
        self.semantic = SemanticRetriever(records, encoder)

    def search(self, query: str, k: int = 5, candidate_k: int = 20) -> dict:
        if k < 1 or candidate_k < 1:
            raise ValueError("k and candidate_k must be positive")
        candidate_k = max(k, candidate_k)
        bm25 = self.lexical.search(query, candidate_k)
        semantic = self.semantic.search(query, candidate_k)
        for hit in bm25:
            hit["retriever"] = "bm25"
        for hit in semantic:
            hit["retriever"] = "semantic"
        fused = reciprocal_rank_fusion([bm25, semantic], limit=k)
        return {
            "question": query,
            "retrieval_method": "bm25_semantic_rrf",
            "evidence_status": "retrieved_not_verified",
            "hits": fused,
            "hit_count": len(fused),
        }


def retrieve_hybrid(
    question: str, k: int = 5, model_name: str = DEFAULT_MODEL
) -> dict:
    """Explicitly opt into model download/inference; never silently use fake vectors."""
    records = load_evidence()
    if not records:
        return {
            "question": question, "retrieval_method": "bm25_semantic_rrf",
            "evidence_status": "retrieved_not_verified", "hits": [], "hit_count": 0
        }
    return HybridRetriever(records, load_sentence_encoder(model_name)).search(
        question, k=k
    )
