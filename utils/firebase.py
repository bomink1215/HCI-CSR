import requests
import threading
import concurrent.futures
from requests.adapters import HTTPAdapter

API_KEY    = "새로운 키"
PROJECT_ID = "zzook-52423"

_AUTH      = "https://identitytoolkit.googleapis.com/v1/accounts"
_FS        = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"
_COMMIT    = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents:commit"
_BATCH_GET = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents:batchGet"
_RUN_QUERY = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents:runQuery"

TIMEOUT = 6

# ── 커넥션 풀 세션 — TCP/TLS 재사용으로 요청 속도 향상 ──────────────────
_http = requests.Session()
_http.mount("https://", HTTPAdapter(pool_connections=2, pool_maxsize=8, max_retries=0))

def _prewarm():
    """앱 시작 시 Firebase 서버와 미리 TLS 핸드쉐이크"""
    try:
        _http.get("https://identitytoolkit.googleapis.com/", timeout=5)
    except Exception:
        pass

threading.Thread(target=_prewarm, daemon=True).start()


def _email(username: str) -> str:
    return f"{username.lower()}@zzook.app"


# ── 중복 확인 ─────────────────────────────────────────────────────────
def username_exists(username: str) -> bool:
    try:
        r = _http.get(f"{_FS}/usernames/{username.lower()}", timeout=TIMEOUT)
        return r.status_code == 200
    except Exception:
        return False

def nickname_exists(nickname: str) -> bool:
    try:
        r = _http.get(f"{_FS}/nicknames/{nickname}", timeout=TIMEOUT)
        return r.status_code == 200
    except Exception:
        return False


# ── 회원가입 ──────────────────────────────────────────────────────────
def sign_up(username: str, password: str, nickname: str,
            nickname_verified: bool = False) -> dict:
    # 1. 아이디 중복 확인
    if username_exists(username):
        return {"error": "Username already taken"}

    # 2. 닉네임 중복 확인 (UI에서 이미 했으면 생략)
    if not nickname_verified and nickname_exists(nickname):
        return {"error": "Nickname already taken"}

    # 3. Firebase Auth 계정 생성
    r = _http.post(
        f"{_AUTH}:signUp?key={API_KEY}",
        json={"email": _email(username), "password": password, "returnSecureToken": True},
        timeout=TIMEOUT,
    )
    d = r.json()
    if "error" in d:
        msg = d["error"].get("message", "")
        if "WEAK_PASSWORD" in msg:
            return {"error": "Password must be at least 6 characters"}
        if "EMAIL_EXISTS" in msg:
            return {"error": "Username already taken"}
        return {"error": f"Sign-up failed: {msg}"}

    uid     = d["localId"]
    token   = d["idToken"]
    headers = {"Authorization": f"Bearer {token}"}

    # 4. Firestore 쓰기 — fire-and-forget
    def _write():
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
                ex.submit(_http.patch,
                    f"{_FS}/users/{uid}",
                    headers=headers,
                    json={"fields": {
                        "uid":       {"stringValue": uid},
                        "username":  {"stringValue": username},
                        "nickname":  {"stringValue": nickname},
                        "focus_min": {"integerValue": "0"},
                        "sessions":  {"integerValue": "0"},
                    }},
                    timeout=TIMEOUT,
                )
                ex.submit(_http.patch,
                    f"{_FS}/usernames/{username.lower()}",
                    headers=headers,
                    json={"fields": {"uid": {"stringValue": uid}}},
                    timeout=TIMEOUT,
                )
                ex.submit(_http.patch,
                    f"{_FS}/nicknames/{nickname}",
                    headers=headers,
                    json={"fields": {"uid": {"stringValue": uid}}},
                    timeout=TIMEOUT,
                )
        except Exception:
            pass

    threading.Thread(target=_write, daemon=True).start()

    return {
        "uid":           uid,
        "id_token":      token,
        "refresh_token": d["refreshToken"],
        "username":      username,
        "nickname":      nickname,
    }


# ── 로그인 ────────────────────────────────────────────────────────────
def sign_in(username: str, password: str) -> dict:
    r = _http.post(
        f"{_AUTH}:signInWithPassword?key={API_KEY}",
        json={"email": _email(username), "password": password, "returnSecureToken": True},
        timeout=TIMEOUT,
    )
    d = r.json()
    if "error" in d:
        msg = d["error"].get("message", "")
        if any(k in msg for k in ("INVALID_LOGIN_CREDENTIALS", "EMAIL_NOT_FOUND",
                                   "WRONG_PASSWORD", "INVALID_PASSWORD")):
            return {"error": "Incorrect username or password"}
        return {"error": f"Login failed: {msg}"}

    uid   = d["localId"]
    token = d["idToken"]

    # 인증 완료 즉시 반환 — 닉네임은 백그라운드에서 세션 업데이트
    result = {
        "uid":           uid,
        "id_token":      token,
        "refresh_token": d["refreshToken"],
        "username":      username,
        "nickname":      username,   # Firestore 조회 전 임시 fallback
    }

    def _fetch_nickname():
        try:
            r2 = _http.get(
                f"{_FS}/users/{uid}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=3,
            )
            if r2.status_code == 200:
                fields = r2.json().get("fields", {})
                nick = fields.get("nickname", {}).get("stringValue", "")
                if nick:
                    result["nickname"] = nick
                    from utils import session as _sess
                    user = _sess.get_user()
                    if user and user.get("uid") == uid:
                        user["nickname"] = nick
                        _sess.set_user(user)
                        _sess.save(user)
        except Exception:
            pass

    threading.Thread(target=_fetch_nickname, daemon=True).start()
    return result


# ── 비밀번호 변경 ─────────────────────────────────────────────────────
def change_password(id_token: str, new_password: str) -> dict:
    r = _http.post(
        f"{_AUTH}:update?key={API_KEY}",
        json={"idToken": id_token, "password": new_password, "returnSecureToken": True},
        timeout=TIMEOUT,
    )
    d = r.json()
    if "error" in d:
        msg = d["error"].get("message", "")
        if "WEAK_PASSWORD" in msg:
            return {"error": "Password must be at least 6 characters"}
        return {"error": f"Failed: {msg}"}
    return {"id_token": d["idToken"], "refresh_token": d["refreshToken"]}


# ── 닉네임 변경 ───────────────────────────────────────────────────────
def change_nickname(uid: str, id_token: str,
                    old_nickname: str, new_nickname: str) -> dict:
    if nickname_exists(new_nickname):
        return {"error": "Nickname already taken"}

    headers = {"Authorization": f"Bearer {id_token}"}

    def _write():
        try:
            _http.patch(
                f"{_FS}/users/{uid}",
                headers=headers,
                json={"fields": {"nickname": {"stringValue": new_nickname}}},
                timeout=TIMEOUT,
            )
            _http.patch(
                f"{_FS}/nicknames/{new_nickname}",
                headers=headers,
                json={"fields": {"uid": {"stringValue": uid}}},
                timeout=TIMEOUT,
            )
            _http.delete(
                f"{_FS}/nicknames/{old_nickname}",
                headers=headers,
                timeout=TIMEOUT,
            )
        except Exception:
            pass

    threading.Thread(target=_write, daemon=True).start()
    return {"ok": True}


# ── 유저 정보 조회 ────────────────────────────────────────────────────
def get_user(uid: str, id_token: str) -> dict:
    r = _http.get(
        f"{_FS}/users/{uid}",
        headers={"Authorization": f"Bearer {id_token}"},
        timeout=TIMEOUT,
    )
    if r.status_code != 200:
        return {}
    fields = r.json().get("fields", {})
    return {k: v.get("stringValue", "") for k, v in fields.items()}


# ── 포모도로 통계 업데이트 (원자적 증가) ──────────────────────────────
def refresh_id_token(refresh_token: str) -> dict:
    """Firebase Secure Token Service로 ID 토큰 갱신 (만료 1시간)."""
    try:
        r = _http.post(
            f"https://securetoken.googleapis.com/v1/token?key={API_KEY}",
            json={"grant_type": "refresh_token", "refresh_token": refresh_token},
            timeout=TIMEOUT,
        )
        d = r.json()
        if "id_token" in d:
            return {
                "id_token":      d["id_token"],
                "refresh_token": d.get("refresh_token", refresh_token),
            }
        return {"error": str(d.get("error", "Refresh failed"))}
    except Exception as ex:
        return {"error": str(ex)}


def update_stats(uid: str, id_token: str,
                 delta_focus_min: int, delta_sessions: int) -> dict:
    try:
        r = _http.post(
            _COMMIT,
            headers={"Authorization": f"Bearer {id_token}"},
            json={"writes": [{
                "transform": {
                    "document": f"projects/{PROJECT_ID}/databases/(default)/documents/users/{uid}",
                    "fieldTransforms": [
                        {"fieldPath": "focus_min",
                         "increment": {"integerValue": str(delta_focus_min)}},
                        {"fieldPath": "sessions",
                         "increment": {"integerValue": str(delta_sessions)}},
                    ],
                }
            }]},
            timeout=TIMEOUT,
        )
        if r.status_code not in (200, 201):
            return {"error": r.text}
        return {"ok": True}
    except Exception as ex:
        return {"error": str(ex)}


def update_today_posture(uid: str, id_token: str,
                         score: int, date_str: str) -> dict:
    """오늘 자세 점수를 Firebase에 덮어씀."""
    try:
        r = _http.patch(
            f"{_FS}/users/{uid}",
            params=[("updateMask.fieldPaths", "today_posture_score"),
                    ("updateMask.fieldPaths", "today_posture_date")],
            headers={"Authorization": f"Bearer {id_token}"},
            json={
                "fields": {
                    "today_posture_score": {"integerValue": str(score)},
                    "today_posture_date":  {"stringValue": date_str},
                }
            },
            timeout=TIMEOUT,
        )
        return {"ok": True} if r.status_code in (200, 201) else {"error": r.text}
    except Exception as ex:
        return {"error": str(ex)}


def update_today_focus(uid: str, id_token: str,
                       focus_min: int, date_str: str) -> dict:
    """오늘 집중 시간(분)을 Firebase에 덮어씀 — 날짜가 바뀌면 자동 리셋."""
    try:
        r = _http.patch(
            f"{_FS}/users/{uid}",
            params=[("updateMask.fieldPaths", "today_focus_min"),
                    ("updateMask.fieldPaths", "today_date")],
            headers={"Authorization": f"Bearer {id_token}"},
            json={
                "fields": {
                    "today_focus_min": {"integerValue": str(focus_min)},
                    "today_date":      {"stringValue": date_str},
                }
            },
            timeout=TIMEOUT,
        )
        return {"ok": True} if r.status_code in (200, 201) else {"error": r.text}
    except Exception as ex:
        return {"error": str(ex)}


# ── 유저 문서 파싱 헬퍼 ──────────────────────────────────────────────
def _parse_user_fields(fields: dict, fallback_uid: str = "") -> dict:
    def _i(k): return int(fields.get(k, {}).get("integerValue", 0) or 0)
    def _s(k): return fields.get(k, {}).get("stringValue", "")
    return {
        "uid":                _s("uid") or fallback_uid,
        "username":           _s("username"),
        "nickname":           _s("nickname"),
        "focus_min":          _i("focus_min"),
        "sessions":           _i("sessions"),
        "today_focus_min":    _i("today_focus_min"),
        "today_date":         _s("today_date"),
        "today_posture_score":_i("today_posture_score"),
        "today_posture_date": _s("today_posture_date"),
    }


def get_user_stats(uid: str, id_token: str) -> dict | None:
    """단일 유저 문서를 직접 조회 — 쿼리 필드 누락 문제 우회."""
    try:
        r = _http.get(
            f"{_FS}/users/{uid}",
            headers={"Authorization": f"Bearer {id_token}"},
            timeout=TIMEOUT,
        )
        if r.status_code != 200:
            return None
        fields = r.json().get("fields", {})
        return _parse_user_fields(fields, fallback_uid=uid) if fields else None
    except Exception:
        return None


# ── 전체 유저 랭킹 조회 ───────────────────────────────────────────────
def get_all_users_ranked(id_token: str, limit: int = 100) -> list:
    try:
        # orderBy __name__ → focus_min 필드가 없는 문서도 포함됨
        body = {
            "structuredQuery": {
                "from": [{"collectionId": "users"}],
                "orderBy": [{"field": {"fieldPath": "__name__"},
                             "direction": "ASCENDING"}],
                "limit": limit,
            }
        }
        r = _http.post(
            _RUN_QUERY,
            headers={"Authorization": f"Bearer {id_token}"},
            json=body,
            timeout=TIMEOUT,
        )
        results = []
        for item in r.json():
            doc = item.get("document")
            if not doc:
                continue
            # 문서 경로에서 uid 추출 (uid 필드가 없는 구 계정 대비)
            path_uid = doc.get("name", "").split("/")[-1]
            fields   = doc.get("fields", {})
            results.append(_parse_user_fields(fields, fallback_uid=path_uid))
        return results
    except Exception:
        return []


# ── 닉네임으로 uid 조회 (내부용) ─────────────────────────────────────
def _get_uid_by_nickname(nickname: str) -> str | None:
    try:
        r = _http.get(f"{_FS}/nicknames/{nickname}", timeout=TIMEOUT)
        if r.status_code == 200:
            fields = r.json().get("fields", {})
            return fields.get("uid", {}).get("stringValue") or None
    except Exception:
        pass
    return None


# ── 친구 요청 전송 ────────────────────────────────────────────────────
def send_friend_request(from_uid: str, from_nickname: str, from_username: str,
                         to_nickname: str, id_token: str) -> dict:
    to_uid = _get_uid_by_nickname(to_nickname)
    if not to_uid:
        return {"error": "User not found"}
    if to_uid == from_uid:
        return {"error": "Cannot add yourself"}

    headers = {"Authorization": f"Bearer {id_token}"}

    r = _http.get(f"{_FS}/users/{from_uid}/friends/{to_uid}",
                  headers=headers, timeout=TIMEOUT)
    if r.status_code == 200:
        return {"error": "Already friends"}

    r = _http.get(f"{_FS}/users/{to_uid}/incoming_requests/{from_uid}",
                  headers=headers, timeout=TIMEOUT)
    if r.status_code == 200:
        return {"error": "Request already sent"}

    try:
        r = _http.patch(
            f"{_FS}/users/{to_uid}/incoming_requests/{from_uid}",
            headers=headers,
            json={"fields": {
                "from_uid":      {"stringValue": from_uid},
                "from_nickname": {"stringValue": from_nickname},
                "from_username": {"stringValue": from_username},
            }},
            timeout=TIMEOUT,
        )
        if r.status_code not in (200, 201):
            return {"error": "Failed to send request"}
        return {"ok": True}
    except Exception as ex:
        return {"error": str(ex)}


# ── 내게 온 친구 요청 목록 ────────────────────────────────────────────
def get_incoming_requests(uid: str, id_token: str) -> list:
    try:
        r = _http.get(
            f"{_FS}/users/{uid}/incoming_requests",
            headers={"Authorization": f"Bearer {id_token}"},
            timeout=TIMEOUT,
        )
        if r.status_code != 200:
            return []
        docs = r.json().get("documents", [])
        results = []
        for doc in docs:
            fields = doc.get("fields", {})
            results.append({
                "from_uid":      fields.get("from_uid",      {}).get("stringValue", ""),
                "from_nickname": fields.get("from_nickname", {}).get("stringValue", ""),
                "from_username": fields.get("from_username", {}).get("stringValue", ""),
            })
        return results
    except Exception:
        return []


# ── 친구 요청 수락 ────────────────────────────────────────────────────
def accept_friend_request(uid: str, id_token: str,
                           my_nickname: str, my_username: str,
                           from_uid: str, from_nickname: str,
                           from_username: str) -> dict:
    try:
        headers = {"Authorization": f"Bearer {id_token}"}
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
            ex.submit(_http.patch,
                f"{_FS}/users/{uid}/friends/{from_uid}",
                headers=headers,
                json={"fields": {
                    "uid":      {"stringValue": from_uid},
                    "nickname": {"stringValue": from_nickname},
                    "username": {"stringValue": from_username},
                }},
                timeout=TIMEOUT,
            )
            ex.submit(_http.patch,
                f"{_FS}/users/{from_uid}/friends/{uid}",
                headers=headers,
                json={"fields": {
                    "uid":      {"stringValue": uid},
                    "nickname": {"stringValue": my_nickname},
                    "username": {"stringValue": my_username},
                }},
                timeout=TIMEOUT,
            )
            ex.submit(_http.delete,
                f"{_FS}/users/{uid}/incoming_requests/{from_uid}",
                headers=headers,
                timeout=TIMEOUT,
            )
        return {"ok": True}
    except Exception as ex:
        return {"error": str(ex)}


# ── 친구 요청 거절 ────────────────────────────────────────────────────
def reject_friend_request(uid: str, id_token: str, from_uid: str) -> dict:
    try:
        _http.delete(
            f"{_FS}/users/{uid}/incoming_requests/{from_uid}",
            headers={"Authorization": f"Bearer {id_token}"},
            timeout=TIMEOUT,
        )
        return {"ok": True}
    except Exception as ex:
        return {"error": str(ex)}


# ── 친구 목록 + stats batchGet ───────────────────────────────────────
def get_friends_with_stats(uid: str, id_token: str) -> list:
    try:
        headers = {"Authorization": f"Bearer {id_token}"}
        r = _http.get(f"{_FS}/users/{uid}/friends",
                      headers=headers, timeout=TIMEOUT)
        if r.status_code != 200:
            return []
        docs = r.json().get("documents", [])
        if not docs:
            return []

        friend_uids = [
            doc.get("fields", {}).get("uid", {}).get("stringValue", "")
            for doc in docs
        ]
        friend_uids = [u for u in friend_uids if u]
        if not friend_uids:
            return []

        doc_paths = [
            f"projects/{PROJECT_ID}/databases/(default)/documents/users/{fuid}"
            for fuid in friend_uids
        ]
        r2 = _http.post(
            _BATCH_GET,
            headers=headers,
            json={"documents": doc_paths},
            timeout=TIMEOUT,
        )
        results = []
        for item in r2.json():
            doc = item.get("found")
            if not doc:
                continue
            path_uid = doc.get("name", "").split("/")[-1]
            fields   = doc.get("fields", {})
            results.append(_parse_user_fields(fields, fallback_uid=path_uid))
        results.sort(key=lambda x: x["today_focus_min"], reverse=True)
        return results
    except Exception:
        return []
