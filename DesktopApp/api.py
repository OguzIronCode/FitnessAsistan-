"""Simple FitTrack API client for the Desktop PoC.

This mirrors the frontend `api.js` semantics minimally for login/profile.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

API_BASE_URL = "http://localhost:8000/api"
TOKEN_FILE = Path(__file__).parent / "token.json"


class FitTrackAPI:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self._token: Optional[str] = None
        self._user_id: Optional[str] = None
        self._load_token()

    def _load_token(self) -> None:
        if TOKEN_FILE.exists():
            try:
                d = json.loads(TOKEN_FILE.read_text())
                self._token = d.get("token")
                self._user_id = d.get("user_id")
            except Exception:
                self._token = None

    def _save_token(self, token: str, user_id: Optional[str] = None) -> None:
        self._token = token
        self._user_id = user_id
        TOKEN_FILE.write_text(json.dumps({"token": token, "user_id": user_id}))

    def clear_token(self) -> None:
        self._token = None
        self._user_id = None
        try:
            TOKEN_FILE.unlink()
        except FileNotFoundError:
            pass

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        return h

    def login(self, email: str, password: str) -> dict:
        # Offline mode: accept any credentials and return a demo token
        token = "demo-token"
        user_id = "user-1"
        self._save_token(token, user_id)
        return {"access_token": token, "user_id": user_id}

    def get_profile(self) -> dict:
        # Offline demo profile
        if not self._token:
            raise RuntimeError("Unauthorized - token missing or expired")
        return {
            "id": "user-1",
            "full_name": "Demo Kullanıcı",
            "email": "demo@example.com",
            "age": 30,
            "weight_kg": 75,
            "goal": "maintain",
            "calorie_target": 2000,
            "protein_target": 120,
            "carb_target": 200,
            "fat_target": 60,
        }


if __name__ == "__main__":
    # quick manual test (requires backend running)
    api = FitTrackAPI()
    print("Has token:", bool(api._token))
