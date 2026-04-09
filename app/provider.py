from __future__ import annotations

from typing import Protocol

from app.config import AppConfig
from app.models import GeneratedDocument, IssueRequest
from app.openai_client import OpenAIResponsesClient


class DocumentGenerator(Protocol):
    def generate_document(self, issue_request: IssueRequest) -> GeneratedDocument:
        ...


def build_generator(config: AppConfig) -> DocumentGenerator:
    return OpenAIResponsesClient(config.openai_api_key or "", config.openai_model)
