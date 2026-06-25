#!/usr/bin/env python3
"""
push_yt_helper.py
──────────────────
Pushes YouTube Helper files to:
  https://github.com/akhil304/YouTube_Helper

Usage (Windows):
    set GITHUB_TOKEN=ghp_your_token
    python push_yt_helper.py
"""

import os, json, urllib.request, urllib.error
from pathlib import Path

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_USER  = "akhil304"
REPO_NAME    = "YouTube_Helper"
BRANCH       = "main"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept":        "application/vnd.github+json",
    "Content-Type":  "application/json",
    "User-Agent":    "youtube-helper-push",
}

def gh(method, path, body=None):
    url  = f"https://api.github.com{path}"
    data = json.dumps(body).encode() if body else None
    req  = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code

def read(p):
    try:
        return Path(p).read_text(encoding="utf-8")
    except Exception:
        return ""

def get_head_sha():
    for branch in ("main", "master"):
        d, s = gh("GET", f"/repos/{GITHUB_USER}/{REPO_NAME}/git/refs/heads/{branch}")
        if s == 200 and "object" in d:
            print(f"  Branch: {branch}")
            return d["object"]["sha"], branch
    return None, None

def push():
    if not GITHUB_TOKEN:
        print("ERROR: Set GITHUB_TOKEN first.")
        print("  set GITHUB_TOKEN=ghp_your_token")
        return

    print(f"\nConnecting to github.com/{GITHUB_USER}/{REPO_NAME}...")
    info, s = gh("GET", f"/repos/{GITHUB_USER}/{REPO_NAME}")
    if s != 200:
        print(f"Cannot access repo ({s}): {info.get('message')}")
        print("Check your token has 'repo' scope and the repo exists at github.com/akhil304/YouTube_Helper")
        return
    print(f"  Repo: {info['full_name']}")

    head_sha, branch = get_head_sha()
    if not head_sha:
        print("Could not find main/master branch.")
        return

    commit_info, _ = gh("GET", f"/repos/{GITHUB_USER}/{REPO_NAME}/git/commits/{head_sha}")
    base_tree = commit_info["tree"]["sha"]

    # Files at repo root — no subfolder prefix
    file_map = {
        "ui/index.html":                   read("ui/index.html"),
        "agents/__init__.py":              read("agents/__init__.py"),
        "agents/youtube_helper_agent.py":  read("agents/youtube_helper_agent.py"),
        "connectors/__init__.py":          read("connectors/__init__.py"),
        "connectors/youtube_connector.py": read("connectors/youtube_connector.py"),
        "core/__init__.py":                read("core/__init__.py"),
        "core/yt_history_store.py":        read("core/yt_history_store.py"),
        "core/tag_engine.py":              read("core/tag_engine.py"),
        "core/mood_engine.py":             read("core/mood_engine.py"),
        "core/usage_tracker.py":           read("core/usage_tracker.py"),
        "core/github_sync.py":             read("core/github_sync.py"),
        "requirements_yt.txt":             read("requirements_yt.txt"),
        "README_YT.md":                    read("README_YT.md"),
        ".env.example":                    read(".env.example"),
        "storage/.gitkeep":                "",
        "tests/.gitkeep":                  "",
    }

    print(f"\nUploading {len(file_map)} files...")
    entries = []
    for path, content in file_map.items():
        blob, _ = gh("POST", f"/repos/{GITHUB_USER}/{REPO_NAME}/git/blobs",
                     {"content": content, "encoding": "utf-8"})
        entries.append({"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        print(f"  + {path}")

    tree, _ = gh("POST", f"/repos/{GITHUB_USER}/{REPO_NAME}/git/trees",
                 {"base_tree": base_tree, "tree": entries})

    commit, _ = gh("POST", f"/repos/{GITHUB_USER}/{REPO_NAME}/git/commits", {
        "message": (
            "feat: YouTube Helper AI Agent — initial release\n\n"
            "- Single-file dashboard (Music, Entertainment, Podcasts, Workout)\n"
            "- YouTube OAuth2 connector (liked videos, playlists, subscriptions)\n"
            "- Claude-powered auto-tagging with rule-based fallback\n"
            "- Mood engine: 6 moods x time-of-day recommendation scoring\n"
            "- Watch history store (JSON-backed, CSV export)\n"
            "- Usage monitor with daily/weekly tracking by category\n"
            "- Taste fingerprint from tag/category analysis\n"
            "- AI chat powered by Claude with full history context\n"
            "- Tag editor modal for manual edits\n"
            "- GitHub sync utility for incremental pushes"
        ),
        "tree":    tree["sha"],
        "parents": [head_sha],
    })

    gh("PATCH", f"/repos/{GITHUB_USER}/{REPO_NAME}/git/refs/heads/{branch}",
       {"sha": commit["sha"], "force": False})

    print(f"\n✅ Done!")
    print(f"   https://github.com/{GITHUB_USER}/{REPO_NAME}")

if __name__ == "__main__":
    push()
