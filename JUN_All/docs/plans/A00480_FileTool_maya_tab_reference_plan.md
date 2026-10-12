---
title: A00480_FileTool — Maya 탭 · Reference 하위탭 계획서
aliases: [FileTool Maya tab, Reference import plan, A00480 Maya plan]
tags: [plan, maya-python, file, reference, namespace, A00480_FileTool, A00240_PathTool, framework]
updated: 2026-10-12
---

# Maya 탭 · Reference 하위탭 계획서

A00480_FileTool 에 **`Maya` 탭**을 추가한다. 마야 파일(씬 파일 자체)을 다루는 명령을 모으는 탭이며,
첫 하위탭은 **`Reference`** — 여러 마야 파일이 어떤 파일을 레퍼런스로 부르는지 보고, 고른 레퍼런스를
**각 파일 안으로 임포트해서 다시 저장**한다.

> 이 문서는 **계획서**다. 구현 전 진단 · 설계 · 검증 계획과, 사용자가 정해 줘야 할 것을 담는다.
> **구현은 §11 의 결정이 내려진 뒤 시작한다.**

---

## 1. 요청 요약

| # | 요청 | 비고 |
|---|------|------|
| 1 | `Maya` 탭 신설, 그 안에 하위탭. 첫 하위탭은 `Reference` | 나중에 **독립 툴로 분리될 수 있음** → 코드 배치가 그걸 전제해야 한다 |
| 2 | **Tree** (A00240 Tree 탭과 같은 기능 · UI) 로 마야 파일을 찾아 **체크박스**로 여러 개 고른다 | Shift 범위 선택 뒤 체크 하나로 전부 체크/해제 |
| 3 | **Maya File** 리스트 — 고른 파일을 담는다. 추가 · 일부/전체 제거 | |
| 4 | **Get Reference** — Maya File 에서 선택한 파일들이 부르는 레퍼런스를 **Reference** 리스트에 | |
| 5 | Reference 는 **트리** — 레퍼런스 안의 레퍼런스(중첩)를 자식으로, **기본 전부 접힘** | TSL 이 아니어도 됨 |
| 6 | Reference 각 행에 **체크박스**, Shift 다중 체크 | |
| 7 | **Import Reference** — 체크된 레퍼런스를 **그 레퍼런스를 부르는 마야 파일마다** 임포트하고 저장. 중첩 레퍼런스도 함께 임포트 | 예: Ref_maya_01 · 02 체크 → File_01 은 둘 다, File_03 은 02 만 |
| 8 | 진행률은 공용 **진행률 팝업**(`JUN_mod_progress_qt_v01`) | |
| 9 | **Remove namespace** 체크박스(기본 ON) — 임포트 뒤 레퍼런스 네임스페이스 제거 | |
| 10 | 두 리스트 모두 **우클릭 `Reveal in File Explorer` · `Copy file path`**, **더블클릭 = Reveal** | A00240 Tree 와 동일 |

---

## 2. 진단 — 지금 있는 것

| 필요한 것 | 어디에 | 상태 |
|-----------|--------|------|
| 폴더 트리 UI (Browse · Depth · Show files · File Types · Filter · Refresh · Adaptive · Omit · Expand · 정션 빨강 · 우클릭 Reveal/Copy · 더블클릭) | `A00240_PathTool/app/ui/tree_tab.py` (1214 줄) + `core/tree_scanner.py` · `core/prefetcher.py` | **있다.** 다만 **A00240 안에 있어 A00480 이 바로 못 쓴다** (§4.2) |
| 탐색기 열기 | `Framework/core/file_opener.open_path` | **공용** — A00240 도 이걸 쓴다 |
| 리스트 체크박스 Shift 다중 체크 | `Framework/qt/MOD_checkList_qt_v01` | **QListWidget 전용.** 트리(QTreeWidget) 판이 없다 (§4.3) |
| 파일 이름 리스트 + Add/Del/Up/Down | `Framework/qt/MOD_tsl_qt_v01` (`attach_uuids=False` 로 씬 노드가 아닌 항목도 됨) | **있다.** 우클릭 메뉴 · 더블클릭은 덧붙여야 |
| 진행률 팝업 | `Framework/qt/MOD_progress_qt_v01` (phases + step) | **있다** |
| 씬의 레퍼런스 관계 수집(중첩 포함) | `A00211_RefLineage/app/core/ref_scanner.collect_scene_references` | **현재 열린 씬만** 본다. 파일 여러 개를 디스크에서 읽는 건 없다. 참고용 |
| 레퍼런스 임포트 · 네임스페이스 제거 · 파일 저장 | 없음 | **새로 만든다** |
| 로그 · 메뉴 · Pin · 탭 스크롤 · fit_to_content | `A00480 main_window.py` | **있다.** 탭 하나 더 끼우면 된다 |

### 릴리즈 제약 (코드 배치를 정하는 사실)

릴리즈본은 **툴 폴더 안에 Framework 사본을 동봉**하고 다른 툴 폴더는 싣지 않는다
(`docs/Release_Layout.md`). 그래서 A00480 이 `tools.A00240_PathTool...` 을 import 하면 **남의 PC 에서
열리지 않는다.** (A00211 이 A00210 을 import 하는 전례가 있지만 같은 이유로 릴리즈가 안 되는 형태다.)
→ A00240 의 Tree 를 쓰려면 **Framework 로 올리거나 복사**해야 한다. §4.2 에서 정한다.

---

## 3. 마야 동작 실측 (mayapy 2024, 2026-10-12)

계획의 알고리즘은 아래 실측 위에 세웠다. 스크립트: 스크래치 `refcheck/verify.py`
(Ref_maya_02.mb ← Ref_maya_01.mb(02 를 중첩) · File_01.mb(01, 02) · File_03.ma(02, Ref_fbx_01.fbx)).

| # | 확인한 것 | 결과 |
|---|-----------|------|
| 1 | `file -o -loadReferenceDepth none` 으로 열면 레퍼런스 노드가 보이나 | **보인다.** 최상위 레퍼런스 노드 + `referenceQuery -filename` 가능, `isLoaded=False`. **중첩 레퍼런스는 안 보인다**(부모가 로드돼야 생김). `-namespace` 질의는 언로드 상태에서 **에러** |
| 2 | `-loadReferenceDepth all` 로 열면 | 중첩까지 전부. 중첩 노드는 `Ref_maya_01:Ref_maya_02RN`, `referenceQuery -parent` 로 부모 노드 |
| 3 | `.ma` 텍스트에 레퍼런스 정보가 있나 | **있다.** 헤더의 `file -rdi <depth> -ns .. -rfn .. "경로";` 가 **중첩까지** 깊이와 함께 적혀 있고, 뒤에 `file -r ...` 가 최상위. 단 **한 문장이 여러 줄**(`-op "..."` 다음 줄에 경로)이라 `;` 까지 이어 붙여 파싱해야 한다 |
| 4 | 언로드 레퍼런스를 바로 `importReference` 하면 | **에러** `cannot be imported because it is unloaded` → **먼저 `loadReference`** |
| 5 | 부모 레퍼런스를 임포트하면 중첩은 | 부모의 중첩 레퍼런스가 **씬 최상위 레퍼런스로 올라온다**(`parent=None`, 언로드 상태). 즉 중첩까지 임포트하려면 **올라온 것을 다시 load → import** 를 반복 |
| 6 | 임포트한 노드 이름 | 네임스페이스가 그대로 붙는다 (`Ref_maya_01:cube01`, 중첩은 `Ref_maya_01:Ref_maya_02:cube02`) |
| 7 | 네임스페이스 제거 | `namespace -removeNamespace <ns> -mergeNamespaceWithRoot` 로 된다. **깊은 것부터.** 남아 있는(임포트 안 한) 레퍼런스의 네임스페이스는 지우면 안 된다(레퍼런스 노드 이름이 바뀌어 `RN1` 처럼 꼬인다) |
| 8 | FBX 레퍼런스 | `file -r -type FBX` 로 레퍼런스가 되고, **importReference 도 된다** |
| 9 | 저장 | `file -q -type` 이 `mayaAscii`/`mayaBinary` 를 준다 → **원래 타입 그대로 저장** |
| 10 | `file -q -r` | 현재 씬의 **최상위** 레퍼런스 파일 경로만 |

---

## 4. 설계 결정

### 4.1 코드 배치 — 나중에 떼어 낼 수 있게

A00480 의 기존 배치는 `app/core/*.py` + `app/ui/*.py` 평면이다. Maya 탭은 **자기 폴더 하나에 core 와 ui 를
함께** 둔다. 폴더째 복사하면 새 툴이 되도록 **폴더 밖을 가리키는 import 는 Framework 뿐**이다.

```
tools/A00480_FileTool/app/
├── core/ · ui/                      # 기존 Export · Import · Path (손대지 않음)
└── maya/                            # ← Maya 탭. 이 폴더가 통째로 분리 단위
    ├── __init__.py
    ├── core/                        # DCC 로직. Qt 없음. 함수 안에서 maya.cmds lazy import
    │   ├── __init__.py
    │   ├── ref_scanner.py           # 디스크의 마야 파일 → 레퍼런스 트리 (§4.6)
    │   ├── ref_importer.py          # 파일마다 open → import → ns 제거 → save (§4.7)
    │   ├── ma_parser.py             # .ma 헤더의 file -r / -rdi 파싱 (§4.6)
    │   └── scene_guard.py           # 현재 씬 저장 여부 확인 · 되돌리기 (§4.8)
    └── ui/
        ├── __init__.py
        ├── maya_tab.py              # QTabWidget 하나 — 하위탭을 담는다 (log 콜백만 받음)
        ├── reference_tab.py         # Reference 하위탭 (Tree + Maya File + Reference + 버튼)
        └── reference_tree.py        # Reference 트리 위젯 (QTreeWidget 서브클래스)
```

- `main_window.py` 는 `from tools.A00480_FileTool.app.maya.ui.maya_tab import MayaTab` 한 줄과
  `self.tabs.addTab(self.maya_tab, "Maya")` 로 끼운다. **탭은 `log` 콜백만 받는다**(기존 탭과 같다).
- `maya/` 안에서는 **상대 import** (`from ..core import ref_scanner`) 만 쓴다. 분리할 때 바꿀 줄이 없다.
- 분리 시나리오: `app/maya/` → `A005XX_MayaFileTool/app/` 로 복사 + `launch.py` · `main_window.py`(메뉴 ·
  로그 · Pin) 만 새로 쓴다. 그때 `maya_tab.py` 가 그 툴의 본체가 된다.

### 4.2 폴더 트리 — A00240 Tree 를 Framework 로 승격 (권장)

| 안 | 내용 | 장점 | 단점 |
|----|------|------|------|
| **A. Framework 승격** (권장) | `tree_tab.py` → `Framework/qt/MOD_fileTree_qt_v01.py`(`JUN_mod_fileTree_qt_v01`), `tree_scanner.py` · `prefetcher.py` → `Framework/core/`. A00240 은 `path_opener.py` 처럼 **re-export 한 줄**로 남긴다 | 한 벌만 고친다(이미 `file_opener` · 토큰 위젯 · 로그창이 같은 길을 갔다). 릴리즈 OK. 앞으로 다른 툴(A00210 · A00220)도 쓸 수 있다 | A00240 을 건드린다(동작 변화 없음, 버전 올림). 작업량이 복사보다 조금 많다 |
| B. A00480 안으로 복사 | 1214 + 300 줄을 `app/maya/ui/` 에 복사 | A00240 무수정 | 같은 코드 두 벌 — A00240 Tree 가 고쳐질 때마다 갈라진다 |
| C. `tools.A00240...` 직접 import | 한 줄 | 가장 쉽다 | **릴리즈본에서 안 열린다**(§2). 기각 |

**A 로 간다.** 승격하면서 덧붙이는 것 (A00240 의 기본 동작은 그대로):

- 생성 옵션 `checkable_files=False` — True 면 **파일 행에 체크박스**(폴더 행은 없음 — 폴더는 고를 대상이 아니다).
- 옵션 `default_types=None` — 처음 Build 때 File Types 에서 **체크해 둘 확장자**(Maya 탭은 `("ma", "mb")`,
  나머지 확장자는 보이되 체크 해제). None 이면 지금처럼 전부 체크.
- `checked_paths()` — 체크된 파일 절대경로 목록. `checksChanged` 시그널.
- Build · Refresh · 필터로 행이 다시 그려져도 **체크 상태는 경로로 기억**해 복원한다(펼침 · 선택을 복원하는
  `_capture_view_state` 와 같은 자리).
- Expand 창(큰 트리)에도 같은 체크 동작이 붙는다(메인 트리와 체크 상태 공유 — 지금 펼침 상태를 공유하듯).

### 4.3 트리 체크 다중 전파 — 공용 `MOD_checkTree_qt_v01`

`JUN_mod_checkList_qt_v01` 은 QListWidget 의 viewport 이벤트를 직접 먹어 **"고른 행 전부에 체크 전파"** 를
한다. 트리에도 같은 함정(체크박스 누르기가 선택을 한 행으로 푼다)이 있다. → **같은 규칙의 QTreeWidget 판**을
새 공용 모듈로 만든다. 규칙은 checkList 와 동일:

- Shift / Ctrl 로 여러 행 선택, 그중 하나의 체크박스를 누르면 **보이는 선택 행 전부**가 같은 상태.
- 안 고른 행의 체크박스는 그 행 하나만. Space 는 선택 행 전부 뒤집기.
- 체크박스 없는 행(폴더 · `...` · 정보 행)은 건너뛴다.
- `checksChanged(list)` 한 번 + `itemChanged` 한 번.

폴더 트리(§4.2)와 Reference 트리(§4.5) **둘 다** 이걸 붙인다.

### 4.4 Maya File 리스트 — 공용 TSL

`JUN_mod_tsl_qt_v01(title="Maya File", attach_uuids=False, show_select=False, show_sort=True, show_order=False)`.

- 행 텍스트는 **파일 이름**, `Qt.UserRole` 에 절대경로, 툴팁에 절대경로. 같은 이름이 다른 폴더에 있으면
  둘 다 들어가되 이름 뒤에 ` (폴더명)` 을 붙여 구분한다.
- 추가 경로 두 가지: **`Add Checked`**(Tree 에서 체크한 파일, 중복은 건너뛰고 로그) · **`Browse...`**(파일
  다이얼로그, `*.ma *.mb` 다중 선택 — Tree 를 안 써도 되게. 작다).
- 제거: TSL 의 `Del`(선택 행) + `Clear`(전부). 둘 다 확인 없이(되돌릴 데이터가 아니다).
- 우클릭 메뉴 `Reveal in File Explorer` · `Copy file path`, 더블클릭 = Reveal — A00240 Tree 의 두 메서드를
  **공용 `Framework/qt/path_context.py`**(작은 헬퍼: 메뉴 띄우기 · 복사 · reveal + 실패 안내) 로 빼서 폴더
  트리 · Maya File · Reference 트리 셋이 같은 함수를 쓴다.
- 파일이 디스크에 없으면 행을 **빨강**(TSL 의 `null_item_color`) 으로, Get Reference 때 건너뛰고 로그.

### 4.5 Reference 트리 — QTreeWidget

TSL 은 평면 리스트라 중첩을 못 담는다. **QTreeWidget** (`reference_tree.py`) 로 간다.

```
Reference                                   Used by
├ [ ] Ref_maya_01.mb                         File_01.mb
│   └   Ref_maya_02.mb        (nested)       -
├ [ ] Ref_maya_02.mb                         File_01.mb, File_03.ma
└ [ ] Ref_fbx_01.fbx                         File_03.ma
```

- **최상위 행 = 스캔한 마야 파일들이 직접 부르는 레퍼런스 파일, 경로로 중복 제거**(같은 파일을 두 마야 파일이
  부르면 한 행). 열 2 `Used by` 에 그 레퍼런스를 부르는 마야 파일 이름들. 툴팁에 절대경로.
- **자식 행 = 그 레퍼런스 파일이 또 부르는 레퍼런스**(중첩, 재귀). **기본 전부 접힘.**
- 자식 행에는 **체크박스를 두지 않는다**(제안, §11-④) — 부모를 임포트하면 중첩은 **자동으로 함께** 임포트되는
  규칙이므로 체크가 뜻이 없다. 자식 행은 회색 글씨 + `(nested)`.
- 파일이 디스크에 없는 레퍼런스(끊긴 경로)는 **빨강** + 체크 불가 + 툴팁 `File not found` — 임포트하면 마야가
  에러를 내므로 미리 건너뛴다. 로드는 되는데 경로만 다른 경우(마야의 경로 치환)는 v1 범위 밖.
- 우클릭 · 더블클릭은 §4.4 와 같은 헬퍼.
- Shift 다중 체크는 §4.3.
- Maya File 리스트가 바뀌어도 Reference 트리는 **다음 Get Reference 까지 그대로**(위 `Used by` 가 기준).
  대신 트리 위에 `Scanned: File_01.mb, File_03.ma (2)` 라벨로 **무엇을 스캔한 결과인지** 보여 준다.

### 4.6 스캔 알고리즘 (Get Reference) — `core/ref_scanner.py`

입력: 마야 파일 경로 목록. 출력: 파일마다 레퍼런스 트리(dict) + 전체 노드 테이블.

```
scan(files, progress) -> {
  "roots": {abs_file: [ref_norm...]},      # 마야 파일별 최상위 레퍼런스
  "nodes": {norm_path: {"path", "exists", "children": [norm...], "used_by": [...]}},
}
```

파일 하나의 **직접 레퍼런스**를 읽는 방법은 확장자로 갈린다.

| 확장자 | 방법 | 근거 |
|--------|------|------|
| `.ma` | **텍스트 파싱**(`ma_parser.py`). 헤더의 `file -r ...` 문장(여러 줄이면 `;` 까지 이어 붙임)에서 경로 · `-ns` · `-rfn` · `-typ` 을 뽑는다. 씬을 **열지 않는다** | §3-3 |
| `.mb` | `file -o -force -loadReferenceDepth none -prompt false` 로 **연 뒤** `ls -references` + `referenceQuery -filename -withoutCopyNumber` | §3-1. 바이너리라 파싱 불가 |
| `.fbx` 등 | 레퍼런스를 가질 수 없다 → **잎** | |

중첩은 **재귀**: 직접 레퍼런스 파일마다 같은 함수를 다시 부른다. `norm_path` 로 **한 파일은 한 번만** 읽고
(`nodes` 캐시), 조상에 있는 파일이 또 나오면 **순환**으로 보고 내려가지 않는다(로그 `[WARN]`).
(`.ma` 의 `-rdi` 줄만으로 중첩을 다 알 수 있지만, 중첩 파일이 `.mb` 면 어차피 열어야 하므로 v1 은
**직접 레퍼런스만 파싱하고 중첩은 재귀**로 통일한다 — 방식이 하나라 검증이 쉽다.)

`.mb` 가 하나라도 있으면 **현재 씬이 바뀐다** → §4.8 의 씬 보호를 Get Reference 에도 건다.
`.ma` 만 있으면 씬을 건드리지 않는다(로그에 `scanned without opening`).

### 4.7 임포트 알고리즘 (Import Reference) — `core/ref_importer.py`

입력: 스캔 결과 + 체크된 레퍼런스 `norm_path` 집합 + 옵션(remove_namespace, backup). **마야 파일마다**:

```
for maya_file in scanned_files:                               # 진행률: 파일 단위
    targets = {체크된 norm} ∩ {그 파일의 직접 레퍼런스}
    if not targets: 건너뜀 (로그)                               # File_03 에 Ref_maya_01 은 없다
    backup(maya_file)                                          # §11-③
    file -o -force -loadReferenceDepth none -prompt false
    imported_ns = []
    queue = [targets 에 해당하는 레퍼런스 노드들]
    while queue:
        rn = queue.pop()
        if not isLoaded(rn): file -loadReference rn            # §3-4
        imported_ns.append(referenceQuery -namespace rn)
        top_before = {씬 최상위 ref 노드}
        file -importReference -referenceNode rn                # §3-5
        new_top = {씬 최상위 ref 노드} - top_before              # 올라온 중첩 레퍼런스
        queue.extend(new_top)                                  # 중첩도 임포트 (요청 7)
    if remove_namespace:
        for ns in sorted(imported_ns, key=depth, reverse=True): # 깊은 것부터, §3-7
            namespace -removeNamespace ns -mergeNamespaceWithRoot
    file -save -type <원래 타입>                                # §3-9
```

- **임포트하지 않는 레퍼런스**(체크 안 함)는 손대지 않는다 — 로드도 안 하므로 큰 파일을 공짜로 건너뛴다.
- 네임스페이스는 **임포트한 것만** 지운다(남은 레퍼런스의 ns 를 건드리면 §3-7 처럼 노드가 꼬인다).
  이름이 루트의 노드와 겹치면 마야가 `cube1` 처럼 숫자를 붙인다 — 그 행마다 로그 `[WARN] renamed`.
- 실패(파일 못 열음 · 임포트 에러)는 **그 파일만 건너뛰고** 다음 파일로. 요약 로그 `3 files, 2 saved, 1 failed`.
- 중첩 레퍼런스가 **끊긴 경로**면 load 가 실패 → 그 파일은 저장하지 않고 건너뛴다(반쯤 임포트된 채 저장 금지).
- 스크립트 노드 실행 끄기: `file -o -executeScriptNodes false`(2024 지원) — 남의 파일을 열며 스크립트가 도는
  일을 막는다.

### 4.8 현재 씬 보호 — `core/scene_guard.py`

Get Reference(.mb 포함) · Import Reference 는 **씬을 바꾼다.** 두 버튼 앞에:

1. 현재 씬이 **수정됨**(`file -q -modified`) 이면 `Save / Don't Save / Cancel` 다이얼로그.
2. 현재 씬 경로를 기억해 두고, 작업이 끝나면 **다시 연다**(옵션 `Reopen current scene when done`, 기본 ON.
   untitled 였으면 `file -new`).
3. 작업 중 열리는 파일은 전부 `-prompt false` 라 마야 다이얼로그가 끼어들지 않는다.

> 대안 — **mayapy 하위 프로세스**(§11-②). 현재 씬을 안 건드리고 백그라운드에서 돈다. 대신 mayapy 기동
> 15~30초, 플러그인 · 환경 차이, 진행률은 stdout 을 읽어야 한다. v1 은 세션 안에서 하고, 필요해지면 코어가
> Qt 비의존이므로 그대로 mayapy 에 태울 수 있다.

### 4.9 진행률 팝업

`JUN_mod_progress_qt_v01`, 단계는 **마야 파일 단위**로 `set_phases([(파일명, 1)...])`, 파일 안에서는
`step(k, n, "Importing Ref_maya_01.mb")`. Cancel 은 **파일 경계에서만** 반영(저장 중간에 끊지 않는다).
Get Reference 도 같은 팝업(`.mb` 를 열 때만 체감이 되지만 통일).

### 4.10 로그

창 공용 로그에 영어로. 파일마다 한 줄 요약 + 레퍼런스마다 한 줄 (`  imported Ref_maya_02.mb (ns removed)`),
건너뛴 이유, 마지막에 집계.

---

## 5. UI 배치 (Maya > Reference)

```
┌ Maya ───────────────────────────────────────────────────────────┐
│ [Reference]  (다음 하위탭은 여기에 추가)                          │
│ ┌ Tree (A00240 Tree 그대로 + 파일 체크박스, File Types 기본 ma/mb) ┐│
│ │ Path [________________________] [Browse] [Build] [Refresh] …  ││
│ │ ▸ [ ] 📁 Characters                                           ││
│ │   [v] File_01.mb   [v] File_03.ma   [ ] File_02.mb            ││
│ └──────────────────────────────────────────────────────────────┘│
│                       [Add Checked]   [Browse...]                │
│ ┌ Maya File ───────────────┐  ┌ Reference ─────────── Used by ──┐│
│ │ File_01.mb               │  │ [v] Ref_maya_01.mb   File_01    ││
│ │ File_02.mb               │  │   ▸  Ref_maya_02.mb  (nested)   ││
│ │ File_03.ma               │  │ [v] Ref_maya_02.mb   File_01,03 ││
│ │ Del  Clear  Up  Down Sort│  │ [ ] Ref_fbx_01.fbx   File_03    ││
│ └──────────────────────────┘  │ Check All  Uncheck All          ││
│ Scanned: File_01.mb, File_03.ma (2)                             ││
│ [Get Reference]   [x] Remove namespace  [x] Backup  [x] Reopen current scene  [Import Reference] │
└─────────────────────────────────────────────────────────────────┘
```

- 창 높이는 이미 `fit_to_content` 가 화면에 맞추고 탭이 스크롤 칸에 있으므로, Tree 와 두 리스트는 **세로
  스플리터**로 나눠 사용자가 비율을 정하게 한다(Tree 가 1214 줄짜리 컨트롤을 갖고 있어 공간을 많이 먹는다).
- 좌우는 Maya File(좌) · Reference(우) — 요청 그림은 위아래지만, 창 폭(960)에 두 리스트를 나란히 두면 Tree
  높이를 더 줄 수 있다. **§11-⑦** 에서 고른다.

---

## 6. 바뀌는 파일

### 신규

| 파일 | 역할 |
|------|------|
| `Framework/qt/MOD_fileTree_qt_v01.py` | A00240 Tree 승격 + `checkable_files` · `default_types` · `checked_paths()` |
| `Framework/core/tree_scanner.py` · `Framework/core/prefetcher.py` | A00240 core 승격 (내용 그대로) |
| `Framework/qt/MOD_checkTree_qt_v01.py` | QTreeWidget 다중 체크 동작 |
| `Framework/qt/path_context.py` | Reveal / Copy file path 메뉴 · 더블클릭 공용 헬퍼 |
| `tools/A00480_FileTool/app/maya/**` | §4.1 의 8개 파일 |
| `docs/Framework_MOD_fileTree_qt.md` · `docs/Framework_MOD_checkTree_qt.md` | 공용 위젯 안내 |

### 수정

| 파일 | 내용 |
|------|------|
| `A00240_PathTool/app/ui/tree_tab.py` · `core/tree_scanner.py` · `core/prefetcher.py` | re-export 한 줄씩 (`path_opener.py` 와 같은 꼴). A00240 **v01.19 → 01.20**, CHANGELOG · `docs/A00240_PathTool.md` 한 줄 |
| `A00480_FileTool/app/ui/main_window.py` | Maya 탭 추가 · About 문구 |
| `A00480_FileTool/app/config/version.py` · `CHANGELOG.md` · `docs/A00480_FileTool.md` | **v01.09 → 01.10**, Maya 탭 절 |
| `Framework/qt/__init__.py` | 새 위젯 별칭 노출(기존 위젯들과 같은 방식) |
| `docs/WORKLOG.md` · `docs/portfolio/*`(EN/KR) | 작업 기록 · 포트폴리오 기능 줄 |
| `.claude/memory/` | Maya 탭 메모 + 실측 함정(언로드 임포트 불가 · 중첩은 올라온다 · ma 여러 줄) |

---

## 7. 작업 순서

| 단계 | 일 | 검증 |
|------|----|------|
| 0 | §11 결정 받기 | — |
| 1 | **Tree 승격** — 세 파일을 Framework 로 옮기고 A00240 을 re-export 로. 동작 변화 0 | A00240 기존 오프스크린 테스트 재통과 · A00240 창 생성 OK |
| 2 | `MOD_checkTree_qt_v01` + Tree 의 `checkable_files` · `default_types` · `checked_paths` | PySide offscreen QTest — Shift 범위 체크 전파, 폴더 행 제외, Build/Refresh 뒤 체크 유지, Expand 창 공유 |
| 3 | `path_context.py` 공용화 — Tree 가 먼저 쓰도록 바꿈 | 1 과 함께 |
| 4 | `core/ma_parser.py` · `core/ref_scanner.py` | **mayapy 2024** — §3 의 샘플 파일 5개로 트리 = 기대값, 순환 · 끊긴 경로 · 같은 파일 두 번 |
| 5 | `core/ref_importer.py` · `core/scene_guard.py` | mayapy — File_01 (01+02 체크) 저장 뒤 다시 열어 레퍼런스 0 · 노드 이름 ns 없음, File_03 은 02 만 임포트 · fbx 는 레퍼런스로 남음, `.ma` 타입 유지, 백업 파일 존재, 중첩이 끊긴 경우 저장 안 함 |
| 6 | UI — `maya_tab.py` · `reference_tab.py` · `reference_tree.py` + main_window 연결 | offscreen — 창 생성, 탭 4개, 체크 → Add Checked → Get Reference(목 스캐너) → 트리 접힘 · Used by · 더블클릭/우클릭 |
| 7 | 문서 · 버전 · CHANGELOG · WORKLOG · 포트폴리오 · 메모 | — |
| 8 | **마야 GUI 확인은 사용자**(창 크기 · 스플리터 비율 · 진행률 팝업 · 실제 파일) | 보고에 "GUI 확인 아직" 명시 |

예상 분량: Framework 승격 + 체크 동작이 절반, 코어 두 파일이 1/4, UI 가 1/4. 커밋은 단계 1 · 2-3 · 4-5 · 6 ·
7 로 나눈다(1 은 A00240 만 건드리는 독립 커밋이라 먼저 올릴 수 있다).

---

## 8. 검증 계획 (자세히)

- **mayapy headless** — §3 스크립트를 테스트로 승격. 코어는 Qt 없이 돌므로 그대로 호출.
  - 스캔: `.ma` 만 → 현재 씬 그대로(`file -q -sceneName` 불변). `.mb` 포함 → 열렸다가 Reopen 으로 복귀.
  - 임포트: 저장 뒤 **다시 열어** `ls -references` 와 노드 이름으로 판정(저장 전 상태를 믿지 않는다).
  - Remove namespace OFF 면 `Ref_maya_01:cube01` 이 남는지.
  - 이름 충돌: 루트에 `cube01` 이 있는 파일 → 번호가 붙고 `[WARN]` 로그.
- **Qt offscreen** — 트리 체크 전파는 QTest 로 실측(checkList 가 그랬듯 "되겠지" 가 틀렸던 자리다).
- **창 크기** — 테마를 입힌 뒤 잰다. 잰 값을 창 크기로 박지 않는다.

---

## 9. 위험 · 한계

| 위험 | 대응 |
|------|------|
| **원본 마야 파일을 덮어쓴다** | 기본 Backup ON(§11-③). 실패한 파일은 저장하지 않는다. 로그에 저장한 파일 전부 기록 |
| 작업 중 현재 씬이 닫힌다 | §4.8 다이얼로그 + Reopen. 사용자에게 **실행 전 한 번 더 확인** 팝업(`N files will be opened and saved`) |
| 큰 레퍼런스 로드 시간 | 체크한 것만 로드. 진행률 팝업 · 파일 경계 Cancel |
| 마야 버전 | 2023 · 2024 둘 다 쓰는 플래그만(`loadReferenceDepth` · `importReference` · `mergeNamespaceWithRoot`). `executeScriptNodes` 는 없으면 뺀다 |
| 레퍼런스 경로가 환경변수 · 상대경로 | `referenceQuery -filename` 은 **해석된** 절대경로를 준다. `.ma` 파싱은 적힌 그대로라 `$PROJECT` 같은 변수는 `os.path.expandvars` 뒤 존재 확인, 못 찾으면 빨강 |
| 같은 파일을 두 번 레퍼런스(복사본 `{1}`) | `withoutCopyNumber` 로 한 행. 임포트는 노드마다 |
| 레퍼런스 편집(reference edits) · 언로드 상태로 저장된 레퍼런스 | 임포트하면 편집은 적용된 채 굳는다(마야 기본). 저장 시 언로드였던 레퍼런스는 로드 후 임포트 |
| `.ma` 헤더 파싱이 깨지는 파일(수동 편집) | 파싱 실패 시 **열어서 읽는 경로로 폴백** + 로그 |

---

## 10. 범위 밖 (v1 에서 하지 않는 것)

- 레퍼런스 경로 바꾸기 · 끊긴 레퍼런스 다시 잇기(별도 하위탭 후보 `Repath`).
- 레퍼런스 **추가**(마야 파일에 새 레퍼런스 걸기) · 언로드/삭제.
- mayapy 백그라운드 실행(§4.8 대안).
- Reference 트리에서 중첩 행만 골라 임포트.

---

## 11. 결정이 필요한 것

| # | 질문 | 제안(기본값) |
|---|------|--------------|
| ① | A00240 Tree 를 **Framework 로 승격**해도 되나(A00240 v01.20, 동작 변화 없음)? 아니면 A00480 안에 복사? | **승격** (§4.2 A) |
| ② | 스캔 · 임포트를 **현재 마야 세션에서**(씬이 바뀜, 저장 확인 + 끝나면 원래 씬 다시 열기) 할지, **mayapy 백그라운드**로 할지 | **세션 안** (§4.8). 코어가 Qt 비의존이라 나중에 바꿀 수 있다 |
| ③ | 저장 전 **백업** — 켤지, 어디에(같은 폴더 `File_01.mb.bak` / 같은 폴더 `_backup/` / 안 함)? | **켬, 같은 폴더 `_backup/File_01.mb`**(덮어쓰지 않고 `_01`, `_02` 번호) |
| ④ | Reference 트리의 **중첩(자식) 행에 체크박스**를 둘지 — 부모 임포트 시 중첩은 자동으로 함께 임포트되므로 체크의 뜻이 없다 | **두지 않음**, 회색 `(nested)` |
| ⑤ | Import Reference 의 **대상 마야 파일** — 마지막 Get Reference 로 스캔한 파일들(라벨 `Scanned:` 에 표시) 인지, 그 순간 Maya File 에서 **선택된** 파일인지 | **스캔한 파일들** — Reference 트리가 그 파일들 기준이므로 |
| ⑥ | Remove namespace 가 **임포트한 레퍼런스의 네임스페이스만** 지운다(남은 레퍼런스 · 파일에 원래 있던 네임스페이스는 그대로). 이대로 OK? | OK |
| ⑦ | 두 리스트 배치 — 요청 그림대로 **위아래** / 창 폭을 쓰는 **좌우** | **좌우** (Tree 높이 확보) |
| ⑧ | Tree 의 File Types 기본 체크를 **`.ma` · `.mb` 만**으로(다른 확장자는 보이되 꺼짐) | 그렇게 |
| ⑨ | Maya File 에 **Browse... (파일 다이얼로그)** 추가 경로도 둘지 | 둠 (작고, Tree 없이도 쓸 수 있다) |
| ⑩ | 임포트 뒤 **원래 열려 있던 씬을 다시 여는** 옵션 기본 ON? | ON |
| ⑪ | 테스트용 **실제 마야 파일 묶음**(레퍼런스 · 중첩 · fbx 가 섞인 것)이 있으면 경로를 알려 달라. 없으면 §3 의 생성 스크립트로 만든 샘플로 검증한다 | 샘플 |

결정이 오면 §7 순서로 시작한다.
