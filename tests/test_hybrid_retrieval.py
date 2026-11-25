import numpy as np
import pytest

from app.hybrid_retrieval import (
    HybridRetriever, SemanticRetriever, reciprocal_rank_fusion,
)


class ToyEncoder:
    """Deterministic test fixture, not a scientific embedding model."""
    def encode(self, texts, **kwargs):
        result = []
        for text in texts:
            t = text.lower()
            result.append([
                float("src" in t or "yes1" in t),
                float("egfr" in t),
                float("resistance" in t),
            ])
        return np.asarray(result, dtype=np.float32)


RECORDS = [
    {"pmid": "111", "title": "SRC YES1 resistance", "abstract": "SRC in TNBC", "url": "https://pubmed.ncbi.nlm.nih.gov/111/"},
    {"pmid": "222", "title": "EGFR inhibitors", "abstract": "EGFR in TNBC", "url": "https://pubmed.ncbi.nlm.nih.gov/222/"},
]


def test_semantic_ranked_with_provenance():
    results = SemanticRetriever(RECORDS, ToyEncoder()).search("SRC resistance", 2)
    assert results[0]["pmid"] == "111"
    assert results[0]["url"].endswith("/111/")


def test_hybrid_fusion_is_deduplicated():
    results = HybridRetriever(RECORDS, ToyEncoder()).search("SRC resistance", k=2)
    assert results["retrieval_method"] == "bm25_semantic_rrf"
    assert results["hits"][0]["pmid"] == "111"
    assert len({r["pmid"] for r in results["hits"]}) == len(results["hits"])
    assert results["evidence_status"] == "retrieved_not_verified"


def test_rrf_ignores_duplicate_same_source_and_invalid_pmid():
    a = [{"pmid": "111", "retriever": "bm25"},
         {"pmid": "111", "retriever": "bm25"},
         {"pmid": "DEMO", "retriever": "bm25"}]
    b = [{"pmid": "111", "retriever": "semantic"}]
    fused = reciprocal_rank_fusion([a, b])
    assert len(fused) == 1
    assert fused[0]["retrievers"] == ["bm25", "semantic"]
    assert fused[0]["fusion_score"] == round(2 / 61, 8)


def test_empty_and_bad_dimensions():
    assert SemanticRetriever([], ToyEncoder()).search("SRC") == []
    with pytest.raises(ValueError):
        SemanticRetriever(RECORDS, ToyEncoder()).search("SRC", k=0)
