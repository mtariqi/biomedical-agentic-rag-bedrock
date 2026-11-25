# Phase 5 — Retrieval benchmarking and evidence candidate extraction

## Scope

Adds comparative BM25, real semantic, and hybrid RRF benchmarking, plus
auditable PubMed abstract excerpt export. No fabricated relevance labels, no
claim-level causal inference, and no LLM-generated citations.

## Expert relevance judgments

Prepare a JSON array containing **independently reviewed** query labels:

```json
[
  {
    "query": "SRC YES1 kinase resistance in triple-negative breast cancer",
    "relevant_pmids": ["39037997", "39390250"]
  }
]
```

**The PMIDs above are an illustrative schema, not certified relevance labels.**
Review the source abstracts and, where possible, full texts before adopting
any relevance labels. Judgments must refer to PMIDs in the QC corpus.
Missing judgments, duplicates, and out-of-corpus PMIDs are rejected.
An exhaustive relevance pool is preferable for unbiased Recall@K.

## Benchmark

```bash
python -m scripts.benchmark_phase5 \
  --judgments data/processed/relevance_judgments.json --k 5
```

The script uses the existing 47 QC abstracts and the locally cached model.
It produces `reports/evaluation/phase5_comparison.json` containing per-query
Recall@K, Precision@K, MRR@K, nDCG@K and method-level means. Metrics are
not meaningful without complete and independently curated relevance labels.

## Reviewable evidence CSV

```bash
python -m scripts.export_evidence_phase5 \
  --query "SRC YES1 kinase resistance in triple-negative breast cancer" --k 10
```

Produces `reports/evidence/tnbc_kinase_evidence.csv` with PMID, URL, title,
detected biomedical terms and verbatim abstract excerpts. These are
**candidate excerpts only**, not verified mechanisms, causal relationships,
clinical recommendations or validated scientific claims.

The CSV exporter intentionally uses BM25 as a no-model dependency baseline.
Hybrid evidence exports can be added after the comparative benchmark is
reviewed. Original abstracts may contain XML/HTML tags; no full-text
evidence verification is performed.
