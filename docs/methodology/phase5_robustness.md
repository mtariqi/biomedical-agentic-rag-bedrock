# Phase 5 robustness and relevance-label audit

## PMID 28653902: relevance reassessment

**Article:** *NF-κB as the main node of resistance to receptor tyrosine kinase inhibitors in triple-negative breast cancer.*

The supplied PubMed abstract describes TNBC, resistance to **receptor tyrosine kinase inhibitors**, and NF-κB. It does **not explicitly name EGFR**. The provisional label `1` for *EGFR signaling and resistance to targeted therapy in TNBC* is therefore **borderline**: it supports a broad RTK-resistance interpretation, not a demonstrated EGFR-specific relationship.

Two prespecified scenarios are reported without overwriting the original JSON:

- `original_broad_rtk`: preserve original positive label (5 queries).
- `strict_egfr`: do not count PMID 28653902 as an established EGFR-specific positive. If this leaves the EGFR query with zero known positives, **exclude that query from recall, MRR, and nDCG aggregation** rather than report misleading zero or perfect recall (4 queries).

This is a **sensitivity analysis**, not independent expert adjudication. Full-text review and new corpus search may identify EGFR-specific articles. The strict scenario cannot determine whether the retrieval methods actually perform well on EGFR evidence.

## Multiple cutoffs

Report Recall, Precision, MRR and nDCG at 1, 3, 5, and 10. The denominators and query counts are explicit in the JSON report. Precision@K is computed with K in the denominator.

## RRF sensitivity

Evaluate RRF constants 10, 30, 60, 100 and candidate pools 5, 10, 20, 40. The **pre-existing baseline** is RRF constant 60 and candidate pool 20. Rankings and sentence embeddings are reused within the run, and original relevance labels are not changed.

The parameter grid is descriptive, **not a hyperparameter search used to claim improved held-out performance**. Selecting a best configuration on these same five queries would introduce optimism; evaluate any selected settings on a separate independently annotated test set.

## Run

```bash
python -m scripts.phase5_robustness \
  --judgments data/processed/relevance_judgments.json
```

Output: `reports/evaluation/phase5_robustness.json`.

Requires the existing QC corpus, cached PubMedBERT model, and provisional judgments. No new PubMed download, embedding-index rebuild, or API key is required.
