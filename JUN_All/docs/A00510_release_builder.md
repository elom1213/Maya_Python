# A00510_release_builder — Release Builder (사용 안내)

> v01.03 (2026-10-12) 까지 폴더 이름은 `dev/release_builder_QT` 였다. dev 의 툴도 tools 와 같은 `A00XXX_` 번호 규칙으로 관리한다.

툴을 **골라서 릴리즈 폴더로 복사**하는 개발용 Qt 창이다. 손으로 `dev/build_release.py`(지금은 `legacy/` 에 보존)의
`TOOL_PATH` 를 고쳐 가며 돌리던 일을 대체한다.

- 버전: `v01.04` (`app/config/version.py`) — v01.02 에 **목록 검색(Filter)** · **공용 로그창** · **아이콘**, v01.03 에 이름 변경 + 셸프 설치,
  v01.04 에 **마야 UI 테마 오염 수정** + `Run_ReleaseBuilder.bat` · 아이콘 바로가기
- 위치: `JUN_All/dev/A00510_release_builder` (배포 대상이 아니라 **개발 도구**다)
- 형태: 아키텍처 (B) — PySide. 복사 로직(`app/core/release_builder.py`)은 **Qt 비의존**

---

## 1. 실행

**더블클릭 (v01.04~)**: `dev/A00510_release_builder/Run_ReleaseBuilder.bat`.
설치된 64비트 파이썬 중 PySide6(또는 PySide2) 가 있는 것을 찾아(`py -3.14` … `-3.7` → PATH 의 `python`,
스토어 바로가기는 건너뜀) **콘솔 없이**(`pythonw`) 띄운다. 아무것도 설치하지 않는다.

- ★ **`.bat` 파일은 Windows 에서 아이콘을 바꿀 수 없다.** 그래서 bat 이 실행될 때마다 같은 폴더에
  **`Release Builder.lnk`**(툴 아이콘 · launch 와 같은 AppUserModelID) 를 만들어 둔다 — 탐색기에서
  평소에도 툴 아이콘으로 보이고, 이후엔 이 바로가기를 더블클릭하면 된다. 작업 표시줄에 고정해도
  파이썬 아이콘이 아니다.
- 바로가기는 절대 경로(파이썬 · 폴더)를 담아 **git 에 넣지 않는다**(`.gitignore`). 내용을
  `.shortcut_stamp` 에 적어 두고 파이썬이나 폴더가 바뀌었을 때만 다시 만든다(`make_shortcut.py`).
- 옵션: `--console`(오류가 화면에 남음) · `--shortcut`(바로가기 다시 만들기) · `--no-launch`(확인만)

마야 셸프: `dev/A00510_release_builder/__dragDrop_A00510.py` 를 뷰포트로 드래그&드롭하면 `Release` 버튼이 생긴다
(`dev.A00510_release_builder.run()`). 터미널:

```bash
python JUN_All/dev/A00510_release_builder/launch.py
```

마야 안에서도 뜬다(이미 도는 이벤트 루프를 감지해 창만 돌려준다).

> ★ **v01.04 수정 — 마야 UI 가 이 툴의 테마로 바뀌던 문제.** 예전 `launch.run()` 은 마야 안에서도
> `ThemeManager.load_theme_dev(app, "dark")` 로 qss 를 **QApplication** 에 입혔다. 마야 안의 app 은
> 마야 자신이라 **마야의 모든 위젯**이 dark.qss 를 받았다. 또 launch 를 import 하는 것만으로
> `SetCurrentProcessExplicitAppUserModelID` 가 불려 **마야 프로세스의 작업 표시줄 ID** 가 바뀌었다.
> 이제 앱 전역에 손대는 것(qss · 앱 아이콘 · AUMID)은 **이 프로세스가 QApplication 을 만들 때만** 하고,
> 마야 안에서는 `ThemeManager.load_theme_to_widget(win, "dark")` 로 **이 창에만** 입힌다.
> 셸프 버튼을 다시 누르면 이전 창을 닫고 새로 띄운다.

```python
from dev.A00510_release_builder.launch import run
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

`icon/A00510_release_builder.svg` · `.png`(32px) · `.ico`(16·24·32·48·64·128·256).

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
dev/A00510_release_builder/
├─ launch.py                 # 내 앱이면 AUMID -> QApplication -> 앱 테마, 마야면 창에만 테마
├─ Run_ReleaseBuilder.bat    # 더블클릭 실행 (v01.04)
├─ make_shortcut.py          # 툴 아이콘 바로가기 Release Builder.lnk (v01.04)
├─ icon/A00510_release_builder.svg|.png|.ico
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

v01.04 (오프스크린, PySide6): **앱이 이미 있을 때**(= 마야) `run()` 두 번 → 앱 qss 빈 채 그대로 ·
다른 위젯 qss 없음 · 창에만 qss · 프로세스 AUMID 그대로 · 이전 창 닫힘. **앱이 없을 때** → 앱 qss 적용 후
정상 종료. `Run_ReleaseBuilder.bat --no-launch` → Python 3.11 선택 · 바로가기 생성(대상 pythonw + launch.py,
아이콘 .ico), 두 번째 실행은 스탬프로 건너뜀(0.46초). **실제 마야 GUI 확인 아직.**
