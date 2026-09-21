# release_builder_QT — Release Builder (사용 안내)

툴을 **골라서 릴리즈 폴더로 복사**하는 개발용 Qt 창이다. 손으로 `dev/build_release.py` 의
`TOOL_PATH` 를 고쳐 가며 돌리던 일을 대체한다.

- 버전: `v01.02` (`app/config/version.py`) — **목록 검색(Filter)** · **공용 로그창** · **아이콘**
- 위치: `JUN_All/dev/release_builder_QT` (배포 대상이 아니라 **개발 도구**다)
- 형태: 아키텍처 (B) — PySide. 복사 로직(`app/core/release_builder.py`)은 **Qt 비의존**

---

## 1. 실행

```bash
python JUN_All/dev/release_builder_QT/launch.py
```

마야 안에서도 뜬다(이미 도는 이벤트 루프를 감지해 창만 돌려준다).

```python
from dev.release_builder_QT.launch import run
run()
```

---

## 2. 화면

```
┌───────────────────────────────────────────────┐
│ Tools to release                Number: 3 / 66│  ← 필터 중이면 보이는수 / 전체수
│ ┌───────────────────────────────────────────┐ │
│ │ ☑ A00020_move_skineWeightTool             │ │
│ │ ☐ A00270_skinMigrate                      │ │
│ └───────────────────────────────────────────┘ │
│ Filter [ skin              ] [ Clear ]        │  ← v01.02
│ [ Select All ] [ Clear ] [ Refresh ]          │
│ Release destination                           │
│ [ G:/.../Maya_Tool_Release/tools ] [Browse...]│
│ ☑ Include docs                                │
│ [               Release               ]       │
│ ┌ 로그 (Expand / Shrink / Clear / Copy) ────┐ │  ← v01.02, 공용 위젯
│ └───────────────────────────────────────────┘ │
└───────────────────────────────────────────────┘
```

---

## 3. `Filter` — 목록 검색 (v01.02~)

툴이 60개를 넘으면서 눈으로 찾는 것이 일이 됐다. 공용 위젯
[`JUN_mod_filter_qt_v01`](Framework_MOD_filter_qt.md) 을 붙였고, 규칙은 **다른 툴과 같다.**

- **부분 일치 · 대소문자 무시** — `skin` → `A00020_move_skineWeightTool`, `A00275_skinTool_V01`
- 공백으로 나눈 **여러 단어는 AND** — `tool skin` 은 둘 다 가진 것만
- 항목을 지우는 게 아니라 **가린다** → `Clear` 로 비우면 그대로 돌아온다
- 헤더에 **`Number: 보이는수 / 전체수`**

### ★ 체크와 필터는 따로 논다

Qt 는 **숨긴 항목의 체크를 유지한다.** 그래서 두 가지를 정해 두었다.

| 동작 | 규칙 |
|------|------|
| `Select All` / `Clear` | **보이는 것에만** 건다 — 그게 필터를 쓰는 이유다. 가려진 항목은 하던 대로 둔다 |
| `Release` | 체크된 것은 **가려져 있어도 릴리즈한다.** 대신 로그에 `[NOTE] N checked tool(s) are hidden by the filter - they are released too.` 를 남긴다 |

체크는 **명시적인 의사표시**라 필터에 가렸다고 없던 일로 만들지 않되, **모르고 나가는 일도
없게** 한다(같은 판단이 `A00145_RigConnect` 의 Attribute 탭에도 있다).

`Refresh` 는 폴더를 다시 읽고 **필터 글자는 그대로 둔 채** 다시 먹인다
(`Filter 'curve' is on - showing 2 of them.` 이 로그에 남는다).

---

## 4. 로그창 (v01.02~)

공용 위젯 [`JUN_mod_log_qt_v01`](Framework_MOD_log_qt.md) 로 바꿨다 —
`Expand`(별도 창) / `Shrink` / `Clear` / `Copy`. 릴리즈 로그가 길어 **Expand 로 크게 보는 것**이
실익이다. 툴은 `appendPlainText` 로 쓴다 — 이 로그에는 경로와 `=` 구분선이 들어가는데
`append()` 는 **HTML 로 해석**하기 때문이다.

---

## 5. 아이콘 (v01.02~)

`icon/release_builder_QT.svg` · `.png`(32px) · `.ico`(16·24·32·48·64·128·256).

- 그림: 공통 배경 틀(rx=6) 위에 **열린 상자 + 위로 나가는 화살표**(= 내보내기).
- 창 아이콘은 `MainWindow` 가, 앱 아이콘은 `launch.py` 가 건다.
- ★ **작업 표시줄은 아이콘만으로 안 바뀐다** — 터미널로 띄우면 프로세스가 `python.exe` 라
  파이썬 아이콘이 남는다. 그래서 `QApplication` 을 만들기 **전에**
  `SetCurrentProcessExplicitAppUserModelID` 를 부른다(`app/config/app_meta.py`).
  배경은 [`taskbar_icon_guide.md`](taskbar_icon_guide.md).
- `.ico` 는 **각 크기를 SVG 에서 직접 렌더**해 만들고 **가장 큰 프레임을 base** 로 저장한다.
  한 장을 축소해 만들면 `QIcon.availableSizes()` 가 한 크기만 본다.

---

## 6. 구조

```
dev/release_builder_QT/
├─ launch.py                 # AppUserModelID -> QApplication -> 테마 -> 창
├─ icon/release_builder_QT.svg|.png|.ico
└─ app/
   ├─ config/version.py
   ├─ config/app_meta.py     # 아이콘 경로 + AppUserModelID
   ├─ core/release_builder.py  # 복사 로직 (Qt 비의존)
   └─ ui/main_window.py      # 목록 · 필터 · 목적지 · 릴리즈 · 로그
```

---

## 7. 검증

오프스크린 Qt **30항목 통과** — 목록 채우기 · 필터(부분 일치 · AND · 없음 · 비우기 ·
`Number` 라벨) · **Select All / Clear 가 보이는 것에만** · 체크가 필터를 넘어 유지되는지 ·
**가려진 체크 수를 릴리즈 때 알리는지** · Refresh 가 필터를 지키는지 ·
공용 로그창 교체와 Expand/Collapse · 평문 기록 · 아이콘(.ico 다중 크기 · 창 아이콘 · AUMID).
