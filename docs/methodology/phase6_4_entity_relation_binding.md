# Phase 6.4 — Conservative entity normalization and relation-aware binding

## Scope

A **new** extraction branch (not an overwrite of Phase 6.2) uses an explicit
gene-identifier subset and limited surface-pattern binding. This is a pilot,
not general biomedical NER, dependency parsing, HGNC service integration or
clinical drug-target verification.

Gene normalization recognizes SRC (HGNC:11283), CSK (HGNC:2444),
YES1 (HGNC:12841) and FYN (HGNC:4037). The long name
"C-terminal Src kinase" is recognized as CSK and its internal "Src"
is not independently counted as SRC.

## Run

```bash
git fetch origin
git switch feature/phase6-4-entity-relation-binding
python -m pytest tests/ -q
python -m scripts.phase6_4_bind_relations
```

Outputs: `reports/evidence/phase6_4_bound_relations.json` and `.csv`.

The script checks that every source sentence occurs verbatim in the PubMed
abstract QC corpus. It does **not** modify Phase 6.2 predictions or the
Phase 6.3 expert annotation files.

## Bound relations

Only explicit patterns are recognized:

- `SRC inhibitor dasatinib` → dasatinib / inhibits_target_mentioned / SRC
- `dasatinib inhibits SRC` → same predicate
- `paclitaxel-sensitive and -resistant` → two drug/phenotype mentions

The output records the matching text span, rule, sentence-level context and
speculation/aim qualifiers. It does not infer an inhibition-of-resistance
relationship from an SRC inhibitor co-mentioned with chemoresistance.

## Evaluation

Keep the original 16 Phase 6.2 predictions as a fixed baseline. For fair
comparison, annotate all 36 source sentences independently and evaluate both
models against the same curated gold relation inventory. A new output ontology
(subject/predicate/object) will need an explicitly documented mapping to the
older unordered-pair/predicate-cue representation before computing comparative
precision/recall/F1. Do **not** compare raw candidate counts as accuracy.

## Limitations

- Curated gene list covers four symbols only.
- Sentence-local disease context cannot confirm a TNBC study population.
- Surface patterns miss passive voice, long-distance arguments, coordination,
  negation scope and most mechanistic interactions.
- An explicit textual assertion is not automatically an experimentally verified
  interaction. All output remains unverified pending expert adjudication.
