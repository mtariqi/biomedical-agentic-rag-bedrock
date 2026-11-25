"""Run Phase 6.5 independent gold-pair evaluation; no label generation."""
import argparse
import json
from pathlib import Path

from app.comparative_benchmark import evaluate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase62", type=Path,
                        default=Path("reports/evidence/phase6_2_relationships.json"))
    parser.add_argument("--phase64", type=Path,
                        default=Path("reports/evidence/phase6_4_bound_relations.json"))
    parser.add_argument("--synthesis", type=Path,
                        default=Path("reports/evidence/phase6_synthesis.json"))
    parser.add_argument("--annotations", type=Path,
                        default=Path("reports/evidence/phase6_3_annotations"))
    parser.add_argument("--output", type=Path,
                        default=Path("reports/evidence/phase6_5_comparison.json"))
    args = parser.parse_args()
    load = lambda p: json.loads(p.read_text(encoding="utf-8"))
    result = evaluate(
        load(args.phase62), load(args.phase64), load(args.synthesis),
        args.annotations / "sentence_audit.csv",
        args.annotations / "gold_relationships.csv",
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    print("No expert annotations or baseline predictions were modified.")


if __name__ == "__main__":
    main()
