"""Auditable PubMed abstract retrieval. No LLM or fabricated evidence.

BM25 is a reproducible lexical baseline, not a semantic embedding model.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

from .config import PROCESSED_DIR

TOKEN_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = frozenset(
    "a an and are as at be by for from how in into is of on or that the to "
    "was were what which with supports evidence role mechanisms".split()
)


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall(text.lower()) if t not in STOPWORDS]


def load_evidence(path: Path | None = None) -> list[dict]:
    """Load QC abstracts and reject missing/duplicate identifiers and abstracts."""
    source = path or PROCESSED_DIR / "pubmed_articles_qc.json"
    if not source.is_file():
        raise FileNotFoundError(
            f"Missing QC corpus: {source}. Run python scripts/qc_pubmed.py first."
        )
    records = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("QC corpus must be a JSON array")
    valid, seen = [], set()
    for item in records:
        if not isinstance(item, dict):
            continue
        pmid = str(item.get("pmid") or "").strip()
        abstract = str(item.get("abstract") or "").strip()
        if not pmid.isdigit() or not abstract or pmid in seen:
            continue
        seen.add(pmid)
        valid.append({
            "pmid": pmid,
            "title": str(item.get("title") or ""),
            "abstract": abstract,
            "journal": str(item.get("journal") or ""),
            "year": str(item.get("year") or ""),
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        })
    return valid


class BM25Retriever:
    """Document-level BM25; keeps full abstract provenance attached to every hit."""

    def __init__(self, records: list[dict], k1: float = 1.5, b: float = 0.75):
        if k1 <= 0 or not 0 <= b <= 1:
            raise ValueError("Invalid BM25 parameters")
        self.records = records
        self.k1, self.b = k1, b
        self.tokens = [
            tokenize(f"{r['title']} {r['abstract']}") for r in records
        ]
        self.term_counts = [Counter(t) for t in self.tokens]
        self.avg_len = sum(map(len, self.tokens)) / len(records) if records else 0
        self.df = Counter()
        for counts in self.term_counts:
            self.df.update(counts.keys())

    def search(self, query: str, k: int = 5) -> list[dict]:
        if k < 1:
            raise ValueError("k must be positive")
        terms = set(tokenize(query))
        if not terms or not self.records:
            return []
        n = len(self.records)
        scored = []
        for record, counts, tokens in zip(self.records, self.term_counts, self.tokens):
            score = 0.0
            length_norm = self.k1 * (
                1 - self.b + self.b * len(tokens) / (self.avg_len or 1)
            )
            for term in terms:
                tf = counts.get(term, 0)
                if not tf:
                    continue
                df = self.df[term]
                idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
                score += idf * tf * (self.k1 + 1) / (tf + length_norm)
            if score > 0:
                scored.append((score, record))
        scored.sort(key=lambda pair: (-pair[0], pair[1]["pmid"]))
        return [
            {
                "rank": rank,
                "score": round(score, 6),
                **record,
            }
            for rank, (score, record) in enumerate(scored[:k], start=1)
        ]


def retrieve_evidence(
    question: str, k: int = 5, path: Path | None = None
) -> dict:
    """Return source-backed search hits; does NOT assert that they support a claim."""
    hits = BM25Retriever(load_evidence(path)).search(question, k)
    return {
        "question": question,
        "retrieval_method": "bm25_lexical_baseline",
        "evidence_status": "retrieved_not_verified",
        "hits": hits,
        "hit_count": len(hits),
    }
