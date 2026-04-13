# Model Card: Music Recommender Simulation

## 1. Model Name  

**VibeMatch CLI** — a tiny content-based recommender that ranks songs from a CSV using genre, mood, energy, valence, and a simple acoustic preference.

---

## 2. Intended Use  

This tool suggests up to five songs from a fixed classroom catalog based on a short taste profile (genre, mood, target energy, valence, and whether the user likes acoustic sounds). It assumes the user can describe what they want in those labels and numbers. It is for learning and demos only, not for real listeners or production traffic.

---

## 3. How the Model Works  

For each song, the program adds points when the genre matches, when the mood matches, and when the song's energy and valence sit close to what the user asked for. It also adds a small bonus if the song's acousticness lines up with whether the user said they like acoustic or produced tracks. Everything is added into one score per song; then the songs are sorted so the highest scores float to the top. The experiment mode in Phase 4 only changes how much genre versus energy counts; the idea stays the same.

---

## 4. Data  

The catalog has **20** songs in `data/songs.csv`, including pop, lofi, rock, jazz, ambient, synthwave, hip-hop, classical, metal, country, r&b, edm, reggae, blues, folk, trap, and indie pop. Moods include happy, chill, intense, focused, moody, hype, peaceful, angry, and others. Extra rows were added after the starter so genres like classical and blues show up. The set is still tiny: many real-world niches (K-pop, gospel, hyperpop) are missing, so some users never get a true genre match.

---

## 5. Strengths  

It behaves sensibly when the profile lines up with the data. **Chill lofi** profiles reliably surface the lofi chill tracks. **High-energy pop** keeps Sunrise City and other pop picks near the top. **Intense rock** pulls Storm Runner first. The printed reasons make it easy to see why a song scored well, which is good for debugging and for explaining results to someone who does not code.

---

## 6. Limitations and Bias  

The scorer cannot resolve conflicting signals. In testing, a profile that asked for **pop**, **melancholic** mood, but **very high energy** still ranked **Gym Hero** (pop, intense, happy-ish valence) above actual sad or mellow tracks, because genre and energy points drowned out the missing mood match. That is a form of **filter bubble**: the system keeps favoring loud pop whenever pop and high energy are both set, even when the mood label does not fit how someone actually feels. The catalog also has only one **melancholic** song (blues), so sad taste has almost nowhere to go. Energy is always a distance score, not higher is better, so a user who wants calm music is not accidentally pushed toward loud tracks—but if they mismatch genre and mood on purpose, the model has no way to complain. Finally, **indie pop** is not the same string as **pop**, so users who think of them as the same family still miss the genre bonus unless we normalize labels.

---

## 7. Evaluation  

I stress-tested **four** profiles in `src/main.py`: **High-Energy Pop**, **Chill Lofi**, **Deep Intense Rock**, and an **adversarial** profile (pop + melancholic mood + club-level energy). The first three mostly matched my intuition. The adversarial one was the eye-opener: **Gym Hero** jumped to number one even though the mood was wrong, which showed how strong the genre and energy rails are. I also ran `python -m src.main --experiment-weights`, which cuts genre weight in half and doubles energy weight. For High-Energy Pop the **order of the top songs did not change**, but the **gaps between scores** grew on the energy line—so the list looked similar even though the math shifted. Full narrative comparisons live in **`reflection.md`**.

---

## 8. Future Work  

Normalize genre aliases (e.g. map indie pop toward pop when the user says pop). Add a **penalty** or cap when mood and valence disagree badly with the track. Pull in **diversity**: after the best match, require the next pick to differ in genre or artist. Support **skips** or **soft** preferences instead of one hard favorite genre.

---

## 9. Personal Reflection  

Building this made it obvious why apps blend **content** features with **what similar people played**. Our toy model only sees tags and numbers, so it happily recommends a hyped workout pop track to someone who said they felt melancholic, as long as pop and high energy still match. That is a good reminder that **Gym Hero** can keep appearing—not because the code loves that song, but because the **rules** and **weights** say loud pop near your target energy wins. Human judgment still has to decide if that output is emotionally right.
