from __future__ import annotations
import json, re
from pathlib import Path
from typing import Any
from Bio import Entrez
from langchain_core.tools import tool
from .config import RAW_DIR, PROCESSED_DIR, settings

GENE_PATTERN = re.compile(r"\b(?:EGFR|ERBB2|HER2|ERBB3|MET|AXL|FGFR1|FGFR2|IGF1R|SRC|JAK2|ABL1|PIK3CA|AKT1|MTOR|MAPK1|MAPK3|ESR1)\b", re.I)
DISEASE_PATTERN = re.compile(r"\b(?:breast cancer|tumou?r|carcinoma|resistance|vaccine|infection|immune response)\b", re.I)

@tool
def pubmed_search(query: str, retmax: int = 10) -> str:
    """Search PubMed and save basic article metadata. Returns JSON records with PMID, title, abstract, journal, year."""
    Entrez.email = settings.ncbi_email
    if settings.ncbi_api_key:
        Entrez.api_key = settings.ncbi_api_key
    handle = Entrez.esearch(db="pubmed", term=query, retmax=retmax, sort="relevance")
    ids = Entrez.read(handle).get("IdList", [])
    if not ids:
        return "[]"
    fetch = Entrez.efetch(db="pubmed", id=",".join(ids), rettype="xml", retmode="xml")
    records = Entrez.read(fetch)
    articles = []
    for item in records.get("PubmedArticle", []):
        medline = item["MedlineCitation"]
        article = medline["Article"]
        pmid = str(medline["PMID"])
        title = str(article.get("ArticleTitle", ""))
        abstract_parts = article.get("Abstract", {}).get("AbstractText", [])
        abstract = " ".join(str(x) for x in abstract_parts)
        journal = str(article.get("Journal", {}).get("Title", ""))
        year = str(article.get("Journal", {}).get("JournalIssue", {}).get("PubDate", {}).get("Year", ""))
        articles.append({"pmid": pmid, "title": title, "abstract": abstract, "journal": journal, "year": year})
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out = RAW_DIR / "pubmed_articles.json"
    out.write_text(json.dumps(articles, indent=2), encoding="utf-8")
    return json.dumps(articles, indent=2)

@tool
def extract_biomedical_entities(text: str) -> str:
    """Extract simple biomedical entities for demo purposes. Replace with SciSpacy/BioBERT for production."""
    genes = sorted({m.group(0).upper().replace("HER2", "ERBB2") for m in GENE_PATTERN.finditer(text)})
    diseases = sorted({m.group(0).lower() for m in DISEASE_PATTERN.finditer(text)})
    return json.dumps({"genes_proteins": genes, "diseases_processes": diseases}, indent=2)

@tool
def generate_hypothesis(evidence_summary: str) -> str:
    """Generate a conservative biomedical hypothesis from an evidence summary."""
    return json.dumps({
        "hypothesis": "Concurrent RTK and non-RTK kinase signaling may create compensatory bypass routes that reduce sensitivity to single-pathway inhibition in breast cancer.",
        "testable_prediction": "Dual perturbation of dominant RTK drivers and SRC/JAK/PI3K-axis nodes should reduce pathway rebound versus monotherapy in resistant models.",
        "validation_plan": ["curate literature", "map kinase pathways", "prioritize genes", "test in public expression/phosphoproteomics datasets"]
    }, indent=2)

@tool
def log_evaluation(question: str, answer: str, confidence: float = 0.5) -> str:
    """Log a RAG answer evaluation record locally as JSONL."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    path = PROCESSED_DIR / "rag_evaluations.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"question": question, "answer": answer, "confidence": confidence}) + "\n")
    return str(path)
