"""Phase 6.4: conservative, explicitly scoped biomedical relation binding.

This module creates *new* rule-based candidates. It does not alter the Phase
6.2 baseline, and never equates co-mention with a verified causal claim.
"""
from __future__ import annotations

import re
from collections import Counter

# HGNC IDs: SRC 11283; CSK 2444; YES1 12841; FYN 4037.
GENES = {
    "SRC": {"hgnc_id": "HGNC:11283", "symbol": "SRC"},
    "CSK": {"hgnc_id": "HGNC:2444", "symbol": "CSK"},
    "YES1": {"hgnc_id": "HGNC:12841", "symbol": "YES1"},
    "FYN": {"hgnc_id": "HGNC:4037", "symbol": "FYN"},
}
DRUGS = {"dasatinib", "paclitaxel", "epirubicin", "docetaxel"}
CONTEXT = {
    "tnbc": re.compile(r"\b(?:TNBC|triple[- ]negative breast cancer)\b", re.I),
    "hormone_receptor": re.compile(r"\b(?:tamoxifen|estrogen receptor|ER-positive|hormone receptor)\b", re.I),
}
AIM = re.compile(r"\b(?:we intend to|we aim(?:ed)? to|we sought to)\b", re.I)
SPECULATIVE = re.compile(r"\b(?:predicted|potential|may|might|suggest(?:s|ed)?)\b", re.I)


def normalize_gene_mentions(sentence: str) -> list[dict]:
    """Conservative gene recognition with CSK long-name span exclusion."""
    csk_spans = [m.span() for m in re.finditer(
        r"\bC-terminal\s+Src\s+kinase\b", sentence, re.I)]
    matches = []
    for symbol in GENES:
        patterns = [rf"\b{symbol}\b"]
        if symbol == "CSK":
            patterns.append(r"\bC-terminal\s+Src\s+kinase\b")
        for pattern in patterns:
            for match in re.finditer(pattern, sentence, re.I):
                if symbol == "SRC" and any(
                    lo <= match.start() and match.end() <= hi
                    for lo, hi in csk_spans
                ):
                    continue
                matches.append({
                    **GENES[symbol],
                    "surface": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                })
    return sorted(matches, key=lambda x: (x["start"], x["end"], x["symbol"]))


def disease_context(sentence: str) -> dict:
    found = [name for name, pattern in CONTEXT.items() if pattern.search(sentence)]
    return {"contexts_mentioned": found,
            "tnbc_specific": found == ["tnbc"],
            "context_verified": False}


def bind_sentence(sentence: str) -> list[dict]:
    """Bind only high-specificity surface constructions, not generic co-mentions.

    Supported patterns:
    * '<GENE> inhibitor <DRUG>' (drug inhibits gene target, as described)
    * '<DRUG> inhibit(s/ed) <GENE>' (explicit predicate arguments)
    * '<DRUG>-sensitive/-resistant' (drug-response phenotype)

    'Supported' here refers only to *textual predicate binding*. It does not
    mean that pharmacological effect or clinical efficacy was verified.
    """
    genes = normalize_gene_mentions(sentence)
    bindings = []
    lower = sentence.lower()
    qualifier = ("study_aim" if AIM.search(sentence) else
                 "speculative" if SPECULATIVE.search(sentence) else "unqualified")
    context = disease_context(sentence)

    def add(subject, predicate, obj, span, rule):
        item = {
            "subject": subject, "predicate": predicate, "object": obj,
            "rule": rule, "text_span": sentence[span[0]:span[1]],
            "evidence_qualification": qualifier,
            "relation_status": "textually_bound_requires_expert_review",
            **context,
        }
        if not any((x["subject"], x["predicate"], x["object"]) ==
                   (subject, predicate, obj) for x in bindings):
            bindings.append(item)

    # Explicit gene inhibitor noun phrase: "SRC inhibitor Dasatinib".
    for gene in genes:
        for drug in DRUGS:
            pattern = re.compile(
                rf"\b{re.escape(gene['surface'])}\s+inhibitor\s+{drug}\b", re.I)
            for match in pattern.finditer(sentence):
                if match.start() != gene["start"]:
                    continue
                add(drug, "inhibits_target_mentioned", gene["symbol"],
                    match.span(), "gene_inhibitor_drug")

    # Explicit verb pattern: "dasatinib inhibits SRC", not generic inhibition.
    for drug in DRUGS:
        for gene in genes:
            pattern = re.compile(
                rf"\b{drug}\s+inhibit(?:s|ed)?\s+{re.escape(gene['surface'])}\b", re.I)
            for match in pattern.finditer(sentence):
                if match.end() != gene["end"]:
                    continue
                add(drug, "inhibits_target_mentioned", gene["symbol"],
                    match.span(), "drug_inhibits_gene")

    # Handle 'paclitaxel-sensitive and -resistant' explicitly.
    for drug in DRUGS:
        for match in re.finditer(
            rf"\b{drug}[- ](?:sensitive|resistant)\b", sentence, re.I):
            phenotype = ("drug_sensitivity" if
                         re.search(r"sensitive$", match.group(0), re.I)
                         else "drug_resistance")
            add(drug, "phenotype_mentioned", phenotype,
                match.span(), "drug_phenotype_adjective")
            if phenotype == "drug_sensitivity":
                tail = sentence[match.end():match.end() + 32]
                paired = re.match(r"\s+and\s+-resistant\b", tail, re.I)
                if paired:
                    add(drug, "phenotype_mentioned", "drug_resistance",
                        (match.start(), match.end() + paired.end()),
                        "coordinated_drug_phenotypes")
    return bindings


def extract_bound_relations(synthesis: dict) -> dict:
    candidates = []
    counts = Counter()
    for row in synthesis.get("evidence", []):
        sentence = row["verbatim_excerpt"]
        for index, binding in enumerate(bind_sentence(sentence), 1):
            counts[binding["rule"]] += 1
            candidates.append({
                "candidate_id": f"{row['evidence_id']}:B{index}",
                "evidence_id": row["evidence_id"],
                "pmid": str(row["pmid"]),
                "verbatim_excerpt": sentence,
                **binding,
            })
    return {
        "question": synthesis.get("question", ""),
        "candidate_count": len(candidates),
        "rule_counts": dict(sorted(counts.items())),
        "candidates": candidates,
        "verified_claims": [],
        "limitations": [
            "Rules cover selected explicit surface patterns, not all biomedical relations",
            "Gene symbols and identifiers are a small manually curated subset",
            "TNBC context is sentence-local and not verified study-level context",
            "No causal mechanism or drug efficacy is inferred",
            "All outputs require independent expert annotation",
        ],
    }
