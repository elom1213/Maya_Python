# A00330_NamingTool 사용법

## 1. 개요

씬 오브젝트의 **이름을 일괄 변경**하는 PySide(Qt) 툴이다. 레거시 maya.cmds 단일 파일 툴
`JUN_PY_NamingTool_V03_04` 를 `A00310_SearchTool` 과 같은 **하나의 창 + 탭** 구조로 이식했고,
원본 2개 탭에 더해 `ref/ref_01.mel`(현장용 빠른 리네임)을 **3번째 탭**으로 통합했다.

1. **Naming Dyn** — 오브젝트와 그 transform 자손을 `Token1_Token2_Token3_Index1_Index2` 로 일괄 리네임.
   (구 Naming Dynamics 탭)
2. **Copy Name** — Base 리스트의 leaf 이름(+Prefix)을 Targets 리스트에 순서대로 적용. (구 Copy name 탭)
3. **Quick Rename** — **현재 선택** 기준으로 앞/뒤 글자 추가·제거, 새 이름+인덱스 부여. (`ref/ref_01.mel` 이식, 신규)

- 모든 UI 문자열/로그는 영어. 리스트(TSL)는 공용 위젯 `JUN_mod_tsl_qt_v01`(**Select / Add / Del / Up / Down / Sort**)을 쓴다.
- 로직(리네임)은 `app/core`(maya.cmds), 화면은 `app/ui`(PySide)로 분리한다. 모든 작업은 **단일 Undo** 로 묶인다.

---

## 2. 폴더 구조

```
A00330_NamingTool/
├── __init__.py            # from .launch import run
├── launch.py              # run(): MainWindow 생성 → 테마(green_dark) → show()
├── __dragDrop_A00330.py   # 셸프 버튼 설치 + 드래그&드롭 진입점 (TOOL_LABEL = "NamingTool")
├── icon/                  # 셸프 아이콘 (svg + png 64/32)
├── ref/ref_01.mel         # Quick Rename 원본 (참고)
└── app/
    ├── config/version.py  # VERSION / LAST_UPDATE
    ├── core/              # 로직 (UI 비의존, maya.cmds)
    │   ├── naming_ops.py      # rename_dynamics / copy_name / insert_front /
    │   │                      #   add_rear / change_new / trim_front / trim_rear / all_apply
    │   └── __init__.py        # core 재노출
    └── ui/main_window.py  # 전체 UI (3개 탭 + 공유 로그창 + 메뉴 바)
```

- 위젯/핸들러는 탭별 접두사로 분리한다: **Naming Dyn = `dyn_*`**, **Copy Name = `copy_*`**, **Quick Rename = `qr_*`**.
  공유하는 것은 `self._log()`(공용 로그창)뿐이다.

---

## 3. 설치

`A00330_NamingTool/__dragDrop_A00330.py` 를 Maya 뷰포트로 **드래그&드롭**하면 현재 셸프에
"NamingTool" 버튼이 설치된다(중복 버튼은 자동 제거).

---

## 4. 실행

- **셸프 버튼** 클릭, 또는 스크립트 에디터에서:
  ```python
  import tools.A00330_NamingTool as A00330_NamingTool
  A00330_NamingTool.run(True)   # True 면 DEV_MODE 에서 Framework + 자기 자신 reload
  ```
- 창은 `objectName`(`JUN_A00330_NamingTool_window`)으로 관리되어 재실행 시 중복 없이 교체된다.
- PySide2(Maya ~2024) / PySide6(2025+) 양쪽 지원(`Framework.qt.qt` 자동 분기).

---

## 5. UI 구성

- **상단 탭**: Naming Dyn / Copy Name / Quick Rename.
- **하단 공유 로그창**: 모든 결과·경고(`[WARN]`)가 누적된다.
- **Help > About**: 세 탭의 기능 요약.
- 리스트(TSL)의 버튼: **Select**(현재 선택으로 교체) · **Add**(현재 선택 추가) · **Del** · **Up** · **Down** · **Sort**.
  리스트 항목을 클릭하면 그 오브젝트가 씬에서 선택된다.

---

## 6. 사용 순서

### 6.1 Naming Dyn 탭

1. 씬에서 루트 오브젝트들을 선택하고 **Select Base** → Objects 리스트에 채운다(순서가 곧 그룹 순서).
2. **Token 1/2/3** 에 이름 토큰을, **Index 1/2** 에 시작 번호를, 그 아래 **pad 0** 에 자리수를 입력한다.
3. **Naming Dynamics** 클릭 → 각 오브젝트와 transform 자손이 `T1_T2_T3_Idx1_Idx2` 로 리네임된다.

### 6.2 Copy Name 탭

1. 좌측 **Select Base**, 우측 **Select Targets** 로 두 리스트를 채운다. (필요하면 각 **Sort**)
2. **Prefix** 에 접두어를 입력한다(선택).
3. **Copy Name** 클릭 → Targets[i] 가 `Prefix + Base[i] 의 leaf 이름` 으로 리네임된다(리스트 순서 기준).

### 6.3 Quick Rename 탭 (현재 선택 기준)

1. 씬에서 대상 오브젝트를 선택한다(리스트가 아니라 **실제 선택**을 사용).
2. 원하는 동작:
   - **Front Insert** + **Insert Apply** — 이름 앞에 텍스트 삽입.
   - **Change New** (+ **Start (Index)**) + **New Apply** — 새 이름 + 증가 인덱스로 변경.
   - **Last Add** + **Add Apply** — 이름 뒤에 텍스트 추가.
   - **-1 Front / -1 Rear** — 이름의 앞/뒤 한 글자 제거.
   - **All Apply** — Change New → Front Insert → Last Add 순으로 한 번에 적용.

---

## 7. 동작 규칙

- **Naming Dyn 인덱스**: `Index1` 은 **루트 그룹마다** 1 증가, `Index2` 는 **그룹 내 항목마다** 증가하고 그룹이 바뀌면
  `Index2` 시작값으로 리셋된다. 각 인덱스는 **pad 0** 자리수로 0 패딩된다(예: pad=2 → `00, 01, …`).
- **자손 수집**: 루트가 transform 이면 자손 중 **transform 만** 남긴다(shape 노드 제외). `[root, 얕은→깊은 자손]` 순서.
- **Change New 패딩**: 10 미만은 `0` 패딩(`01…09`), 이후는 그대로(`10, 11…`).
  Start 가 비어 있고 **단일 선택**이면 번호 없이 이름만, **다중 선택**이면 `01` 부터 자동 부여.
- **이름 정리**: 모든 처리에서 DAG 경로(`|`)와 네임스페이스(`:`)를 제거한 leaf 이름을 기준으로 한다.
- **Undo**: 각 버튼 동작은 `core.undo_chunk` 로 묶여 **한 번의 Undo** 로 되돌릴 수 있다.

> **주의(레거시 동일 한계)**: Naming Dyn 에서 동일한 short name 자손이 여러 부모에 걸쳐 있으면
> 경로 모호성으로 일부 rename 이 실패할 수 있다. 그룹 단위로 나눠 실행하면 회피된다.

---

## 8. 로그 · 문제 해결

- 정상: `Naming Dynamics : 12 node(s) renamed.` / `Copy Name : 8 target(s) renamed.` / `Front Insert : 3 renamed.`
- 경고:
  - `[WARN] Objects list is empty. Use Select Base first.` — Naming Dyn 리스트가 비어 있음.
  - `[WARN] Index / pad must be integers.` — 인덱스/패딩에 숫자가 아닌 값.
  - `[WARN] Both Base and Targets lists must be filled.` — Copy Name 양쪽 리스트 필요.
  - `[WARN] Base(n) and Targets(m) counts differ; renaming first k item(s).` — 개수 불일치 시 앞쪽만 처리.
  - `[WARN] Enter a new name. (Change New is empty)` — Change New 비어 있음.
- **이름이 안 바뀜**: Quick Rename 은 리스트가 아니라 **현재 씬 선택**을 대상으로 한다. 선택 여부를 먼저 확인.
