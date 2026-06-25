#!/usr/bin/env python3
"""
core/tag_engine.py
───────────────────
Uses Claude to infer tags AND a category for each video
from its title, channel, and description.

Tags encode: genre, mood, time-of-day suitability, topic.
Category ∈ {music, entertainment, podcast, workout, education, news, other}
"""

import json
import re


CATEGORY_RULES = [
    (["music","song","playlist","hip hop","jazz","lofi","lo-fi","beats","album","rap","rock","pop","rnb","classical","edm","piano","guitar"], "music"),
    (["workout","hiit","exercise","fitness","gym","yoga","pilates","running","strength","cardio"], "workout"),
    (["podcast","interview","episode","talk show","conversation","show"], "podcast"),
    (["news","breaking","update","report","politics","economy","world"], "news"),
    (["tutorial","course","learn","how to","explained","lesson","education","study"], "education"),
    (["vlog","comedy","entertainment","sketch","film","movie","show","series","funny","challenge"], "entertainment"),
]

MOOD_MAP = {
    "music":         ["chill","relaxing","ambient","upbeat","energising","focus","melancholic"],
    "workout":       ["energising","motivating","intense","pump-up"],
    "podcast":       ["thoughtful","educational","inspiring","conversational"],
    "entertainment": ["fun","entertaining","light","engaging","emotional"],
    "education":     ["focused","educational","productive"],
    "news":          ["informed","critical","aware"],
    "other":         [],
}

TAG_SYSTEM = """You are a content tagging engine for a personal YouTube history tracker.

Given a video title, channel name, and brief description, return a JSON object with:
  - "category": one of music | entertainment | podcast | workout | education | news | other
  - "tags": list of 3-7 lowercase kebab-case tags capturing genre, mood, topic, and suitable time-of-day

Respond ONLY with valid JSON, no markdown fences, no preamble.

Example output:
{"category":"music","tags":["lo-fi","study","chill","morning","focus"]}
"""


class TagEngine:
    def __init__(self, anthropic_client):
        self.client = anthropic_client

    # ── RULE-BASED FALLBACK ───────────────────
    @staticmethod
    def _rule_based(video: dict) -> tuple[str, list[str]]:
        text = (video.get("title","") + " " + video.get("channel","") + " " + video.get("description","")).lower()
        category = "other"
        for keywords, cat in CATEGORY_RULES:
            if any(kw in text for kw in keywords):
                category = cat
                break
        # simple tag extraction: unique words > 3 chars that aren't stop words
        STOPWORDS = {"with","from","this","that","your","have","been","will","they","what","when","where","which","there","their"}
        words = re.findall(r'\b[a-z]{4,}\b', text)
        tags = list(dict.fromkeys(w for w in words if w not in STOPWORDS))[:5]
        return category, tags

    # ── CLAUDE INFERENCE ─────────────────────
    def infer_tags(self, video: dict) -> list[str]:
        """
        Return tags (and update category) for a video using Claude.
        Falls back to rule-based on API errors.
        """
        prompt = (
            f"Title      : {video.get('title','')}\n"
            f"Channel    : {video.get('channel','')}\n"
            f"Description: {video.get('description','')[:250]}"
        )
        try:
            resp = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=200,
                system=TAG_SYSTEM,
                messages=[{"role":"user","content":prompt}],
            )
            raw = resp.content[0].text.strip()
            data = json.loads(raw)
            video["category"] = data.get("category", video.get("category","other"))
            return data.get("tags", [])
        except Exception:
            category, tags = self._rule_based(video)
            video["category"] = video.get("category") or category
            return tags

    def batch_infer(self, videos: list[dict]) -> list[dict]:
        """Tag a batch of videos, returning them with updated tags/category."""
        for v in videos:
            if not v.get("tags"):
                v["tags"] = self.infer_tags(v)
        return videos
