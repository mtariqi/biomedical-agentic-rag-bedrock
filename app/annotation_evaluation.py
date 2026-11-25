"""Phase 6.3 expert annotation preparation and conservative evaluation.

Candidate precision requires fully adjudicated predictions. Recall additionally
requires an independently exhaustive gold inventory over the evaluation corpus.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

CANDIDATE_LABELS = {"supported", "unsupported", "uncertain"}
GOLD_LABELS = {"supported", "unsupported", "uncertain"}
REVIEW_STATES = {"pending", "adjudicated"}
FIELDS = [
    "candidate_id", "evidence_id", "pmid", "entity_a", "entity_b",
    "predicate_cue", "verbatim_excerpt", "review_status", "label",
    "reviewer_id", "evidence_rationale", "relation_direction",
    "full_text_checked",
]
SENTENCE_FIELDS = [
    "evidence_id", "pmid", "verbatim_excerpt", "review_status",
    "exhaustive_review_complete", "reviewer_id", "notes",
]
GOLD_FIELDS = [
    "gold_id", "evidence_id", "pmid", "entity_a", "entity_b",
    "predicate_cue", "label", "review_status", "reviewer_id",
    "evidence_rationale",
]


def _write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def prepare_annotations(relations: dict, synthesis: dict, output_dir: Path) -> dict:
    """Generate blank human-review templates; never infer labels."""
    candidates = relations.get("candidates", [])
    sentences = synthesis.get("evidence", [])
    known = {s["evidence_id"]: s for s in sentences}
    ids = set()
    rows = []
    for c in candidates:
        cid = c["candidate_id"]
        if cid in ids:
            raise ValueError(f"Duplicate candidate_id: {cid}")
        ids.add(cid)
        source = known.get(c["evidence_id"])
        if (not source or str(source["pmid"]) != str(c["pmid"])
                or source["verbatim_excerpt"] != c["verbatim_excerpt"]):
            raise ValueError(f"Candidate evidence mismatch: {cid}")
        rows.append({**c, "review_status": "pending", "label": "",
                     "reviewer_id": "", "evidence_rationale": "",
                     "relation_direction": "", "full_text_checked": ""})
    sentence_rows = [
        {**s, "review_status": "pending", "exhaustive_review_complete": "",
         "reviewer_id": "", "notes": ""}
        for s in sentences
    ]
    _write_csv(output_dir / "candidate_annotations.csv", FIELDS, rows)
    _write_csv(output_dir / "sentence_audit.csv", SENTENCE_FIELDS, sentence_rows)
    _write_csv(output_dir / "gold_relationships.csv", GOLD_FIELDS, [])
    return {"candidate_rows": len(rows), "sentence_rows": len(sentence_rows)}


def _read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _key(row: dict) -> tuple[str, str, str, str]:
    """Exact sentence + unordered entities + predicate cue."""
    return (row["evidence_id"], *sorted((row["entity_a"], row["entity_b"])),
            row["predicate_cue"])


def evaluate_annotations(relations: dict, candidate_csv: Path,
                         sentence_csv: Path, gold_csv: Path) -> dict:
    """Return metrics only when annotation requirements are met.

    Precision: all predictions adjudicated and no uncertain labels.
    Recall/F1: plus exhaustive audited sentences and gold relationships.
    """
    expected = {c["candidate_id"]: c for c in relations["candidates"]}
    rows = _read_csv(candidate_csv)
    if len(rows) != len(expected) or len({r["candidate_id"] for r in rows}) != len(rows):
        raise ValueError("Candidate annotations must cover every unique prediction")
    for r in rows:
        src = expected.get(r["candidate_id"])
        if not src or any(str(r[k]) != str(src[k]) for k in
                          ("evidence_id", "pmid", "entity_a", "entity_b",
                           "predicate_cue", "verbatim_excerpt")):
            raise ValueError(f"Candidate identity/provenance mismatch: {r['candidate_id']}")
        if r["review_status"] not in REVIEW_STATES:
            raise ValueError("Invalid candidate review_status")
        if r["label"] and r["label"] not in CANDIDATE_LABELS:
            raise ValueError("Invalid candidate label")
        if r["review_status"] == "adjudicated" and (
            not r["reviewer_id"].strip() or not r["evidence_rationale"].strip()
            or r["label"] not in CANDIDATE_LABELS
        ):
            raise ValueError("Adjudicated candidate requires reviewer, rationale, label")
    complete = all(r["review_status"] == "adjudicated" and
                   r["label"] != "uncertain" for r in rows)
    output = {
        "candidate_count": len(rows),
        "adjudicated_count": sum(r["review_status"] == "adjudicated" for r in rows),
        "label_counts": dict(Counter(r["label"] or "unlabeled" for r in rows)),
        "precision": None, "recall": None, "f1": None,
        "precision_status": "requires_complete_unambiguous_candidate_adjudication",
        "recall_status": "requires_exhaustive_sentence_audit_and_gold_inventory",
    }
    if not complete:
        return output
    tp = sum(r["label"] == "supported" for r in rows)
    fp = sum(r["label"] == "unsupported" for r in rows)
    output["precision"] = tp / (tp + fp) if tp + fp else None
    output["precision_status"] = "candidate_level_expert_precision"
    audit = _read_csv(sentence_csv)
    gold = _read_csv(gold_csv)
    audit_ids = {r["evidence_id"] for r in audit}
    expected_evidence = {c["evidence_id"] for c in relations["candidates"]}
    if not expected_evidence.issubset(audit_ids):
        raise ValueError("Sentence audit missing predicted evidence")
    # Gold inventory is not complete unless all audited source sentences are
    # explicitly marked as exhaustively reviewed. Require >= 1 sentence.
    if not audit or len(audit_ids) != len(audit) or not all(
        r["review_status"] == "adjudicated"
        and r["exhaustive_review_complete"].strip().lower() == "yes"
        and r["reviewer_id"].strip()
        for r in audit
    ):
        return output
    audit_pmids = {r["evidence_id"]: str(r["pmid"]) for r in audit}
    seen_gold = set()
    for g in gold:
        if g["evidence_id"] not in audit_pmids or str(g["pmid"]) != audit_pmids[g["evidence_id"]]:
            raise ValueError("Gold relationship outside audited sentences")
        if g["review_status"] != "adjudicated" or not g["reviewer_id"].strip() or not g["evidence_rationale"].strip():
            raise ValueError("Gold relationship is not adjudicated")
        if g["label"] not in GOLD_LABELS or g["label"] == "uncertain":
            raise ValueError("Gold relationships must have unambiguous labels")
        key = _key(g)
        if key in seen_gold:
            raise ValueError("Duplicate gold relation key")
        seen_gold.add(key)
    predicted_supported = {_key(r) for r in rows if r["label"] == "supported"}
    gold_supported = {_key(g) for g in gold if g["label"] == "supported"}
    # A candidate marked supported must exist in gold, otherwise annotation
    # is internally inconsistent and metrics must not be reported.
    if not predicted_supported.issubset(gold_supported):
        raise ValueError("Supported candidate missing from exhaustive gold inventory")
    tp_gold = len(predicted_supported & gold_supported)
    fn = len(gold_supported - predicted_supported)
    output["recall"] = tp_gold / (tp_gold + fn) if tp_gold + fn else None
    if output["precision"] is not None and output["recall"] is not None:
        p, r = output["precision"], output["recall"]
        output["f1"] = 2 * p * r / (p + r) if p + r else 0.0
    output["recall_status"] = "expert_gold_inventory_exhaustively_reviewed"
    return output
