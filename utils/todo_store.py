"""
공유 투두 스토어 — TodoView와 DashboardView가 같은 데이터를 바라봄.
tasks 리스트를 직접 변경하지 말고 반드시 이 모듈의 함수를 사용할 것.
태스크는 로컬 JSON 파일에 영구 저장됨.
"""

import json
import os
from datetime import date as _date

_DATA_DIR    = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_TASKS_FILE  = os.path.join(_DATA_DIR, "tasks_anonymous.json")
_ARCHIVE_FILE = os.path.join(_DATA_DIR, "archives_anonymous.json")


def _load() -> list:
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        with open(_TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _load_archive() -> list:
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        with open(_ARCHIVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save():
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        with open(_TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(_tasks, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _save_archive():
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        with open(_ARCHIVE_FILE, "w", encoding="utf-8") as f:
            json.dump(_archives, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


_tasks: list[dict]    = _load()
_archives: list[dict] = _load_archive()
_listeners: list      = []


def init_for_user(uid: str):
    """UID별 tasks/archives 파일로 전환 — 계정 전환 시 반드시 호출."""
    global _TASKS_FILE, _ARCHIVE_FILE, _tasks, _archives
    safe = (uid or "anonymous").replace("/", "_").replace(".", "_")
    _TASKS_FILE   = os.path.join(_DATA_DIR, f"tasks_{safe}.json")
    _ARCHIVE_FILE = os.path.join(_DATA_DIR, f"archives_{safe}.json")
    _tasks    = _load()
    _archives = _load_archive()
    _notify()


def archive_completed_and_expired() -> int:
    """완료되거나 기한이 지난 투두를 아카이브로 이동. 이동된 개수 반환."""
    global _tasks
    today = _date.today().isoformat()
    to_archive, to_keep = [], []
    for task in _tasks:
        due     = task.get("due", "")
        expired = bool(due) and due < today
        if task["done"] or expired:
            entry = dict(task)
            entry["archived_at"] = today
            entry["reason"] = "done" if task["done"] else "expired"
            to_archive.append(entry)
        else:
            to_keep.append(task)
    _archives.extend(to_archive)
    _tasks = to_keep
    _save()
    _save_archive()
    return len(to_archive)


def get_archives() -> list[dict]:
    """아카이브된 투두 반환 (최신순)."""
    return list(reversed(_archives))


# ── 조회 ─────────────────────────────────────────────────────────────
def get_tasks() -> list[dict]:
    return _tasks


# ── 리스너 ───────────────────────────────────────────────────────────
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


# ── 변경 함수 ────────────────────────────────────────────────────────
def add_task(task: dict):
    _tasks.append(task)
    _save()
    _notify()


def delete_task(task: dict):
    if task in _tasks:
        _tasks.remove(task)
    _save()
    _notify()


def toggle_task(task: dict):
    task["done"] = not task["done"]
    _save()
    _notify()


def cycle_priority(task: dict):
    opts = ["High", "Medium", "Low"]
    cur = opts.index(task["priority"]) if task["priority"] in opts else 0
    task["priority"] = opts[(cur + 1) % len(opts)]
    _save()
    _notify()
