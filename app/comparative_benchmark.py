"""Phase 6.5: strict, independent entity-pair benchmark for two extractors.

Entity-pair detection only; predicate correctness, direction, causality, and
clinical efficacy are NOT measured. No automated expert labels.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


def read_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def canonical_entity(value: str) -> str:
    """Small explicit crosswalk, not general biomedical ontology mapping."""
    aliases = {
        "src": "HGNC:11283", "csk": "HGNC:2444",
        "yes1": "HGNC:12841", "fyn": "HGNC:4037",
        "drug_resistance": "phenotype:drug_resistance",
        "drug_sensitivity": "phenotype:drug_sensitivity",
        "dasatinib": "drug:dasatinib",
        "paclitaxel": "drug:paclitaxel",
        "epirubicin": "drug:epirubicin",
        "docetaxel": "drug:docetaxel",
    }
    name = value.strip().lower()
    if name not in aliases:
        raise ValueError(f"Unmapped entity {value!r}; extend curated crosswalk first")
    return aliases[name]


def pair_key(evidence_id: str, entity_a: str, entity_b: str) -> tuple[str, str, str]:
    a, b = canonical_entity(entity_a), canonical_entity(entity_b)
    if a == b:
        raise ValueError("Self-pair is not eligible")
    return (evidence_id, *sorted((a, b)))


def predictions(phase62: dict, phase64: dict, audited_ids: set[str]) -> dict[str, set]:
    base = set()
    for item in phase62["candidates"]:
        if item["evidence_id"] not in audited_ids:
            raise ValueError("Phase 6.2 prediction outside audited corpus")
        base.add(pair_key(item["evidence_id"], item["entity_a"], item["entity_b"]))
    new = set()
    for item in phase64["candidates"]:
        if item["evidence_id"] not in audited_ids:
            raise ValueError("Phase 6.4 prediction outside audited corpus")
        new.add(pair_key(item["evidence_id"], item["subject"], item["object"]))
    return {"phase6_2": base, "phase6_4": new}


def evaluate(phase62: dict, phase64: dict, synthesis: dict,
             sentence_audit_csv: Path, gold_csv: Path) -> dict:
    """Withhold scores unless all 36 source sentences are independently audited.

    This cannot verify reviewer independence or annotation completeness;
    it enforces explicit reviewer attestations.
    """
    sentences = synthesis["evidence"]
    expected = {row["evidence_id"]: row for row in sentences}
    if len(expected) != len(sentences) or not expected:
        raise ValueError("Evidence sentence IDs must be unique and nonempty")
    audit = read_rows(sentence_audit_csv)
    if len(audit) != len(expected) or len({r["evidence_id"] for r in audit}) != len(audit):
        raise ValueError("Audit must cover each evidence sentence exactly once")
    for row in audit:
        source = expected.get(row["evidence_id"])
        if source is None or str(row["pmid"]) != str(source["pmid"]) or (
            row["verbatim_excerpt"] != source["verbatim_excerpt"]
        ):
            raise ValueError("Sentence audit provenance mismatch")
    pred = predictions(phase62, phase64, set(expected))
    result = {
        "task": "sentence_level_unordered_entity_pair_detection",
        "evidence_sentence_count": len(expected),
        "prediction_pair_counts": {name: len(pairs) for name, pairs in pred.items()},
        "scores_available": False,
        "reason": "requires_exhaustive_independent_sentence_gold_review",
        "metrics": None,
    }
    if not all(
        row["review_status"] == "adjudicated"
        and row["exhaustive_review_complete"].strip().lower() == "yes"
        and row["reviewer_id"].strip()
        for row in audit
    ):
        return result
    gold_rows = read_rows(gold_csv)
    gold = set()
    for row in gold_rows:
        source = expected.get(row["evidence_id"])
        if source is None or str(row["pmid"]) != str(source["pmid"]):
            raise ValueError("Gold relation outside corpus or wrong PMID")
        if (row["review_status"] != "adjudicated"
                or row["label"] not in {"supported", "unsupported"}
                or not row["reviewer_id"].strip()
                or not row["evidence_rationale"].strip()):
            raise ValueError("Gold relation must have unambiguous adjudication")
        if row["label"] == "supported":
            gold.add(pair_key(row["evidence_id"], row["entity_a"], row["entity_b"]))
    metrics = {}
    for name, found in pred.items():
        tp = len(found & gold)
        fp = len(found - gold)
        fn = len(gold - found)
        precision = tp / (tp + fp) if tp + fp else None
        recall = tp / (tp + fn) if tp + fn else None
        f1 = (2 * precision * recall / (precision + recall)
              if precision is not None and recall is not None and precision + recall
              else 0.0 if precision is not None and recall is not None else None)
        metrics[name] = {
            "tp": tp, "fp": fp, "fn": fn, "precision": precision,
            "recall": recall, "f1": f1,
        }
    result.update({
        "scores_available": True, "reason": "expert_gold_review_attested",
        "gold_pair_count": len(gold), "metrics": metrics,
    })
    return result
