#!/usr/bin/env python3
"""
agents/youtube_helper_agent.py
──────────────────────────────
YouTube Helper — core AI agent that ties together:
  • YouTube OAuth2 data pull
  • Tag inference via Claude
  • Time-of-day / mood-based recommendations
  • Conversational chat via Claude API
"""

import os
import json
import datetime
from pathlib import Path
from anthropic import Anthropic

from core.yt_history_store import YTHistoryStore
from core.tag_engine        import TagEngine
from core.mood_engine       import MoodEngine
from core.usage_tracker     import UsageTracker

STORAGE_DIR = Path("storage")
STORAGE_DIR.mkdir(exist_ok=True)

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))


# ─────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────
def build_system_prompt(store: YTHistoryStore, mood: str, time_slot: str) -> str:
    summary = store.get_summary()
    return f"""You are YouTube Helper, an intelligent personal entertainment assistant.

ROLE
- Help the user discover what to watch/listen to based on their history, mood and time of day.
- Answer questions about their habits, top tags, categories and playlists.
- Suggest creative themed sessions (e.g. "90s jazz Sunday morning", "HIIT warm-up playlist").

CURRENT CONTEXT
- Mood      : {mood}
- Time slot : {time_slot}
- Videos tracked: {summary['total_videos']}
- Top categories: {json.dumps(summary['top_categories'])}
- Top tags       : {json.dumps(summary['top_tags'][:10])}
- Recent videos  : {json.dumps([v['title'] for v in summary['recent'][:5]])}

RULES
- Be concise (≤ 4 sentences unless the user asks for more).
- If you recommend content, tie it to their actual history when possible.
- Never make up video titles; use patterns from the data.
- When the user says "tag [video]", call the tag editor flow.
- Use Markdown sparingly — plain conversational text is preferred.
"""


# ─────────────────────────────────────────────
# TIME SLOT HELPER
# ─────────────────────────────────────────────
def get_time_slot() -> str:
    h = datetime.datetime.now().hour
    if   5 <= h < 9:  return "Morning (5–9 AM) — great for workout & podcasts"
    if   9 <= h < 13: return "Midday (9 AM–1 PM) — focus music & talks"
    if  13 <= h < 18: return "Afternoon (1–6 PM) — entertainment & vlogs"
    if  18 <= h < 21: return "Evening (6–9 PM) — wind-down podcasts & documentaries"
    return "Late Night — ambient & chill"


# ─────────────────────────────────────────────
# YOUTUBE HELPER AGENT
# ─────────────────────────────────────────────
class YouTubeHelperAgent:
    """
    Main agent loop. Maintains conversation history and
    coordinates all sub-systems.
    """

    MOODS = ["😊 Happy", "😤 Focused", "😔 Chill", "🔥 Energised", "💪 Workout", "😴 Tired"]

    def __init__(self):
        self.store       = YTHistoryStore()
        self.tag_engine  = TagEngine(client)
        self.mood_engine = MoodEngine()
        self.tracker     = UsageTracker()
        self.history: list[dict] = []
        self.mood = self._detect_mood()

    # ── MOOD ─────────────────────────────────
    def _detect_mood(self) -> str:
        """Auto-detect mood from time of day as a first-run default."""
        h = datetime.datetime.now().hour
        if 5  <= h < 9:  return "💪 Workout"
        if 9  <= h < 13: return "😤 Focused"
        if 13 <= h < 18: return "😊 Happy"
        if 18 <= h < 21: return "😔 Chill"
        return "😴 Tired"

    def set_mood(self, mood: str):
        if mood in self.MOODS:
            self.mood = mood
            print(f"  Mood set to {mood}")
        else:
            print(f"  Available moods: {', '.join(self.MOODS)}")

    # ── CHAT ─────────────────────────────────
    def chat(self, user_msg: str) -> str:
        """Send a message and return the agent's reply."""
        self.history.append({"role": "user", "content": user_msg})

        response = client.messages.create(
            model      = "claude-sonnet-4-6",
            max_tokens = 1000,
            system     = build_system_prompt(self.store, self.mood, get_time_slot()),
            messages   = self.history,
        )
        reply = response.content[0].text
        self.history.append({"role": "assistant", "content": reply})
        return reply

    # ── TAG OPERATIONS ───────────────────────
    def auto_tag_all(self, force: bool = False):
        """Run Claude-powered auto-tagging on every untagged video."""
        videos = self.store.get_all()
        to_tag = [v for v in videos if force or not v.get("tags")]
        if not to_tag:
            print("  All videos already tagged.")
            return
        print(f"  Auto-tagging {len(to_tag)} videos…")
        for v in to_tag:
            tags = self.tag_engine.infer_tags(v)
            self.store.update_tags(v["id"], tags)
            print(f"    ✓ {v['title'][:50]:50s} → {tags}")

    def edit_tags(self, video_id: str, tags: list[str]):
        """Manually set tags for a video."""
        self.store.update_tags(video_id, tags)
        print(f"  Tags updated for video {video_id}: {tags}")

    # ── RECOMMENDATIONS ──────────────────────
    def recommend(self, n: int = 5) -> list[dict]:
        """Get top-N recommendations for current mood + time slot."""
        return self.mood_engine.recommend(
            self.store.get_all(),
            mood=self.mood,
            time_slot=get_time_slot(),
            n=n,
        )

    # ── USAGE ────────────────────────────────
    def log_watch(self, video_id: str, minutes: float):
        """Log that a video was watched for `minutes`."""
        video = self.store.get_by_id(video_id)
        if video:
            self.tracker.log(video, minutes)

    def usage_report(self) -> dict:
        return self.tracker.report()

    # ── INTERACTIVE CLI ──────────────────────
    def run_cli(self):
        """Minimal CLI for terminal testing."""
        print("\n╔══════════════════════════════════╗")
        print("║  YouTube Helper — AI Agent CLI   ║")
        print("╚══════════════════════════════════╝")
        print(f"  Mood: {self.mood}  |  {get_time_slot()}")
        print("  Commands: mood, tag-all, recommend, usage, quit")
        print("  Or just type to chat.\n")

        while True:
            try:
                user = input("You › ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nBye!"); break

            if not user:
                continue
            if user == "quit":
                break
            elif user == "mood":
                for i, m in enumerate(self.MOODS, 1):
                    print(f"  {i}. {m}")
                sel = input("  Choose › ").strip()
                try:
                    self.set_mood(self.MOODS[int(sel)-1])
                except (ValueError, IndexError):
                    print("  Invalid choice.")
            elif user == "tag-all":
                self.auto_tag_all()
            elif user == "recommend":
                recs = self.recommend()
                print("\n  ── Recommendations ──")
                for r in recs:
                    print(f"  ▶ {r['title']} ({r.get('category','?')}) — tags: {r.get('tags',[])}")
            elif user == "usage":
                rpt = self.usage_report()
                print(f"\n  Today : {rpt['today_mins']:.0f} min")
                print(f"  Week  : {rpt['week_mins']:.0f} min")
            else:
                reply = self.chat(user)
                print(f"\nAgent › {reply}\n")


# ─────────────────────────────────────────────
if __name__ == "__main__":
    agent = YouTubeHelperAgent()
    agent.run_cli()
