# Reflection — comparing profiles

Short notes on how different taste inputs change the top five, in plain language.

---

**High-Energy Pop vs Chill Lofi**

High-Energy Pop chases loud, bright, produced tracks, so the list fills with **pop** and **edm / hip-hop** that sit close to the high energy and valence targets. Chill Lofi does the opposite: the top spots are **lofi** with **chill** mood and soft energy, and the acoustic bonus kicks in because that profile says they like acoustic sounds. Same scoring code, totally different neighborhood of the catalog—so the system is really testing whether your numbers and labels point at “party” or “study.”

---

**Chill Lofi vs Deep Intense Rock**

Chill Lofi rewards low energy and gentle acousticness, so **Library Rain** and **Midnight Coding** fight for first place. Deep Intense Rock wants **rock**, **intense** mood, and high energy, so **Storm Runner** wins and other intense tracks (**trap**, **metal**) show up lower in the list even without a genre match, purely from energy and valence proximity. The big shift is genre and mood: swap those two knobs and the recommender stops acting like a study playlist and starts acting like a gym or highway playlist.

---

**High-Energy Pop vs Deep Intense Rock**

Both profiles ask for high energy, so **Overdrive** and **Block Party Anthem** often linger in the middle of the pack for either user. What moves the winner is the **genre and mood match**: pop + happy lifts **Sunrise City**; rock + intense lifts **Storm Runner**. So the “energy gap” math is shared, but the categorical bonuses decide which lane you stay in. That is why two hype-seeking people can still get different top songs—it is not only how loud the track is.

---

**Adversarial (melancholic + high energy + pop) vs High-Energy Pop**

For a normal High-Energy Pop listener, **Sunrise City** is the star: pop, happy, and close on energy. For the adversarial profile, there is almost no **melancholic pop** in the data, so the model never pays the mood bonus. Instead **Gym Hero** wins: still **pop**, very high energy, wrong mood but huge genre + energy points. Compared to the regular pop profile, the list looks more “intense” and less “happy,” which makes sense in the math but feels wrong emotionally. That gap is the whole point of the edge-case test.

---

**Why Gym Hero keeps showing up for “Happy Pop” people**

If someone says they want **happy pop** and **high energy**, Gym Hero is **pop**, extremely **high energy**, and gets the same “produced” bonus as other radio pop. It only misses the **happy** mood tag because the row says **intense**—but the genre and energy haul can still keep it second or third. So it is not random: the song is a **near miss** that wins on the features we weighted heavily. To a non-programmer: *the app is doing what we told it to do, not what a friend would guess you meant by “happy.”*

---

## Final Project Reflection (VibeFinder 2.0 — Web RAG)

### What I extended from Modules 1–3
My original system (**VibeFinder 1.0**) was a transparent content-based recommender: it scored songs from a CSV using genre/mood matches plus numeric proximity (energy/valence) and returned top picks with “reasons” that showed the math.

For the final project, I turned it into **VibeFinder 2.0**, a Streamlit web app that uses **Retrieval-Augmented Generation (RAG)** with **local Ollama models**. Instead of scoring the whole catalog directly from a structured profile, the system first retrieves the most relevant songs for a free-text prompt, then the LLM generates a recommendation grounded in that retrieved set and lists **“Sources used.”**

### What surprised me while testing reliability
The first time I ran my evaluation harness, everything failed even though the UI outputs looked fine. The problem turned out to be my evaluator: it assumed sources would be formatted as dash bullets, but the model sometimes printed sources inline. I updated the harness to check for grounded song titles (titles that actually appear in the output) rather than relying on formatting.

### Limitations and biases
Even with more songs, the biggest limitation is still catalog coverage and labeling. If the dataset doesn’t contain a clean match for a request, retrieval will return “nearest neighbors” that can feel emotionally off. RAG helps prevent hallucinated recommendations, but it can’t invent songs that aren’t in the catalog.

### Collaboration with AI (one helpful + one flawed)
- Helpful: AI helped me outline the pipeline (retriever → optional re-rank → generator) and shape the README to match the rubric.
- Flawed: AI gave me an incorrect implementation detail for an Ollama endpoint, which caused a confusing “405 method not allowed” error. Fixing it was a good reminder that I still need to verify API details and not trust confident-sounding suggestions blindly.
