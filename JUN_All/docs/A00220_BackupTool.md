# A00220_BackupTool — 사용 안내

컴퓨터가 사고로 종료되는 상황에 대비해, **지정한 파일들을 일정 주기마다 자동으로 복사·백업**하는
파이프라인 보조 툴. 작업 파일을 옆에 계속 복제해 두어 **갑작스러운 종료/크래시 시 직전 상태를
복구**할 수 있게 한다.

> 이 툴은 Maya 안에서 도는 툴이 아니라 `A00210_FileManager` 처럼 **Windows 에서 독립 실행되는
> PySide6 앱** 이다. Maya 설치/실행 없이 동작한다.

---

## 1. 핵심 개념

| 개념 | 설명 |
|------|------|
| **Target Files** | 백업할 파일 목록. 여러 개를 한 번에 등록할 수 있다. |
| **backup 폴더** | 백업본이 쌓이는 곳. **각 원본 파일이 있는 폴더 아래**에 만들어진다(폴더가 이미 있으면 그대로 사용). 폴더 이름은 UI 에서 지정(기본 `backup`). |
| **Suffix** | 백업 파일 이름 뒤에 붙는 표식(기본 `BU`). `scene.mb` → `scene_BU.mb`. |
| **Save Mode** | `Overwrite`(기본) 또는 `Version Up`. |
| **Interval** | 저장 주기(분 + 초). |

백업 파일은 확장자 **앞**에 접미사를 붙인다: `scene.mb` → `scene_BU.mb`(덮어쓰기) /
`scene_BU_01.mb`, `scene_BU_02.mb` …(버전업).

설정(파일 목록·옵션·주기)은 git 으로 공유하지 않고 **로컬 prefs** 에 저장된다:
`%USERPROFILE%/.jun_backuptool/prefs.json` (다음 실행 시 자동 복원).

---

## 2. 실행

- **개발 실행**: `python JUN_All/tools/A00220_BackupTool/launch.py`
- **exe 빌드**: 툴 폴더의 `build_exe.bat`(PyInstaller, `launch.spec`) → `dist/A00220_BackupTool.exe`
- 필요 패키지: `PySide6`, `pyinstaller`. 백업 로직은 **표준 라이브러리**(shutil/os/re/json)만 쓴다.

---

## 3. 화면 구성

```
┌ Target Files ─────────────────────────────────┐
│ C:/work/sceneA.mb                              │
│ C:/work/charB/rig.ma                           │
│ [Add Files...] [Remove Selected] [Clear]       │
└────────────────────────────────────────────────┘
┌ Settings ─────────────────────────────────────┐
│ Backup Folder Name [ backup ]                  │
│ Suffix             [ BU ]                       │
│ Save Mode   (•) Overwrite   ( ) Version Up     │
│ Max Versions [ 10 ]                            │
│ Interval     [ 5 ] min  [ 0 ] sec              │
└────────────────────────────────────────────────┘
┌ Control ──────────────────────────────────────┐
│ [           Start            ]                  │
│        🦖  (Chrome-Dino 애니메이션)            │
│  ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾                  │
│                  Next save in  --:--           │
└────────────────────────────────────────────────┘
┌ Log ──────────────────────────────────────────┐
│ ...                                            │
└────────────────────────────────────────────────┘
```

---

## 4. 저장 모드

| 모드 | 동작 | 결과 파일 |
|------|------|-----------|
| **Overwrite** (기본) | 매 주기마다 같은 이름으로 **덮어쓴다**. | `scene_BU.mb` 하나만 계속 갱신 |
| **Version Up** | 매 주기마다 번호를 올려 새 파일을 만든다. **최근 N개만 유지**(N 초과 시 가장 오래된 버전 자동 삭제 = 롤오버). `Max Versions` 로 N 지정. | `scene_BU_01.mb`, `scene_BU_02.mb` … |

---

## 5. 상태 표시 — Chrome Dino (v01.04)

`Control` 의 상태는 **글자 대신 Chrome-Dino(T-Rex) 픽셀 애니메이션**으로 보인다
(이미지 에셋 없이 `app/ui/dino_widget.py` 가 QPainter 로 그린다 — 테마 무관, exe 번들 불필요).

| 공룡 동작 | 의미 |
|-----------|------|
| **가만히 서 있음** | 정지 상태(기본, Deactive). |
| **제자리 달리기 + 주기적 점프** | 주기 백업 동작 중(Active). 다리가 교차하고 바닥 점선이 흐르며 약 2.6초마다 점프. |
| **추가 점프(hop)** | 지금 백업 파일을 쓰는 순간(Saving) 한 번 더 폴짝 뛰어 강조. |
| `Next save in  MM:SS` | 다음 자동 저장까지 남은 시간(1초마다 갱신). 정지 시 `--:--`. |

---

## 6. 사용 순서

1. `Add Files...` 로 백업할 파일을 등록한다(여러 개 가능).
2. `Backup Folder Name` / `Suffix` 를 원하면 바꾼다(기본 `backup` / `BU`).
3. `Save Mode` 선택 — 보통 `Overwrite`. 이력을 남기려면 `Version Up` + `Max Versions`.
4. `Interval` 에 저장 주기(분·초)를 넣는다.
5. `Start` — 즉시 1회 백업 후 주기마다 반복. 상태가 `Active...` 로 바뀌고 카운트다운이 흐른다.
6. `Stop` — 백업 중지(`Deactive`). 창을 닫으면 타이머가 멈추고 설정이 저장된다.

> 백업 도중 원본 파일이 사라지면 그 파일만 건너뛰고(로그에 표기) 나머지는 계속 백업한다.

---

## 7. 구조 (개발 참고)

```
A00220_BackupTool/
├── launch.py                 # standalone 진입점 (green_dark 테마)
└── app/
    ├── config/version.py     # VERSION / LAST_UPDATE
    ├── core/
    │   ├── backup_manager.py # 백업 핵심 로직 (Qt/DCC 비의존)
    │   └── prefs.py          # 로컬 설정 영속화
    └── ui/main_window.py     # Qt UI + 타이머(주기·점 애니메이션·카운트다운)
```

- `app/core`(로직)와 `app/ui`(화면)를 분리한다(`backup_manager` 는 표준 라이브러리만 사용).
- import 는 **툴 고유 경로**(`tools.A00220_BackupTool.app...`)와 내부 **상대 import** 로 한다 —
  여러 standalone 툴을 한 인터프리터에서 동시에 띄울 때 최상위 `app` 패키지가 충돌하지 않도록.
