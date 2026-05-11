from __future__ import annotations

import hashlib
import math
import re
from typing import Any
from uuid import uuid4

import chromadb

from backend.app.knowledge import CONDITION_PROTOCOLS


EMBED_DIMENSION = 128


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def embed_text(text: str) -> list[float]:
    tokens = tokenize(text)
    vector = [0.0] * EMBED_DIMENSION
    if not tokens:
        return vector
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        slot = int.from_bytes(digest[:2], "big") % EMBED_DIMENSION
        vector[slot] += 1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


class ChromaStore:
    def __init__(self, path: str):
        self.client = chromadb.PersistentClient(path=path)
        self.guidance = self.client.get_or_create_collection("mediflow_guidance")
        self.cases = self.client.get_or_create_collection("mediflow_cases")
        self._seed_guidance()

    def _seed_guidance(self) -> None:
        if self.guidance.count() > 0:
            return

        self.guidance.add(
            ids=[item["id"] for item in CONDITION_PROTOCOLS],
            documents=[item["content"] for item in CONDITION_PROTOCOLS],
            metadatas=[{"title": item["title"]} for item in CONDITION_PROTOCOLS],
            embeddings=[embed_text(item["content"]) for item in CONDITION_PROTOCOLS],
        )

    def search_guidance(self, query: str, limit: int = 3) -> list[str]:
        result = self.guidance.query(
            query_embeddings=[embed_text(query)],
            n_results=limit,
        )
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        lines: list[str] = []
        for meta, doc in zip(metas, docs):
            title = meta.get("title", "Guidance")
            lines.append(f"{title}: {doc}")
        return lines

    def search_cases(self, query: str, limit: int = 2) -> list[str]:
        if self.cases.count() == 0:
            return []
        result = self.cases.query(
            query_embeddings=[embed_text(query)],
            n_results=limit,
        )
        docs = result.get("documents", [[]])[0]
        return list(docs)

    def store_case(self, request_payload: dict[str, Any], response_payload: dict[str, Any]) -> str:
        session_id = response_payload["session_id"]
        summary = (
            f"Symptoms: {', '.join(request_payload.get('symptoms', []))}. "
            f"Risk: {response_payload.get('risk_level')}. "
            f"Summary: {response_payload.get('summary')}. "
            f"Follow up: {response_payload.get('follow_up')}."
        )
        self.cases.upsert(
            ids=[session_id or str(uuid4())],
            documents=[summary],
            metadatas=[
                {
                    "name": request_payload.get("name", ""),
                    "duration": request_payload.get("duration", ""),
                    "risk_level": response_payload.get("risk_level", ""),
                }
            ],
            embeddings=[embed_text(summary)],
        )
        return session_id
