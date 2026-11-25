"""Regression tests for non-destructive expert-review triage."""
from copy import deepcopy

from app.relation_quality import quality_flags, triage_candidates


def candidate(sentence, a="SRC", b="drug_resistance", cue="resistance_mentioned"):
    return {"candidate_id": "c1", "pmid": "123", "evidence_id": "e1",
            "verbatim_excerpt": sentence, "entity_a": a, "entity_b": b,
            "predicate_cue": cue}


def test_csk_not_src_flagged():
    c = candidate("C-terminal Src kinase (CSK) is linked to drug resistance.")
    assert "src_csk_entity_ambiguity" in quality_flags(c)


def test_explicit_src_and_csk_not_automatically_conflated():
    c = candidate("SRC and C-terminal Src kinase (CSK) regulate drug resistance.")
    assert "src_csk_entity_ambiguity" not in quality_flags(c)


def test_paclitaxel_mismatched_cue_flagged():
    c = candidate("Paclitaxel-sensitive and -resistant tumors.",
                  "paclitaxel", "drug_resistance", "sensitivity_mentioned")
    assert "phenotype_predicate_mismatch" in quality_flags(c)


def test_matched_paclitaxel_cue_retained():
    c = candidate("Paclitaxel-sensitive and -resistant tumors.",
                  "paclitaxel", "drug_resistance", "resistance_mentioned")
    assert "phenotype_predicate_mismatch" not in quality_flags(c)


def test_aim_not_result_flagged():
    c = candidate("We intend to explore SRC in tamoxifen resistance.")
    assert "study_aim_not_result" in quality_flags(c)


def test_inhibitor_scope_flagged():
    c = candidate("The SRC inhibitor dasatinib may affect chemoresistant TNBC.",
                  "SRC", "drug_resistance", "inhibition_mentioned")
    assert "inhibitor_target_scope_ambiguous" in quality_flags(c)


def test_original_preserved_and_all_candidates_retained():
    original = {"question": "TNBC", "candidates": [
        candidate("C-terminal Src kinase (CSK) and resistance."),
        candidate("SRC and resistance.")]}
    snapshot = deepcopy(original)
    triaged = triage_candidates(original)
    assert original == snapshot
    assert triaged["candidate_count"] == 2
    assert all(c["auto_excluded"] is False and c["expert_label"] is None
               for c in triaged["candidates"])
    assert [c["candidate_id"] for c in triaged["candidates"]] == ["c1", "c1"]
