# Phase 4 — Hybrid biomedical retrieval (BM25 + semantic + RRF)

Phase 4 extends the merged Phase 3 PMID-grounded retrieval without changing
the existing LangGraph agent, FAISS demo index, or PubMed ingestion pipeline.

## Install only the new optional dependency

```bash
pip install -r requirements-semantic.txt
```

The default real sentence encoder is `pritamdeka/S-PubMedBert-MS-MARCO`.
The first invocation downloads model weights from Hugging Face, which requires
internet access and disk space. Review the model license before redistribution.
Model inference is CPU-compatible but can be slow. Set `--model` to a
different compatible SentenceTransformer model if desired.

## Run against the *existing* 47-record QC corpus

```bash
python -m scripts.run_hybrid_retrieval \
  --query "SRC YES1 kinase resistance in triple-negative breast cancer" --k 5
python -m pytest tests/ -v
```

This uses `data/processed/pubmed_articles_qc.json` and computes real semantic
vectors in memory per invocation. It does **not** rebuild FAISS, redownload
PubMed, or persist model embeddings. For larger corpora, add a versioned
embedding cache keyed by model ID and corpus checksum.

## Methods and interpretation

1. Document-level BM25 retrieves exact biomedical vocabulary.
2. SentenceTransformer encodes titles + abstracts and the query; cosine
   similarity ranks documents.
3. Reciprocal Rank Fusion combines rankings with default constant 60.
4. PMID deduplication and source metadata are preserved.

The `fusion_score` is not a probability or evidence confidence. Retrieved
PMIDs are candidates, not verified supporting citations. The default 47
abstracts are a small convenience sample; a proper research evaluation
requires manually labeled relevance judgments and comparison to the Phase 3
BM25 baseline using Recall@K, Precision@K, and MRR.

The existing demo LLM, static hypotheses and SHA-based FAISS embeddings
remain unchanged and should not be used for scientific claims. This phase
implements **retrieval only**, not citation-grounded generation.
