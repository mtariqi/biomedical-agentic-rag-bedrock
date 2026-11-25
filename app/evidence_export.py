"""Extract source-backed, reviewable abstract excerpts without asserting causality.

No LLM calls. Excerpts are verbatim substrings of the retrieved abstracts.
"""
from __future__ import annotations

import re

_SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
_TARGETS = ("YES1", "SRC", "FYN", "EGFR", "ERBB2", "MAPK", "ERK", "AKT", "NF-κB", "FOXM1")


def evidence_rows(hits: list[dict], max_excerpts: int = 3) -> list[dict]:
    if max_excerpts < 1:
        raise ValueError("max_excerpts must be positive")
    rows = []
    seen = set()
    for hit in hits:
        pmid = str(hit.get("pmid", ""))
        abstract = str(hit.get("abstract") or "")
        if not pmid.isdigit() or not abstract or pmid in seen:
            continue
        seen.add(pmid)
        targets = [
            target for target in _TARGETS
            if re.search(r"(?<![A-Za-z0-9])" + re.escape(target) + r"(?![A-Za-z0-9])",
                         abstract, flags=re.IGNORECASE)
        ]
        sentences = [s.strip() for s in _SENTENCE.split(abstract) if s.strip()]
        excerpts = [
            sentence for sentence in sentences
            if any(re.search(r"(?<![A-Za-z0-9])" + re.escape(target) + r"(?![A-Za-z0-9])",
                             sentence, flags=re.IGNORECASE) for target in targets)
        ][:max_excerpts]
        rows.append({
            "pmid": pmid,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "title": hit.get("title", ""),
            "year": hit.get("year", ""),
            "journal": hit.get("journal", ""),
            "rank": hit.get("rank"),
            "detected_terms_not_verified_entities": targets,
            "verbatim_abstract_excerpts": excerpts,
            "evidence_status": "requires_human_review",
            "study_design": "not_assessed",
            "causal_support": "not_assessed",
        })
    return rows
