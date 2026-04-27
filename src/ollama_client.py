from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

import requests


class OllamaError(RuntimeError):
    pass


@dataclass(frozen=True)
class OllamaConfig:
    base_url: str = "http://127.0.0.1:11434"
    chat_model: str = "llama3.2"
    embed_model: str = "nomic-embed-text"
    timeout_s: float = 60.0


def _post_json(url: str, payload: dict[str, Any], timeout_s: float) -> dict[str, Any]:
    try:
        resp = requests.post(url, json=payload, timeout=timeout_s)
    except requests.RequestException as e:
        raise OllamaError(
            "Could not reach Ollama. Is it running locally on http://127.0.0.1:11434 ? "
            "Try: `ollama serve`"
        ) from e

    if resp.status_code >= 400:
        raise OllamaError(f"Ollama error {resp.status_code}: {resp.text[:500]}")

    try:
        return resp.json()
    except json.JSONDecodeError as e:
        raise OllamaError(f"Invalid JSON from Ollama: {resp.text[:200]}") from e


def _get_json(url: str, timeout_s: float) -> dict[str, Any]:
    try:
        resp = requests.get(url, timeout=timeout_s)
    except requests.RequestException as e:
        raise OllamaError(
            "Could not reach Ollama. Is it running locally on http://127.0.0.1:11434 ? "
            "Try: `ollama serve`"
        ) from e

    if resp.status_code >= 400:
        raise OllamaError(f"Ollama error {resp.status_code}: {resp.text[:500]}")

    try:
        return resp.json()
    except json.JSONDecodeError as e:
        raise OllamaError(f"Invalid JSON from Ollama: {resp.text[:200]}") from e


def ping(config: OllamaConfig) -> None:
    """Raise OllamaError if Ollama is unreachable."""
    # Ollama tags endpoint is GET (POST returns 405).
    _get_json(f"{config.base_url}/api/tags", timeout_s=config.timeout_s)


def embed_texts(config: OllamaConfig, texts: Sequence[str]) -> list[list[float]]:
    """Embed texts via Ollama embeddings API. Returns one vector per input."""
    vectors: list[list[float]] = []
    for t in texts:
        out = _post_json(
            f"{config.base_url}/api/embeddings",
            payload={"model": config.embed_model, "prompt": t},
            timeout_s=config.timeout_s,
        )
        emb = out.get("embedding")
        if not isinstance(emb, list) or not emb:
            raise OllamaError("Ollama embeddings response missing `embedding`.")
        vectors.append([float(x) for x in emb])
    return vectors


def chat(
    config: OllamaConfig,
    *,
    system: str,
    user: str,
    context_chunks: Iterable[str] | None = None,
    temperature: float = 0.2,
) -> str:
    """Chat via Ollama generate endpoint; returns plain text response."""
    context = ""
    if context_chunks:
        context = "\n\n".join(context_chunks)

    prompt = f"{user}\n\n---\nRetrieved context:\n{context}".strip()
    out = _post_json(
        f"{config.base_url}/api/generate",
        payload={
            "model": config.chat_model,
            "system": system,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        },
        timeout_s=config.timeout_s,
    )
    resp = out.get("response")
    if not isinstance(resp, str):
        raise OllamaError("Ollama generate response missing `response`.")
    return resp.strip()

