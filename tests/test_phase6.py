import pytest

from app.evidence_synthesis import detect_entities, synthesize_evidence, summarize_mentions


def test_detect_kinase_pathway_drug_and_model_mentions():
    entities = detect_entities(
        "YES1 and SRC activate MAPK/ERK in PDX models treated with dasatinib."
    )
    assert entities["kinase"] == ["SRC", "YES1"]
    assert "MAPK/ERK" in entities["pathway"]
    assert entities["drug"] == ["dasatinib"]
    assert entities["experimental_model"] == ["PDX"]


def test_no_substring_false_positive():
    entities = detect_entities("SOURCE data were collected in the desert.")
    assert "SRC" not in entities["kinase"]
    assert "ERK2" not in entities["kinase"]


def test_verbatim_provenance_and_no_causality():
    abstract = "YES1 regulates FOXM1. Dasatinib treatment improved response in mice."
    report = synthesize_evidence([
        {"pmid": "12345", "title": "Example", "abstract": abstract, "rank": 1},
    ], "YES1 TNBC")
    assert report["source_count"] == 1
    assert all(e["verbatim_excerpt"] in abstract for e in report["evidence"])
    assert all(e["causal_support"] == "not_assessed" for e in report["evidence"])
    assert report["claims"] == [] and report["hypotheses"] == []


def test_duplicate_and_invalid_pmids_are_excluded():
    hit = {"pmid": "123", "abstract": "SRC resistance."}
    report = synthesize_evidence([hit, hit, {"pmid": "invalid", "abstract": "EGFR."}], "q")
    assert report["source_count"] == 1
    assert len(report["evidence"]) == 1


def test_entity_index_deduplicates_sources():
    report = synthesize_evidence([
        {"pmid": "111", "abstract": "YES1 kinase. YES1 in TNBC."},
        {"pmid": "222", "abstract": "YES1 and SRC signaling."},
    ], "YES1")
    index = summarize_mentions(report)
    yes1 = next(row for row in index if row["entity"] == "YES1")
    assert yes1["source_count"] == 2
    assert yes1["pmids"] == ["111", "222"]


def test_max_sentences_validated():
    with pytest.raises(ValueError, match="positive"):
        synthesize_evidence([], "q", max_sentences=0)
