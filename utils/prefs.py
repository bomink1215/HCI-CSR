"""
유저별 로컬 환경설정 (튜토리얼 표시 여부 등)
data/prefs.json  →  { uid: { "tutorial_seen": true, ... }, ... }
"""
import json
import os

_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "prefs.json")


def _load() -> dict:
    try:
        if os.path.exists(_PATH):
            with open(_PATH, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save(data: dict):
    os.makedirs(os.path.dirname(_PATH), exist_ok=True)
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f)


def is_tutorial_seen(uid: str) -> bool:
    return _load().get(uid, {}).get("tutorial_seen", False)


def mark_tutorial_seen(uid: str):
    d = _load()
    d.setdefault(uid, {})["tutorial_seen"] = True
    _save(d)
