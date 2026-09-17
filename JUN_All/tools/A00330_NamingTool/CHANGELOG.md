# Changelog — A00330_NamingTool

## v01.08 (2026-09-17)
**[UI] Token 칸 폭을 2/3 로 — 120 → 80px.**

- 80px 에 그대로는 안 들어갔다(실제 윈도우 폰트로 측정): `Numbering` 콤보 89px, `Start` 라벨 + 스핀박스 한 줄 107px.
  - 칸 좌우 여백 0, 규칙 콤보만 padding 1px · 화살표 폭 12px → 79px.
  - `Start` / `Pad 0` 라벨을 스핀박스 **위**로 → 69px. 그만큼 토큰 영역이 15px 높아졌다.
- 기존 61항목 재통과, 실제 폰트 캡처로 글자 잘림 없음 확인.

## v01.07 (2026-09-17)
**[Feature] 상위 탭 `Rename` — `Naming Dyn`(→ `Token`) · `Set Rename` 을 하위 탭으로. `Token` 탭 규칙 · 칸 수 · 프로파일.**

- 상위 탭: `Rename`(Token / Set Rename) · `Copy Name` · `Quick Rename`.
- **토큰 칸마다 규칙**: `Custom`(글자 그대로) / `Numbering`(Start + Pad 0). A00480_FileTool Export 탭의 Naming 처럼 칸 밑 콤보.
- **칸 수 자유**: 칸 머리를 눌러 고르고 `Add Token`(오른쪽에 삽입) / `Delete Token`(마지막 한 칸은 남김). 칸이 넘치면 가로 스크롤.
- **Numbering 개수가 세는 대상을 정한다**: 1 개 = 전체 순번, 2 개 = 오브젝트 / 오브젝트 안 노드(레거시 Index1 / Index2), 3 개 이상은 실행 안 함.
- **Profile**(json): 콤보 + `New`(지금 칸 복사) / `Rename` / `Delete`. 칸을 고치면 바로 저장. 처음엔 레거시 규칙 `Default`
  (`dyn_asset_side_{번호}_{번호}`, Pad 2)를 만든다. `data/` 는 git 추적 안 함.
- **실행 전 검사**: Custom 은 영문·숫자·`_` 만, 이름이 숫자로 시작하면 막는다 — 마야는 `01_a` 를 **조용히 `_a`** 로 만든다(실측).
- `Preview` 줄: 첫 이름 · 다음 노드 · 다음 오브젝트.
- 네임스페이스 보존(레거시 Naming Dyn 은 루트로 옮겼다). 빈 Custom 토큰은 건너뛴다(`__` 없음).
- 핵심 로직은 순수 파이썬 `core/token_ops.py`, 파일은 `core/token_profile_prefs.py`, UI 는 `ui/token_tab.py`.

**검증**(mayapy 2024 headless, 61항목 통과): `Default` 결과 = 레거시 `rename_dynamics`(같은 이름 노드 포함 계층) ·
번호 규칙 1/2/3 개 · 검사(숫자 시작 · 금지 문자 · 빈 이름) · 단일 Undo · 네임스페이스 보존 · 충돌 보고 ·
프로파일 생성/깨진 파일/전환/New/Rename/Delete/마지막 남김/다시 열면 복원 · Add/Delete Token 자리 · 가로 스크롤 ·
칸이 늘어도 창 최소 폭 불변 · 칸 높이 잘림 없음 · 고른 칸 강조 · 하위 탭 구성.

## v01.05 (2026-09-17)
**[Feature] `Copy Name` 에 `Search` / `Replace`.**

Set Rename 탭의 찾아 바꾸기를 Copy Name 탭에도 넣었다. **Base 이름 속 `Search` 를 `Replace` 로 바꾼 결과**를
Targets 에 복사한다 — 예: Base `L_arm_jnt`, Search `jnt`, Replace `ctrl` → Target `L_arm_ctrl`.

- 치환은 Set Rename 과 같은 `replace_in_name` 을 쓴다(글자 그대로, 전부 치환, `Case sensitive` 기본 켬).
- **Base 이름에만** 건다. `Prefix` / `Set suffix` 는 치환 뒤에 붙는다. 네임스페이스 보존은 그대로.
- `Search` 가 비면 기존 동작과 같다(`copy_name` 새 인자는 전부 기본값이 있어 호출부 호환).
- 치환 결과가 **빈 이름**이면 rename 이 에러를 내므로, 그 대상은 건너뛰고 `[Warning]` 을 남긴다.

**검증**(mayapy headless, 12항목 통과): 대소문자 구분/무시 · Prefix 는 치환 뒤 · 단일 Undo ·
빈 이름 건너뛰기 · Search 빈칸 = 기존 복사 · 네임스페이스 보존 · 세트 접미사는 치환 뒤 ·
UI(치환 적용 · Targets 리스트 갱신 · 로그) · 버전.

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
