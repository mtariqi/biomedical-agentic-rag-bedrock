"""Regression checks for Phase 6.2 false-positive relation candidates."""
from app.relationship_extraction import extract_relationship_candidates


def _report(sentence):
    return {
        "question": "TNBC",
        "sources": [{"pmid": "12345"}],
        "source_count": 1,
        "evidence": [{
            "pmid": "12345",
            "evidence_id": "PMID:12345:S1",
            "verbatim_excerpt": sentence,
        }],
    }


def test_phenotype_only_pairs_excluded():
    report = extract_relationship_candidates(
        _report("Chemotherapy resistance was associated with drug response.")
    )
    assert report["candidate_count"] == 0


def test_drug_to_phenotype_retained():
    report = extract_relationship_candidates(
        _report("Paclitaxel resistance was associated with drug response.")
    )
    assert report["candidate_count"] > 0
    assert all(
        not (c["entity_a_category"] == c["entity_b_category"] == "phenotype")
        for c in report["candidates"]
    )


def test_molecular_candidate_preserved():
    report = extract_relationship_candidates(
        _report("Dasatinib inhibited SRC in TNBC.")
    )
    assert any(
        {c["entity_a"], c["entity_b"]} == {"SRC", "dasatinib"}
        for c in report["candidates"]
    )
    assert report["verified_claims"] == []
