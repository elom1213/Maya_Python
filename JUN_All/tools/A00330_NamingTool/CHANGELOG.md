# Changelog — A00330_NamingTool

## v01.03 (2026-08-27)
**[Feature] `Set Rename` 에 `Add` / `Del`, `Copy Name` 이 세트도 대상으로.**

**1. `Set Rename` — `Add` / `Del`**

다른 탭의 TSL 과 같은 조작을 목록에 붙였다.
- `Add` : 선택과 관련된 세트를 **기존 목록에 더한다**(중복은 건너뛰고 몇 개가 이미 있었는지 로그).
- `Del` : 하이라이트한 행을 **목록에서만** 뺀다. **씬의 세트는 지워지지 않는다**(툴팁·로그에 명시).
  필터에 가려진 선택은 남긴다("보이는 것이 작업 대상").

**2. `Copy Name` — 세트 지원 + `Set suffix`(기본 `_copy`)**

세트는 DG 노드라 **이미 쓰이는 이름을 그대로 못 쓴다.** 실측으로 확인한 것:

| | 결과 |
|---|---|
| 트랜스폼 `myName` 이 있는데 세트를 `myName` 으로 | **조용히 `myName1`** |
| 세트 `shared` 가 있는데 트랜스폼을 `shared` 로 | **조용히 `shared2`** |
| DAG 두 개가 부모만 다르면 같은 이름 | **허용** (`\|g1\|c` 와 `\|g2\|c` 공존) |

→ 대상이 **세트일 때만** `Set suffix` 를 붙인다(DAG 는 문제가 없으므로 안 붙인다).
비워 두면 접미사 없이 시도하고, 마야가 이름을 바꾸면 **실제로 붙은 이름**을 `[Warning]` 으로 보고한다.

세트 판정은 **`nodeType(inherited=True)`** 로 한다 — `shadingEngine` 은 `objectSet` 의
하위 타입이라 `nodeType()` 문자열 비교로는 놓친다(실측:
`['containerBase', 'entity', 'objectSet', 'shadingEngine']`).

세트는 `cmds.select(set)` 이 멤버를 펼쳐 버려 평범한 Select/Add 로 담기 어려우므로
두 리스트에 **`Add Sets`** 버튼을 붙였다(선택에 든 세트 + 선택한 오브젝트가 속한 세트).

**[Fix] `Copy Name` 이 네임스페이스를 벗기던 문제.**
짧은 이름으로 `rename` 하면 노드가 **루트 네임스페이스로 옮겨간다** — 세트만이 아니라
**트랜스폼도 마찬가지다**(실측). 레퍼런스에서 온 대상을 리네임하면 네임스페이스를 잃었다.
이제 대상의 네임스페이스를 떼어 두고 짧은 이름만 바꿔 다시 붙인다.
(`copy_name` 의 반환이 `(new_names, warning)` → **`(new_names, warning, notes)`** 로 늘었다.)

**검증**(mayapy headless, **124항목 전부 통과** — v01.02 의 92항목 포함):
Add/Del 의 목록 변화와 **씬 불변** · 중복 Add · 선택이 무관할 때 거부 ·
`is_set_node` 4종 · 접미사 기본/커스텀/빈 값 · 오브젝트 대상은 접미사 없음 ·
prefix 와 동시 적용 · **네임스페이스 보존(세트·트랜스폼)** · 개수 불일치 경고 ·
UI 의 `Add Sets` 와 `Set suffix` 경로.

## v01.02 (2026-08-27)
**[Feature] `Set Rename` 탭 신규 — 세트 이름의 부분 문자열 찾아 바꾸기.**

마야 기본 `Modify > Search and Replace Names` 로는 세트 이름을 바꿀 수 없다는 요청에서
출발했다. **원인을 먼저 실측했다** — 막힌 것은 명령이 아니라 **세트를 선택하는 방법**이다.

- `searchReplaceNames` 는 `"all"` 모드로 돌리면 세트도 잘 바꾼다(실측: 세트 5개 포함 8개).
- 그런데 **`cmds.select(set)` 은 세트가 아니라 그 멤버를 펼쳐 선택한다** — `ls(sl)` 이
  `['pCube1']` 이다. 그래서 `"selected"` 모드는 세트를 영영 못 본다.
  `noExpand=True` 로 고르면 세트 자신이 잡히고 마야 기본 기능도 동작하지만,
  뷰포트·아웃라이너 조작으로는 그 상태를 만들기가 어렵다.
- `"all"` 모드는 대안이 못 된다 — 씬의 메시·조인트·카메라까지 전부 바꾼다.

→ 그래서 이 탭은 **세트를 직접 열거해 고르게 하고, 바꾸기 전에 미리보기를 준다.**

**기능**

- `Refresh`(씬의 모든 세트) / `From Selection`(선택한 오브젝트가 **속한** 세트)
- 공용 Filter 로 목록 좁히기 — **필터에 가려진 선택은 대상에서 빠지고 로그로 알린다**
- `Search` / `Replace` 를 치면 목록의 `New name` · `Status` 열이 **즉시** 갱신된다
- 옵션: `Case sensitive`(기본 켜짐, 마야와 같음) · `Shading Engines`(기본 꺼짐) ·
  `Partitions`(기본 꺼짐) · `Select Sets in Scene`(세트 자신을 `noExpand` 로 선택)
- 전체가 **undo 한 스텝**

**실측으로 알아낸 함정 4가지 — 전부 이 탭이 막는다**

- **네임스페이스가 벗겨진다.** `rename("NS:in_ns", "plain")` 은 세트를 **루트
  네임스페이스로 옮긴다.** → 네임스페이스를 떼어 두고 **짧은 이름만 치환한 뒤 다시 붙인다.**
- **마야가 이름을 조용히 고친다.** `1bad` → `bad`(**맨 앞 숫자가 사라진다**),
  `has space` → `has_space`, `a|b` → `a_b`. 경고만 뜬다.
  → **미리 걸러 내고 건너뛴다**(조용한 변환을 흉내 내지 않는다).
- **이름이 겹치면 번호를 붙인다**(`dst_set` → `dst_set1`, 에러가 아니다).
  → `name taken` 으로 미리 표시하고, 실행 후 **실제로 붙은 이름**을 보고한다.
- **`ls(readOnly=True)` 는 빈 리스트를 준다** — 기본 세트 판정에 쓰면 안 된다.
  `ls(defaultNodes=True)` 로 골라야 `initialShadingGroup` 을 걸러 낼 수 있다.

또 하나: **`partition` 은 `objectSet` 이 아니다** — `ls(type="objectSet")` 에 안 잡혀
따로 열거해야 한다(옵션).

**Framework**: 공용 Filter 위젯 `JUN_mod_filter_qt_v01` 에 **`QTreeWidget` 모드**를 더했다
(컬럼이 있는 목록용, 기존 호출부 무영향). 여기서 **`QTreeWidget.selectedItems()` 는 숨긴
항목을 빼고 준다**(QListWidget 은 그대로 준다)는 차이를 실측으로 잡아, 트리 모드는
`isSelected()` 로 직접 판정하게 했다 — 안 그러면 "가려진 선택 수" 가 늘 0 이 되어 경고가 사라진다.

**검증**(mayapy headless, **92항목 전부 통과**): 이름 헬퍼(네임스페이스 분리·치환·유효성) ·
열거(세트/SG/partition/기본/잠금) · `From Selection` 과 `select(set)` 확장 거동 ·
미리보기가 씬을 바꾸지 않는가 · 상태 7종 · **네임스페이스 보존(+ 벗겨지는 대조군)** ·
충돌 시 실제 이름 보고 · **undo 한 스텝** · Filter 리스트/트리 모드 · UI 버튼 경로.

## v01.01 (2026-07-03)
- Fix: `Naming Dynamics` failing with `RuntimeError: Invalid path ...` when the
  scene contains multiple objects sharing the same name (e.g. two `joint_02`
  under different roots). Renaming now resolves each node by UUID instead of by
  short name, so duplicate names in the scene no longer break the tool.
- Same UUID-based hardening applied to `Copy Name` and all `Quick Rename`
  actions (Front Insert / Change New / Last Add / -1 trim), which also renamed
  by ambiguous names before.

## v01.00 (2026-06-30)
- Initial Qt(PySide) port of legacy `JUN_PY_NamingTool_V03_04.py`.
  Tabs: Naming Dyn / Copy Name / Quick Rename.
