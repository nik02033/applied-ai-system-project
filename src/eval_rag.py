from __future__ import annotations

import json
import re
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.ollama_client import OllamaConfig, OllamaError, chat, ping
from src.rag_index import load_or_build_index


SYSTEM = """You are VibeFinder 2.0 evaluator mode.
You must recommend songs ONLY from the provided context.
Always include a "Sources used" section with bullet points listing song titles you used.
"""


@dataclass(frozen=True)
class EvalCase:
    name: str
    query: str
    min_sources: int = 3


CASES: list[EvalCase] = [
    EvalCase("running_pop", "Upbeat pop for running, high energy, not too dark.", 3),
    EvalCase("study_lofi", "Chill lofi for studying, low energy, more acoustic.", 3),
    EvalCase("sad_blues", "Melancholic, reflective, acoustic-leaning. Slow tempo if possible.", 3),
    EvalCase("party_edm", "Euphoric EDM for a party. Very high energy and danceable.", 3),
    EvalCase("rock_intense", "Intense rock for the gym. High energy, not happy-pop.", 3),
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _csv_path() -> str:
    return str(_repo_root() / "data" / "songs.csv")


def _extract_sources(text: str) -> list[str]:
    # very lightweight parser: look for a "Sources used" section and bullets under it
    m = re.search(r"Sources used\s*(?:\n|\r\n)([\s\S]+)$", text, flags=re.IGNORECASE)
    if not m:
        # Fallback: sometimes the model outputs sources on the same line.
        m_inline = re.search(r"Sources used\s*:\s*(.+)$", text, flags=re.IGNORECASE | re.MULTILINE)
        if not m_inline:
            return []
        tail = m_inline.group(1).strip()
        # Common separators seen in outputs: bullets, middots, pipes, commas
        parts = re.split(r"\s*(?:•|·|\||,|;)\s*", tail)
        return [p.strip() for p in parts if p.strip()]
    tail = m.group(1)
    sources: list[str] = []
    for line in tail.splitlines():
        line = line.strip()
        if line.startswith("-") or line.startswith("•"):
            sources.append(line.lstrip("-•").strip())
    return [s for s in sources if s]


def _count_grounded_titles(text: str, titles: list[str]) -> int:
    """
    Robust grounding check: count how many retrieved titles appear anywhere in the output.
    This avoids brittle parsing differences (bullets vs inline lists).
    """
    t = text.lower()
    seen = set()
    for title in titles:
        key = title.strip()
        if not key:
            continue
        if key.lower() in t:
            seen.add(key.lower())
    return len(seen)


def run_eval(
    *,
    config: OllamaConfig,
    retrieve_k: int = 8,
    cache_dir: str | None = None,
) -> dict[str, Any]:
    ping(config)

    cache_dir = cache_dir or str(_repo_root() / ".cache")
    index = load_or_build_index(config=config, csv_path=_csv_path(), cache_dir=cache_dir)

    results: list[dict[str, Any]] = []
    sims_all: list[float] = []
    passed = 0

    for case in CASES:
        t0 = time.time()
        retrieved = index.retrieve(config, case.query, top_k=retrieve_k)
        sims_all.extend([float(r["similarity"]) for r in retrieved])

        context = []
        for r in retrieved:
            s = r["song"]
            context.append(f"{s['title']} — {s['artist']} | {s['genre']}/{s['mood']} energy={s['energy']:.2f} valence={s['valence']:.2f}")

        answer = chat(
            config,
            system=SYSTEM,
            user=f"Query: {case.query}\nReturn top picks + Sources used.",
            context_chunks=context,
            temperature=0.2,
        )
        elapsed = time.time() - t0
        sources = _extract_sources(answer)
        retrieved_titles = [r["song"]["title"] for r in retrieved]
        grounded_count = _count_grounded_titles(answer, retrieved_titles)

        # Require: explicit "Sources used" signal + at least N grounded titles
        ok_sources = ("sources used" in answer.lower()) and (grounded_count >= case.min_sources)
        ok_nonempty = len(answer.strip()) > 0
        ok = ok_sources and ok_nonempty
        if ok:
            passed += 1

        results.append(
            {
                "case": case.name,
                "ok": ok,
                "ok_sources": ok_sources,
                "sources_count": grounded_count,
                "elapsed_s": round(elapsed, 3),
                "query": case.query,
            }
        )

    summary = {
        "passed": passed,
        "total": len(CASES),
        "avg_retrieval_similarity": round(statistics.mean(sims_all), 3) if sims_all else None,
        "cases": results,
    }
    return summary


def main() -> None:
    config = OllamaConfig()
    try:
        summary = run_eval(config=config)
    except OllamaError as e:
        raise SystemExit(str(e))

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

