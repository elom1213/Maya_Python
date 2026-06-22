# A00250_SceneMemo — 제작 계획서

> 마야 씬의 오브젝트(메시 / 커브 / 트랜스폼 등)에 사용자 메모를 남기고, 씬을 닫았다
> 다시 열어도 보존되며, 한국어 입력과 사후 편집이 가능한 in-DCC PySide 툴.

- **번호/이름**: `A00250_SceneMemo` (A00240은 PathTool로 사용 중 → 다음 빈 번호)
- **아키텍처**: B형 (PySide / Qt, in-Maya). `A00110_animTool` 복제로 시작
- **작성일**: 2026-06-22
- **상태**: 계획 (Draft)

---

## 1. 요구사항 정리

| # | 요구 | 대응 |
|---|------|------|
| R1 | 원하는 오브젝트들을 리스트업 | 선택 오브젝트를 "Add Selected"로 목록에 추가, 테이블로 표시 |
| R2 | 메모 작성 후 저장 | 멀티라인 에디터 + Save → 씬 내부 storage 노드에 기록 |
| R3 | 씬 닫고 다시 열어도 보존 | 메모를 **씬 내부 network 노드**에 저장 → `.ma/.mb` 파일에 포함 |
| R4 | 한국어 기록 | string 어트리뷰트(JSON, 유니코드) 저장. fileInfo(비ASCII 깨짐 위험) 미사용 |
| R5 | 사후 편집 | 행 선택 → 에디터에서 수정 → Save로 갱신. 삭제도 지원 |

---

## 2. 저장 전략 (핵심 설계)

### 2.1 정본(source of truth): 씬 내부 storage 노드

- 씬에 **`JUN_memo_store`** 라는 `network` 노드 1개를 생성(없으면 자동 생성).
- 이 노드에 긴 `string` 어트리뷰트 **`.junMemoData`** 를 추가하고 **JSON 문자열**을 저장.
- JSON 구조 (UUID 키):

```json
{
  "version": 1,
  "memos": {
    "5E2F...UUID...": { "memo": "머리 컨트롤러", "ts": 1718000000, "name_hint": "ctrl_head" },
    "9A11...UUID...": { "memo": "눈 리그 주의", "ts": 1718000100, "name_hint": "L_eye_jnt" }
  }
}
```

- **키는 노드 UUID** (`cmds.ls(sel, uuid=True)`): 리네임/부모변경에도 안 끊김.
- `name_hint`는 노드가 삭제됐을 때 "무엇이었는지" 사람이 알아보게 하는 참고용 이름.
- **왜 이 방식인가**
  - 메모가 `.ma/.mb` 파일 **안에** 들어가므로 Save As / 복사 / 이동에도 자동으로 따라감.
  - 미저장(Untitled) 씬에서도 노드로 보관 가능.
  - string 어트리뷰트는 유니코드(한국어) 안정적. (fileInfo는 구버전에서 비ASCII 깨질 수 있어 배제)
  - 노드 하나에 전체 메모가 모여 있어 목록화/편집/삭제/export가 단순.

### 2.2 부가: 마야 파일 옆으로 Export / Import (사이드카)

- "각 마야 파일 경로에 두고 싶다"는 요구는 **백업/공유/버전관리용 부가 기능**으로 제공.
- 마야 파일 옆에 직접 두지 않고 **전용 하위 폴더 `JUN_memo/`** 에 모아 저장 (`*_memo.json` 흩어짐 방지).
  - 폴더명 `JUN_memo`는 이 repo의 기존 컨벤션과 일치(CLAUDE.md `.gitignore: **/JUN_memo/`).
  - 경로: `os.path.join(os.path.dirname(scenePath), "JUN_memo", "<sceneName>_memo.json")`
  - 폴더 없으면 Export 시 자동 생성(`os.makedirs(..., exist_ok=True)`).
  - 씬이 미저장이면 Export 비활성 + 안내 메시지("Save the scene first").

```
<scene 폴더>/
├── charA_rig.ma
└── JUN_memo/
    └── charA_rig_memo.json
```
- 사이드카는 정본이 아님(아티스트가 .ma만 복사하면 desync 위험). 어디까지나 씬 내부 노드의 백업/이식 수단.

### 2.3 (옵션) 노드 notes 미러링

- 토글로 메모를 각 노드 내장 `notes` 어트리뷰트에도 복사 → Attribute Editor의 Notes 칸에서도 확인 가능.
- 기본 OFF. (referenced 노드는 reference edit로 저장되어 지저분해질 수 있어 신중히)

---

## 3. 모듈 구조 (B형, A00110 복제)

```
JUN_All/tools/A00250_SceneMemo/
├── __init__.py                 # from .launch import run
├── launch.py                   # run(reload_module=True): reload → MainWindow → 테마 → show
├── __dragDrop_A00250.py        # 셸프 버튼 설치 (basename 고유, 끝에서 sys.modules.pop)
├── requirements.txt
└── app/
    ├── __init__.py
    ├── config/
    │   ├── __init__.py
    │   └── version.py          # VERSION = "01.00", LAST_UPDATE
    ├── core/                   # ★ 로직 (DCC 의존은 여기만, UI와 분리)
    │   ├── __init__.py
    │   ├── memo_store.py       # MemoStore: storage 노드 ↔ JSON 읽기/쓰기 (CRUD)
    │   ├── memo_io.py          # 사이드카 Export/Import (json 파일)
    │   └── scene_callbacks.py  # (옵션) sceneOpened/selectionChanged 콜백 등록/해제
    └── ui/
        ├── __init__.py
        └── main_window.py      # MainWindow(QWidget) — A00110 패턴
```

- `launch.py` / `__dragDrop_A00250.py` / `__init__.py`는 A00110에서 복제 후 번호만 치환.
  - 셸프 명령은 `tools.A00250_SceneMemo.run(True)`, `WINDOW_OBJECT_NAME = "JUN_A00250_SceneMemo_window"`.
  - reload는 `from dev.reloader_v02 import reload_for_tool` → `reload_for_tool("tools.A00250_SceneMemo")`.
- UI import는 `from Framework.qt.qt import *`, `from Framework.qt.maya_window import maya_main_window`.
- 테마: `ThemeManager.load_theme_to_widget(window_instance, "coral_dark")` (A00110과 동일).

---

## 4. core 설계

### 4.1 `MemoStore` (memo_store.py) — DCC 로직의 중심

```
STORE_NODE = "JUN_memo_store"
DATA_ATTR  = "junMemoData"

class MemoStore:
    def _ensure_store(self) -> str        # 노드/어트리뷰트 없으면 생성, 노드명 반환
    def _read_raw(self) -> dict           # JSON 파싱 (없으면 빈 구조)
    def _write_raw(self, data: dict)      # JSON dump → string attr 세팅

    def list_memos(self) -> list[dict]    # [{uuid, node(현재명 or None), memo, ts, missing}]
    def set_memo(self, uuid, memo, name_hint)   # 추가/수정 (upsert)
    def add_selected(self) -> int         # 선택 노드들 등록(메모 빈 값으로) → 추가 개수
    def remove(self, uuid)                # 삭제
    def clean_orphans(self) -> int        # 현재 씬에 없는 UUID 항목 제거 → 정리 개수
    def select_in_scene(self, uuid)       # UUID로 노드 찾아 cmds.select
```

- 현재 노드명 resolve: `cmds.ls(uuid)[0]` → 없으면 `missing=True` (UI에서 회색/“(missing)” 표시).
- 저장 시 `name_hint`도 같이 갱신(현재 노드명 스냅샷).
- 유니코드: `json.dumps(data, ensure_ascii=False)`, attr 세팅은 `cmds.setAttr(attr, val, type="string")`.

### 4.2 `memo_io.py` — 사이드카

```
def export_sidecar(store: MemoStore) -> str|None    # <scene>_memo.json 쓰기, 경로 반환
def import_sidecar(store: MemoStore, path: str)     # json 읽어 store에 merge
```

- 파일 IO는 `encoding="utf-8"`. 머지 정책(겹치는 UUID는 import 우선/스킵)은 UI에서 선택.

### 4.3 `scene_callbacks.py` (옵션, 2차)

- `OpenMaya.MSceneMessage` 로 `kAfterOpen` 콜백 등록 → UI 자동 새로고침.
- 창 닫힐 때(`closeEvent`) 콜백 해제 (A00110의 hotkey restore 패턴과 동일하게 안전 처리).

---

## 5. UI 설계 (main_window.py)

```
┌ Scene Memo  v01.00 ──────────────────────────────┐
│ [ Add Selected ] [ Remove ] [ Refresh ]          │
│ Search: [____________________]                   │
│ ┌──────────────────────────────────────────────┐│
│ │ Object         | Memo (preview)   | Updated   ││  ← QTableWidget
│ │ ctrl_head      | 머리 컨트롤러     | 06-22 ... ││
│ │ (missing) L_.. | 눈 리그 주의      | 06-22 ... ││  ← 삭제된 노드 회색
│ └──────────────────────────────────────────────┘│
│ Memo:                                            │
│ ┌──────────────────────────────────────────────┐│
│ │ (QPlainTextEdit — 멀티라인, 한국어)            ││
│ └──────────────────────────────────────────────┘│
│ [ Save Memo ]   [ Select in Scene ]              │
│ ─ Tools ─ [ Clean Orphans ] [ Export ] [ Import ]│
└──────────────────────────────────────────────────┘
```

- **테이블**: 행 = 메모 항목. 컬럼 = Object(현재명) / Memo preview / Updated. 행 클릭 → 하단 에디터에 로드.
- **Add Selected**: 선택 오브젝트를 빈 메모로 등록 → 바로 편집.
- **Memo 에디터**: `QPlainTextEdit` (한국어 IME 정상). Save Memo로 현재 행에 반영.
- **Select in Scene**: 행의 UUID로 씬에서 노드 선택.
- **Search**: 노드명/메모 내용 필터.
- **Clean Orphans / Export / Import**: 4장 core 호출.
- **저장 안내**: "Saved to scene — remember to save the Maya file (Ctrl+S)." (메모는 씬 노드에 들어가므로 실제 디스크 영속은 씬 저장 시점). UI 텍스트는 영어, 코드/주석은 한국어.

> UI 문자열은 전부 영어(메모리 가이드 `ui-text-english-only`). 메모 **내용**은 사용자가 한국어로 입력.

---

## 6. 엣지 케이스 / 주의

- **UUID 중복/충돌**: import 머지 시 동일 UUID 정책 명시(기본: import가 덮어씀, 토글로 skip).
- **referenced 노드**: storage 노드 자체는 항상 현재 씬에 생성(레퍼런스로 들어온 노드도 UUID로 메모 가능). notes 미러링은 referenced 노드에서 신중.
- **노드 삭제**: 메모는 orphan으로 남음 → "Clean Orphans"로 정리. 자동 삭제는 안 함(실수로 지운 뒤 메모 복구 여지).
- **Undo**: setAttr 기반이라 Maya undo에 잡힘. 필요 시 `cmds.undoInfo(openChunk/closeChunk)`로 묶기.
- **Untitled 씬**: 저장 노드는 OK, 사이드카 Export만 비활성.
- **Maya 2023 호환**(메모리 `maya-2023-compat`): 사용하는 cmds(`addAttr`/`setAttr`/`ls uuid`/`scriptNode` 미사용)는 2023 OK.

---

## 7. 구현 순서 (마일스톤)

1. **M1 — 스캐폴드**: A00110 복제 → 번호 치환(`__init__`, `launch`, `__dragDrop_A00250`, `version`), 빈 MainWindow 띄우기.
2. **M2 — MemoStore CRUD**: storage 노드 생성/JSON 읽기쓰기, list/set/remove/add_selected. (마야에서 단위 확인)
3. **M3 — UI 연결**: 테이블 + 에디터 + Add/Save/Remove/Refresh/Select. 한국어 입력·저장·재로드 검증.
4. **M4 — 영속 검증**: 저장 → 씬 저장 → 닫기 → 재오픈 → 메모 복원 확인 (R3 핵심).
5. **M5 — 부가**: Search, Clean Orphans, Export/Import 사이드카.
6. **M6 — (옵션)**: sceneOpened 콜백 자동 새로고침, notes 미러링 토글.
7. **M7 — 마무리**: `JUN_All/docs/A00250_SceneMemo.md` 가이드 작성, CHANGELOG/version, WORKLOG 갱신, push(메모리 `push-includes-tool-guide-docs`, `push-target-dnable-dev`).

---

## 8. 확정 필요 사항

- [x] 이름: **A00250_SceneMemo**
- [x] 저장: **씬 내부 storage 노드(JSON) 정본 + 사이드카 Export/Import 부가**
- [ ] notes 미러링(6번) 포함할지 여부 — 1차에서 제외 권장
- [x] 사이드카 위치: 마야 파일 옆 **`JUN_memo/` 하위 폴더**에 `<sceneName>_memo.json`
