"""CLI for Phase 4 real semantic hybrid retrieval over existing PubMed QC data."""
import argparse
import json
from app.hybrid_retrieval import DEFAULT_MODEL, retrieve_hybrid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()
    result = retrieve_hybrid(args.query, k=args.k, model_name=args.model)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
