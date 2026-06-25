#!/usr/bin/env python3
"""
core/usage_tracker.py
──────────────────────
Tracks daily / weekly watch time by category.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

USAGE_FILE = Path("storage/usage.json")


class UsageTracker:
    def __init__(self):
        self._data: list[dict] = []
        self._load()

    def _load(self):
        if USAGE_FILE.exists():
            self._data = json.loads(USAGE_FILE.read_text())

    def _save(self):
        USAGE_FILE.parent.mkdir(exist_ok=True)
        USAGE_FILE.write_text(json.dumps(self._data, indent=2))

    def log(self, video: dict, minutes: float):
        entry = {
            "video_id": video.get("id"),
            "title":    video.get("title",""),
            "category": video.get("category","other"),
            "minutes":  minutes,
            "ts":       datetime.utcnow().isoformat(),
        }
        self._data.append(entry)
        self._save()

    def report(self) -> dict:
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0)
        week_start  = now - timedelta(days=7)

        today_entries  = [e for e in self._data if datetime.fromisoformat(e["ts"]) >= today_start]
        weekly_entries = [e for e in self._data if datetime.fromisoformat(e["ts"]) >= week_start]

        def by_cat(entries):
            d: dict[str, float] = {}
            for e in entries:
                c = e.get("category","other")
                d[c] = d.get(c, 0) + e["minutes"]
            return d

        return {
            "today_mins":  sum(e["minutes"] for e in today_entries),
            "week_mins":   sum(e["minutes"] for e in weekly_entries),
            "today_by_cat": by_cat(today_entries),
            "week_by_cat":  by_cat(weekly_entries),
        }
