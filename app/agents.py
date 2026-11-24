from __future__ import annotations
from typing import TypedDict
from langgraph.graph import StateGraph, END
from .rag_chain import answer_question, build_vector_store, load_pubmed_documents
from .tools import pubmed_search, extract_biomedical_entities, generate_hypothesis, log_evaluation

class AgentState(TypedDict, total=False):
    question: str
    query: str
    literature: str
    rag: dict
    entities: str
    hypothesis: str
    log_path: str


def plan_query(state: AgentState) -> AgentState:
    q = state["question"]
    state["query"] = f'({q}) AND (breast cancer OR vaccine OR drug resistance OR kinase)'
    return state


def retrieve_literature(state: AgentState) -> AgentState:
    try:
        state["literature"] = pubmed_search.invoke({"query": state["query"], "retmax": 8})
    except Exception as exc:
        state["literature"] = f"PubMed retrieval skipped: {exc}"
    return state


def index_and_answer(state: AgentState) -> AgentState:
    build_vector_store(load_pubmed_documents())
    state["rag"] = answer_question(state["question"], k=5)
    return state


def extract_entities_node(state: AgentState) -> AgentState:
    text = state.get("literature", "") + "\n" + state.get("rag", {}).get("answer", "")
    state["entities"] = extract_biomedical_entities.invoke({"text": text})
    return state


def hypothesis_node(state: AgentState) -> AgentState:
    state["hypothesis"] = generate_hypothesis.invoke({"evidence_summary": state.get("rag", {}).get("answer", "")})
    return state


def evaluate_node(state: AgentState) -> AgentState:
    state["log_path"] = log_evaluation.invoke({"question": state["question"], "answer": state.get("rag", {}).get("answer", ""), "confidence": 0.65})
    return state


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("planner", plan_query)
    graph.add_node("retriever", retrieve_literature)
    graph.add_node("rag_answer", index_and_answer)
    graph.add_node("entity_extraction", extract_entities_node)
    graph.add_node("hypothesis_generation", hypothesis_node)
    graph.add_node("evaluation_logging", evaluate_node)
    graph.set_entry_point("planner")
    graph.add_edge("planner", "retriever")
    graph.add_edge("retriever", "rag_answer")
    graph.add_edge("rag_answer", "entity_extraction")
    graph.add_edge("entity_extraction", "hypothesis_generation")
    graph.add_edge("hypothesis_generation", "evaluation_logging")
    graph.add_edge("evaluation_logging", END)
    return graph.compile()


def run_agent(question: str) -> AgentState:
    return build_graph().invoke({"question": question})
