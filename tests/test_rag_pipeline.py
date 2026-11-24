from app.rag_chain import answer_question, build_vector_store
from app.tools import extract_biomedical_entities


def test_entity_extraction():
    out = extract_biomedical_entities.invoke({"text": "EGFR, HER2, SRC and JAK2 are relevant to breast cancer resistance."})
    assert "EGFR" in out
    assert "ERBB2" in out
    assert "breast cancer" in out


def test_rag_answer_demo_mode():
    build_vector_store()
    result = answer_question("What evidence supports RTK and non-RTK kinase redundancy in breast cancer resistance?")
    assert "answer" in result
    assert "citations" in result
