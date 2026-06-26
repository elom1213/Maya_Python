# A00310_SearchTool 사용법

## 1. 개요

씬에서 **오브젝트를 타입/이름으로 골라 선택**하는 PySide(Qt) 툴이다. 레거시 maya.cmds 단일 파일
툴 두 개(`JUN_PY_SelectionTool_V02_01`, `JUN_PY_SearchTool_V01_02`)를 `A00170_driverTool` 과 같은
**하나의 창 + 탭** 구조로 통합했다. **두 개의 탭**과 **공유 로그창**으로 구성된다.

1. **Selection** — 선택(또는 그 계층)에서 오브젝트/노드 타입을 리스트업하고, **타입별로** 선택한다.
   (구 `JUN_PY_SelectionTool`)
2. **Search** — 오브젝트 이름에 **토큰(부분 문자열)** 이 들어간 것을 선택한다. (구 `JUN_PY_SearchTool`)

- 모든 UI 문자열/로그는 영어. 두 탭의 리스트는 공용 위젯 `JUN_mod_tsl_qt_v01` 을 쓰며
  **Select 계열 + Add / Del / Up / Down / Sort** 버튼을 갖는다.
- 로직(선택/검색)은 `app/core`(maya.cmds), 화면은 `app/ui`(PySide)로 분리한다.

---

## 2. 폴더 구조

```
A00310_SearchTool/
├── __init__.py            # from .launch import run
├── launch.py              # run(): MainWindow 생성 → 테마(coral_dark) → show()
├── __dragDrop_A00310.py   # 셸프 버튼 설치 + 드래그&드롭 진입점 (TOOL_LABEL = "SearchTool")
├── icon/                  # 셸프 아이콘 (svg + png)
└── app/
    ├── config/version.py  # VERSION / LAST_UPDATE
    ├── core/              # 로직 (UI 비의존, maya.cmds)
    │   ├── maya_scene.py      # 선택/계층 펼치기/노드 타입/존재 (cmds 어댑터)
    │   ├── search_select.py   # collect_from_selection / collect_types /
    │   │                      #   select_by_types / select_by_token (+ CONSTRAINT_TYPES)
    │   └── __init__.py        # core 재노출
    └── ui/main_window.py  # 전체 UI (2개 탭 + 공유 로그창 + 메뉴 바)
```

- `main_window.py` 의 위젯/핸들러는 탭별 접두사로 분리한다: **Selection = `sel_*`**, **Search = `sch_*`**.
  공유하는 것은 `self._log()`(공용 로그창)뿐이다.

---

## 3. 설치 / 실행

- **설치**: `A00310_SearchTool/__dragDrop_A00310.py` 를 Maya 뷰포트로 **드래그&드롭**하면 현재 셸프에
  "SearchTool" 버튼이 설치된다(중복 버튼은 자동 제거).
- **실행**: 셸프 버튼 클릭, 또는 스크립트 에디터에서
  ```python
  import tools.A00310_SearchTool as A00310_SearchTool
  A00310_SearchTool.run(True)   # True 면 DEV_MODE 에서 Framework + 자기 자신 reload
  ```
- 창은 `objectName`(`JUN_A00310_SearchTool_window`)으로 관리되어 재실행 시 중복 없이 교체된다.

---

## 4. 공통 옵션

두 탭 모두 상단에 **Source** 옵션과 **Invert** 체크박스가 있다.

- **Source — Hierarchy / Selected**: `Get`/`List Types` 가 무엇을 대상으로 할지 정한다.
  - **Hierarchy**(기본): 선택한 오브젝트 각각의 **자손 transform 까지 펼쳐서** 대상으로 삼는다(shape 제외).
  - **Selected**: 현재 선택만 그대로 대상으로 삼는다.
- **Invert**: 선택 결과를 **여집합**으로 뒤집는다. 즉 Objects 리스트에서 조건에 **맞지 않는** 것을 선택한다.

> 각 리스트(TSL)의 버튼: **Get/List Types**(채우기) · **Add**(현재 선택 추가) · **Del** · **Up** · **Down** ·
> **Sort**(이름 정렬). 리스트 항목을 클릭하면 그 오브젝트가 씬에서 선택된다.

---

## 5. Selection 탭

선택(또는 계층)에서 오브젝트와 노드 타입을 리스트업하고, 타입별로 선택한다.

1. 씬에서 오브젝트를 선택하고 Objects 리스트의 **Get** → 대상 오브젝트를 채운다.
2. (선택) Types 리스트의 **List Types** → 대상의 **노드 타입**(shape 가 있으면 shape 타입, 없으면
   transform 타입)을 정렬·중복제거해 채운다.
3. 원하는 방식으로 선택:
   - **Select By Shape**: 고정 버튼 — **Mesh / nurbsCurve / Joint / Constraint**. Objects 리스트 중 그
     타입인 것을 선택한다. (Constraint 는 `aim/orient/point/scale/parentConstraint` 5종을 모두 매칭)
   - **Select By Type (use selected types)**: Types 리스트에서 **선택한 타입들**과 일치하는 Objects 를 선택한다.
4. 선택 결과는 씬에 반영되고 Objects 리스트에서도 하이라이트된다. **Invert** 면 여집합을 선택한다.

---

## 6. Search 탭

오브젝트 이름에 토큰이 포함된 것을 선택한다.

1. **Search Token** 에 찾을 부분 문자열을 입력한다.
2. 씬에서 오브젝트를 선택하고 Objects 리스트의 **Get** → 대상 오브젝트를 채운다.
3. **Search By Token**(또는 토큰 입력 후 Enter) → 이름에 토큰이 들어간 오브젝트를 선택한다.
   **Invert** 면 토큰이 **없는** 것을 선택한다.

---

## 7. 로그 / About

- 두 탭의 모든 결과·경고(`[WARN]`)는 창 하단의 **공유 로그창**에 누적된다.
- **Help > About** 에 두 탭의 기능 설명이 표기된다.
