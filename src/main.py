"""
CLI runner for the Music Recommender Simulation.

Run from the project root:
  python -m src.main
  python -m src.main --experiment-weights   # Phase 4: energy-heavy scoring
"""

from __future__ import annotations

import argparse
from pathlib import Path

from src.recommender import (
    configure_scoring_baseline,
    configure_scoring_experiment_energy_over_genre,
    load_songs,
    recommend_songs,
)


PROFILES: dict[str, dict] = {
    "high_energy_pop": {
        "label": "High-Energy Pop",
        "genre": "pop",
        "mood": "happy",
        "energy": 0.92,
        "valence": 0.88,
        "likes_acoustic": False,
    },
    "chill_lofi": {
        "label": "Chill Lofi",
        "genre": "lofi",
        "mood": "chill",
        "energy": 0.34,
        "valence": 0.58,
        "likes_acoustic": True,
    },
    "deep_intense_rock": {
        "label": "Deep Intense Rock",
        "genre": "rock",
        "mood": "intense",
        "energy": 0.9,
        "valence": 0.45,
        "likes_acoustic": False,
    },
    "adversarial_sad_but_hype": {
        "label": "Edge case: wants melancholic mood + club energy",
        "genre": "pop",
        "mood": "melancholic",
        "energy": 0.9,
        "valence": 0.35,
        "likes_acoustic": False,
    },
}


def _print_recommendations(title: str, user_prefs: dict, songs: list, k: int = 5) -> None:
    """Pretty-print ranked picks with scores and per-feature reasons."""
    genre = user_prefs["genre"]
    mood = user_prefs["mood"]
    energy = user_prefs["energy"]
    valence = user_prefs.get("valence", 0.5)

    print(f"\n  {title}")
    print(f"  Profile: {genre} / {mood}  |  energy {energy}  |  valence {valence}")
    print("  " + "-" * 52)

    rows = recommend_songs(user_prefs, songs, k=k)
    for i, (song, score, reasons) in enumerate(rows, start=1):
        print(f"\n  {i}. {song['title']}")
        print(f"     {song['artist']}  ·  {song['genre']}  ·  {song['mood']}")
        print(f"     Final score: {score:.2f}")
        print("     Reasons:")
        for line in reasons:
            print(f"       • {line}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Music recommender simulation (CLI-first).")
    parser.add_argument(
        "--experiment-weights",
        action="store_true",
        help="Halve genre weight and double energy weight (Phase 4 sensitivity run).",
    )
    args = parser.parse_args()

    if args.experiment_weights:
        configure_scoring_experiment_energy_over_genre()
        mode_banner = "WEIGHT EXPERIMENT (genre 1.0, energy 3.0)"
    else:
        configure_scoring_baseline()
        mode_banner = "BASELINE WEIGHTS (genre 2.0, energy 1.5)"

    root = Path(__file__).resolve().parent.parent
    csv_path = root / "data" / "songs.csv"

    songs = load_songs(str(csv_path))
    print(f"Loaded songs: {len(songs)}")
    print(f"Scoring mode: {mode_banner}")

    print("\n" + "=" * 58)
    print("  Music Recommender — stress test profiles")
    print("=" * 58)

    for _key, prefs in PROFILES.items():
        label = prefs["label"]
        user_prefs = {k: v for k, v in prefs.items() if k != "label"}
        _print_recommendations(f"[{label}]", user_prefs, songs, k=5)

    print("\n" + "=" * 58)
    if args.experiment_weights:
        print("  Tip: run without --experiment-weights to compare baseline rankings.")
    print()


if __name__ == "__main__":
    main()
