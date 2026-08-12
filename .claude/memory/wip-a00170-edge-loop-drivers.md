---
name: wip-a00170-edge-loop-drivers
description: A00170 AttachCrv > Edge Loop 하위 탭 — 엣지 루프→커브→버텍스 자리 널→어태치(+조인트)를 한 번에 (v01.14)
metadata:
  node_type: memory
  type: project
---

A00170_driverTool `AttachCrv` 를 **하위 탭 2개**로 나눴다 (v01.13→**01.14**, 2026-08-12).
`Default` = 기존 기능 그대로, `Edge Loop` = 신규.

**Edge Loop 탭**: 저장한 엣지 루프 → 커브, 저장한 버텍스 자리 → 널, 널 → 가장 가까운 커브에
어태치, (체크박스 기본 ON) 널마다 조인트. 입술/눈꺼풀 드라이버 셋업이 버튼 하나.
코어는 `app/core/loop_rig.py`.

**설계 판단**

- 커브 생성은 A00400_CurveTool 방식(연결 성분별 `polyToCurve(form=2, ch=True)`)을 **복사**했다.
  **A00400 을 import 하지 않는다** — `dev/build_release.py` 가 툴 하나 + Framework 만 복사하므로
  툴끼리 물리면 릴리스 패키지가 깨진다. (공용으로 올릴 거면 Framework 로.)
- 어태치는 같은 툴의 `attach_curve.build_attach_to_closest` 를 그대로 호출 — 커브별로 **모아서 한 번**
  불러야 norCrv/POCI 세트가 커브마다 하나씩 생긴다.
- 커브가 여럿이면 널마다 `nearestPointOnCurve` 로 거리를 재 **가장 가까운 커브**에 붙인다.
- **조인트는 널 밑으로 parent 하지 않고 `parentConstraint`** — 스켈레톤 계층을 따로 둬야 스킨·
  익스포트가 자유롭다. 어태치가 끝난 **널의 최종 위치**에 만든다(먼저 만들면 자리가 틀어진다).
- 저장한 엣지/버텍스는 리스트 위젯 없이 요약 라벨 + Select/Clear ([[wip-a00275-expand-bind]] 와 같은
  이유 — 루프 하나가 수십~수백 컴포넌트).

**마야 메모**: `cmds.polyToCurve` 가 만드는 히스토리 노드 타입은 `polyToCurve` 가 아니라
**`polyEdgeToCurve`** 다(실측). 닫힌 엣지 루프면 `form=2` 로 주기적 커브가 나온다.

검증: 코어 34 + UI 27 항목 headless 통과([[mayapy-headless-verify]]), 기존 Default 탭 회귀 포함.
