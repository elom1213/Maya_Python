---
name: xform-silent-on-locked-channels
description: "cmds.xform 은 잠긴 채널에 에러 없이 아무것도 안 한다 — 스킨된 메시를 복제하면 t/r/s 잠금이 히스토리를 지워도 남아서, 배치가 조용히 실패한다. 놓은 뒤 월드 행렬을 되읽어 확인할 것"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 8a1f639d-1fbe-4096-98f7-2265e5589a17
  modified: 2026-09-07T01:06:00.198Z
---

**`cmds.xform` 은 잠긴(또는 연결된) 채널에 대해 에러도 경고도 없이 그냥 넘어간다.**
`setAttr` 은 `RuntimeError: ... is locked or connected` 를 내는데 `xform` 은 조용하다.

가장 자주 걸리는 상황: **마야는 `skinCluster` 가 붙은 메시의 트랜스폼 t/r/s 를 잠그고,
그 메시를 `duplicate` 하면 복제본도 잠긴 채로 나온다.** `delete -constructionHistory` 로
디포머를 지워도 **잠금은 남는다**(`getAttr(plug, settable=True)` = False, 연결은 없음).

증상이 특히 고약했던 예 — A00145 Mirror([[wip-a00145-mirror-tab]]): 메시는 트랜스폼을
놓은 뒤 정점을 한 번 더 반사하는데, 그 보정이 **현재 트랜스폼을 읽어서** 계산되므로
트랜스폼이 안 놓여도 **월드 형상은 정확히 맞아 보인다.** 트랜스폼만 엉뚱한 자리에 있다.

대처 두 가지를 같이 쓴다.

1. 놓기 직전에만 t/r/s(조인트는 `jointOrient` 까지, 축 채널 `translateX` 등도 함께)
   잠금을 풀고 **원래 상태로 되돌린다** — 리거가 일부러 잠근 채널을 열어 두면 안 된다.
2. 적용 뒤 `xform -q -ws -m` 로 **되읽어 확인**한다. 어긋나면 그 노드를 보고한다.
   확인이 없으면 어디가 안 놓였는지 알 길이 없다.

관련: [[getattr-settable-lies-for-constrained]] (settable 은 컨스트레인트에는 거짓말),
[[shape-pnts-is-post-deformation]].
