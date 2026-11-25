# Phase 3: Auditable PMID-grounded retrieval

This module adds a reproducible **document-level BM25 baseline** to the existing
PubMed/FAISS demo. It does not replace the FAISS index or change the existing
LangGraph agent; no previous setup or indexing needs to be repeated.

## Run on the existing quality-controlled corpus

```bash
python - <<'PY'
from app.evidence_retrieval import retrieve_evidence
import json
result = retrieve_evidence("SRC YES1 kinase resistance in triple-negative breast cancer", k=5)
print(json.dumps(result, indent=2))
PY
python -m pytest tests/ -v
```

Input: `data/processed/pubmed_articles_qc.json` (already generated locally).
Each hit includes its PMID, title, journal, year, abstract, and PubMed URL.
Only valid numeric PMIDs and nonempty abstracts are retained; duplicates are
removed. Retrieval scores are *ranking scores*, not confidence probabilities.

## Benchmark against expert judgments

Create a local JSON file at `data/processed/relevance_judgments.json`:

```json
[
  {"query": "SRC resistance in TNBC", "relevant_pmids": ["REPLACE_WITH_VERIFIED_PMID"]}
]
```

Replace the placeholder with PMIDs manually judged relevant, then run:

```bash
python scripts/evaluate_retrieval.py --judgments data/processed/relevance_judgments.json --k 5
```

The output reports Recall@K, Precision@K and MRR@K; all require human
relevance judgments. No evaluation score is manufactured in their absence.

## Scientific limitations

- BM25 is lexical, **not a biomedical semantic embedding model**.
- The first 50 PubMed records are a convenience sample, not a systematic review.
- A retrieved abstract is **not proof** that a proposed mechanism is supported.
- PMID links establish provenance, not verification of generated statements.
- The existing fake LLM, SHA-based embeddings, fixed confidence field and demo
  fallback remain separate prototype components; do not present them as
  validated biomedical inference.
- Next: compare a real biomedical sentence-embedding model against this BM25
  baseline on the same expert-labeled query set, then integrate evidence gating
  into the LangGraph synthesis node.
