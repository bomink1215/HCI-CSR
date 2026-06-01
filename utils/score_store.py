"""
일별 자세 점수 / 포모도로 집중 시간 저장소.
- posture: 모니터링 중 1분마다 측정한 점수의 평균
- focus_minutes: 완료된 포모도로 집중 세션의 합계 (분)
집중 점수 = min(100, focus_minutes * 100 / FOCUS_MAX)
"""

import json
import os
import time
from datetime import date, timedelta

_DATA_DIR  = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_FILE      = os.path.join(_DATA_DIR, "scores_anonymous.json")   # 로그인 전 임시
FOCUS_MAX  = 240   # 4시간 집중 = 100점


def _load():
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        with open(_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save():
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        with open(_FILE, "w", encoding="utf-8") as f:
            json.dump(_data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


_data: dict      = _load()
_listeners: list = []
_last_posture_t  = 0.0   # 1분 throttle용
_goal_minutes    = FOCUS_MAX  # 사용자 설정 하루 목표 (분). 기본값 = FOCUS_MAX


# ── UID별 데이터 전환 ─────────────────────────────────────────────────
def init_for_user(uid: str):
    """로그인 / 로그아웃 시 호출 — uid별 scores 파일로 전환하고 상태 초기화."""
    global _FILE, _data, _last_posture_t, _goal_minutes
    safe = (uid or "anonymous").replace("/", "_").replace(".", "_")
    _FILE = os.path.join(_DATA_DIR, f"scores_{safe}.json")
    _data = _load()
    _last_posture_t = 0.0
    _goal_minutes   = FOCUS_MAX
    _notify()


def add_listener(fn):
    if fn not in _listeners:
        _listeners.append(fn)


def remove_listener(fn):
    if fn in _listeners:
        _listeners.remove(fn)


def _notify():
    for fn in list(_listeners):
        try:
            fn()
        except Exception:
            pass


def _day(d: date = None) -> str:
    return (d or date.today()).isoformat()


def _ensure(day: str):
    if day not in _data:
        _data[day] = {
            "posture_scores": [],
            "focus_minutes":  0,
            "synced_minutes": 0,
            "history":        [],
        }


# ── 목표 설정 ────────────────────────────────────────────────────────
def set_focus_goal(session_count: int, session_minutes: int):
    """포모도로 설정(세션 수 × 집중 시간)으로 하루 목표 갱신."""
    global _goal_minutes
    _goal_minutes = max(1, session_count * session_minutes)


def get_focus_goal() -> int:
    return _goal_minutes


# ── 기록 ────────────────────────────────────────────────────────────
def record_posture(score: int):
    """모니터링 중 매초 호출해도 안전 — 1분에 1번만 실제 기록."""
    global _last_posture_t
    now = time.time()
    if now - _last_posture_t < 60:
        return
    _last_posture_t = now
    day = _day()
    _ensure(day)
    _data[day]["posture_scores"].append(int(score))
    _save()
    _notify()


def add_focus_minutes(minutes: int):
    """포모도로 집중 세션 완료 시 호출."""
    if minutes <= 0:
        return
    day = _day()
    _ensure(day)
    _data[day]["focus_minutes"]  = _data[day].get("focus_minutes", 0) + minutes
    _data[day]["focus_sessions"] = _data[day].get("focus_sessions", 0) + 1
    _save()
    _notify()


def get_today_focus_sessions() -> int:
    """오늘 완료된 포커스 세션 수."""
    return _data.get(_day(), {}).get("focus_sessions", 0)


def add_history_entry(mode_label: str, start: str, end: str, status: str):
    """Today's Log 항목 저장 — 로그아웃해도 오늘치는 유지."""
    day = _day()
    _ensure(day)
    if "history" not in _data[day]:
        _data[day]["history"] = []
    _data[day]["history"].append({
        "mode": mode_label, "start": start,
        "end":  end,        "status": status,
    })
    _save()


def get_today_history() -> list:
    """오늘의 로그 목록 — (mode_label, start, end, status) 튜플 리스트."""
    entries = _data.get(_day(), {}).get("history", [])
    return [(e["mode"], e["start"], e["end"], e["status"]) for e in entries]


# ── 조회 ────────────────────────────────────────────────────────────
def get_today_focus_minutes() -> int:
    return _data.get(_day(), {}).get("focus_minutes", 0)


def get_unsynced_minutes() -> int:
    """Firebase에 아직 올리지 않은 오늘 집중 시간(분)."""
    day = _day()
    total  = _data.get(day, {}).get("focus_minutes", 0)
    synced = _data.get(day, {}).get("synced_minutes", 0)
    return max(0, total - synced)


def mark_synced(minutes: int):
    """Firebase 업로드 완료된 분량 기록."""
    day = _day()
    _ensure(day)
    _data[day]["synced_minutes"] = _data[day].get("synced_minutes", 0) + minutes
    _save()


def get_today_posture() -> int:
    scores = _data.get(_day(), {}).get("posture_scores", [])
    return round(sum(scores) / len(scores)) if scores else 0


def get_week_posture() -> list:
    """월~일 순서로 일평균 자세 점수 (0-100) 7개."""
    today  = date.today()
    monday = today - timedelta(days=today.weekday())
    result = []
    for i in range(7):
        d      = _day(monday + timedelta(days=i))
        scores = _data.get(d, {}).get("posture_scores", [])
        result.append(round(sum(scores) / len(scores)) if scores else 0)
    return result


def get_week_focus() -> list:
    """월~일 순서로 집중 점수 (0-100) 7개.
    하루 점수 = 세션수 × 집중시간(분) → FOCUS_MAX 기준으로 정규화."""
    today  = date.today()
    monday = today - timedelta(days=today.weekday())
    result = []
    for i in range(7):
        d       = _day(monday + timedelta(days=i))
        minutes = _data.get(d, {}).get("focus_minutes", 0)
        result.append(min(100, round(minutes * 100 / _goal_minutes)))
    return result


def get_week_focus_minutes() -> list:
    """월~일 순서로 실제 집중 시간 (분) 7개."""
    today  = date.today()
    monday = today - timedelta(days=today.weekday())
    result = []
    for i in range(7):
        d = _day(monday + timedelta(days=i))
        result.append(_data.get(d, {}).get("focus_minutes", 0))
    return result


def get_weekly_focus_avg_minutes() -> int:
    """이번 주 일별 집중 시간의 평균 (분). 데이터 있는 날만."""
    mins = [m for m in get_week_focus_minutes() if m > 0]
    return round(sum(mins) / len(mins)) if mins else 0


def get_weekly_posture_avg() -> int:
    """이번 주 일별 자세 점수의 평균. 데이터 있는 날만."""
    vals = [v for v in get_week_posture() if v > 0]
    return round(sum(vals) / len(vals)) if vals else 0
