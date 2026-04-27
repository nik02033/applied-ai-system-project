from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from src.ollama_client import OllamaConfig, embed_texts
from src.recommender import load_songs, recommend_songs


@dataclass(frozen=True)
class SongDoc:
    song: dict[str, Any]
    text: str


def _song_to_doc_text(song: dict[str, Any]) -> str:
    """
    Turn a song row into a retrieval-friendly description.
    Keep it short, consistent, and grounded in the CSV fields.
    """
    energy = float(song["energy"])
    valence = float(song["valence"])
    acoustic = float(song["acousticness"])
    tempo = float(song["tempo_bpm"])

    if energy >= 0.8:
        energy_tag = "high energy"
    elif energy <= 0.4:
        energy_tag = "low energy"
    else:
        energy_tag = "medium energy"

    if valence >= 0.7:
        valence_tag = "bright/uplifting"
    elif valence <= 0.4:
        valence_tag = "darker/serious"
    else:
        valence_tag = "balanced"

    if acoustic >= 0.75:
        acoustic_tag = "very acoustic"
    elif acoustic <= 0.25:
        acoustic_tag = "very produced/electronic"
    else:
        acoustic_tag = "mixed acoustic/electronic"

    return (
        f"{song['title']} by {song['artist']}.\n"
        f"Genre: {song['genre']}. Mood: {song['mood']}.\n"
        f"Vibe: {energy_tag}, {valence_tag}, {acoustic_tag}.\n"
        f"Audio features: energy {energy:.2f}, valence {valence:.2f}, tempo {tempo:.0f} bpm, "
        f"danceability {float(song['danceability']):.2f}, acousticness {acoustic:.2f}.\n"
        f"Use when someone wants {song['genre']} with a {song['mood']} mood."
    ).strip()


def build_song_docs(csv_path: str) -> list[SongDoc]:
    songs = load_songs(csv_path)
    return [SongDoc(song=s, text=_song_to_doc_text(s)) for s in songs]


def _cosine_sim_matrix(query_vec: np.ndarray, doc_matrix: np.ndarray) -> np.ndarray:
    q = query_vec / (np.linalg.norm(query_vec) + 1e-12)
    d = doc_matrix / (np.linalg.norm(doc_matrix, axis=1, keepdims=True) + 1e-12)
    return d @ q


def _cache_key(config: OllamaConfig, docs: Iterable[SongDoc]) -> str:
    h = hashlib.sha256()
    h.update(config.embed_model.encode("utf-8"))
    for d in docs:
        h.update(str(d.song.get("id", "")).encode("utf-8"))
        h.update(d.text.encode("utf-8"))
    return h.hexdigest()[:16]


@dataclass
class RAGIndex:
    docs: list[SongDoc]
    vectors: np.ndarray  # shape: (N, D)

    def retrieve(self, config: OllamaConfig, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        qv = np.array(embed_texts(config, [query])[0], dtype=np.float32)
        sims = _cosine_sim_matrix(qv, self.vectors)
        idxs = np.argsort(-sims)[:top_k]
        results: list[dict[str, Any]] = []
        for i in idxs:
            doc = self.docs[int(i)]
            results.append(
                {
                    "song": doc.song,
                    "doc_text": doc.text,
                    "similarity": float(sims[int(i)]),
                }
            )
        return results


def load_or_build_index(
    *,
    config: OllamaConfig,
    csv_path: str,
    cache_dir: str = ".cache",
) -> RAGIndex:
    docs = build_song_docs(csv_path)
    cache_root = Path(cache_dir)
    cache_root.mkdir(parents=True, exist_ok=True)

    key = _cache_key(config, docs)
    cache_json = cache_root / f"song_index_{key}.json"
    cache_npy = cache_root / f"song_index_{key}.npy"

    if cache_json.exists() and cache_npy.exists():
        meta = json.loads(cache_json.read_text(encoding="utf-8"))
        vectors = np.load(str(cache_npy))
        # Rehydrate docs from current CSV (meta is just sanity check)
        if meta.get("count") == len(docs):
            return RAGIndex(docs=docs, vectors=vectors)

    vecs = embed_texts(config, [d.text for d in docs])
    mat = np.array(vecs, dtype=np.float32)

    cache_json.write_text(
        json.dumps({"count": len(docs), "embed_model": config.embed_model}, indent=2),
        encoding="utf-8",
    )
    np.save(str(cache_npy), mat)
    return RAGIndex(docs=docs, vectors=mat)


def rerank_with_original_scorer(
    retrieved: list[dict[str, Any]],
    *,
    user_prefs: dict[str, Any],
    k: int = 5,
) -> list[dict[str, Any]]:
    """
    Optional: apply the original deterministic scoring to just the retrieved candidates.
    This keeps the “VibeFinder 1.0” scoring logic as a transparent component in V2.
    """
    songs = [r["song"] for r in retrieved]
    ranked = recommend_songs(user_prefs, songs, k=min(k, len(songs)))
    id_to_row: dict[int, dict[str, Any]] = {int(r["song"]["id"]): r for r in retrieved}

    out: list[dict[str, Any]] = []
    for song, score, reasons in ranked:
        row = id_to_row[int(song["id"])].copy()
        row["score_vibefinder"] = float(score)
        row["reasons_vibefinder"] = reasons
        out.append(row)
    return out

