# YouTube Helper 🎬

An intelligent personal AI agent that learns your YouTube taste, tracks your history, auto-tags every video, and recommends what to watch based on your **mood** and **time of day**.

---

## Features

| Feature | Description |
|---|---|
| **YouTube OAuth2 Connect** | Full Google OAuth2 flow — pulls liked videos, playlists, subscriptions |
| **History Tracking** | Every watched/liked video stored locally with metadata |
| **AI Auto-Tagging** | Claude infers genre, mood, topic tags for every video |
| **Tag Editor** | Edit tags on any video manually via the dashboard |
| **Sections** | Music · Entertainment · Podcasts · Workout |
| **Time-of-Day Recs** | Morning workout, midday focus, evening wind-down |
| **Mood Engine** | 6 moods (Happy, Focused, Chill, Energised, Workout, Tired) boost relevant content |
| **Usage Monitor** | Daily/weekly watch time by category |
| **Taste Fingerprint** | Weighted profile of your content DNA |
| **AI Chat** | Natural language Q&A about your history and preferences |
| **GitHub Sync** | Push all data/code to your repo automatically |

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements_yt.txt
```

### 2. Set environment variables (Windows)
```bat
set ANTHROPIC_API_KEY=sk-ant-...
set YT_CLIENT_ID=...apps.googleusercontent.com
set YT_CLIENT_SECRET=...
set GITHUB_TOKEN=ghp_...
```

### 3. Get Google OAuth2 Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → APIs & Services → Enable **YouTube Data API v3**
3. Create **OAuth 2.0 Client ID** (Desktop app)
4. Copy Client ID and Secret → paste into Settings in the dashboard

### 4. Open the Dashboard
Open `ui/index.html` in your browser (works offline, no server needed).

### 5. Run the CLI Agent (optional)
```bash
python -m agents.youtube_helper_agent
```

### 6. Push to GitHub
```bash
set GITHUB_TOKEN=ghp_...
python core/github_sync.py
```

---

## Architecture

```
youtube_helper/
├── ui/
│   └── index.html              ← Single-file dashboard (dark theme)
├── agents/
│   └── youtube_helper_agent.py ← Main AI agent + CLI
├── connectors/
│   └── youtube_connector.py    ← YouTube Data API v3 OAuth2
├── core/
│   ├── yt_history_store.py     ← JSON-backed video store
│   ├── tag_engine.py           ← Claude-powered auto-tagging
│   ├── mood_engine.py          ← Time + mood recommendation scorer
│   ├── usage_tracker.py        ← Watch time logging
│   └── github_sync.py          ← Incremental GitHub push
├── storage/                    ← Local data (gitignored)
├── requirements_yt.txt
└── .env.example
```

---

## Mood System

| Mood | Boosted Tags | Boosted Categories |
|---|---|---|
| 😊 Happy | upbeat, fun, energising | Entertainment, Music |
| 😤 Focused | focus, study, lo-fi | Music, Education |
| 😔 Chill | chill, relaxing, ambient | Music |
| 🔥 Energised | energising, pump-up, hiit | Workout, Music |
| 💪 Workout | workout, gym, fitness | Workout |
| 😴 Tired | ambient, relaxing, sleep | Music |

---

## GitHub Pages

Enable at: **Settings → Pages → Branch: main / folder: /ui**

Live URL: `https://akhil304.github.io/Personal-Entertainment-Guide/ui/`
