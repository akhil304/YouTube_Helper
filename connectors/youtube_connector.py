#!/usr/bin/env python3
"""
connectors/youtube_connector.py
────────────────────────────────
Connects to YouTube Data API v3 via OAuth2.
Pulls: liked videos, playlists, watch history proxy.

Usage
-----
    from connectors.youtube_connector import YouTubeConnector
    yt = YouTubeConnector()
    yt.authenticate()
    videos = yt.get_liked_videos(max_results=50)
    playlists = yt.get_playlists()
"""

import os
import json
import webbrowser
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
import urllib.request

TOKEN_FILE  = Path("storage/yt_token.json")
SCOPES      = "https://www.googleapis.com/auth/youtube.readonly"
REDIRECT_URI= "http://localhost:8090/callback"
AUTH_URL    = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL   = "https://oauth2.googleapis.com/token"
API_BASE    = "https://www.googleapis.com/youtube/v3"


class _CallbackHandler(BaseHTTPRequestHandler):
    code = None
    def log_message(self, *a): pass
    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        _CallbackHandler.code = params.get("code", [None])[0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"<h2>YouTube Helper: auth complete. You can close this tab.</h2>")


class YouTubeConnector:
    """OAuth2 connector for YouTube Data API v3."""

    def __init__(self):
        self.client_id     = os.environ.get("YT_CLIENT_ID", "")
        self.client_secret = os.environ.get("YT_CLIENT_SECRET", "")
        self.access_token  = None
        self.refresh_token = None
        self._load_token()

    # ── TOKEN PERSISTENCE ─────────────────────
    def _load_token(self):
        if TOKEN_FILE.exists():
            d = json.loads(TOKEN_FILE.read_text())
            self.access_token  = d.get("access_token")
            self.refresh_token = d.get("refresh_token")

    def _save_token(self, data: dict):
        TOKEN_FILE.parent.mkdir(exist_ok=True)
        TOKEN_FILE.write_text(json.dumps(data, indent=2))
        self.access_token  = data.get("access_token")
        self.refresh_token = data.get("refresh_token")

    # ── OAUTH FLOW ────────────────────────────
    def authenticate(self) -> bool:
        """Full OAuth2 auth. Opens browser, waits for callback."""
        if not self.client_id:
            raise ValueError("Set YT_CLIENT_ID env var (from Google Cloud Console).")
        if self.access_token:
            print("  Already authenticated.")
            return True

        params = {
            "client_id":     self.client_id,
            "redirect_uri":  REDIRECT_URI,
            "response_type": "code",
            "scope":         SCOPES,
            "access_type":   "offline",
            "prompt":        "consent",
        }
        url = AUTH_URL + "?" + urlencode(params)
        print(f"\n  Opening browser for YouTube auth…\n  {url}\n")
        webbrowser.open(url)

        server = HTTPServer(("localhost", 8090), _CallbackHandler)
        print("  Waiting for callback on http://localhost:8090 …")
        while _CallbackHandler.code is None:
            server.handle_request()
        code = _CallbackHandler.code
        server.server_close()

        # Exchange code for tokens
        body = urlencode({
            "code":          code,
            "client_id":     self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri":  REDIRECT_URI,
            "grant_type":    "authorization_code",
        }).encode()
        req  = urllib.request.Request(TOKEN_URL, data=body, method="POST")
        with urllib.request.urlopen(req) as r:
            token_data = json.loads(r.read())
        self._save_token(token_data)
        print("  ✓ Authenticated and token saved.")
        return True

    def _refresh(self):
        if not self.refresh_token:
            raise RuntimeError("No refresh token — call authenticate() first.")
        body = urlencode({
            "refresh_token": self.refresh_token,
            "client_id":     self.client_id,
            "client_secret": self.client_secret,
            "grant_type":    "refresh_token",
        }).encode()
        req = urllib.request.Request(TOKEN_URL, data=body, method="POST")
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read())
        data.setdefault("refresh_token", self.refresh_token)
        self._save_token(data)

    def _get(self, endpoint: str, params: dict) -> dict:
        params["key"] = self.access_token  # use access token as bearer
        url = API_BASE + endpoint + "?" + urlencode(params)
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.access_token}"})
        try:
            with urllib.request.urlopen(req) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 401:
                self._refresh()
                return self._get(endpoint, params)
            raise

    # ── DATA FETCHERS ─────────────────────────
    def get_liked_videos(self, max_results: int = 50) -> list[dict]:
        """Fetch the authenticated user's liked videos."""
        items, page_token = [], None
        while len(items) < max_results:
            params = {
                "part":       "snippet,contentDetails",
                "myRating":   "like",
                "maxResults": min(50, max_results - len(items)),
            }
            if page_token:
                params["pageToken"] = page_token
            data = self._get("/videos", params)
            for item in data.get("items", []):
                sn = item["snippet"]
                items.append({
                    "id":          item["id"],
                    "title":       sn.get("title", ""),
                    "channel":     sn.get("channelTitle", ""),
                    "description": sn.get("description", "")[:300],
                    "publishedAt": sn.get("publishedAt", ""),
                    "duration":    item.get("contentDetails", {}).get("duration", ""),
                    "category":    None,
                    "tags":        [],
                    "source":      "liked",
                })
            page_token = data.get("nextPageToken")
            if not page_token:
                break
        return items

    def get_playlists(self) -> list[dict]:
        """Fetch user's playlists."""
        data = self._get("/playlists", {"part": "snippet", "mine": "true", "maxResults": 50})
        playlists = []
        for item in data.get("items", []):
            playlists.append({
                "id":    item["id"],
                "title": item["snippet"]["title"],
                "count": item.get("contentDetails", {}).get("itemCount", 0),
            })
        return playlists

    def get_playlist_videos(self, playlist_id: str, max_results: int = 200) -> list[dict]:
        """Fetch videos from a specific playlist."""
        items, page_token = [], None
        while len(items) < max_results:
            params = {
                "part":       "snippet",
                "playlistId": playlist_id,
                "maxResults": min(50, max_results - len(items)),
            }
            if page_token:
                params["pageToken"] = page_token
            data = self._get("/playlistItems", params)
            for item in data.get("items", []):
                sn = item["snippet"]
                items.append({
                    "id":      sn.get("resourceId", {}).get("videoId", ""),
                    "title":   sn.get("title", ""),
                    "channel": sn.get("videoOwnerChannelTitle", ""),
                    "description": sn.get("description", "")[:300],
                    "addedAt": sn.get("publishedAt", ""),
                    "category": None,
                    "tags":    [],
                    "source":  f"playlist:{playlist_id}",
                })
            page_token = data.get("nextPageToken")
            if not page_token:
                break
        return items

    def get_subscriptions(self, max_results: int = 100) -> list[dict]:
        """Fetch user's channel subscriptions."""
        data = self._get("/subscriptions", {
            "part": "snippet", "mine": "true", "maxResults": min(50, max_results),
        })
        return [
            {"channel_id": i["snippet"]["resourceId"]["channelId"],
             "title":      i["snippet"]["title"],
             "description":i["snippet"]["description"][:200]}
            for i in data.get("items", [])
        ]
