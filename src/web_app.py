from __future__ import annotations

import sys
import time
from pathlib import Path

import streamlit as st

# Streamlit runs files as scripts, so `src.*` imports can fail because sys.path[0] becomes `.../src`.
# Make repo root importable so `from src...` works whether you run from repo root or not.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.ollama_client import OllamaConfig, OllamaError, chat, ping  # noqa: E402
from src.rag_index import load_or_build_index, rerank_with_original_scorer  # noqa: E402


APP_SYSTEM_PROMPT = """You are VibeFinder 2.0, a music recommender assistant.

Rules:
- Only recommend songs that appear in the Retrieved context.
- Use the songs' CSV-based attributes (genre, mood, energy, valence, tempo, acousticness) in your reasoning.
- If the request is ambiguous, ask 1 short clarifying question and still provide a best-effort shortlist.
- Output format:
  1) "Top picks" (numbered list, each with Title — Artist, plus 1–2 sentence explanation)
  2) "Sources used" (bullet list of the song titles you relied on)
"""


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _default_csv_path() -> str:
    return str(_repo_root() / "data" / "songs.csv")


def main() -> None:
    st.set_page_config(page_title="VibeFinder 2.0 — Web RAG", layout="wide")
    st.title("VibeFinder 2.0 — Web RAG Music Recommender")
    st.caption("Local RAG using Ollama (embeddings + chat) grounded in your song catalog.")

    with st.sidebar:
        st.subheader("Local model settings")
        base_url = st.text_input("Ollama base URL", value="http://127.0.0.1:11434")
        chat_model = st.text_input("Chat model", value="llama3.2")
        embed_model = st.text_input("Embedding model", value="nomic-embed-text")
        timeout_s = st.number_input("Timeout (seconds)", min_value=10, max_value=300, value=60)

        st.divider()
        st.subheader("Retrieval & ranking")
        retrieve_k = st.slider("Retrieve top-k candidates", min_value=3, max_value=15, value=8, step=1)
        final_k = st.slider("Show top-k picks", min_value=3, max_value=10, value=5, step=1)
        use_rerank = st.checkbox("Re-rank with original VibeFinder scoring", value=True)
        show_debug = st.checkbox("Show debug (retrieved context + scores)", value=False)

        st.divider()
        st.subheader("Optional preference hints (for re-rank)")
        col_a, col_b = st.columns(2)
        with col_a:
            pref_genre = st.text_input("Preferred genre (optional)", value="")
            pref_mood = st.text_input("Preferred mood (optional)", value="")
        with col_b:
            pref_energy = st.slider("Target energy", 0.0, 1.0, 0.6, 0.01)
            pref_valence = st.slider("Target valence", 0.0, 1.0, 0.6, 0.01)
        likes_acoustic = st.checkbox("Likes acoustic", value=False)

    config = OllamaConfig(
        base_url=base_url.strip(),
        chat_model=chat_model.strip(),
        embed_model=embed_model.strip(),
        timeout_s=float(timeout_s),
    )

    st.subheader("Your request")
    query = st.text_area(
        "Describe what you want to listen to",
        value="Upbeat pop for running, high energy, not too dark.",
        height=90,
    )

    cols = st.columns([1, 1, 2])
    with cols[0]:
        run = st.button("Recommend", type="primary")
    with cols[1]:
        st.button("Clear", on_click=lambda: None)

    if not run:
        return

    query = (query or "").strip()
    if not query:
        st.error("Please enter a non-empty request.")
        return

    try:
        ping(config)
    except OllamaError as e:
        st.error(str(e))
        st.info("Setup tips: install Ollama, run `ollama serve`, then `ollama pull llama3.2` and `ollama pull nomic-embed-text`.")
        return

    csv_path = _default_csv_path()

    t0 = time.time()
    with st.spinner("Building/loading index (cached) and retrieving songs..."):
        index = load_or_build_index(config=config, csv_path=csv_path, cache_dir=str(_repo_root() / ".cache"))
        retrieved = index.retrieve(config, query, top_k=int(retrieve_k))
    t_retrieve = time.time() - t0

    candidates = retrieved
    if use_rerank:
        user_prefs = {
            "genre": pref_genre.strip(),
            "mood": pref_mood.strip(),
            "energy": float(pref_energy),
            "valence": float(pref_valence),
            "likes_acoustic": bool(likes_acoustic),
        }
        candidates = rerank_with_original_scorer(retrieved, user_prefs=user_prefs, k=int(final_k))
    else:
        candidates = candidates[: int(final_k)]

    context_chunks = []
    for r in candidates:
        s = r["song"]
        context_chunks.append(
            f"[{s['id']}] {s['title']} — {s['artist']} | genre={s['genre']} mood={s['mood']} "
            f"energy={s['energy']:.2f} valence={s['valence']:.2f} tempo={s['tempo_bpm']:.0f} "
            f"acousticness={s['acousticness']:.2f} danceability={s['danceability']:.2f}"
        )

    t1 = time.time()
    with st.spinner("Generating answer grounded in retrieved songs..."):
        answer = chat(
            config,
            system=APP_SYSTEM_PROMPT,
            user=f"User request: {query}\nReturn {final_k} picks.",
            context_chunks=context_chunks,
            temperature=0.2,
        )
    t_gen = time.time() - t1

    st.success(f"Done. Retrieval: {t_retrieve:.2f}s · Generation: {t_gen:.2f}s")

    left, right = st.columns([2, 1])
    with left:
        st.subheader("AI output")
        st.write(answer)

    with right:
        st.subheader("Candidates")
        for r in candidates:
            s = r["song"]
            st.markdown(f"**{s['title']}** — {s['artist']}")
            st.caption(f"{s['genre']} · {s['mood']} · energy {s['energy']:.2f} · valence {s['valence']:.2f}")
            if "score_vibefinder" in r:
                st.caption(f"VibeFinder score: {r['score_vibefinder']:.2f}")

    if show_debug:
        st.divider()
        st.subheader("Debug: retrieval results")
        for r in retrieved:
            s = r["song"]
            st.markdown(f"**sim {r['similarity']:.3f}** — {s['title']} — {s['artist']} ({s['genre']}/{s['mood']})")
            st.code(r["doc_text"])


if __name__ == "__main__":
    main()

