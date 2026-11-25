import json
from pathlib import Path

source = Path("data/raw/pubmed_articles.json")
output = Path("data/processed/pubmed_articles_qc.json")
report = Path("reports/tables/pubmed_qc_summary.json")

articles = json.loads(source.read_text(encoding="utf-8"))

seen = set()
valid = []
missing_abstract = []
duplicates = []

for article in articles:
    pmid = str(article.get("pmid", "")).strip()
    abstract = str(article.get("abstract", "")).strip()

    if not pmid or pmid in seen:
        duplicates.append(pmid)
        continue

    seen.add(pmid)

    if not abstract:
        missing_abstract.append(pmid)
        continue

    valid.append(article)

output.parent.mkdir(parents=True, exist_ok=True)
report.parent.mkdir(parents=True, exist_ok=True)

output.write_text(
    json.dumps(valid, indent=2),
    encoding="utf-8"
)

summary = {
    "total_records": len(articles),
    "valid_records": len(valid),
    "missing_abstract_pmids": missing_abstract,
    "duplicate_or_invalid_pmids": duplicates,
    "abstract_completeness": (
        len(valid) / len(articles) if articles else 0
    )
}

report.write_text(
    json.dumps(summary, indent=2),
    encoding="utf-8"
)

print(json.dumps(summary, indent=2))
