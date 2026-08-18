---
name: pointposition-points-only
description: "cmds.pointPosition 은 점 컴포넌트만 받는다 — 엣지/페이스는 RuntimeError, xform -q -ws -t 평균으로"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 5ea9f25d-fd66-4b79-a930-ec982f8f7f17
  modified: 2026-08-18T01:00:26.410Z
---

`cmds.pointPosition(comp, world=True)` 는 **점 컴포넌트(vtx / cv / ep / uv)만** 받는다.
엣지(`.e[i]`)나 페이스(`.f[i]`)를 주면 `RuntimeError` 다.

대신 `cmds.xform(comp, q=True, ws=True, translation=True)` 는 **컴포넌트가 걸친 점들의 좌표를
전부** 돌려준다(엣지=6개, 페이스=3×N개, 점=3개). 3개씩 끊어 평균을 내면 컴포넌트 중심이고,
점 컴포넌트면 `pointPosition` 과 **정확히 같은 값**이라 한 코드로 통일할 수 있다.

**Why:** "component 는 pointPosition 으로" 라고 적어 두면 vtx/cv 테스트만 통과하고 엣지·페이스는
조용히 실패한다. A00145 Match 탭이 그랬다 — 독스트링에는 edge/face 를 지원한다고 적혀 있었지만
실제로는 예외가 나고 있었고, 캐시 기능을 검증하다 드러났다(2026-08-18, v01.30 에서 수정).

**How to apply:** 컴포넌트 위치가 필요하면 처음부터 `xform -q -ws -t` 평균 헬퍼를 쓴다
(A00145 `match_manager._component_center`). 테스트에는 **엣지와 페이스를 반드시 넣는다** —
vtx/cv 만으로는 이 차이가 드러나지 않는다. 관련: [[wip-a00145-match-cache]]
