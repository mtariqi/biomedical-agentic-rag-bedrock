"""Phase 6: conservative, auditable biomedical evidence synthesis.

Rules find *mentions*, not validated biological entities or causal interactions.
No LLM, invented PMID, or unsupported direction-of-effect inference.
"""
from __future__ import annotations

import re
from collections import defaultdict

from .evidence_export import _SENTENCE

ENTITY_LEXICON = {
    "kinase": {
        "SRC": (r"\bSRC\b",), "YES1": (r"\bYES1\b",),
        "FYN": (r"\bFYN\b",), "EGFR": (r"\bEGFR\b",),
        "AKT": (r"\bAKT\b",), "ERK2": (r"\bERK2\b",),
    },
    "pathway": {
        "MAPK/ERK": (r"\bMAPK\b", r"\bERK\b", r"\bERK2\b"),
        "PI3K/AKT": (r"\bPI3K\b", r"\bAKT\b"),
        "NF-kappa-B": (r"\bNF[- ]?κ?B\b", r"\bNF[- ]?kappa[- ]?B\b"),
        "TGF-beta": (r"\bTGF[- ]?β\w*\b", r"\bTGF[- ]?beta\w*\b"),
    },
    "drug": {
        "dasatinib": (r"\bdasatinib\b",),
        "epirubicin": (r"\bepirubicin\b",),
        "paclitaxel": (r"\bpaclitaxel\b",),
        "docetaxel": (r"\bdocetaxel\b",),
        "taxane": (r"\btaxanes?\b",),
    },
    "experimental_model": {
        "PDX": (r"\bPDX\b", r"\bpatient[- ]derived xenografts?\b"),
        "cell_line": (r"\bcell lines?\b",),
        "patient_cohort": (r"\bpatient cohorts?\b",),
        "mouse_model": (r"\bmice\b", r"\bmouse models?\b"),
    },
    "phenotype": {
        "drug_resistance": (r"\b(?:chemo|drug|therapy)[- ]?resistan\w*\b",
                            r"\bresistance\b", r"\bresistant\b"),
        "drug_sensitivity": (r"\bsensitiv\w*\b", r"\bresponse\b"),
    },
}
# These terms are evidence cues only, not proof of a causal claim.
EXPERIMENTAL_CUES = (
    r"\b(?:knockout|knockdown|silencing|inhibition|inhibitor|suppression)\b",
    r"\b(?:treated|treatment|experiment|assay|xenograft)\b",
)


def detect_entities(text: str) -> dict[str, list[str]]:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return {
        category: [
            label for label, patterns in vocabulary.items()
            if any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)
        ]
        for category, vocabulary in ENTITY_LEXICON.items()
    }


def _sentences(abstract: str) -> list[str]:
    return [part.strip() for part in _SENTENCE.split(abstract) if part.strip()]


def synthesize_evidence(hits: list[dict], query: str, max_sentences: int = 4) -> dict:
    """Return source-exact, deduplicated sentence records with transparent statuses."""
    if max_sentences < 1:
        raise ValueError("max_sentences must be positive")
    sources = []
    evidence = []
    seen_pmids = set()
    for hit in hits:
        pmid = str(hit.get("pmid") or "")
        abstract = str(hit.get("abstract") or "")
        if not pmid.isdigit() or not abstract or pmid in seen_pmids:
            continue
        seen_pmids.add(pmid)
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        source = {
            "pmid": pmid, "url": url, "title": hit.get("title", ""),
            "journal": hit.get("journal", ""), "year": hit.get("year", ""),
            "retrieval_rank": hit.get("rank"),
            "entities_mentioned_in_abstract": detect_entities(abstract),
        }
        sources.append(source)
        candidate_sentences = []
        for index, sentence in enumerate(_sentences(abstract)):
            entities = detect_entities(sentence)
            if not any(entities.values()):
                continue
            candidate_sentences.append((index, sentence, entities))
        # Retain order of occurrence and enforce exact-substring provenance.
        for index, sentence, entities in candidate_sentences[:max_sentences]:
            assert sentence in abstract
            cue = any(re.search(pattern, sentence, flags=re.IGNORECASE)
                      for pattern in EXPERIMENTAL_CUES)
            evidence.append({
                "evidence_id": f"PMID:{pmid}:S{index + 1}",
                "pmid": pmid, "url": url,
                "sentence_index": index + 1,
                "verbatim_excerpt": sentence,
                "entities_mentioned": entities,
                "experimental_language_detected": cue,
                "relationship_status": "co_mention_only_not_verified",
                "causal_support": "not_assessed",
                "evidence_status": "requires_human_review",
            })
    return {
        "question": query,
        "retrieval_status": "retrieved_not_verified",
        "synthesis_status": "candidate_evidence_only",
        "source_count": len(sources),
        "evidence_sentence_count": len(evidence),
        "sources": sources, "evidence": evidence,
        "claims": [],
        "hypotheses": [],
        "limitations": [
            "Entity labels are regex mentions, not normalized biomedical entities",
            "Co-mentions and experimental-language cues do not establish causality",
            "Only retrieved abstracts were inspected; full text was not assessed",
            "No automated scientific claims or hypotheses are asserted",
        ],
    }


def summarize_mentions(report: dict) -> list[dict]:
    """Cross-source entity mention index, not a relationship or support graph."""
    index = defaultdict(set)
    for source in report["sources"]:
        for category, labels in source["entities_mentioned_in_abstract"].items():
            for label in labels:
                index[(category, label)].add(source["pmid"])
    return [
        {"category": category, "entity": label,
         "source_count": len(pmids), "pmids": sorted(pmids)}
        for (category, label), pmids in sorted(index.items())
    ]
