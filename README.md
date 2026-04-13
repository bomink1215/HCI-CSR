# FocusMate — Flet 데스크탑 앱

집중력을 높이는 올인원 생산성 도구: 자세 교정 · 뽀모도로 · 할 일 · 친구 랭킹

## 빠른 시작

```bash
pip install -r requirements.txt
python main.py
```

## 프로젝트 구조

```
focusmate/
├── main.py                  # 앱 진입점, 페이지 설정, 네비게이션
├── requirements.txt
├── components/
│   ├── nav.py               # 사이드 네비게이션 바
│   ├── notification.py      # 자세 경고 팝업
│   └── ui.py                # 공통 UI 헬퍼 (card, btn 등)
└── views/
    ├── dashboard.py         # 대시보드 (오늘의 현황)
    ├── posture.py           # 웹캠 자세 교정
    ├── pomodoro.py          # 뽀모도로 타이머 (실제 작동)
    ├── todo.py              # 할 일 메모 (CRUD)
    └── ranking.py           # 친구 집중 시간 랭킹
```

## 다음 단계: 자세 감지 연동

`views/posture.py`의 `_toggle_monitoring`에 아래 로직을 추가합니다:

```python
import cv2, mediapipe as mp

def posture_worker(self):
    mp_pose = mp.solutions.pose
    cap = cv2.VideoCapture(0)
    with mp_pose.Pose() as pose:
        while self.monitoring:
            ret, frame = cap.read()
            if not ret: break
            results = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if results.pose_landmarks:
                score = calculate_posture_score(results.pose_landmarks)
                self._update_score(score)
    cap.release()
```

## 디자인 토큰

| 변수 | 값 | 용도 |
|------|----|------|
| BG_DARK | #080B10 | 앱 배경 |
| BG_CARD | #0D1117 | 카드 배경 |
| ACCENT  | #00E5CC | 주요 강조색 |
| ACCENT2 | #FF6B6B | 경고/위험 |
| PURPLE  | #A78BFA | 보조 포인트 |

## 패키징 (Windows/Mac)

```bash
# Windows exe
flet pack main.py --name FocusMate --icon assets/icon.ico

# macOS .app
flet pack main.py --name FocusMate --icon assets/icon.icns
```
