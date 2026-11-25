import math

import numpy as np
import pytest

from app.evidence_export import evidence_rows
from app.retrieval_benchmark import benchmark, rank_metrics, validate_judgments


RECORDS = [
    {"pmid": "111", "title": "YES1 SRC TNBC", "abstract": "YES1 regulates FOXM1. SRC is associated with resistance."},
    {"pmid": "222", "title": "EGFR signaling", "abstract": "EGFR is a kinase."},
]


class Encoder:
    def encode(self, texts, **kwargs):
        return np.array([
            [1.0, 0.0] if "SRC" in text or "YES1" in text else [0.0, 1.0]
            for text in texts
        ], dtype=np.float32)


def test_metrics_with_known_labels():
    metrics = rank_metrics([{"pmid": "222"}, {"pmid": "111"}], {"111"}, 2)
    assert metrics["recall_at_k"] == 1
    assert metrics["precision_at_k"] == 0.5
    assert metrics["reciprocal_rank_at_k"] == 0.5
    assert metrics["ndcg_at_k"] == pytest.approx(1 / math.log2(3))


def test_rejects_unknown_pmid_and_unlabeled_queries():
    with pytest.raises(ValueError, match="not in QC corpus"):
        validate_judgments([{"query": "TNBC", "relevant_pmids": ["999"]}], {"111"})
    with pytest.raises(ValueError, match="nonempty"):
        validate_judgments([{"query": "TNBC", "relevant_pmids": []}], {"111"})


def test_benchmark_three_methods():
    result = benchmark(RECORDS, [{"query": "YES1 SRC", "relevant_pmids": ["111"]}],
                       Encoder(), k=2)
    assert set(result["retrieval_methods"]) == {"bm25", "semantic", "hybrid_rrf"}
    assert all(v["queries"] == 1 for v in result["retrieval_methods"].values())


def test_evidence_excerpts_are_verbatim_and_unverified():
    rows = evidence_rows([{"pmid": "111", "title": "SRC", "abstract": RECORDS[0]["abstract"]}])
    assert rows[0]["detected_terms_not_verified_entities"] == ["YES1", "SRC", "FOXM1"]
    assert rows[0]["verbatim_abstract_excerpts"][0] == "YES1 regulates FOXM1."
    assert rows[0]["causal_support"] == "not_assessed"
    assert rows[0]["evidence_status"] == "requires_human_review"
