from __future__ import annotations
from typing import Any
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.embeddings import Embeddings
from .config import settings

class HashEmbeddings(Embeddings):
    """Deterministic local fallback embeddings for tests/demo without AWS credentials."""
    def _embed(self, text: str) -> list[float]:
        import hashlib, math
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        vals = [(b - 128) / 128 for b in digest]
        vec = (vals * 48)[:1536]
        norm = math.sqrt(sum(x*x for x in vec)) or 1.0
        return [x / norm for x in vec]
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]
    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

def get_llm() -> Any:
    if settings.use_fake_llm:
        return FakeListChatModel(responses=[
            "Evidence summary: Retrieved literature suggests kinase bypass and compensatory signaling may contribute to resistance. Structured JSON: {\"summary\": \"demo response\", \"confidence\": 0.55}"
        ])
    from langchain_aws import ChatBedrock
    return ChatBedrock(model_id=settings.bedrock_model_id, region_name=settings.aws_region, model_kwargs={"temperature": 0.1})

def get_embeddings() -> Embeddings:
    if settings.use_fake_llm:
        return HashEmbeddings()
    from langchain_aws import BedrockEmbeddings
    return BedrockEmbeddings(model_id=settings.bedrock_embedding_model_id, region_name=settings.aws_region)
