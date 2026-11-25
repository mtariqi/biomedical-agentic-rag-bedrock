# Phase 6.2: Biomedical relationship candidates and evidence classification

## Goal

Convert Phase 6 verbatim PMID-linked sentences into **reviewable** relation candidates without claiming that the described biology is true. This is a conservative rule-based baseline, not a validated biomedical relation extraction model.

## Extraction

A candidate requires two recognized non-model biomedical entity mentions **and** an explicit relation-language cue in the same sentence. Entities are represented as an **unordered pair** because regex cues alone cannot establish the grammatical subject, object, or biological direction. Predicate values such as `inhibition_mentioned` identify text cues, not established inhibition. No causal claim or verified triple is emitted.

Flags for negation and hedging are recorded. Context classes (review, intervention, observational, undetermined) are **sentence-level language heuristics**, not verified study designs. Experimental-model labels are mentions only.

The script validates **every** original Phase 6 evidence excerpt against the locally loaded QC abstract before exporting candidates. Altered evidence causes a hard error.

## Run

```bash
python -m pytest tests/ -v
python -m scripts.phase6_2_relations \
  --input reports/evidence/phase6_synthesis.json
```

Outputs:
- `reports/evidence/phase6_2_relationships.json`
- `reports/evidence/phase6_2_relationships.csv`

## Human adjudication requirements

For each candidate, a domain reviewer must inspect the full source, verify entity normalization, determine grammatical direction and mechanistic interpretation, assess negation and speculation, verify model and treatment, and classify study design. Cross-sentence relationships and unsupported causal conclusions are **not** generated.

The next increment can add a manually reviewed gold-standard set and evaluate relation extraction precision, recall, direction, and negation handling.
