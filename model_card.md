# Model Card: VibeFinder (1.0 → 2.0)

## VibeFinder 2.0 (Final Project) — Web RAG Music Recommender

### What it is
**VibeFinder 2.0** is a Streamlit web app that recommends songs from `data/songs.csv` using **Retrieval‑Augmented Generation (RAG)** with **local Ollama models**. The system retrieves relevant songs first (embeddings), then generates a grounded recommendation that includes a **“Sources used”** section.

### Intended use
For learning and portfolio demonstration: show how retrieval + ranking + explanation can work together in a small, testable recommender. Not intended for real users or high-stakes decisions.

### How it works (high level)
1) Convert each song row into a short text “song document”.
2) Embed song documents with a local embedding model and retrieve top‑K for the user’s prompt.
3) Generate the final response with a local chat model using only retrieved songs as context.
4) (Optional) Re-rank retrieved candidates with the original VibeFinder 1.0 scoring for transparency and consistency.

### Data
The catalog is a small CSV with hand-authored labels and numeric features (genre, mood, energy, tempo, valence, danceability, acousticness). This means the system is only as good as what the catalog contains and how consistent the labels are.

### Strengths
- Grounded outputs: recommendations are limited to retrieved catalog songs rather than generic music advice.
- Inspectable behavior: the UI shows candidate songs and the response lists sources used.
- Simple reliability check: an eval script verifies grounding behavior across fixed prompts.

### Limitations / risks
- Catalog bias: retrieval can over-represent whatever the catalog has more of (and under-serve missing genres/moods).
- “Nearest neighbor” problem: if the exact vibe doesn’t exist in the data, the system returns closest matches that can feel off.
- Explanation risk: the model can produce confident-sounding reasons; grounding helps, but doesn’t guarantee perfect “vibe” alignment.

### Evaluation
I run `python -m src.eval_rag`, which sends a small set of predefined prompts through retrieval + generation and checks:
- the response includes “Sources used”
- at least 3 retrieved song titles appear in the output (grounding)

---

## VibeFinder 1.0 (Original Modules 1–3 project)

## Model Name

**VibeFinder 1.0** — a small classroom recommender that ranks songs from a CSV using taste tags and a few numbers.

---

## Goal / Task

The system tries to **suggest which songs in the catalog best fit a user’s profile**. It does not predict plays or skips from real behavior. It only scores each track against things like favorite genre, mood, target energy, and valence, then returns the top matches.

---

## Data Used

There are **20 songs** in `data/songs.csv`. Each row has **genre, mood, energy, tempo (bpm), valence, danceability, and acousticness**. Genres range from pop and lofi to classical, blues, and trap, but the list is still small. Many real genres and moods are missing, so some users never get a clean genre match. **Indie pop** and **pop** are different strings, which trips up matching if we do not normalize labels.

---

## Algorithm Summary

Each song gets **points** that add up to one score. **Genre match** adds the most. **Mood match** adds a smaller chunk. **Energy** and **valence** use “closeness”: the nearer the song is to what you asked, the more points. There is a small **acoustic vs produced** bonus if the song matches that preference. After every song has a score, the program **sorts high to low** and shows the top few. A separate run can **lower genre weight and raise energy weight** to see how sensitive the list is.

---

## Observed Behavior / Biases

When someone asked for **pop**, **melancholic** mood, and **very high energy**, **Gym Hero** still won. Genre and energy mattered more than mood, and there is almost no melancholic pop in the data. So the system can **feel loud and “wrong”** even when it is following the math. That is a **filter bubble** risk: the same kind of track keeps winning if your weights favor genre and hype.

---

## Evaluation Process

I ran **`python -m src.main`** with four profiles: high-energy pop, chill lofi, deep intense rock, and an edge case (sad mood + club energy). The first three mostly matched intuition. The edge case exposed the bias above. I also ran **`--experiment-weights`** (halve genre, double energy). Top order often stayed the same, but **energy** mattered more in the printed reasons. I compared runs side by side in the terminal and wrote short notes in `reflection.md`.

---

## Intended Use and Non-Intended Use

**Intended:** Learning how recommenders turn **features + rules** into a ranked list. Demos in class, debugging scoring, and talking through tradeoffs with plain-language reasons.

**Not intended:** Real streaming products, personalized playlists for paying users, or any decision that should rely on fairness, diversity, or listening history. It does not know what you actually played, skipped, or liked.

---

## Ideas for Improvement

1. **Group similar genres** (e.g. treat indie pop like pop when the user says pop).  
2. **Penalize** big mood or valence mismatches so sad requests do not always lose to loud pop.  
3. **Force variety** in the top five (different artists or genres after the first pick).

---

## Personal Reflection

My biggest learning moment was the **adversarial profile**: the output looked silly emotionally, but the code was doing exactly what we weighted. That split between “correct math” and “good vibe” stuck with me.

**AI tools** helped me draft scoring ideas and boilerplate fast. I still had to **double-check** weights, CSV fields, and whether explanations matched the numbers—models can sound confident when the logic is wrong.

It surprised me that **adding and sorting** could still *feel* like a real recommender when the profiles matched the data. The reasons list made that illusion break in a useful way when things went off the rails.

**If I extended the project**, I would add real **skip/like** simulation or collaborative-style “users like you” on top of content scores, and a **diversity** rule so Gym Hero does not dominate every nearby profile.
