import csv
from pathlib import Path

import pytest

from app.annotation_evaluation import prepare_annotations, evaluate_annotations


def fixture_data():
    sentence = "Dasatinib inhibited SRC."
    evidence = {"evidence_id": "PMID:123:S1", "pmid": "123",
                "verbatim_excerpt": sentence}
    candidate = {**evidence, "candidate_id": "PMID:123:S1:1",
                 "entity_a": "SRC", "entity_b": "dasatinib",
                 "predicate_cue": "inhibition_mentioned"}
    return {"candidates": [candidate]}, {"evidence": [evidence]}


def update_csv(path, update):
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields, rows = reader.fieldnames, list(reader)
    for row in rows:
        row.update(update)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_blank_templates_and_no_premature_metrics(tmp_path):
    rel, syn = fixture_data()
    assert prepare_annotations(rel, syn, tmp_path) == {
        "candidate_rows": 1, "sentence_rows": 1}
    result = evaluate_annotations(rel, tmp_path / "candidate_annotations.csv",
                                  tmp_path / "sentence_audit.csv",
                                  tmp_path / "gold_relationships.csv")
    assert result["precision"] is None
    assert result["recall"] is None
    assert result["f1"] is None


def test_precision_only_after_review(tmp_path):
    rel, syn = fixture_data()
    prepare_annotations(rel, syn, tmp_path)
    update_csv(tmp_path / "candidate_annotations.csv", {
        "review_status": "adjudicated", "label": "supported",
        "reviewer_id": "reviewer_1", "evidence_rationale": "Direct evidence"})
    result = evaluate_annotations(rel, tmp_path / "candidate_annotations.csv",
                                  tmp_path / "sentence_audit.csv",
                                  tmp_path / "gold_relationships.csv")
    assert result["precision"] == 1.0
    assert result["recall"] is None


def test_full_audit_and_gold_enables_recall(tmp_path):
    rel, syn = fixture_data()
    prepare_annotations(rel, syn, tmp_path)
    update_csv(tmp_path / "candidate_annotations.csv", {
        "review_status": "adjudicated", "label": "supported",
        "reviewer_id": "reviewer_1", "evidence_rationale": "Reviewed"})
    update_csv(tmp_path / "sentence_audit.csv", {
        "review_status": "adjudicated", "exhaustive_review_complete": "yes",
        "reviewer_id": "reviewer_1"})
    gold_path = tmp_path / "gold_relationships.csv"
    with gold_path.open("a", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow([
            "G1", "PMID:123:S1", "123", "SRC", "dasatinib",
            "inhibition_mentioned", "supported", "adjudicated",
            "reviewer_1", "Reviewed"])
    result = evaluate_annotations(rel, tmp_path / "candidate_annotations.csv",
                                  tmp_path / "sentence_audit.csv", gold_path)
    assert result["precision"] == 1.0
    assert result["recall"] == 1.0
    assert result["f1"] == 1.0


def test_tampered_candidate_rejected(tmp_path):
    rel, syn = fixture_data()
    prepare_annotations(rel, syn, tmp_path)
    update_csv(tmp_path / "candidate_annotations.csv", {"pmid": "999"})
    with pytest.raises(ValueError, match="mismatch"):
        evaluate_annotations(rel, tmp_path / "candidate_annotations.csv",
                             tmp_path / "sentence_audit.csv",
                             tmp_path / "gold_relationships.csv")


def test_gold_missing_supported_candidate_rejected(tmp_path):
    rel, syn = fixture_data()
    prepare_annotations(rel, syn, tmp_path)
    update_csv(tmp_path / "candidate_annotations.csv", {
        "review_status": "adjudicated", "label": "supported",
        "reviewer_id": "reviewer_1", "evidence_rationale": "Reviewed"})
    update_csv(tmp_path / "sentence_audit.csv", {
        "review_status": "adjudicated", "exhaustive_review_complete": "yes",
        "reviewer_id": "reviewer_1"})
    with pytest.raises(ValueError, match="missing"):
        evaluate_annotations(rel, tmp_path / "candidate_annotations.csv",
                             tmp_path / "sentence_audit.csv",
                             tmp_path / "gold_relationships.csv")


def test_duplicate_candidate_rejected(tmp_path):
    rel, syn = fixture_data()
    rel["candidates"].append(rel["candidates"][0].copy())
    with pytest.raises(ValueError, match="Duplicate"):
        prepare_annotations(rel, syn, tmp_path)
