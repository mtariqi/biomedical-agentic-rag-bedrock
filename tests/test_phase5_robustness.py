import numpy as np
import pytest

from app.phase5_robustness import (
    EGFR_QUERY, label_scenarios, run_robustness,
)


class Encoder:
    def encode(self, texts, **kwargs):
        return np.asarray([
            [1., 0.] if "EGFR" in text else [0., 1.]
            for text in texts
        ], dtype=np.float32)


RECORDS = [
    {"pmid": "28653902", "title": "RTK inhibition", "abstract": "TNBC NF kappa B resistance"},
    {"pmid": "111", "title": "SRC signaling", "abstract": "SRC resistance in TNBC"},
    {"pmid": "222", "title": "EGFR response", "abstract": "EGFR signaling and response"},
]
JUDGMENTS = [
    {"query": EGFR_QUERY, "relevant_pmids": ["28653902"]},
    {"query": "SRC resistance", "relevant_pmids": ["111"]},
]


def test_strict_scenario_excludes_unjudged_query():
    scenarios = label_scenarios(JUDGMENTS)
    assert len(scenarios["original_broad_rtk"]["judgments"]) == 2
    strict = scenarios["strict_egfr"]
    assert strict["excluded_no_positive_queries"] == [EGFR_QUERY]
    assert [j["query"] for j in strict["judgments"]] == ["SRC resistance"]


def test_multi_cutoff_and_rrf_sweep():
    result = run_robustness(RECORDS, JUDGMENTS, Encoder(),
                            cutoffs=(1, 2, 3), constants=(10, 60),
                            candidate_pools=(1, 3))
    assert len(result["rrf_sensitivity"]) == 2 * 2 * 2
    assert result["evaluation"]["original_broad_rtk"]["methods"]["bm25"]["queries"] == 2
    assert result["evaluation"]["strict_egfr"]["methods"]["bm25"]["queries"] == 1
    assert result["evaluation"]["original_broad_rtk"]["methods"]["hybrid_rrf_baseline"]["per_cutoff"]["3"]["recall_at_k"] >= 0


def test_invalid_cutoff_rejected():
    with pytest.raises(ValueError, match="cutoffs"):
        run_robustness(RECORDS, JUDGMENTS, Encoder(), cutoffs=(0,))


def test_does_not_mutate_original_judgments():
    import copy
    original = copy.deepcopy(JUDGMENTS)
    run_robustness(RECORDS, JUDGMENTS, Encoder(), cutoffs=(1, 3),
                   constants=(60,), candidate_pools=(2,))
    assert JUDGMENTS == original
