"""Create expert annotation templates or evaluate completed annotation CSVs."""
import argparse
import json
from pathlib import Path

from app.annotation_evaluation import prepare_annotations, evaluate_annotations


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--relations", type=Path,
                        default=Path("reports/evidence/phase6_2_relationships.json"))
    parser.add_argument("--synthesis", type=Path,
                        default=Path("reports/evidence/phase6_synthesis.json"))
    parser.add_argument("--output-dir", type=Path,
                        default=Path("reports/evidence/phase6_3_annotations"))
    parser.add_argument("--evaluate", action="store_true")
    args = parser.parse_args()
    relations = json.loads(args.relations.read_text(encoding="utf-8"))
    if args.evaluate:
        result = evaluate_annotations(
            relations, args.output_dir / "candidate_annotations.csv",
            args.output_dir / "sentence_audit.csv",
            args.output_dir / "gold_relationships.csv",
        )
        path = args.output_dir / "evaluation.json"
        path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
    else:
        synthesis = json.loads(args.synthesis.read_text(encoding="utf-8"))
        counts = prepare_annotations(relations, synthesis, args.output_dir)
        print("Annotation templates generated:", counts)
        print("IMPORTANT: running without --evaluate overwrites existing annotation CSVs.")


if __name__ == "__main__":
    main()
