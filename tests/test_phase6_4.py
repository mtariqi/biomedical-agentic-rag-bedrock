"""Phase 6.4 conservative binding regression tests."""
from app.biomedical_relation_binding import (
    normalize_gene_mentions, bind_sentence, disease_context,
    extract_bound_relations,
)


def test_csk_long_name_not_src():
    genes = normalize_gene_mentions("C-terminal Src kinase (CSK) affects resistance.")
    assert {g["symbol"] for g in genes} == {"CSK"}


def test_src_and_csk_distinct():
    genes = normalize_gene_mentions("SRC and C-terminal Src kinase (CSK) were examined.")
    assert {g["symbol"] for g in genes} == {"SRC", "CSK"}


def test_src_identifier():
    assert normalize_gene_mentions("SRC")[0]["hgnc_id"] == "HGNC:11283"


def test_dasatinib_src_binding():
    relations = bind_sentence("The SRC inhibitor Dasatinib was predicted to be useful.")
    assert any(r["subject"] == "dasatinib" and
               r["object"] == "SRC" and
               r["predicate"] == "inhibits_target_mentioned"
               for r in relations)
    assert relations[0]["evidence_qualification"] == "speculative"


def test_no_inhibitor_to_resistance_cross_product():
    relations = bind_sentence(
        "A SRC inhibitor Dasatinib was predicted for chemoresistant TNBC.")
    assert all(r["object"] != "drug_resistance" for r in relations)


def test_paclitaxel_dual_phenotype():
    relations = bind_sentence("paclitaxel-sensitive and -resistant tumors")
    assert {r["object"] for r in relations} == {
        "drug_sensitivity", "drug_resistance"}


def test_aim_does_not_produce_unsupported_relation():
    relations = bind_sentence(
        "We intend to clarify the role of SRC in tamoxifen resistance.")
    assert relations == []


def test_csk_does_not_generate_src_binding():
    relations = bind_sentence(
        "C-terminal Src kinase (CSK) and drug resistance were examined.")
    assert relations == []


def test_context_flags():
    assert disease_context("TNBC cells")["tnbc_specific"] is True
    assert disease_context("tamoxifen resistant breast cancer")["tnbc_specific"] is False


def test_unchanged_synthesis_and_new_ids():
    synthesis = {
        "question": "TNBC",
        "evidence": [{"evidence_id": "PMID:123:S1", "pmid": "123",
                      "verbatim_excerpt": "SRC inhibitor dasatinib."}],
    }
    report = extract_bound_relations(synthesis)
    assert report["candidate_count"] == 1
    assert report["candidates"][0]["candidate_id"] == "PMID:123:S1:B1"
    assert report["verified_claims"] == []
    assert "candidates" not in synthesis
