import json

from app.evidence_retrieval import BM25Retriever, load_evidence, retrieve_evidence
from scripts.evaluate_retrieval import evaluate


def corpus(tmp_path):
    path = tmp_path / "articles.json"
    path.write_text(json.dumps([
        {"pmid": "111", "title": "SRC kinase TNBC", "abstract": "SRC resistance in triple negative breast cancer"},
        {"pmid": "222", "title": "EGFR signaling", "abstract": "EGFR inhibition in breast cancer"},
        {"pmid": "333", "title": "No abstract", "abstract": ""},
        {"pmid": "111", "title": "Duplicate", "abstract": "should be discarded"},
        {"pmid": "DEMO", "title": "Demo", "abstract": "not a real PMID"}
    ]), encoding="utf-8")
    return path


def test_corpus_qc_and_provenance(tmp_path):
    records = load_evidence(corpus(tmp_path))
    assert len(records) == 2
    assert records[0]["url"] == "https://pubmed.ncbi.nlm.nih.gov/111/"


def test_bm25_retrieval(tmp_path):
    result = retrieve_evidence("SRC kinase resistance TNBC", k=2, path=corpus(tmp_path))
    assert result["hits"][0]["pmid"] == "111"
    assert result["evidence_status"] == "retrieved_not_verified"
    assert all(hit["pmid"] != "DEMO" for hit in result["hits"])


def test_no_matches(tmp_path):
    assert BM25Retriever(load_evidence(corpus(tmp_path))).search("xyznonexistent") == []


def test_evaluation_metrics(tmp_path):
    retriever = BM25Retriever(load_evidence(corpus(tmp_path)))
    report = evaluate(
        [{"query": "SRC kinase resistance TNBC", "relevant_pmids": ["111"]}],
        retriever, k=2
    )
    assert report["mean_recall_at_k"] == 1.0
    assert report["mrr_at_k"] == 1.0
    assert report["mean_precision_at_k"] == 0.5
