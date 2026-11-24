# Biomedical Agentic RAG System for Vaccine & Drug Discovery Intelligence

A portfolio project demonstrating an LLM-powered biomedical intelligence platform for drug discovery, vaccine R&D, clinical research, and translational science.

## Why this project fits Digital R&D

This project simulates an agentic AI system that decomposes a scientific question into retrieval, evidence synthesis, entity extraction, hypothesis generation, and evaluation. It uses LangChain/LangGraph for agent planning and tool orchestration, Amazon Bedrock for managed foundation-model access, PubMed/NCBI for biomedical literature retrieval, FAISS or Bedrock Knowledge Bases for vector retrieval, and Airflow/Snakemake for reproducible workflow execution.

## Reference architecture

```text
User Question
   ↓
LangChain / LangGraph Agent
   ↓
Planner Agent
   ↓
Tools:
   1. PubMed literature retriever
   2. Vector DB / Bedrock Knowledge Base
   3. Gene/protein extraction tool
   4. Summarization tool
   5. Hypothesis generation tool
   6. Evaluation/logging tool
   ↓
Amazon Bedrock LLM
   ↓
Cited biomedical answer + structured JSON output
   ↓
Airflow / Snakemake workflow execution
```

## Core workflow

1. Ingest biomedical papers from PubMed.
2. Chunk and embed abstracts using Amazon Titan Embeddings or local deterministic embeddings in demo mode.
3. Store document embeddings in FAISS locally or migrate to Amazon Bedrock Knowledge Bases / OpenSearch Serverless.
4. Retrieve relevant evidence for a biomedical question.
5. Generate grounded answers with citations.
6. Extract genes, proteins, diseases, and biological processes.
7. Generate conservative, testable hypotheses.
8. Log results for RAG evaluation and reproducibility.

## Example scientific question

```text
What evidence supports RTK and non-RTK kinase redundancy in breast cancer resistance?
```

Expected output:

```text
1. Evidence summary
2. Key genes/proteins
3. Signaling pathways
4. Candidate resistance mechanisms
5. Therapeutic hypothesis
6. Retrieved source citations
7. Confidence score
8. Structured JSON output
```

## Repository structure

```text
biomedical-agentic-rag-bedrock/
├── app/
│   ├── agents.py
│   ├── api.py
│   ├── bedrock_llm.py
│   ├── config.py
│   ├── main.py
│   ├── prompts.py
│   ├── rag_chain.py
│   └── tools.py
├── workflows/
│   ├── Snakefile
│   ├── config.yaml
│   └── airflow_biomedical_rag_dag.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── vector_store/
├── notebooks/
│   └── rag_evaluation.ipynb
├── tests/
│   └── test_rag_pipeline.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── README.md
└── .github/workflows/ci.yml
```

## Quick start: local demo mode

Demo mode runs without AWS credentials and uses deterministic local embeddings plus a fake LLM response for testing.

```bash
git clone <your-repo-url>
cd biomedical-agentic-rag-bedrock
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
pytest -q
python -m app.main
```

## Run the API

```bash
uvicorn app.api:app --reload
```

Then call:

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What evidence supports RTK and non-RTK kinase redundancy in breast cancer resistance?"}'
```

## Enable Amazon Bedrock

Set the following in `.env`:

```bash
USE_FAKE_LLM=false
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0
BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
NCBI_EMAIL=<your-email>
NCBI_API_KEY=<optional-ncbi-api-key>
```

Authenticate with AWS using one of the standard methods:

```bash
aws configure
# or IAM role / SSO / environment variables
```

## Run with Docker

```bash
docker compose up --build
```

## Run with Snakemake

```bash
snakemake -s workflows/Snakefile --cores 1
```

## Airflow deployment note

Place the repository under `/opt/airflow/project` or update the `bash_command` path in `workflows/airflow_biomedical_rag_dag.py`.

## Production extensions

- Replace regex-based entity extraction with SciSpacy, BioBERT, PubTator, or AWS HealthScribe/Comprehend Medical where appropriate.
- Replace FAISS with Amazon Bedrock Knowledge Bases backed by OpenSearch Serverless for managed retrieval.
- Add MLflow metrics for groundedness, citation precision, retrieval recall, entity extraction F1, and answer latency.
- Add LangSmith or OpenTelemetry tracing for agent reasoning, tool calls, and failure modes.
- Add domain-specific datasets: GEO, cBioPortal, TCGA, PRIDE, Reactome, KEGG, DrugBank, and ClinicalTrials.gov.

## Resume bullet

Designed a biomedical agentic RAG system using LangChain, Amazon Bedrock, vector retrieval, and multi-step workflow orchestration to support scientific literature mining, hypothesis generation, and evidence-grounded decision support for drug discovery and vaccine R&D.

## Stronger resume bullet

Built an LLM-powered biomedical intelligence platform using LangChain and Amazon Bedrock, integrating RAG, tool-calling agents, vector search, Airflow/Snakemake workflow orchestration, and structured biomedical entity extraction to simulate agentic AI workflows for drug discovery, clinical research, and translational science.

## LinkedIn/GitHub project description

This project demonstrates an agentic AI architecture for biomedical R&D. It combines LangChain, Amazon Bedrock, retrieval-augmented generation, vector databases, and workflow orchestration with Airflow/Snakemake to decompose complex scientific questions into multi-step reasoning, retrieval, analysis, and hypothesis-generation tasks.

## Notes on current documentation

LangChain provides Bedrock chat-model integrations, Amazon Bedrock Knowledge Bases support RAG with private data sources, and NCBI E-utilities provide programmatic PubMed access through Entrez. See the cited documentation in the project write-up or application notes.
