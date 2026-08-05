---
name: wip-a00110-euler-filter-range
description: "A00110 Euler Filter 탭 - filterCurve 는 startTime/endTime 을 실제로 존중하고, 앵커는 구간 안 첫 키다"
metadata: 
  node_type: memory
  type: project
  originSessionId: 8214290d-2633-4d40-9048-e0b22634a4b7
  modified: 2026-08-05T01:23:13.468Z
---

A00110_animTool 에 **Euler Filter 탭**(v01.37, `app/core/euler_filter_manager.py`) 추가 — TSL 대상 +
공용 timeRange 구간으로 **[Start, End] 안의 회전 키만** 오일러 필터.

headless(mayapy 2024)로 확인한, 문서에 잘 안 나오는 두 가지:

1. **`cmds.filterCurve(curves, filter="euler", startTime=, endTime=)` 는 구간을 실제로 존중한다.**
   구간 밖 키는 값이 안 바뀐다. 마야 메뉴 `Curves > Euler Filter` 가 전 구간을 처리하는 건 필터에
   구간 개념이 없어서가 아니라 **MEL 이 구간을 안 넘겨서**다. → 오일러 수식(±360 언와인딩 +
   `(θ1+180, 180-θ2, θ3+180)` 플립)을 직접 구현할 필요 없다. `rotateOrder` 가 `zxy` 여도 마야가
   순서에 맞는 축을 반전해준다.
2. **앵커는 "구간 안 첫 키"이고 그 키는 절대 안 바뀐다.** 그래서 플립 지점이 Start 바로 앞이면
   (20f 에서 뒤집혔는데 구간 `[20-40]`) 구간 안 키들끼리는 이미 일관돼 **아무것도 안 고쳐진다**.
   → `anchor_previous` 옵션(기본 ON)은 필터 구간을 **Start 직전 키까지 뒤로 넓혀** 실행한다.
   그 키가 앵커가 되어 값이 유지되므로 "구간 밖은 그대로"를 지키면서 앞쪽 이음매가 사라진다.

기타: 애님 레이어가 있으면 `cmds.keyframe(plug, q=True, name=True)` 는 **선택된 레이어 커브 하나만**
돌려준다 → 마야 기본 필터처럼 작업 중 레이어에만 적용됨. 변경 집계는 필터 전/후 값 스냅샷 비교로
하고(실제 바뀐 키 수), End 경계 이음매를 경고로 알린다. 검증 스크립트는 9 케이스.

관련: [[mayapy-headless-verify]], [[framework-timerange-widget]], [[undo-chunk-by-default]]
