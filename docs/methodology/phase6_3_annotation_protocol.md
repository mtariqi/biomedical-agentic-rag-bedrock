# Phase 6.3 — Expert annotation and evaluation protocol

## Research objective

Measure candidate-level precision for Phase 6.2 relation extraction; estimate recall/F1 only after an independently exhaustive review of the evaluated evidence sentences. **No model-generated labels count as gold standard.**

## Generate templates

```bash
python -m pytest tests/ -q
python -m scripts.phase6_3_annotate
```

Outputs in `reports/evidence/phase6_3_annotations/`:

1. `candidate_annotations.csv`: all generated candidates (currently 16). Fill `review_status` with `adjudicated`, `label` with `supported`/`unsupported`/`uncertain`, plus `reviewer_id` and `evidence_rationale`. Also record `relation_direction` and `full_text_checked` as applicable. `supported` means the *candidate pairing and predicate cue are justified by the text*, not necessarily a validated causal interaction.
2. `sentence_audit.csv`: all extracted evidence sentences (currently 36). Review **every sentence** for *all* relevant relations, including ones omitted by the extractor. Fill `review_status=adjudicated`, `exhaustive_review_complete=yes`, and `reviewer_id` only after an exhaustive audit.
3. `gold_relationships.csv`: add a row for every relevant manually identified relation in the audited sentences, including those missed by Phase 6.2. Use exactly the entity spellings and predicate-cue vocabulary of the candidate export when evaluating strict exact-match metrics. Assign unique `gold_id`; `label=supported`, `review_status=adjudicated`, reviewer and rationale. This is a narrow **exact-match benchmark**, not semantic equivalence scoring.

## Evaluation

```bash
python -m scripts.phase6_3_annotate --evaluate
```

Precision is withheld until all candidate labels are adjudicated and unambiguous. Recall/F1 are withheld until all supplied sentence-audit rows are explicitly marked exhaustive and the gold relationship inventory is fully adjudicated. These checks cannot independently guarantee that a human reviewer did not overlook a relation.

**Important:** Running without `--evaluate` recreates and overwrites all three annotation templates. Preserve completed annotation CSVs before rerunning.

## Scientific limitations

- The current evidence corpus is a small, query-selected set of PubMed abstracts. Results are a pilot, not a generalizable biomedical relation-extraction benchmark.
- One reviewer is insufficient for inter-rater reliability. For publication, use at least two independent reviewers, blind to predictions when annotating gold relations, reconcile disagreements, and report Cohen's kappa or appropriate agreement measures.
- Exact-match recall is sensitive to entity normalization, predicate vocabulary and duplicate representations; record this limitation and consider a curated relation ontology.
- Verbatim sentence provenance does not imply biological truth, directionality or clinical efficacy.
- Full-text review and study-design verification remain necessary for mechanistic claims.
