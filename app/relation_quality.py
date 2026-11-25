"""Non-destructive, rule-based triage of Phase 6.2 candidates.

Rules flag *possible* extraction errors, not biological truth. The original
candidate set remains immutable for unbiased Phase 6.3 annotation.
"""
from __future__ import annotations

import re
from collections import Counter


def quality_flags(candidate: dict) -> list[str]:
    sentence = str(candidate["verbatim_excerpt"])
    cue = candidate["predicate_cue"]
    entities = {candidate["entity_a"], candidate["entity_b"]}
    flags = []

    # CSK (C-terminal Src kinase) is distinct from SRC. Flag ambiguity
    # rather than automatically deleting genuine SRC mentions elsewhere.
    if "SRC" in entities and re.search(
        r"\b(?:C-terminal\s+Src\s+kinase|CSK)\b", sentence, re.I
    ) and not re.search(r"\bSRC\b", sentence):
        flags.append("src_csk_entity_ambiguity")

    phenotype = entities & {"drug_resistance", "drug_sensitivity"}
    if phenotype:
        if "drug_resistance" in phenotype and cue == "sensitivity_mentioned":
            flags.append("phenotype_predicate_mismatch")
        if "drug_sensitivity" in phenotype and cue == "resistance_mentioned":
            flags.append("phenotype_predicate_mismatch")

    # Generic inhibition does not imply that resistance itself was inhibited.
    if (cue == "inhibition_mentioned" and "drug_resistance" in phenotype
            and re.search(r"\b(?:SRC|Src)\s+inhibitor\b", sentence, re.I)):
        flags.append("inhibitor_target_scope_ambiguous")

    # An aim statement does not establish a tested or confirmed relation.
    if re.search(r"\b(?:we intend to|aim(?:ed|s)? to|we sought to)\b", sentence, re.I):
        flags.append("study_aim_not_result")

    if re.search(r"\b(?:predicted|potential|suggest(?:s|ed)?|may|might)\b", sentence, re.I):
        flags.append("speculative_or_predicted_language")

    return flags


def triage_candidates(report: dict) -> dict:
    """Attach reviewer flags without deleting, relabeling or re-IDing candidates."""
    annotated = []
    flag_counts = Counter()
    for candidate in report.get("candidates", []):
        flags = quality_flags(candidate)
        flag_counts.update(flags)
        annotated.append({
            **candidate,
            "quality_flags": flags,
            "quality_review_priority": "high" if flags else "standard",
            "expert_label": None,
            "auto_excluded": False,
        })
    return {
        "question": report.get("question", ""),
        "candidate_count": len(annotated),
        "flagged_candidate_count": sum(bool(c["quality_flags"]) for c in annotated),
        "quality_flag_counts": dict(sorted(flag_counts.items())),
        "candidates": annotated,
        "limitations": [
            "Quality flags are heuristics, not expert labels or validated errors",
            "No candidates are removed; Phase 6.3 baseline IDs remain unchanged",
            "Full-text and independent expert adjudication are required",
        ],
    }
