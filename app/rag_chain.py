from __future__ import annotations
import json
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from .bedrock_llm import get_embeddings, get_llm
from .config import RAW_DIR, VECTOR_DIR
from .prompts import SYSTEM_PROMPT, ANSWER_TEMPLATE


def load_pubmed_documents(path: Path | None = None) -> list[Document]:
    path = path or RAW_DIR / "pubmed_articles.json"
    if not path.exists():
        return []
    articles = json.loads(path.read_text(encoding="utf-8"))
    docs = []
    for a in articles:
        text = f"Title: {a.get('title','')}\nAbstract: {a.get('abstract','')}"
        docs.append(Document(page_content=text, metadata={"pmid": a.get("pmid"), "journal": a.get("journal"), "year": a.get("year")}))
    return docs


def build_vector_store(docs: list[Document] | None = None) -> FAISS:
    docs = docs or load_pubmed_documents()
    if not docs:
        docs = [Document(page_content="Demo evidence: EGFR, ERBB2/HER2, MET, AXL, SRC, JAK2 and PI3K signaling may participate in breast cancer therapy resistance through bypass or compensatory pathways.", metadata={"pmid":"DEMO", "year":"NA"})]
    splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=120)
    chunks = splitter.split_documents(docs)
    vectordb = FAISS.from_documents(chunks, get_embeddings())
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    vectordb.save_local(str(VECTOR_DIR / "faiss_index"))
    return vectordb


def load_or_build_vector_store() -> FAISS:
    index_dir = VECTOR_DIR / "faiss_index"
    embeddings = get_embeddings()
    if index_dir.exists():
        return FAISS.load_local(str(index_dir), embeddings, allow_dangerous_deserialization=True)
    return build_vector_store()


def answer_question(question: str, k: int = 5) -> dict:
    vectordb = load_or_build_vector_store()
    docs = vectordb.similarity_search(question, k=k)
    context = "\n\n".join([f"PMID: {d.metadata.get('pmid')} | {d.page_content}" for d in docs])
    prompt = ChatPromptTemplate.from_messages([("system", SYSTEM_PROMPT), ("human", ANSWER_TEMPLATE)])
    chain = prompt | get_llm() | StrOutputParser()
    answer = chain.invoke({"question": question, "context": context})
    citations = [d.metadata for d in docs]
    return {"question": question, "answer": answer, "citations": citations}
