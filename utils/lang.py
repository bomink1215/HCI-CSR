"""
EN / KR 언어 설정 저장소.
lang.get() → 'en' | 'ko'
lang.set_lang('ko') → 변경 + 파일 저장 + 리스너 알림
lang.t('key') → 현재 언어 문자열
"""
import json
import os

_DATA_DIR  = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_PREF_FILE = os.path.join(_DATA_DIR, "lang_pref.json")

_lang: str  = "en"
_listeners: list = []


# ── 영속화 ──────────────────────────────────────────────────────────
def _load_pref():
    global _lang
    try:
        if os.path.exists(_PREF_FILE):
            with open(_PREF_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("lang") in ("en", "ko"):
                    _lang = data["lang"]
    except Exception:
        pass


def _save_pref():
    try:
        os.makedirs(_DATA_DIR, exist_ok=True)
        with open(_PREF_FILE, "w", encoding="utf-8") as f:
            json.dump({"lang": _lang}, f)
    except Exception:
        pass


# ── 공개 API ────────────────────────────────────────────────────────
def get() -> str:
    return _lang


def set_lang(lang: str):
    global _lang
    if lang in ("en", "ko") and lang != _lang:
        _lang = lang
        _save_pref()
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


def t(key: str) -> str:
    """현재 언어로 번역된 문자열 반환. 키 없으면 key 그대로."""
    return _STRINGS.get(_lang, _STRINGS["en"]).get(
        key, _STRINGS["en"].get(key, key)
    )


# ── 번역 사전 ────────────────────────────────────────────────────────
_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        # ── Nav ──────────────────────────────────────────────────────
        "nav_dashboard": "Dashboard",
        "nav_posture":   "Posture",
        "nav_timer":     "Pomodoro",
        "nav_todo":      "To-Do",
        "nav_ranking":   "Ranking",
        "nav_profile":   "Profile",
        # ── Auth ─────────────────────────────────────────────────────
        "welcome_back":    "Welcome back",
        "sign_in_sub":     "Sign in to your account or create a new one",
        "create_account":  "Create an account",
        "join_sub":        "Join ZZOOK and start your journey",
        "tagline":         "Build your rhythm of focus and rest",
        "login_tab":       "Log In",
        "signup_tab":      "Sign Up",
        "id_hint":         "ID",
        "password_hint":   "Password",
        "nickname_hint":   "Nickname",
        "remember_me":     "Remember me on this device",
        "check":           "Check",
        "feature_pomo":    "Pomodoro Timer",
        "feature_pomo_d":  "Stay focused with timed sessions",
        "feature_post":    "Posture Monitor",
        "feature_post_d":  "Keep your posture healthy",
        "feature_rank":    "Leaderboard",
        "feature_rank_d":  "Compete with friends",
        # ── Dashboard ────────────────────────────────────────────────
        "greeting_morning":   "Good morning! ☀️",
        "greeting_afternoon": "Have you had lunch? 🍱",
        "greeting_evening":   "Great work today! 🌙",
        "today_overview":     "Today's Overview",
        "today_posture":      "Today's Posture",
        "todays_todo":        "To-Do",
        "pomodoro":           "Pomodoro",
        "ranking":            "Ranking",
        "live":               "Live",
        "rank_focus_time":    "⏱ Focus Time",
        "rank_posture":       "🧘 Posture",
        "no_friends":         "Add friends to see rankings!",
        "no_posture_data":    "No posture data yet",
        "go_to_posture":      "Go to Posture",
        "view_all":           "View All",
        "no_data":            "No data",
        "score_suffix":       " Score",
        "not_measured":       "Not\nmeasured",
        "posture_good":       "Good 👍",
        "posture_fair":       "Fair 😐",
        "posture_poor":       "Poor 😞",
        "live_on":            "Live Detection ON",
        "live_off":           "Live Detection OFF",
        "posture_score_label": "Posture Score",
        "items_fmt":          "{n} item",
        "items_fmt_plural":   "{n} items",
        "avg_focus_fmt":      "Avg {n}min",
        "avg_posture_fmt":    "Avg {n}pts",
        "sessions_label":     "Sessions",
        "weekly_focus":       "Weekly Focus",
        "weekly_posture":     "Weekly Posture",
        "today_log":          "Today's Log",
        "session_ready":      "Session Ready",
        "session_complete":   "Session Complete",
        "paused":             "Paused",
        "focus_avg":          "Focus Avg",
        "posture_avg":        "Posture Avg",
        "start":              "Start",
        "reset":              "Reset",
        "skip":               "Skip",
        "no_tasks":           "No tasks yet",
        # ── Tutorial ─────────────────────────────────────────────────
        "tut_next":           "Next",
        "tut_done":           "Done",
        "tut_skip":           "Skip",
        "tut_help_tooltip":   "Tutorial",
        "nav_lang_label":     "language",
        # ── Posture ──────────────────────────────────────────────────
        "posture_title":    "Posture Correction",
        "posture_sub":      "Track and improve your posture with real-time AI detection",
        "start_monitoring": "Start Monitoring",
        "stop_monitoring":  "Stop Monitoring",
        "live_score":       "Live Score",
        "baseline_not_set": "Baseline not set",
        "baseline_set":     "Baseline posture set ✓",
        "calib_guide":      (
            "When monitoring starts, a 3s countdown begins.\n"
            "Hold a good posture for 3s to set your baseline.\n"
            "If missed, restart monitoring."
        ),
        "cam_on":           "Live Detection On",
        "cam_off":          "Live Detection Off",
        "click_to_begin":   "Click Start Monitoring to begin",
        "press_start":      "Press Start Monitoring\nto open the camera window",
        # ── Pomodoro ─────────────────────────────────────────────────
        "focus_session":    "Focus Session",
        "break_session":    "Break Session",
        # ── Todo ─────────────────────────────────────────────────────
        "add_task":         "Add a task...",
        "due_date":         "Due Date",
        "archive":          "Archive",
        "no_archive":       "No archived tasks",
        "archived_tasks":   "Archived Tasks",
        # ── Pomodoro settings ────────────────────────────────────────
        "pomo_title":         "Pomodoro Timer",
        "pomo_sub":           "Build a rhythm of focus and rest",
        "settings":           "Settings",
        "focus_time_fmt":     "Focus Time  {n}min",
        "break_time_fmt":     "Break Time  {n}min",
        "goal_cycles_fmt":    "Goal Cycles  {n}",
        "sound_alerts":       "Sound Alerts",
        "auto_start":         "Auto Start",
        "test_mode":          "\U0001f9ea Test Mode",
        "test_mode_on":       "\U0001f9ea Test Mode ON  (10s \xd7 2)",
        "focus_progress_fmt": "Focus Progress ({done}/{goal})",
        "goal_achieved":      "Goal Achieved! \U0001f389",
        "cycles_complete_fmt":"{n} cycles completed!",
        "start_again":        "Start Again",
        "session_complete_dlg":"Session Complete! \U0001f389",
        "next_session_fmt":   "Next: {label} session",
        "start_next_session": "Start Next Session",
        # ── Todo extras ──────────────────────────────────────────────
        "todo_title":         "To-Do",
        "todo_sub":           "Manage your tasks for today",
        "add_task_hint":      "What do you need to do?",
        "stat_total":         "Total",
        "stat_done":          "Done",
        "stat_remaining":     "Remaining",
        "stat_completion":    "Completion",
        "cat_label":          "Category",
        "priority_label":     "Priority",
        "no_tasks_yet":       "No tasks yet. Add one above!",
        "other_cat":          "Other",
        "done_reason":        "\u2713 Done",
        "expired_reason":     "\u23f0 Expired",
        "archived_at_label":  "archived",
        "due_prefix":         "due",
        # ── Ranking extras ───────────────────────────────────────────
        "ranking_sub":        "Today\'s leaderboard",
        "tab_friends":        "Friends",
        "tab_all_users":      "All Users",
        "metric_focus":       "Focus",
        "metric_posture":     "Posture",
        "loading":            "Loading...",
        "todays_focus_label": "Today\'s Focus",
        "friend_requests":    "Friend Requests",
        "add_friend":         "Add Friend",
        "search_by_nick":     "Search by nickname",
        "send_btn":           "Send",
        "me_badge":           "Me",
        "sessions_fmt":       "{n} sessions",
        "avg_today":          "avg today",
        "no_data_yet":        "No data yet.",
        "no_friends_yet":     "No friends yet.\nSearch by nickname above!",
        "rank_today_fmt":     "#{n} today",
        "no_record_today":    "No record today",
        "accept":             "Accept",
        "reject_btn":         "Reject",
        "request_sent_fmt":   "Request sent to {nick} \u2713",
        "err_enter_nick":     "Enter a nickname",
        # ── Profile extras ───────────────────────────────────────────
        "profile_title":      "My Profile",
        "profile_sub":        "Manage your account settings",
        "change_nickname":    "Change Nickname",
        "current_nick_fmt":   "Current: {nick}",
        "new_nickname_hint":  "New nickname",
        "save_nickname_btn":  "Save Nickname",
        "change_password":    "Change Password",
        "curr_pw_hint":       "Current password",
        "new_pw_hint":        "New password",
        "confirm_pw_hint":    "Confirm new password",
        "save_password_btn":  "Save Password",
        "log_out":            "Log Out",
        "err_same_nick":      "That\'s your current nickname",
        "err_nick_taken":     "Nickname already taken",
        "ok_nick_available":  "Available \u2713",
        "err_check_nick":     "Please check nickname availability first",
        "ok_nick_updated":    "Nickname updated! \u2713",
        "err_enter_curr_pw":  "Enter your current password",
        "err_enter_new_pw":   "Enter a new password",
        "err_pw_too_short":   "Password must be at least 6 characters",
        "err_pw_no_match":    "Passwords do not match",
        "err_pw_same":        "New password must differ from current",
        "err_curr_pw_wrong":  "Current password is incorrect",
        "ok_pw_updated":      "Password updated! \u2713",

        # ── Common ───────────────────────────────────────────────────
        "mon": "Mon", "tue": "Tue", "wed": "Wed", "thu": "Thu",
        "fri": "Fri", "sat": "Sat", "sun": "Sun",
    },
    "ko": {
        # ── Nav ──────────────────────────────────────────────────────
        "nav_dashboard": "대시보드",
        "nav_posture":   "자세교정",
        "nav_timer":     "뽀모도로",
        "nav_todo":      "투두",
        "nav_ranking":   "랭킹",
        "nav_profile":   "프로필",
        # ── Auth ─────────────────────────────────────────────────────
        "welcome_back":    "다시 오셨네요",
        "sign_in_sub":     "계정에 로그인하거나 새로 만드세요",
        "create_account":  "계정 만들기",
        "join_sub":        "ZZOOK과 함께 시작하세요",
        "tagline":         "집중과 휴식의 리듬을 만들어보세요",
        "login_tab":       "로그인",
        "signup_tab":      "회원가입",
        "id_hint":         "아이디",
        "password_hint":   "비밀번호",
        "nickname_hint":   "닉네임",
        "remember_me":     "이 기기에서 로그인 유지",
        "check":           "확인",
        "feature_pomo":    "뽀모도로 타이머",
        "feature_pomo_d":  "타이머로 집중력을 높이세요",
        "feature_post":    "자세 모니터",
        "feature_post_d":  "바른 자세를 유지하세요",
        "feature_rank":    "리더보드",
        "feature_rank_d":  "친구들과 경쟁하세요",
        # ── Dashboard ────────────────────────────────────────────────
        "greeting_morning":   "좋은 아침이에요! ☀️",
        "greeting_afternoon": "점심은 드셨나요? 🍱",
        "greeting_evening":   "오늘도 수고했어요! 🌙",
        "today_overview":     "오늘의 요약",
        "today_posture":      "오늘의 자세",
        "todays_todo":        "투두",
        "pomodoro":           "뽀모도로",
        "ranking":            "랭킹",
        "live":               "실시간",
        "rank_focus_time":    "⏱ 집중 시간",
        "rank_posture":       "🧘 자세",
        "no_friends":         "친구를 추가하면 랭킹을 볼 수 있어요!",
        "no_posture_data":    "자세 데이터 없음",
        "go_to_posture":      "자세 교정으로",
        "view_all":           "전체 보기",
        "no_data":            "데이터 없음",
        "score_suffix":       " 점수",
        "not_measured":       "미측정",
        "posture_good":       "좋음 👍",
        "posture_fair":       "보통 😐",
        "posture_poor":       "나쁨 😞",
        "live_on":            "실시간 감지 ON",
        "live_off":           "실시간 감지 OFF",
        "posture_score_label": "자세 점수",
        "items_fmt":          "{n}개",
        "items_fmt_plural":   "{n}개",
        "avg_focus_fmt":      "평균 {n}분",
        "avg_posture_fmt":    "평균 {n}점",
        "sessions_label":     "세션",
        "weekly_focus":       "주간 집중",
        "weekly_posture":     "주간 자세",
        "today_log":          "오늘의 기록",
        "session_ready":      "세션 준비 완료",
        "session_complete":   "세션 완료",
        "paused":             "일시정지",
        "focus_avg":          "집중 평균",
        "posture_avg":        "자세 평균",
        "start":              "시작",
        "reset":              "초기화",
        "skip":               "건너뛰기",
        "no_tasks":           "할 일이 없어요",
        # ── Tutorial ─────────────────────────────────────────────────
        "tut_next":           "다음",
        "tut_done":           "완료",
        "tut_skip":           "건너뛰기",
        "tut_help_tooltip":   "튜토리얼",
        "nav_lang_label":     "언어",
        # ── Posture ──────────────────────────────────────────────────
        "posture_title":    "자세 교정",
        "posture_sub":      "실시간 AI로 자세를 추적하고 개선하세요",
        "start_monitoring": "모니터링 시작",
        "stop_monitoring":  "모니터링 중지",
        "live_score":       "실시간 점수",
        "baseline_not_set": "기준 자세 미설정",
        "baseline_set":     "기준 자세 설정됨 ✓",
        "calib_guide":      (
            "모니터링 시작 시 3초 카운트다운이 시작됩니다.\n"
            "3초간 바른 자세를 유지하면 기준 자세가 설정됩니다.\n"
            "놓쳤을 경우 모니터링을 재시작하세요."
        ),
        "cam_on":           "실시간 감지 중",
        "cam_off":          "실시간 감지 꺼짐",
        "click_to_begin":   "모니터링 시작 버튼을 눌러주세요",
        "press_start":      "모니터링 시작 버튼을\n눌러 카메라를 여세요",
        # ── Pomodoro ─────────────────────────────────────────────────
        "focus_session":    "집중 세션",
        "break_session":    "휴식 세션",
        # ── Todo ─────────────────────────────────────────────────────
        "add_task":         "할 일 추가...",
        "due_date":         "마감일",
        "archive":          "아카이브",
        "no_archive":       "보관된 할 일이 없어요",
        "archived_tasks":   "완료/만료 보관함",
        # ── Pomodoro settings ────────────────────────────────────────
        "pomo_title":         "뽀모도로 타이머",
        "pomo_sub":           "집중과 휴식의 리듬을 만드세요",
        "settings":           "설정",
        "focus_time_fmt":     "집중 시간  {n}분",
        "break_time_fmt":     "휴식 시간  {n}분",
        "goal_cycles_fmt":    "목표 사이클  {n}",
        "sound_alerts":       "알림음",
        "auto_start":         "자동 시작",
        "test_mode":          "🧪 테스트 모드",
        "test_mode_on":       "🧪 테스트 모드 ON  (10초 × 2)",
        "focus_progress_fmt": "집중 진행도 ({done}/{goal})",
        "goal_achieved":      "목표 달성! 🎉",
        "cycles_complete_fmt":"{n}사이클 완료!",
        "start_again":        "다시 시작",
        "session_complete_dlg":"세션 완료! 🎉",
        "next_session_fmt":   "다음: {label} 세션",
        "start_next_session": "다음 세션 시작",
        # ── Todo extras ──────────────────────────────────────────────
        "todo_title":         "투두",
        "todo_sub":           "오늘의 할 일을 관리하세요",
        "add_task_hint":      "할 일을 입력하세요...",
        "stat_total":         "전체",
        "stat_done":          "완료",
        "stat_remaining":     "미완",
        "stat_completion":    "달성률",
        "cat_label":          "카테고리",
        "priority_label":     "우선순위",
        "no_tasks_yet":       "할 일이 없어요. 위에서 추가하세요!",
        "other_cat":          "기타",
        "done_reason":        "✓ 완료",
        "expired_reason":     "⏰ 만료",
        "archived_at_label":  "보관됨",
        "due_prefix":         "마감",
        # ── Ranking extras ───────────────────────────────────────────
        "ranking_sub":        "\uc624\ub298\uc758 \ub9ac\ub354\ubcf4\ub4dc",
        "tab_friends":        "\uce5c\uad6c",
        "tab_all_users":      "\uc804\uccb4 \uc720\uc800",
        "metric_focus":       "\uc9d1\uc911",
        "metric_posture":     "\uc790\uc138",
        "loading":            "\ubd88\ub7ec\uc624\ub294 \uc911...",
        "todays_focus_label": "\uc624\ub298\uc758 \uc9d1\uc911",
        "friend_requests":    "\uce5c\uad6c \uc694\uccad",
        "add_friend":         "\uce5c\uad6c \ucd94\uac00",
        "search_by_nick":     "\ub2c9\ub124\uc784\uc73c\ub85c \uac80\uc0c9",
        "send_btn":           "\ubcf4\ub0b4\uae30",
        "me_badge":           "\ub098",
        "sessions_fmt":       "{n}\uc138\uc158",
        "avg_today":          "\uc624\ub298 \ud3c9\uade0",
        "no_data_yet":        "\ub370\uc774\ud130\uac00 \uc5c6\uc5b4\uc694.",
        "no_friends_yet":     "\uce5c\uad6c\uac00 \uc5c6\uc5b4\uc694.\n\uc704\uc5d0\uc11c \ub2c9\ub124\uc784\uc73c\ub85c \uac80\uc0c9\ud574 \uce5c\uad6c \uc694\uccad\uc744 \ubcf4\ub0b4\uc138\uc694!",
        "rank_today_fmt":     "\uc624\ub298 #{n}\uc704",
        "no_record_today":    "\uc624\ub298 \uae30\ub85d \uc5c6\uc74c",
        "accept":             "\uc218\ub77d",
        "reject_btn":         "\uac70\uc808",
        "request_sent_fmt":   "{nick}\uc5d0\uac8c \uce5c\uad6c \uc694\uccad\uc744 \ubcf4\ub0c8\uc5b4\uc694 \u2713",
        "err_enter_nick":     "\ub2c9\ub124\uc784\uc744 \uc785\ub825\ud558\uc138\uc694",
        # ── Profile extras ───────────────────────────────────────────
        "profile_title":      "\ub0b4 \ud504\ub85c\ud544",
        "profile_sub":        "\uacc4\uc815 \uc124\uc815\uc744 \uad00\ub9ac\ud558\uc138\uc694",
        "change_nickname":    "\ub2c9\ub124\uc784 \ubcc0\uacbd",
        "current_nick_fmt":   "\ud604\uc7ac: {nick}",
        "new_nickname_hint":  "\uc0c8 \ub2c9\ub124\uc784",
        "save_nickname_btn":  "\ub2c9\ub124\uc784 \uc800\uc7a5",
        "change_password":    "\ube44\ubc00\ubc88\ud638 \ubcc0\uacbd",
        "curr_pw_hint":       "\ud604\uc7ac \ube44\ubc00\ubc88\ud638",
        "new_pw_hint":        "\uc0c8 \ube44\ubc00\ubc88\ud638",
        "confirm_pw_hint":    "\uc0c8 \ube44\ubc00\ubc88\ud638 \ud655\uc778",
        "save_password_btn":  "\ube44\ubc00\ubc88\ud638 \uc800\uc7a5",
        "log_out":            "\ub85c\uadf8\uc544\uc6c3",
        "err_same_nick":      "\ud604\uc7ac \ub2c9\ub124\uc784\uacfc \uac19\uc544\uc694",
        "err_nick_taken":     "\uc774\ubbf8 \uc0ac\uc6a9 \uc911\uc778 \ub2c9\ub124\uc784\uc774\uc5d0\uc694",
        "ok_nick_available":  "\uc0ac\uc6a9 \uac00\ub2a5\ud574\uc694 \u2713",
        "err_check_nick":     "\ub2c9\ub124\uc784 \uc911\ubcf5 \ud655\uc778\uc744 \uba3c\uc800 \ud574\uc8fc\uc138\uc694",
        "ok_nick_updated":    "\ub2c9\ub124\uc784\uc774 \ubcc0\uacbd\ub418\uc5c8\uc5b4\uc694! \u2713",
        "err_enter_curr_pw":  "\ud604\uc7ac \ube44\ubc00\ubc88\ud638\ub97c \uc785\ub825\ud558\uc138\uc694",
        "err_enter_new_pw":   "\uc0c8 \ube44\ubc00\ubc88\ud638\ub97c \uc785\ub825\ud558\uc138\uc694",
        "err_pw_too_short":   "\ube44\ubc00\ubc88\ud638\ub294 6\uc790 \uc774\uc0c1\uc774\uc5b4\uc57c \ud574\uc694",
        "err_pw_no_match":    "\ube44\ubc00\ubc88\ud638\uac00 \uc77c\uce58\ud558\uc9c0 \uc54a\uc544\uc694",
        "err_pw_same":        "\uc0c8 \ube44\ubc00\ubc88\ud638\ub294 \ud604\uc7ac\uc640 \ub2ec\ub77c\uc57c \ud574\uc694",
        "err_curr_pw_wrong":  "\ud604\uc7ac \ube44\ubc00\ubc88\ud638\uac00 \ud2c0\ub838\uc5b4\uc694",
        "ok_pw_updated":      "\ube44\ubc00\ubc88\ud638\uac00 \ubcc0\uacbd\ub418\uc5c8\uc5b4\uc694! \u2713",

        # ── Common ───────────────────────────────────────────────────
        "mon": "월", "tue": "화", "wed": "수", "thu": "목",
        "fri": "금", "sat": "토", "sun": "일",
    },
}

_load_pref()
