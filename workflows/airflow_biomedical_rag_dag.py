from __future__ import annotations
from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="biomedical_agentic_rag_bedrock",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["bedrock", "rag", "biomedical", "sanofi"],
) as dag:
    ingest_and_answer = BashOperator(
        task_id="run_langgraph_agentic_rag",
        bash_command="cd /opt/airflow/project && python -m app.main",
    )
