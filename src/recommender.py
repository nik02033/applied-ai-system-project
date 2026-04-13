import csv
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class Song:
    """Represents a song row from the catalog."""
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float


@dataclass
class UserProfile:
    """User taste used by the OOP Recommender."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    target_valence: float = 0.5


WEIGHT_GENRE = 2.0
WEIGHT_MOOD = 1.0
WEIGHT_ENERGY = 1.5
WEIGHT_VALENCE = 0.5
ACOUSTIC_BONUS = 0.5


def configure_scoring_baseline() -> None:
    """Restore default weights (genre strongest, then energy proximity)."""
    global WEIGHT_GENRE, WEIGHT_MOOD, WEIGHT_ENERGY, WEIGHT_VALENCE, ACOUSTIC_BONUS
    WEIGHT_GENRE = 2.0
    WEIGHT_MOOD = 1.0
    WEIGHT_ENERGY = 1.5
    WEIGHT_VALENCE = 0.5
    ACOUSTIC_BONUS = 0.5


def configure_scoring_experiment_energy_over_genre() -> None:
    """Phase 4 experiment: halve genre weight, double energy weight; other weights unchanged."""
    configure_scoring_baseline()
    global WEIGHT_GENRE, WEIGHT_ENERGY
    WEIGHT_GENRE = 1.0
    WEIGHT_ENERGY = 3.0


def _build_score_and_reasons(
    song_genre: str,
    song_mood: str,
    song_energy: float,
    song_valence: float,
    song_acousticness: float,
    fav_genre: str,
    fav_mood: str,
    target_energy: float,
    target_valence: float,
    likes_acoustic: bool,
) -> Tuple[float, List[str]]:
    """Compute total score and a list of human-readable reasons with point values."""
    score = 0.0
    reasons: List[str] = []

    if song_genre == fav_genre:
        score += WEIGHT_GENRE
        reasons.append(f"genre match (+{WEIGHT_GENRE})")

    if song_mood == fav_mood:
        score += WEIGHT_MOOD
        reasons.append(f"mood match (+{WEIGHT_MOOD})")

    energy_proximity = 1.0 - abs(target_energy - song_energy)
    energy_pts = round(energy_proximity * WEIGHT_ENERGY, 4)
    score += energy_pts
    reasons.append(
        f"energy proximity (+{energy_pts}) — target {target_energy:.2f}, song {song_energy:.2f}"
    )

    valence_proximity = 1.0 - abs(target_valence - song_valence)
    valence_pts = round(valence_proximity * WEIGHT_VALENCE, 4)
    score += valence_pts
    reasons.append(
        f"valence proximity (+{valence_pts}) — target {target_valence:.2f}, song {song_valence:.2f}"
    )

    if likes_acoustic and song_acousticness >= 0.6:
        score += ACOUSTIC_BONUS
        reasons.append(f"acoustic preference aligned (+{ACOUSTIC_BONUS})")
    elif not likes_acoustic and song_acousticness <= 0.3:
        score += ACOUSTIC_BONUS
        reasons.append(f"produced/electric preference aligned (+{ACOUSTIC_BONUS})")

    return round(score, 4), reasons


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Return (total_score, reasons) for one catalog row against CLI user prefs."""
    target_energy = float(user_prefs.get("energy", 0.5))
    target_valence = float(user_prefs.get("valence", 0.5))
    likes_acoustic = bool(user_prefs.get("likes_acoustic", False))

    return _build_score_and_reasons(
        str(song["genre"]),
        str(song["mood"]),
        float(song["energy"]),
        float(song["valence"]),
        float(song["acousticness"]),
        str(user_prefs.get("genre", "")),
        str(user_prefs.get("mood", "")),
        target_energy,
        target_valence,
        likes_acoustic,
    )


def load_songs(csv_path: str) -> List[Dict]:
    """Read songs.csv into dicts with numeric fields coerced for math."""
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["id"] = int(row["id"])
            row["energy"] = float(row["energy"])
            row["tempo_bpm"] = float(row["tempo_bpm"])
            row["valence"] = float(row["valence"])
            row["danceability"] = float(row["danceability"])
            row["acousticness"] = float(row["acousticness"])
            songs.append(row)
    return songs


def recommend_songs(
    user_prefs: Dict, songs: List[Dict], k: int = 5
) -> List[Tuple[Dict, float, List[str]]]:
    """Score every song with score_song, rank with sorted(), return top k."""
    ranked: List[Tuple[Dict, float, List[str]]] = []
    for song in songs:
        total, reasons = score_song(user_prefs, song)
        ranked.append((song, total, reasons))
    ranked = sorted(ranked, key=lambda item: item[1], reverse=True)
    return ranked[:k]


class Recommender:
    """OOP wrapper: same weights and ranking as the functional API."""

    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return top-k Song objects by score (uses sorted copy, original list unchanged)."""
        scored: List[Tuple[Song, float]] = []
        for song in self.songs:
            total, _ = _build_score_and_reasons(
                song.genre,
                song.mood,
                song.energy,
                song.valence,
                song.acousticness,
                user.favorite_genre,
                user.favorite_mood,
                user.target_energy,
                user.target_valence,
                user.likes_acoustic,
            )
            scored.append((song, total))
        scored = sorted(scored, key=lambda pair: pair[1], reverse=True)
        return [s for s, _ in scored[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """One-line summary of why this song fits the user (non-empty string)."""
        _, reasons = _build_score_and_reasons(
            song.genre,
            song.mood,
            song.energy,
            song.valence,
            song.acousticness,
            user.favorite_genre,
            user.favorite_mood,
            user.target_energy,
            user.target_valence,
            user.likes_acoustic,
        )
        return "Recommended because: " + "; ".join(reasons)
