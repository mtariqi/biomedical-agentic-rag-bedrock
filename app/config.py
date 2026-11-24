from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
VECTOR_DIR = DATA_DIR / "vector_store"

class Settings(BaseSettings):
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    bedrock_model_id: str = Field(default="anthropic.claude-3-5-sonnet-20240620-v1:0", alias="BEDROCK_MODEL_ID")
    bedrock_embedding_model_id: str = Field(default="amazon.titan-embed-text-v2:0", alias="BEDROCK_EMBEDDING_MODEL_ID")
    ncbi_email: str = Field(default="your.email@example.com", alias="NCBI_EMAIL")
    ncbi_api_key: str | None = Field(default=None, alias="NCBI_API_KEY")
    use_fake_llm: bool = Field(default=True, alias="USE_FAKE_LLM")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
