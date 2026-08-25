---
name: wip-a00060-v03-tab-reorg
description: A00060_jointTool_V03 — V02 의 탭 재분류판(카테고리 5 → 기능 11). Curve/Hair 탭이 뒤섞였다는 증거는 "리스트 하나가 세 종류를 담는 것" 이었다 (v03.00)
metadata:
  type: project
---

**`A00060_jointTool_V03`** = `A00060_jointTool_V02` 의 **탭 재분류판** (V02 v01.05 → V03 **03.00**, 2026-08-25).
계획서: `JUN_All/docs/plans/A00060_jointTool_V02_tab_reorg_plan.md`, 문서: `docs/A00060_jointTool_V03.md`.
**V02 는 재분류 전 상태로 그대로 둔다** — 이후 작업은 V03 에서.
[[wip-a00110-tab-taxonomy]] · [[wip-a00275-tab-reorg]] 와 같은 규칙, 골격도 같다
(`_build_sub_tabs` + `_scrolled` + 분류표 튜플).

| 상위 | 뜻 (무엇이 바뀌나) | 하위 |
|---|---|---|
| **Create** | 씬에 조인트가 생긴다 | From Curve · From Object · Divide |
| **Orient** | 있는 조인트의 방향만 바뀐다 | Aim · Set Orient · Orient / Rotate |
| **Chain** | 있는 체인의 구조·연결을 고친다 | Reverse · [[wip-a00060-ik-edit]] |
| **Curve** | 커브·디포머를 다룬다(조인트 준비) | Edit Curve · Clusters |
| **Select** | **씬을 바꾸지 않는다** | Unused Joints |

**뒤섞임을 판별한 방법 — 탭 이름이 아니라 리스트를 봤다.**
`Curve` 탭은 이름과 달리 네 섹션 중 둘만 커브를 썼고(`Clusters` 는 조인트를 만들지도 않는다),
`Hair` 는 기능이 아니라 **쓰임새** 이름이었다. 결정적 증거는 **리스트 하나(`tsl_curve`)를
다섯 기능이 나눠 쓰는데 담아야 할 것이 커브/오브젝트/조인트로 제각각**이라는 것이다.
그래서 리스트를 안 비우고 다른 섹션을 누르면 `Joints to Crv` 는 경고 후 스킵, **`Clusters` 는
타입 검사가 없어 `.spans` 에서 그대로 예외**. → **한 리스트가 여러 타입을 담고 있으면 그 섹션들은
한 탭에 있으면 안 된다.** 다른 툴에도 그대로 쓸 수 있는 판별 기준이다.
V03 은 **하위 탭마다 자기 리스트**를 두고 제목이 타입을 말한다(`Curves` / `Objects` / `Joints` /
`Root Joints`). 접이식은 전부 하위 탭이 되어 `app/ui/collapsible.py` 를 삭제했다.

**A00275 의 함정은 여기엔 없었다.** 상위 탭 인덱스로 갈라 쓰던 `_on_tab_changed` 가 중첩 뒤
영영 일치하지 않는 문제 — 이 툴은 `currentChanged` 연결이 **0건**이었다(grep 이 5초).
대신 **이미 있던 약점**을 같이 고쳤다: IK 편집 상태는 ikHandle 노드에 있는데 V02 는
`_build_ik_edit_tab()` 안에서 **창을 만들 때 한 번만** 읽어, 다른 창에서 편집을 시작/종료하면
버튼과 씬이 어긋났다. 이제 상위·하위 두 `currentChanged` 를 같은 슬롯에 물리고 —
**상위는 위젯 동일성(`self.chain_page`), 하위는 `IKE_SUB_INDEX` 상수**로 판단한다
(`chain_tabs.widget(i)` 는 페이지가 아니라 `QScrollArea` 래퍼라 위젯 비교가 헷갈린다).

**버전 번호를 바로잡았다.** 폴더가 `_V02` 인데 버전이 `01.05` 였던 저장소 유일한 예외
(다른 `_V02` 툴 4개는 전부 `02.xx`). A00110 이 **탭 재분류 시점에** `01.41→02.00` 으로 올린
선례를 따라 V03 은 `03.00` 부터. 복제 체크리스트는 전부 적용 — 드롭 파일
`__dragDrop_A00060_V03.py` · 셸프 `TOOL_LABEL`=`JointTool3` · 아이콘 파일명 ·
`WINDOW_OBJECT_NAME` · `launch.py` 의 `reload_for_tool`/import. (핫키는 이 툴에 없다.
아이콘 아트워크는 버전 표식이 없어 그대로 재사용 — 구분은 셸프 오버레이 라벨이 한다.)

**검증 방법이 핵심이었다** (mayapy headless **128항목 전부 통과**):
V02 와 V03 의 `MainWindow` 를 **같은 프로세스에 띄워 위젯 속성 이름 집합을 diff** →
사라진 것이 `tsl_curve` · `tsl_hair` **둘뿐**이면 어떤 핸들러도 참조를 잃지 않았다는 뜻이다
([[wip-a00110-tab-taxonomy]] 의 스냅샷 기법 재사용). 여기에 15기능 씬 동작 회귀와,
**조용히 틀릴 수 있는 두 지점** — `Match to Sel` 이 `From Object` 탭 리스트의 `Order` 를 읽는지
([[tsl-selection-order]]), `Unused Joints` 가 **자기 탭** 리스트를 하이라이트하는지 —
그리고 IK 세션 인수 + 탭 전환 재조회를 더했다.
`QApplication` 은 `standalone.initialize()` **앞에** ([[qapplication-before-maya-standalone]]).

실측: 상위 탭 바 291px · 가장 넓은 하위 탭 바 241px(`Create`) · 가장 긴 페이지 423px
→ 창 `540 × 820` → **`560 × 720`**(접이식이 갈라지면서 페이지가 짧아졌다).
`app/core/*` 는 한 줄도 안 고쳤다 — 바뀐 것은 `app/ui/main_window.py` 뿐.
