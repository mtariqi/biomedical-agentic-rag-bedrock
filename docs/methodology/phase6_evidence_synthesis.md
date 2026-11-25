# Phase 6: PMID-grounded biomedical evidence synthesis (initial implementation)

## Scope

This is a **deterministic, human-reviewable evidence candidate generator**, not an autonomous clinical research conclusion engine. It reuses the existing QC PubMed abstract corpus, PubMedBERT semantic model, BM25 and RRF constant 60 / candidate pool 20.

## Outputs

- `reports/evidence/phase6_synthesis.json`: provenance, source-level entity mentions, sentence-level candidate evidence, limitations and entity mention index.
- `reports/evidence/phase6_synthesis.csv`: reviewer-friendly sentence records.

Each evidence sentence is copied verbatim from a retrieved abstract and links to its PMID. Detected entities are regex-based *mentions*. Experimental-language detection is a heuristic, not a study design assessment. Every sentence is labeled `co_mention_only_not_verified`, `causal_support=not_assessed`, and `requires_human_review`.

The `claims` and `hypotheses` lists remain empty intentionally: no source-verified mechanistic claim or model-generated hypothesis is invented.

## Run

```bash
python -m pytest tests/ -q
python -m scripts.phase6_synthesize \
  --query "SRC YES1 kinase resistance in triple-negative breast cancer" \
  --k 10 --candidate-k 20
```

## Review requirements before scientific publication

1. Independently adjudicate evidence relevance and relation type from source full text.
2. Normalize entities against authoritative identifiers (HGNC, ChEBI/DrugBank, Reactome).
3. Distinguish mechanistic perturbation evidence from observational association.
4. Document model systems, direction of effect, species and treatment conditions.
5. Validate any LLM-generated summary sentence against exact supporting source excerpts.
6. Expand beyond the pilot 47-abstract corpus and independently annotate a test set.

No API key is required for deterministic synthesis; the semantic model may generate a nonblocking Hugging Face unauthenticated-request warning.
