#!/usr/bin/env python3
"""
core/mood_engine.py
────────────────────
Scores videos against current mood + time slot, returns ranked recommendations.
"""

from datetime import datetime

# Mood → preferred tag signals (positive weights)
MOOD_SIGNALS: dict[str, dict[str, float]] = {
    "😊 Happy":     {"upbeat":2, "fun":2, "energising":1.5, "comedy":1.5, "pop":1, "dance":1},
    "😤 Focused":   {"focus":2, "study":2, "lo-fi":1.8, "instrumental":1.5, "deep-house":1.2, "ambient":1},
    "😔 Chill":     {"chill":2, "relaxing":2, "ambient":1.8, "lo-fi":1.5, "jazz":1.2, "acoustic":1},
    "🔥 Energised": {"energising":2, "pump-up":2, "hiit":1.8, "workout":1.5, "motivating":1.5, "upbeat":1},
    "💪 Workout":   {"workout":3, "hiit":2.5, "gym":2, "fitness":2, "motivating":1.5, "pump-up":1.5},
    "😴 Tired":     {"ambient":2, "relaxing":2, "sleep":2, "chill":1.5, "acoustic":1, "lo-fi":1},
}

# Time slot → preferred category boosts
TIME_SIGNALS: dict[str, dict[str, float]] = {
    "Morning (5–9 AM) — great for workout & podcasts":    {"workout":2, "podcast":1.5, "music":1, "education":1},
    "Midday (9 AM–1 PM) — focus music & talks":           {"education":2, "music":1.5, "podcast":1.2, "entertainment":0.8},
    "Afternoon (1–6 PM) — entertainment & vlogs":         {"entertainment":2, "music":1, "news":1},
    "Evening (6–9 PM) — wind-down podcasts & documentaries": {"podcast":2, "entertainment":1.5, "education":1},
    "Late Night — ambient & chill":                        {"music":2, "entertainment":1, "podcast":1},
}


def _score(video: dict, mood: str, time_slot: str) -> float:
    score = 0.0
    tags = set(video.get("tags") or [])
    category = video.get("category","other")

    # Mood signals from tags
    for tag, weight in MOOD_SIGNALS.get(mood, {}).items():
        if tag in tags:
            score += weight

    # Time-slot signals from category
    for cat, weight in TIME_SIGNALS.get(time_slot, {}).items():
        if category == cat:
            score += weight

    # Small recency boost (newer = higher)
    added = video.get("addedAt","") or video.get("watchedAt","")
    if added:
        try:
            dt = datetime.fromisoformat(added[:10])
            age_days = (datetime.utcnow() - dt).days
            score += max(0, 1 - age_days / 60)
        except ValueError:
            pass

    return score


class MoodEngine:
    def recommend(
        self,
        videos: list[dict],
        mood: str,
        time_slot: str,
        n: int = 8,
    ) -> list[dict]:
        """Return top-N videos ranked for current mood + time slot."""
        scored = []
        for v in videos:
            s = _score(v, mood, time_slot)
            if s > 0:
                scored.append({**v, "_score": round(s, 2)})
        scored.sort(key=lambda x: x["_score"], reverse=True)
        return scored[:n]

    def learn_from_watch(self, video: dict, duration_watched: float, total_duration: float):
        """
        Future: update mood-tag weights based on completion ratio.
        completion_ratio = duration_watched / total_duration
        """
        pass  # hook for future reinforcement learning
