import pytest

from app.relationship_extraction import classify_context, extract_relationship_candidates


def make_report(sentence):
    return {
        "question": "TNBC",
        "source_count": 1,
        "sources": [{"pmid": "123"}],
        "evidence": [{
            "pmid": "123", "evidence_id": "PMID:123:S1",
            "verbatim_excerpt": sentence,
        }],
    }


def test_candidate_keeps_exact_sentence_and_no_direction():
    sentence = "Dasatinib inhibited SRC in TNBC cell lines."
    out = extract_relationship_candidates(make_report(sentence))
    assert out["candidate_count"] >= 1
    assert all(c["verbatim_excerpt"] == sentence for c in out["candidates"])
    assert all(c["direction"] == "undetermined" for c in out["candidates"])
    assert out["verified_claims"] == []


def test_co_mentions_without_predicate_do_not_create_relationship():
    out = extract_relationship_candidates(make_report("SRC and YES1 in TNBC."))
    assert out["candidate_count"] == 0


def test_negated_statement_is_flagged_not_asserted():
    out = extract_relationship_candidates(make_report("Dasatinib did not inhibit SRC."))
    assert out["candidate_count"] >= 1
    assert all(c["negation_cue_detected"] for c in out["candidates"])
    assert all(c["causal_support"] == "not_assessed" for c in out["candidates"])


def test_speculative_statement_is_flagged():
    out = extract_relationship_candidates(make_report("YES1 may regulate SRC."))
    assert out["candidate_count"] >= 1
    assert all(c["hedging_cue_detected"] for c in out["candidates"])


def test_no_unknown_source_or_invalid_pmid():
    report = make_report("SRC regulates YES1.")
    report["sources"] = []
    assert extract_relationship_candidates(report)["candidate_count"] == 0


def test_context_is_cue_not_verified_design():
    context = classify_context(
        "SRC inhibition in patient-derived xenografts treated with dasatinib.",
        {"experimental_model": ["PDX"]},
    )
    assert context["context_class"] == "intervention_language_detected"
    assert context["study_design_verified"] is False
    assert context["experimental_models_mentioned"] == ["PDX"]
