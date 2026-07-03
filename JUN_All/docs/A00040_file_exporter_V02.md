# A00040_file_exporter_V02 사용법

## 1. 개요

Maya 의 **selection set(objectSet)** 단위로 오브젝트를 묶어, 세트마다 하나의 **FBX 파일**로
일괄 내보내는 툴이다. 레거시 maya.cmds 툴 [A00040_file_exporter](A00040_file_exporter.md) 를
**PySide(Qt)** 로 재작업(V02)하고, **타입 필터**(어떤 노드 타입을 포함/제외할지) 기능을 추가했다.

- DCC: Autodesk Maya (in-Maya PySide UI). 아키텍처 (B) 타입.
- 로직(`app/core/export_ops.py`)과 화면(`app/ui/main_window.py`)을 분리한다.
- 설치: `__dragDrop_A00040_V02.py` 를 뷰포트에 드래그&드롭 → 셸프 버튼("FileExporterV2") 생성.
  이후 셸프 버튼 또는 `tools.A00040_file_exporter_V02.run(True)` 로 실행.
- 아이콘은 레거시 A00040 아이콘을 그대로 재사용한다. 테마는 `blue_dark`.

---

## 2. 폴더 구조

```
A00040_file_exporter_V02/
├── __init__.py                    # from .launch import run
├── launch.py                      # run(): MainWindow 생성 → 테마(blue_dark) → show()
├── __dragDrop_A00040_V02.py       # 셸프 버튼 설치 + 드래그&드롭 진입점 (고유 드롭 이름)
├── icon/                          # 레거시 A00040 아이콘 재사용 (svg + png)
├── CHANGELOG.md
└── app/
    ├── config/version.py          # VERSION / LAST_UPDATE
    ├── core/
    │   └── export_ops.py          # 타입 필터 · 파일명 조립 · FBX 내보내기 (maya.cmds)
    └── ui/
        ├── main_window.py         # 전체 UI (Path / Set Up / Naming / Export + 로그)
        └── type_filter_button.py  # 타입 필터 드롭다운 위젯
```

---

## 3. 설치 · 실행

- **설치**: `A00040_file_exporter_V02/__dragDrop_A00040_V02.py` 를 Maya 뷰포트로 **드래그&드롭**
  → 현재 셸프에 "FileExporterV2" 버튼 설치(중복 버튼은 자동 제거).
- **실행**: 셸프 버튼 클릭, 또는:
  ```python
  import tools.A00040_file_exporter_V02 as A00040_file_exporter_V02
  A00040_file_exporter_V02.run(True)   # True 면 DEV_MODE 에서 Framework + 자기 자신 reload
  ```
- 창은 `objectName`(`JUN_A00040_file_exporter_V02_window`)으로 관리되어 재실행 시 중복 없이 교체된다.
- PySide2(Maya ~2024) / PySide6(2025+) 양쪽 지원(`Framework.qt.qt` 자동 분기).

---

## 4. 화면 구성

| 섹션 | 내용 |
|------|------|
| **Export Path** | `Browse` 로 FBX 를 저장할 폴더 선택(읽기 전용 필드에 표시) |
| **Set Up** | 두 개의 TSL — `Set's Name`(내보낼 objectSet 목록, 씬 선택에서 Select/Add) / `File name`(각 세트의 결과 파일명) |
| **Naming** | 토큰 6개(SK / MANU / CH / Name / Type / Version)로 파일명을 조립. 각 토큰은 `Custom`(직접 입력) 또는 `Set's Name`(세트 이름 사용) 모드. **Set Name** 버튼으로 File name 리스트 자동 생성 |
| **Export** | **Move to scene root** 체크박스 + **Type Filter** 드롭다운(포함/제외 타입 선택) + **Export** 버튼 |
| **Log** | 모든 결과·경고(`[OK]`/`[SKIP]`/`[FAIL]`/`[WARN]`)가 누적 |

---

## 5. 사용 흐름

1. **Browse** 로 내보낼 폴더를 지정한다.
2. 씬에서 내보낼 objectSet 들을 선택하고 `Set's Name` 의 **Select Sets**(교체) 또는 **Add**(추가)로 채운다.
3. (선택) **Naming** 토큰을 설정하고 **Set Name** 으로 `File name` 을 자동 생성한다.
   - 토큰 모드가 `Custom` 이면 입력한 텍스트를, `Set's Name` 이면 그 세트의 이름(leaf)을 토큰으로 쓴다.
   - 빈 토큰은 건너뛰어 `__` 가 생기지 않는다.
4. (선택) **Type Filter** 에서 내보낼 타입을 조정한다(§6).
5. **Export** — 각 세트의 멤버를 모아 `{Export Path}/{File name}.fbx` 로 내보낸다.
   - 파일명이 겹치면 `_000`, `_001` … 로 **고유 경로**를 붙인다. 파일명의 `:` 는 `_` 로 치환.

---

## 6. Type Filter (NEW)

내보낼 때 **특정 노드 타입을 포함/제외**할 수 있다. `Export` 섹션의 **"Include Types ▾"** 드롭다운에
등록된 타입이 **체크박스**로 나온다(기본: 모두 체크 = 모두 포함).

- **체크 = 포함, 체크 해제 = 제외.**
- 드롭다운에 **없는 타입(curve, nurbsSurface 등)은 항상 포함**된다. 필터는 오직 "제외"만 한다.
- 현재 등록 타입: **Mesh / Joint**.

예) **Mesh 체크 해제 + Joint 체크** → 각 세트 멤버 중 **메시만 제외**되고 조인트·커브 등 나머지는 모두 FBX 로 내보내진다.

### 6.1 타입 판별 규칙

- 노드 자체가 해당 타입이거나(예: `joint`), 그 트랜스폼 아래 **shape** 이 해당 타입이면(예: `mesh`) 그 타입으로 간주한다.
- **그룹 하위도 필터를 받는다**: 세트 멤버가 그룹이면 그 **계층 전체**를 훑어, 하위에 있는 제외 타입 노드(그룹 안 mesh 등)를
  내보내기 직전에 잠깐 계층 밖으로 빼냈다가(export 후 원위치 복원) 처리한다. 즉 그룹은 유지되고 그 안의 제외 타입만 FBX 에서 빠진다.
- 제외 대상 타입 중 **하나라도** 걸리면: 세트에 **직접 든 멤버**면 그 멤버가 통째로 빠지고, **그룹 하위 노드**면 그 노드(및 그 자손)만 빠진다.
- **레퍼런스 제외 대상 처리**: 계층에서 빼낼 수 없는(레퍼런스) 제외 노드는, 그 타입 **shape 를 `intermediateObject` 로
  잠깐 숨겨** FBX 에서 제외한다(export 후 원복). FBX 는 intermediate shape 를 내보내지 않는다. 따라서 레퍼런스 메시도
  정상 제외된다(단, transform 은 빈 노드로 남을 수 있다). shape 가 없는 타입(예: 레퍼런스 joint)만 제외 불가로 남아
  `[WARN] could not exclude ...` 로 안내된다.

### 6.2 타입 추가하기 (확장)

`app/core/export_ops.py` 의 두 곳만 수정하면 UI·로직에 자동 반영된다.

```python
# ① 드롭다운에 노출할 타입
FILTER_TYPES = [
    {"key": "mesh",  "label": "Mesh"},
    {"key": "joint", "label": "Joint"},
    {"key": "nurbsSurface", "label": "NURBS"},   # 예: 추가
]

# ② 같은 key 로 멤버 판별 함수
_TYPE_MATCHERS = {
    "mesh":  lambda node: _is_type(node, "mesh"),
    "joint": lambda node: _is_type(node, "joint"),
    "nurbsSurface": lambda node: _is_type(node, "nurbsSurface"),   # 예: 추가
}
```

---

## 7. 내보내기 동작 (Move to scene root / Keep hierarchy)

**Move to scene root** 체크박스로 계층 처리 방식을 고른다(기본: **체크 = 씬 최상위로 빼기**).

| 모드 | 동작 | `grp > joint_01`(joint_01 이 세트) 결과 |
|------|------|------|
| **체크 (기본)** | 멤버를 **월드(최상위)로 빼냈다가**(`cmds.parent(world=True)`) 내보낸 뒤 **원부모로 복원** | `joint_01` (부모 제거, 월드 위치 유지) |
| **해제** | 멤버를 옮기지 않고 **제자리에서** 내보냄 | `grp > joint_01` (부모 유지) |

- **해제(계층 유지)** 모드가 되는 이유: FBX *export selected* 는 선택 노드의 **조상(부모) 체인은 포함하되
  형제 가지는 제외**한다. 그래서 빼내지 않고 그대로 내보내면 부모 경로만 보존된다.
- 원래 부모/멤버를 **UUID** 로 기록해 두고 복원한다. 씬에 **같은 이름의 오브젝트**가 있어도, 또
  부모를 옮겨 경로가 바뀌어도 안전하다(참고: [노드 신원 - 이름/경로 vs UUID](study/maya_node_identity_name_vs_uuid.md)).
- 이미 월드 최상위인(부모가 없는) 멤버는 옮기지 않고 그대로 내보낸 뒤 그대로 둔다.
- **타입 필터로 제외된 그룹 하위 노드**도 같은 방식으로 export 직전에 월드로 빼냈다가 원부모로 복원한다(§6).
- **레퍼런스 오브젝트**(레퍼런스 부모 밑의 레퍼런스 노드)는 Maya 가 월드로 빼내는 것을 금지한다. 이 경우
  에러 없이 **제자리에서 내보내고**(복원 생략) 넘어간다. 덕분에 레퍼런스 네임스페이스로 같은 이름이 생긴 씬
  (`Test` + `namespace:Test`)에서도 정상 동작한다. 타입 제외 대상이 레퍼런스라 뺄 수 없으면 로그에
  `[WARN] could not exclude ... still in FBX` 로 알린다.
- 전체 동작은 단일 Undo(`core.undo_chunk`)로 묶인다.

---

## 8. 로그 · 문제 해결

- 정상: `[OK] <set>  ->  <path>` 뒤에 `exported n object(s): ...` / (있으면) `excluded n object(s): ...`.
- 경고/건너뜀:
  - `[WARN] Set's Name list is empty.` — 내보낼 세트를 먼저 추가.
  - `[WARN] Select an export path first.` — Export Path 미지정.
  - `[SKIP] <name> is not an objectSet.` — objectSet 이 아닌 항목.
  - `[FAIL] <set>: nothing left to export after type filter.` — 필터로 전부 제외됨(체크 상태 확인).
- **FBX 미출력**: `fbxmaya` 플러그인이 로드되어 있어야 한다(Maya 기본 제공).

---

## 9. V01 과의 차이

| | V01 (A00040_file_exporter) | V02 (본 툴) |
|---|---|---|
| UI | maya.cmds | **PySide(Qt)** |
| 구조 | 단일 파일 + utility | **app/core · app/ui 분리** |
| 타입 필터 | 없음(세트 멤버 전부) | **드롭다운 체크로 포함/제외** |
| reparent 안전성 | 이름 기반 | **UUID 기반**(동일 이름 안전) |
| 아이콘 | A00040 | **동일 아이콘 재사용** |
