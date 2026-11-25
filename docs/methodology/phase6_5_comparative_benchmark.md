# Phase 6.5 — Independent entity-pair benchmark

## Objective

Compare Phase 6.2 and Phase 6.4 on the **same fixed 36 PubMed abstract sentences**.

The two systems emit different predicate ontologies. This first benchmark
therefore measures only **sentence-level, unordered entity-pair detection**,
not predicate classification, relation direction, causality, or clinical efficacy.
Phase 6.2 duplicate predicate variants are collapsed to one pair per sentence.

## Execute

```bash
git fetch origin
git switch feature/phase6-5-comparative-benchmark
python -m pytest tests/ -q
python -m scripts.phase6_5_compare
```

Expected until human annotation: `scores_available: false`, `metrics: null`.
The script reads the existing Phase 6.3 `sentence_audit.csv` and
`gold_relationships.csv`; it does not modify them.

## Annotation requirements

1. Review **all 36 sentences** independently of the model outputs.
2. For each sentence, identify **all eligible molecular/drug/phenotype pairs**
   and enter each supported pair in `gold_relationships.csv` using
   `label=supported`, `review_status=adjudicated`, a reviewer ID, and
   a rationale. Predicate cue may be recorded for later analysis but is
   ignored in this entity-pair benchmark.
3. Only mark `exhaustive_review_complete=yes` after the entire sentence
   has been reviewed for all eligible pairs.
4. Have a second expert review the annotations and adjudicate discrepancies.
   The current CSV format records only the adjudicated outcome, so retain
   separate raw reviewer records for agreement statistics.
5. Preserve the Phase 6.2 baseline, Phase 6.4 outputs, and all evidence IDs.

## Metrics

For each extractor, deduplicate predictions by evidence sentence and unordered
normalized entity pair. Calculate TP/FP/FN, precision, recall, and F1 against
the identical curated gold pair inventory. No metric is emitted until all
source sentences are attested as exhaustively reviewed.

**Scientific limitations:** The manually curated alias crosswalk is deliberately
small. Unknown entities fail closed. Gold completeness and independence are
reviewer attestations, not machine-verifiable facts. The evaluation uses
retrieval-selected abstracts, so it does not measure general biomedical
performance. A future relation-ontology benchmark should evaluate predicate
arguments and evidence qualification separately.
