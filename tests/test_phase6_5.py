import csv
from pathlib import Path

import pytest

from app.comparative_benchmark import canonical_entity, evaluate, pair_key


def data():
    sentence = "SRC inhibitor dasatinib."
    source = {"evidence_id": "PMID:123:S1", "pmid": "123",
              "verbatim_excerpt": sentence}
    base = {"candidates": [{**source, "entity_a": "SRC",
                            "entity_b": "dasatinib"}]}
    new = {"candidates": [{**source, "subject": "dasatinib",
                           "object": "SRC"}]}
    synthesis = {"evidence": [source]}
    return base, new, synthesis


def csv_write(path, headers, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def annotations(tmp_path, complete=False, gold=True):
    source = data()[2]["evidence"][0]
    audit = {
        **source, "review_status": "adjudicated" if complete else "pending",
        "exhaustive_review_complete": "yes" if complete else "",
        "reviewer_id": "expert1" if complete else "",
    }
    csv_write(tmp_path / "sentence_audit.csv", list(audit), [audit])
    gold_row = {
        "gold_id": "g1", "evidence_id": "PMID:123:S1", "pmid": "123",
        "entity_a": "SRC", "entity_b": "dasatinib", "predicate_cue": "",
        "label": "supported", "review_status": "adjudicated",
        "reviewer_id": "expert1", "evidence_rationale": "Explicit inhibitor phrase",
    }
    csv_write(tmp_path / "gold_relationships.csv", list(gold_row),
              [gold_row] if gold else [])
    return tmp_path / "sentence_audit.csv", tmp_path / "gold_relationships.csv"


def test_gene_crosswalk_distinguishes_csk():
    assert canonical_entity("SRC") != canonical_entity("CSK")


def test_unmapped_entity_fails_closed():
    with pytest.raises(ValueError, match="Unmapped"):
        canonical_entity("unknown_protein")


def test_unordered_pair_dedup():
    assert pair_key("s1", "SRC", "dasatinib") == pair_key(
        "s1", "dasatinib", "SRC")


def test_no_scores_before_audit(tmp_path):
    audit, gold = annotations(tmp_path)
    result = evaluate(*data(), audit, gold)
    assert result["scores_available"] is False
    assert result["metrics"] is None


def test_same_gold_for_both_extractors(tmp_path):
    audit, gold = annotations(tmp_path, complete=True)
    result = evaluate(*data(), audit, gold)
    assert result["scores_available"] is True
    assert result["metrics"]["phase6_2"]["f1"] == 1.0
    assert result["metrics"]["phase6_4"]["f1"] == 1.0


def test_false_positive_counted(tmp_path):
    audit, gold = annotations(tmp_path, complete=True, gold=False)
    result = evaluate(*data(), audit, gold)
    assert result["metrics"]["phase6_2"]["fp"] == 1
    assert result["metrics"]["phase6_2"]["precision"] == 0.0
    assert result["metrics"]["phase6_2"]["recall"] is None


def test_mismatched_pmid_rejected(tmp_path):
    audit, gold = annotations(tmp_path, complete=True)
    rows = list(csv.DictReader(audit.open(encoding="utf-8")))
    rows[0]["pmid"] = "999"
    csv_write(audit, list(rows[0]), rows)
    with pytest.raises(ValueError, match="provenance"):
        evaluate(*data(), audit, gold)


def test_missing_sentence_rejected(tmp_path):
    audit, gold = annotations(tmp_path)
    csv_write(audit, ["evidence_id", "pmid", "verbatim_excerpt",
                      "review_status", "exhaustive_review_complete", "reviewer_id"], [])
    with pytest.raises(ValueError, match="cover"):
        evaluate(*data(), audit, gold)
