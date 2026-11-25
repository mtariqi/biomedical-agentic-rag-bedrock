"""Phase 6.2: conservative, PMID-grounded relation candidates.

A regex cue and two entities in one sentence generate a *candidate*, never
a validated directed causal claim. No LLM inference or fabricated excerpts.
"""
from __future__ import annotations

import re
from collections import Counter

from .evidence_synthesis import detect_entities

CUES = {
    "inhibition_mentioned": (r"\binhibit(?:s|ed|ion|ing|or|ors)?\b", r"\bsuppress(?:es|ed|ion|ing)?\b"),
    "activation_mentioned": (r"\bactivat(?:e|es|ed|ion|ing)\b",),
    "regulation_mentioned": (r"\bregulat(?:e|es|ed|ion|ing)\b",),
    "association_mentioned": (r"\b(?:associat(?:ed|ion)|correlat(?:ed|ion)|linked)\b",),
    "resistance_mentioned": (r"\b(?:resistan\w*|refractory)\b",),
    "sensitivity_mentioned": (r"\b(?:sensitiv\w*|response|responded)\b",),
}
NEGATION = (r"\bno\b", r"\bnot\b", r"\bwithout\b", r"\bfailed to\b", r"\bneither\b")
HEDGING = (r"\bmay\b", r"\bmight\b", r"\bcould\b", r"\bsuggest(?:s|ed)?\b",
           r"\bpotential(?:ly)?\b", r"\bhypothesiz\w*\b")
DESIGNS = {
    "review_language": (r"\breview\b", r"\bwe discuss\b", r"\bthis article summarizes\b"),
    "intervention_language": (r"\btreated\b", r"\btreatment\b", r"\bknockdown\b",
                              r"\bknockout\b", r"\bsilenc\w*\b", r"\binhibitor\b"),
    "observational_language": (r"\bcohort\b", r"\bcorrelat\w*\b", r"\bassociat\w*\b"),
}


def _matched(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def classify_context(sentence: str, entities: dict[str, list[str]]) -> dict:
    """Cues apply only to the supplied sentence, never an entire article."""
    flags = [name for name, patterns in DESIGNS.items() if _matched(sentence, patterns)]
    if "review_language" in flags:
        context = "review_language_detected"
    elif "intervention_language" in flags:
        context = "intervention_language_detected"
    elif "observational_language" in flags:
        context = "observational_language_detected"
    else:
        context = "undetermined"
    return {
        "context_class": context,
        "context_cues": flags,
        "experimental_models_mentioned": entities.get("experimental_model", []),
        "negation_cue_detected": _matched(sentence, NEGATION),
        "hedging_cue_detected": _matched(sentence, HEDGING),
        "study_design_verified": False,
    }


def extract_relationship_candidates(report: dict) -> dict:
    """Create unordered entity-pair candidates with an explicit predicate cue.

    A co-mention is not a mechanistic assertion; no direction is assigned.
    """
    sources = {str(s["pmid"]): s for s in report.get("sources", [])}
    candidates = []
    counts = Counter()
    for row in report.get("evidence", []):
        pmid = str(row.get("pmid") or "")
        sentence = str(row.get("verbatim_excerpt") or "")
        source = sources.get(pmid)
        if not source or not pmid.isdigit() or not sentence:
            continue
        # Exact source sentence cannot be checked without the corpus; preserve
        # original Phase 6 provenance status, and require external QC at export.
        entities = detect_entities(sentence)
        labels = sorted({
            (category, label)
            for category in ("kinase", "pathway", "drug", "phenotype")
            for label in entities.get(category, [])
        })
        context = classify_context(sentence, entities)
        cues = [name for name, patterns in CUES.items() if _matched(sentence, patterns)]
        if len(labels) < 2 or not cues:
            continue
        # Avoid inventing directional triples. Candidate is an unordered pair.
        for i, (category_a, entity_a) in enumerate(labels):
            for category_b, entity_b in labels[i + 1:]:
                if category_a == category_b and entity_a == entity_b:
                    continue
                for cue in cues:
                    candidate = {
                        "candidate_id": f"{row['evidence_id']}:{len(candidates)+1}",
                        "pmid": pmid, "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        "evidence_id": row["evidence_id"],
                        "verbatim_excerpt": sentence,
                        "entity_a": entity_a, "entity_a_category": category_a,
                        "entity_b": entity_b, "entity_b_category": category_b,
                        "predicate_cue": cue,
                        "direction": "undetermined",
                        "relation_status": "sentence_level_candidate_not_verified",
                        "causal_support": "not_assessed",
                        "verification_status": "requires_human_review",
                        **context,
                    }
                    candidates.append(candidate)
                    counts[cue] += 1
    return {
        "question": report.get("question", ""),
        "source_count": report.get("source_count", 0),
        "candidate_count": len(candidates),
        "predicate_counts": dict(sorted(counts.items())),
        "candidates": candidates,
        "verified_claims": [],
        "limitations": [
            "Regex predicate cues may be negated, speculative, or unrelated to the paired entities",
            "Entity pairs are unordered; no subject-object direction or causal relation is asserted",
            "Sentence-level context cues do not verify study design or experimental model",
            "Manual adjudication and full-text assessment are required",
        ],
    }
