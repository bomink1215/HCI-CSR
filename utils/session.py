import json
import os
import threading
import time

_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".zzook_session.json")

# ── 로컬 파일 세션 저장/불러오기 ──────────────────────────────────────
def save(data: dict):
    with open(_PATH, "w") as f:
        json.dump(data, f)

def load() -> dict | None:
    if not os.path.exists(_PATH):
        return None
    try:
        with open(_PATH) as f:
            return json.load(f)
    except Exception:
        return None

def clear():
    if os.path.exists(_PATH):
        os.remove(_PATH)

# ── 인메모리 현재 유저 상태 ───────────────────────────────────────────
_user: dict | None = None

def set_user(u: dict | None):
    global _user
    _user = u

def get_user() -> dict | None:
    return _user


# ── Firebase ID 토큰 자동 갱신 ────────────────────────────────────────
# Firebase ID 토큰은 1시간 후 만료 → 55분마다 자동으로 갱신
_refresh_stop   = threading.Event()
_refresh_thread: threading.Thread | None = None


def _do_refresh(refresh_fn) -> bool:
    """refresh_fn으로 토큰 갱신 후 세션 업데이트. 성공 시 True."""
    user = get_user()
    if not user or not user.get("refresh_token"):
        return False
    try:
        result = refresh_fn(user["refresh_token"])
        if "id_token" in result:
            # dict를 in-place 수정하면 이미 참조를 가진 곳에도 즉시 반영됨
            user["id_token"] = result["id_token"]
            if "refresh_token" in result:
                user["refresh_token"] = result["refresh_token"]
            set_user(user)
            if user.get("remember_me"):
                save(user)
            return True
    except Exception:
        pass
    return False


def _refresh_worker(refresh_fn):
    # 앱 시작 직후 한 번 즉시 갱신 (저장된 세션 토큰이 오래됐을 수 있음)
    _do_refresh(refresh_fn)
    # 이후 55분마다 반복
    while not _refresh_stop.wait(timeout=55 * 60):
        _do_refresh(refresh_fn)


def start_auto_refresh(refresh_fn):
    """로그인/앱 시작 시 호출 — 백그라운드 토큰 갱신 스레드 시작."""
    global _refresh_thread
    _refresh_stop.clear()
    if _refresh_thread and _refresh_thread.is_alive():
        return   # 이미 실행 중
    _refresh_thread = threading.Thread(
        target=_refresh_worker, args=(refresh_fn,), daemon=True,
    )
    _refresh_thread.start()


def stop_auto_refresh():
    """로그아웃 시 호출."""
    _refresh_stop.set()
