# A00210_FileManager — 사용 안내

Maya 씬 파일(`.mb` / `.ma`)의 **버전·작업 기록 추적** 파이프라인 툴.
경로를 지정하면 그 폴더의 Maya 파일들이 **어떤 작업인지(작업자·기록)** 와 **썸네일** 로 보이고,
기록을 **git 으로 push/pull** 해 **어느 PC 에서나 동일하게 로그를 추적**한다.
**원본 mb/ma 는 push 대상이 아니다.**

> 이 툴은 Maya 안에서 도는 툴이 아니라 `A00080_KWI_creator_V02` 처럼 **Windows 에서 독립 실행되는
> PySide6 앱** 이다. Maya 설치/실행 없이 동작한다.

---

## 1. 핵심 개념

| 개념 | 설명 |
|------|------|
| **Project Root** | Maya 파일들이 모여 있는 작업 루트. 기록 키(key)를 이 기준 **상대경로**로 만든다. |
| **Store Repo** | 기록(JSON)·썸네일(PNG)을 모아두는 **중앙 git 데이터 리포**(예: `JUN_FileManager_data`). |
| **key** | `Project Root` 기준 상대경로(예: `chars/charA_rig.mb`). PC 가 달라도(예: `P:/proj` vs `D:/work`) **같은 파일이 같은 기록**에 매핑된다. |
| **원본 제외** | 원본 mb/ma 는 Store Repo 에 애초에 들어가지 않는다(+ `.gitignore` 로 `*.mb`/`*.ma` 이중 차단). |

스토어 레이아웃:
```
JUN_FileManager_data/        # git repo
├── .gitignore               # *.mb, *.ma, __pycache__/
├── records/<key>.json       # records/chars/charA_rig.mb.json
└── thumbs/<key>.png         # thumbs/chars/charA_rig.mb.png
```

PC 마다 다른 절대경로·작업자명은 git 으로 공유하지 않고 **로컬 prefs** 에 저장한다:
`%USERPROFILE%/.jun_filemanager/prefs.json` (push 대상 아님).

---

## 2. 실행

- **개발 실행**: `python JUN_All/tools/A00210_FileManager/launch.py`
- **exe 빌드**: 툴 폴더의 `build_exe.bat`(PyInstaller, `launch.spec`) → `dist/A00210_FileManager.exe`
- 필요 패키지: `PySide6`, `pyinstaller`. git sync 는 **시스템 git(PATH)** 을 사용한다(별도 패키지 없음).

---

## 3. 화면 구성

```
┌ Settings ─────────────────────────────────────────────┐
│ Project Root [............] [Browse]                   │
│ Store Repo   [............] [Browse]                   │
│ Scan Dir     [............] [Browse]                   │
│                            [Recursive]      [ Scan ]   │
│ Remote [..] Branch [..] Author [.....]  [Save Settings]│
└────────────────────────────────────────────────────────┘
┌ 파일 목록 ───────────┐ ┌ 상세 ───────────────────────┐
│ File / Author /      │ │ [ thumbnail 320x180 ]        │
│ Thumb / Record / 수정│ │ [Capture Region][Load Image] │
│ ...                  │ │ Author [...........]         │
│                      │ │ Log history (read only)      │
│                      │ │ New note [...]               │
│                      │ │ [Add Log Entry][Save Record] │
└──────────────────────┘ └──────────────────────────────┘
┌ Git Sync ────────────────────────────────────────────┐
│ [ Pull ] [ Push ]            status...                 │
└────────────────────────────────────────────────────────┘
( 하단 로그 출력 )
```

---

## 4. 사용 흐름

1. **설정**: `Project Root`, `Store Repo`, `Remote`/`Branch`, `Author` 를 채우고 **Save Settings**.
   - 처음이라면 **Pull**(또는 Push) 시 Store Repo 가 git repo 가 아니면 자동으로 `git init` + 스켈레톤(`records/`,
     `thumbs/`, `.gitignore`)을 만든다. 원격에서 받아오려면 Store Repo 를 비운 폴더로 두고 원격 URL 을 사용한다.
2. **스캔**: `Scan Dir` 지정(보통 Project Root 하위) → **Scan**. `.mb`/`.ma` 목록이 뜬다.
   - `Thumb`/`Record` 열의 `O` 는 썸네일·기록 존재 표시. Project Root 밖 파일은 회색(`out of project root`)으로 비활성.
3. **기록 작성**: 파일을 선택 → 우측에서 **Author** 입력, **New note** 작성 후 **Add Log Entry**(타임스탬프 자동) →
   **Save Record**. `records/<key>.json` 이 생성/갱신된다.
4. **썸네일**: **Capture Region** → 화면이 어두워지면 드래그로 영역 선택(예: Maya 뷰포트, 뷰어 등 화면에 보이는 것).
   선택 즉시 `thumbs/<key>.png` 로 저장되고 미리보기가 갱신된다. (`Esc` 취소)
   - 외부 이미지를 쓰려면 **Load Image...** 로 PNG/JPG 를 지정한다.
5. **공유(Push/Pull)**:
   - **Push**: `records`/`thumbs` 변경을 커밋 후 원격에 푸시. **원본 mb/ma 는 포함되지 않는다.**
   - **Pull**: 다른 PC 에서 같은 `Project Root` 를 지정하고 Pull 하면, 동일 상대경로 키로 기록·썸네일이 그대로 보인다.

> 여러 PC 가 같은 파일 기록을 동시에 수정하면 git 충돌이 날 수 있다. **Push 전에 Pull** 하는 습관을 권장한다.

---

## 5. 구조 (개발자용)

```
A00210_FileManager/
├── launch.py            # main(): QApplication → ThemeManager(blue_dark) → MainWindow → exec
├── launch.spec          # PyInstaller
├── build_exe.bat
├── requirements.txt
├── CHANGELOG.md
└── app/
    ├── config/version.py    # VERSION, LAST_UPDATE
    ├── core/                # 순수 로직 (Qt/Maya 비의존)
    │   ├── models.py        # FileRecord, LogEntry
    │   ├── store.py         # MetaStore: 키 산출, record JSON / 썸네일 read·write
    │   ├── scanner.py       # 디렉터리 .mb/.ma 수집 + 기록 조인
    │   ├── prefs.py         # PC 로컬 설정 저장/로드
    │   └── git_sync.py      # GitSync: ensure/clone, pull, push (subprocess git)
    └── ui/
        ├── main_window.py   # MainWindow(QWidget) 조립 + 핸들러
        ├── file_table.py    # 파일 목록 위젯
        └── region_capture.py# 화면 영역 캡쳐 오버레이
```

- **core 는 Qt/Maya 를 import 하지 않는다** → 단위 테스트·exe 빌드 용이. 화면 캡쳐만 Qt(`QScreen.grabWindow`)에 의존.
- Qt 바인딩은 `Framework/qt/qt.py`(PySide6→2 폴백), 테마는 `Framework/themes/theme_manager.py`(`blue_dark.qss`) 재사용.

---

## 6. 주의

- git 은 PATH 의 시스템 `git` 을 사용한다. 미설치/원격 미설정/인증 실패/충돌은 하단 로그에 메시지로 표시되며 앱이
  죽지 않는다. 인증은 캐시된 git 자격증명에 의존한다.
- Store Repo 는 **이 프로젝트 repo 와 별개**의 전용 데이터 리포를 쓴다(예: `JUN_FileManager_data`).
- 화면 캡쳐는 멀티 모니터/DPI 환경의 좌표를 고려한다. 캡쳐 시 앱 오버레이는 잠깐 숨겨져 자기 창은 찍히지 않는다.
- UI 텍스트·로그·git 커밋 메시지는 영어, 주석/문서는 한국어(프로젝트 관례).
