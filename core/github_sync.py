#!/usr/bin/env python3
"""
core/github_sync.py
────────────────────
Pushes YouTube Helper files to:
  https://github.com/akhil304/Personal-Entertainment-Guide

Uses Git Data API (blob → tree → commit → ref) for atomic commits.
Run: python core/github_sync.py
Or:  python core/github_sync.py --files ui/index.html
"""

import os, sys, json, base64, urllib.request, urllib.error
from pathlib import Path

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_USER  = "akhil304"
REPO_NAME    = "Personal-Entertainment-Guide"
BRANCH       = "main"
HEADERS      = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept":        "application/vnd.github+json",
    "Content-Type":  "application/json",
    "User-Agent":    "youtube-helper-sync",
}

# Files to push (relative to project root)
ALL_FILES = [
    "ui/index.html",
    "agents/__init__.py",
    "agents/youtube_helper_agent.py",
    "connectors/__init__.py",
    "connectors/youtube_connector.py",
    "core/__init__.py",
    "core/yt_history_store.py",
    "core/tag_engine.py",
    "core/mood_engine.py",
    "core/usage_tracker.py",
    "core/github_sync.py",
    "storage/.gitkeep",
    "tests/.gitkeep",
    "requirements_yt.txt",
    "README_YT.md",
    ".env.example",
]


def gh(method, path, body=None):
    url  = f"https://api.github.com{path}"
    data = json.dumps(body).encode() if body else None
    req  = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code


def push_files(file_map: dict[str, str], commit_msg: str = "feat: YouTube Helper update"):
    if not GITHUB_TOKEN:
        print("ERROR: Set GITHUB_TOKEN env var first.")
        sys.exit(1)

    print(f"\nConnecting to github.com/{GITHUB_USER}/{REPO_NAME}…")
    info, s = gh("GET", f"/repos/{GITHUB_USER}/{REPO_NAME}")
    if s != 200:
        print(f"Cannot access repo ({s}): {info.get('message')}")
        sys.exit(1)
    print(f"  Repo: {info['full_name']}")

    ref, s = gh("GET", f"/repos/{GITHUB_USER}/{REPO_NAME}/git/refs/heads/{BRANCH}")
    if s != 200:
        print(f"Branch '{BRANCH}' not found."); sys.exit(1)
    head_sha = ref["object"]["sha"]

    commit_info, _ = gh("GET", f"/repos/{GITHUB_USER}/{REPO_NAME}/git/commits/{head_sha}")
    base_tree_sha  = commit_info["tree"]["sha"]

    print(f"\nCreating blobs for {len(file_map)} files…")
    entries = []
    for path, content in file_map.items():
        blob, _ = gh("POST", f"/repos/{GITHUB_USER}/{REPO_NAME}/git/blobs",
                     {"content": content, "encoding": "utf-8"})
        entries.append({"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        print(f"  + {path}")

    tree, _ = gh("POST", f"/repos/{GITHUB_USER}/{REPO_NAME}/git/trees",
                 {"base_tree": base_tree_sha, "tree": entries})

    commit, _ = gh("POST", f"/repos/{GITHUB_USER}/{REPO_NAME}/git/commits",
                   {"message": commit_msg, "tree": tree["sha"], "parents": [head_sha]})

    gh("PATCH", f"/repos/{GITHUB_USER}/{REPO_NAME}/git/refs/heads/{BRANCH}",
       {"sha": commit["sha"], "force": False})

    print(f"\n✅ Pushed! https://github.com/{GITHUB_USER}/{REPO_NAME}")


def read(p: str) -> str:
    try:
        return Path(p).read_text(encoding="utf-8")
    except Exception:
        return ""


if __name__ == "__main__":
    # Allow `--files a.py b.py` to push only specific files
    specific = sys.argv[2:] if len(sys.argv) > 2 and sys.argv[1] == "--files" else None
    target   = specific or ALL_FILES
    file_map = {f: read(f) for f in target}
    push_files(file_map, commit_msg="feat: YouTube Helper — incremental update")
