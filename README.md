# YouTube Helper 🎬

An intelligent personal AI agent that learns your YouTube taste, tracks your history, auto-tags every video, and recommends what to watch based on your **mood** and **time of day**.

---

## 🔗 Live App

**https://akhil304.github.io/YouTube_Helper/**

---

## Features

| Feature | Description |
|---|---|
| **YouTube OAuth2 Connect** | Full Google OAuth2 — pulls liked videos, playlists, subscriptions |
| **Playlist Manager** | Accordion view of all playlists, drag & drop reorder, add/remove videos |
| **Two-Way Sync** | Pull from YouTube + Push changes back via API |
| **History Tracking** | Sync liked videos, subscriptions, playlist content |
| **AI Auto-Tagging** | Claude infers genre, mood, topic tags for every video |
| **Tag Editor** | Edit tags on any video manually |
| **Sections** | Music · Entertainment · Podcasts · Workout |
| **Mood Engine** | 6 moods × time-of-day recommendation scoring |
| **Usage Monitor** | Daily/weekly watch time by category with goal tracking |
| **Taste Fingerprint** | Your content DNA from tag & category analysis |
| **AI Chat** | Claude-powered Q&A with your full watch history as context |
| **Mobile Responsive** | Bottom nav bar, slide-in sidebar, touch-friendly |
| **Google Takeout Import** | Import full watch history from all devices |
| **GitHub Release Button** | Push new releases from inside the dashboard Settings |

---

## Quick Start

1. Open **https://akhil304.github.io/YouTube_Helper/**
2. Go to **Settings → YouTube Connection**
3. Paste your Google OAuth2 Client ID → click **Save**
4. Click **Connect YouTube** in the sidebar → sign in with Google
5. Go to **History → Sync History** to pull your videos
6. Go to **Playlists → Pull from YouTube** to sync all playlists

---

## Google OAuth2 Setup

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create project → Enable **YouTube Data API v3**
3. Create **OAuth 2.0 Client ID** (Web application)
4. Set:
   - **Authorised JavaScript origins:** `https://akhil304.github.io`
   - **Authorised redirect URIs:** `https://akhil304.github.io/YouTube_Helper/`
5. Add your Gmail as a test user under **Audience → Test Users**

---

## Architecture

```
YouTube_Helper/
├── index.html                  ← Root (served by GitHub Pages)
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
└── requirements_yt.txt
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

Live URL: **https://akhil304.github.io/YouTube_Helper/**

Served from: `main` branch / root `/`

## Releases

All releases: **https://github.com/akhil304/YouTube_Helper/releases**
