## VibeFinder 2.0 (Web + RAG) — implementation spec

### Goal
Upgrade the original **VibeFinder 1.0** (content-based scoring recommender) into a **web app** that can answer free-text music requests by using **Retrieval-Augmented Generation (RAG)** over the song catalog.

The RAG feature must be integrated into the main app flow: the model’s response must be grounded in retrieved song “documents,” not generated from generic music knowledge.

### Local AI constraint
Use **local models** via **Ollama**:
- **Embeddings**: `nomic-embed-text`
- **Chat**: `llama3.2` (or any Ollama chat model user has installed)

### User experience (Streamlit)
Inputs:
- Free-text request (e.g., “upbeat pop for running, not too bright”)
- Optional controls: target energy, target valence, acoustic preference, top-k

Outputs:
- Top recommendations (songs from `data/songs.csv`)
- For each song: short explanation (grounded in features and/or reasons)
- “Sources used”: list of retrieved songs used as context
- Debug panel (optional): retrieved chunks, similarity scores, prompts

### Core pipeline (RAG + optional deterministic re-rank)
1. Load songs from `data/songs.csv`
2. Convert each song row into a short text “document” (chunk) + metadata
3. Embed all documents once (cache to disk)
4. For a user query:
   - embed the query
   - retrieve top-N songs by cosine similarity
   - optionally **re-rank** the retrieved candidates using the original deterministic scorer
5. Generate the final response using the retrieved candidates as context

### Guardrails & logging
- Validate Ollama is reachable; show actionable error if not.
- Validate user inputs (ranges, non-empty query).
- Structured logs for: query received → retrieval → generation → output.

### Reliability / evaluation
Add a small evaluation harness that:
- runs fixed queries (5–15)
- checks basic invariants (contains N unique song titles, includes sources, etc.)
- prints a summary (pass/fail counts, avg retrieval similarity)

