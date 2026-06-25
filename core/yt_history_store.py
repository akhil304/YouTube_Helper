#!/usr/bin/env python3
"""
core/yt_history_store.py
─────────────────────────
JSON-backed store for all YouTube video history.
Acts as the single source of truth for the agent.
"""

import json
from pathlib import Path
from datetime import datetime

STORE_PATH = Path("storage/yt_history.json")


class YTHistoryStore:
    def __init__(self, path: Path = STORE_PATH):
        self.path = path
        self._data: dict[str, dict] = {}
        self._load()

    # ── PERSISTENCE ──────────────────────────
    def _load(self):
        if self.path.exists():
            self._data = json.loads(self.path.read_text(encoding="utf-8"))

    def save(self):
        self.path.parent.mkdir(exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")

    # ── CRUD ─────────────────────────────────
    def upsert(self, video: dict):
        """Add or update a video record."""
        vid_id = video.get("id")
        if not vid_id:
            return
        existing = self._data.get(vid_id, {})
        # Preserve manual tags if they exist
        if existing.get("tags") and not video.get("tags"):
            video["tags"] = existing["tags"]
        video.setdefault("addedAt", datetime.utcnow().isoformat())
        self._data[vid_id] = {**existing, **video}

    def upsert_many(self, videos: list[dict]):
        for v in videos:
            self.upsert(v)
        self.save()

    def get_by_id(self, vid_id: str) -> dict | None:
        return self._data.get(vid_id)

    def get_all(self) -> list[dict]:
        return list(self._data.values())

    def update_tags(self, vid_id: str, tags: list[str]):
        if vid_id in self._data:
            self._data[vid_id]["tags"] = tags
            self._data[vid_id]["tagsUpdatedAt"] = datetime.utcnow().isoformat()
            self.save()

    def get_by_category(self, category: str) -> list[dict]:
        return [v for v in self._data.values() if v.get("category") == category]

    def get_by_tag(self, tag: str) -> list[dict]:
        return [v for v in self._data.values() if tag in (v.get("tags") or [])]

    # ── SUMMARY ──────────────────────────────
    def get_summary(self) -> dict:
        all_v = self.get_all()
        # Category counts
        cat_counts: dict[str, int] = {}
        for v in all_v:
            c = v.get("category") or "unknown"
            cat_counts[c] = cat_counts.get(c, 0) + 1
        top_cats = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Tag counts
        tag_counts: dict[str, int] = {}
        for v in all_v:
            for t in (v.get("tags") or []):
                tag_counts[t] = tag_counts.get(t, 0) + 1
        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:20]

        # Recent (last 10 by addedAt)
        sorted_v = sorted(all_v, key=lambda x: x.get("addedAt",""), reverse=True)

        return {
            "total_videos":   len(all_v),
            "top_categories": dict(top_cats),
            "top_tags":       [t for t, _ in top_tags],
            "recent":         sorted_v[:10],
        }

    def export_csv(self, out_path: Path = Path("storage/history_export.csv")):
        import csv
        rows = self.get_all()
        if not rows:
            return
        fields = ["id","title","channel","category","tags","source","addedAt","watchedAt"]
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                r = dict(r)
                r["tags"] = ";".join(r.get("tags") or [])
                w.writerow(r)
        print(f"  Exported {len(rows)} rows to {out_path}")
