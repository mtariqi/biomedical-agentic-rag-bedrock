# Phase 6.3.1 — Non-destructive entity and predicate triage

This phase flags likely errors identified in the 16-candidate pilot, while **preserving all original Phase 6.2 predictions and Phase 6.3 expert annotation templates**.

## Run

```bash
git fetch origin
git switch feature/phase6-3-1-relation-quality
python -m pytest tests/ -q
python -m scripts.phase6_3_1_quality
```

Outputs: `reports/evidence/phase6_3_1_quality.json` and `.csv`. The input `reports/evidence/phase6_2_relationships.json` is read-only.

## Flags

- `src_csk_entity_ambiguity`: SRC candidate likely originated from the distinct C-terminal Src kinase (CSK) name.
- `phenotype_predicate_mismatch`: resistance label with sensitivity cue, or vice versa.
- `inhibitor_target_scope_ambiguous`: inhibitor mention is insufficient to conclude inhibition of resistance.
- `study_aim_not_result`: aim language is not evidence of an established relationship.
- `speculative_or_predicted_language`: prediction/hedging requires careful qualification.

Flags are **review priorities, not adjudications**. Do not use them as labels, silently exclude candidates, or calculate precision from them. Human reviewers should annotate all original candidates and all 36 evidence sentences independently.

## Scientific scope

The present workflow is rule-based triage, not biomedical entity linking, dependency parsing, negation-scope resolution, or verified relation extraction. Robust entity normalization (e.g., HGNC identifiers for SRC vs CSK), predicate argument binding, and disease-context extraction should be separately developed and evaluated against manually curated references. Keep baseline and subsequent improved-model evaluations on the same fixed gold corpus.
