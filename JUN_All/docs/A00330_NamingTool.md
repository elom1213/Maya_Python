# A00330_NamingTool 사용법

## 1. 개요

씬 오브젝트의 **이름을 일괄 변경**하는 PySide(Qt) 툴이다. 레거시 maya.cmds 단일 파일 툴
`JUN_PY_NamingTool_V03_04` 를 `A00310_SearchTool` 과 같은 **하나의 창 + 탭** 구조로 이식했고,
원본 2개 탭에 더해 `ref/ref_01.mel`(현장용 빠른 리네임)을 **3번째 탭**으로 통합했다.

1. **Naming Dyn** — 오브젝트와 그 transform 자손을 `Token1_Token2_Token3_Index1_Index2` 로 일괄 리네임.
   (구 Naming Dynamics 탭)
2. **Copy Name** — Base 리스트의 leaf 이름(+Prefix)을 Targets 리스트에 순서대로 적용. (구 Copy name 탭)
3. **Quick Rename** — **현재 선택** 기준으로 앞/뒤 글자 추가·제거, 새 이름+인덱스 부여. (`ref/ref_01.mel` 이식)
4. **Set Rename** — **세트 이름**의 부분 문자열 찾아 바꾸기. 마야 기본 `Search and Replace Names` 는
   세트를 고를 수 없다(§6.4). (v01.02 신규)

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
   - **세트를 담으려면 `Add Sets`** 를 쓴다(v01.03). `cmds.select(set)` 이 멤버를 펼쳐 버려서
     평범한 Select/Add 로는 세트가 안 담긴다. 이 버튼은 **선택에 든 세트**와
     **선택한 오브젝트가 속한 세트**를 함께 모은다.
2. **Prefix** 에 접두어를 입력한다(선택).
3. **Set suffix** — **대상이 세트일 때만** 뒤에 붙는다. 기본 `_copy` (v01.03).
4. **Copy Name** 클릭 → Targets[i] 가 `Prefix + Base[i] 의 leaf 이름` 으로 리네임된다(리스트 순서 기준).

> **세트에 접미사가 필요한 이유** — 세트는 DG 노드라 **이미 쓰이는 이름을 그대로 못 쓴다.**
> 트랜스폼 `myName` 이 있는 씬에서 세트를 `myName` 으로 바꾸면 **마야가 조용히 `myName1` 로
> 만든다**(실측). DAG 노드는 부모가 다르면 같은 이름을 가질 수 있어(`|g1|c` 와 `|g2|c` 공존)
> 이 문제가 없다 — 그래서 접미사는 **세트 대상에만** 붙는다.
>
> `Set suffix` 를 비우면 접미사 없이 시도하고, 마야가 이름을 바꾸면 **실제로 붙은 이름**을
> 로그에 `[Warning]` 으로 알린다(조용히 넘어가지 않는다).

> **네임스페이스는 보존된다**(v01.03). 짧은 이름만 넘기면 노드가 **루트 네임스페이스로
> 옮겨간다** — 세트도 트랜스폼도 마찬가지다(실측). 이 탭은 대상의 네임스페이스를 그대로 다시 붙인다.

### 6.3 Quick Rename 탭 (현재 선택 기준)

1. 씬에서 대상 오브젝트를 선택한다(리스트가 아니라 **실제 선택**을 사용).
2. 원하는 동작:
   - **Front Insert** + **Insert Apply** — 이름 앞에 텍스트 삽입.
   - **Change New** (+ **Start (Index)**) + **New Apply** — 새 이름 + 증가 인덱스로 변경.
   - **Last Add** + **Add Apply** — 이름 뒤에 텍스트 추가.
   - **-1 Front / -1 Rear** — 이름의 앞/뒤 한 글자 제거.
   - **All Apply** — Change New → Front Insert → Last Add 순으로 한 번에 적용.

---

### 6.4 Set Rename 탭 (v01.02, 신규)

**세트 이름 안의 부분 문자열을 찾아 바꾼다.**

#### 마야 기본 기능은 왜 안 되나 (Maya 2024 실측)

`Modify > Search and Replace Names` 의 실체는 MEL `searchReplaceNames` 다.
**이 명령 자체는 세트도 잘 바꾼다** — `"all"` 모드로 돌리면 세트 이름이 같이 바뀐다
(실측: 세트 5개를 포함해 8개 이름이 한 번에 바뀌었다).

막힌 것은 명령이 아니라 **세트를 선택하는 방법**이다.

```python
cmds.select(mySet)
cmds.ls(sl=True)                    # ['pCube1']  <- 세트가 아니라 멤버가 나온다
cmds.ls(sl=True, type="objectSet")  # []
```

**`cmds.select(set)` 은 세트가 아니라 그 멤버를 펼쳐 선택한다.** 그래서 `"selected"` 모드는
세트를 영영 못 본다. `noExpand=True` 로 넘기면 세트 자신이 선택되고 그때는 마야 기본 기능도
세트를 바꾸지만, 뷰포트·아웃라이너 조작으로 그 상태를 만들기가 어렵다.
`"all"` 모드는 대안이 못 된다 — 씬의 메시·조인트·카메라까지 전부 바꾼다.

→ **이 탭은 세트를 직접 열거해 고르게 하고, 바꾸기 전에 미리보기를 준다.**

#### 쓰는 법

1. **`Refresh`** — 씬의 모든 세트를 나열한다(목록을 **교체**).
   **`From Selection`** — 지금 선택한 오브젝트가 **속한** 세트를 나열한다(목록을 **교체**).
   메시 하나를 고르고 그것이 든 세트를 찾는 흐름이다. 세트 자신을 `noExpand` 로 골라 둔
   경우도 함께 잡는다.
   **`Add`** / **`Del`** (v01.03) — 다른 탭의 TSL 과 같은 조작이다.
   `Add` 는 선택과 관련된 세트를 **기존 목록에 더한다**(이미 있으면 건너뛴다).
   `Del` 은 하이라이트한 행을 **목록에서만** 뺀다 — **씬의 세트는 지워지지 않는다.**
2. **Filter** 로 목록을 좁힌다(부분 일치 · 대소문자 무시 · 공백은 AND).
3. 바꿀 세트를 **하이라이트**한다(다중 선택).
4. **Search / Replace** 를 친다 — **목록의 `New name` · `Status` 열이 즉시 갱신된다.**
5. **`Rename Selected Sets`** — 전체가 **undo 한 스텝**.

> **필터에 가려진 선택은 대상이 아니다.** 가려진 채 선택된 행이 있으면 로그로 알려 준다
> ("보이는 것이 작업 대상" — 공용 Filter 위젯의 규칙).

| 옵션 | 뜻 |
|---|---|
| `Shading Engines` | `shadingEngine` 노드도 목록에. **기본 꺼짐** — 렌더 셋업을 건드리게 된다 |
| `Partitions` | `partition` 노드도 목록에. **`partition` 은 `objectSet` 이 아니라서** 기본 목록에 안 잡힌다 |
| `Case sensitive` | 마야 기본 기능과 같은 동작 (기본 켜짐) |
| `Select Sets in Scene` | 하이라이트한 **세트 자신**을 씬에서 선택한다 (`noExpand=True`) |

#### Status 열

| 상태 | 뜻 | 실행되나 |
|---|---|---|
| `OK` | 문제 없음 | O |
| `name taken` | 같은 이름이 이미 있다 — **마야가 번호를 붙인다**(`dst_set` → `dst_set1`) | O (실제 붙은 이름을 로그로 보고) |
| `no change` | 검색어가 이름에 없다 | X |
| `invalid name` | 마야가 허용하지 않는 문자 (이유를 함께 표시) | X |
| `locked` | 잠긴 노드 | X |
| `referenced` | 레퍼런스에서 온 노드 | X |
| `default set` | `initialShadingGroup` 등 기본 세트 | X |

#### 실측으로 알아낸 함정 (이 탭이 대신 막아 주는 것)

- **네임스페이스가 벗겨진다.** `rename("NS:in_ns", "plain")` 하면 세트가 **루트 네임스페이스로
  옮겨간다**(`NS` 는 비게 된다). 짧은 이름만 바꿔 넘기면 레퍼런스에서 온 세트가 전부
  네임스페이스를 잃는다. → 이 탭은 **네임스페이스를 떼어 두고 짧은 이름만 치환한 뒤 다시
  붙여서** rename 한다.
- **마야가 이름을 조용히 고친다.** `1bad` → `bad`(**맨 앞 숫자가 사라진다**),
  `has space` → `has_space`, `has-dash` → `has_dash`, `a|b` → `a_b`.
  경고만 뜨고 넘어가므로 의도와 다른 이름이 조용히 생긴다. → **미리 걸러 내고 건너뛴다**
  (마야의 조용한 변환을 흉내 내지 않는다).
- **이름이 겹치면 번호를 붙인다**(에러가 아니다). → 미리보기에서 `name taken` 으로 표시하고,
  실행 후 **실제로 붙은 이름**을 `[Warning]` 으로 알린다.
- **기본 세트는 못 바꾼다** — `Cannot rename a read only node`. 다만 **`ls(readOnly=True)` 는
  빈 리스트를 준다**(판정에 쓰면 안 된다) — `ls(defaultNodes=True)` 로 골라야 한다.
- `rename` 은 **undo 된다.**

---

## 7. 동작 규칙

- **Naming Dyn 인덱스**: `Index1` 은 **루트 그룹마다** 1 증가, `Index2` 는 **그룹 내 항목마다** 증가하고 그룹이 바뀌면
  `Index2` 시작값으로 리셋된다. 각 인덱스는 **pad 0** 자리수로 0 패딩된다(예: pad=2 → `00, 01, …`).
- **자손 수집**: 루트가 transform 이면 자손 중 **transform 만** 남긴다(shape 노드 제외). `[root, 얕은→깊은 자손]` 순서.
- **Change New 패딩**: 10 미만은 `0` 패딩(`01…09`), 이후는 그대로(`10, 11…`).
  Start 가 비어 있고 **단일 선택**이면 번호 없이 이름만, **다중 선택**이면 `01` 부터 자동 부여.
- **이름 정리**: 모든 처리에서 DAG 경로(`|`)와 네임스페이스(`:`)를 제거한 leaf 이름을 기준으로 한다.
- **Undo**: 각 버튼 동작은 `core.undo_chunk` 로 묶여 **한 번의 Undo** 로 되돌릴 수 있다.
- **동일 이름 안전(v01.01+)**: 모든 rename 은 노드를 **UUID** 로 잡아 처리한다(`_to_uuid` → `_rename_by_uuid`).
  씬에 같은 이름의 오브젝트가 여러 개 있어도(예: `joint_01`·`joint_03` 밑에 각각 `joint_02`),
  또 부모를 rename 해 자식 경로가 바뀌어도 UUID 로 현재 경로를 다시 찾아가므로 실패하지 않는다.
  (Naming Dyn 은 자손을 `fullPath` 로 수집하고, 입력 이름도 `ls(long=True)` 로 정규화한다.)

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
