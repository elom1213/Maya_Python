---
name: wip-a00400-points-to-curve
description: A00400 Points to Curve 탭 - 월드 위치를 순서대로 잇는 커브. 완화는 라플라시안 결과와 선형보간
metadata: 
  node_type: memory
  type: project
  originSessionId: 559dfd30-01bc-4110-8708-a1499b043ca1
  modified: 2026-08-18T01:32:47.861Z
---

`A00400_CurveTool` **Points to Curve 탭** (v01.03→01.04, 2026-08-18).
TSL 에 담은 오브젝트/조인트/컴포넌트의 **월드 위치**를 **리스트 순서대로** 잇는 커브 하나.

- **Exact**: `cmds.curve(editPoint=...)` — 에디트 포인트 커브라 모든 위치를 **정확히** 지난다(실측 0.0).
  `p=`(CV) 로 만들면 안 지난다(편차 1.79).
- **Smoothed**: 그 커브의 **CV 를 라플라시안 이완**(양 끝 CV 고정).
- 순서가 결과이므로 TSL 은 `order_default=True` ([[tsl-selection-order]]).

**슬라이더 감각을 두 번 고쳤다**
1. `rebuildCurve` span 수로 완화 → **단조롭지 않다**(spans 5→4→3 에서 0.30→1.73→**1.44**). 폐기.
2. 라플라시안 **세기**를 슬라이더에 비례 → 반복 효과가 지수적으로 쌓여 **앞 25% 에서 끝난다**
   (0→2.57→2.68→3.03→3.27).
3. 최종: **완전히 이완한 결과를 한 번 구하고 원본과 선형 보간** → 0→0.77→1.60→2.43→3.27 (선형).

**위치 취득은 `cmds.xform(q, ws, translation)` 하나로 통일** (mayapy 확인):
트랜스폼/조인트/버텍스/CV/래티스는 3개, **엣지는 6개·페이스는 12개**가 나온다 → 평균(중심).
`cmds.pointPosition` 은 **엣지/페이스에서 에러**라 못 쓴다.

**함정**: UI 에서 생성 후 `cmds.select` 를 `undo_chunk` **밖**에서 하면 Ctrl+Z 가 커브가 아니라
선택만 되돌린다 → 생성+선택을 같은 청크로. (Wrap 탭의 `setAttr` 과 같은 부류의 실수)

검증: mayapy 2024 코어 34 + UI 20. 같은 툴: [[wip-a00400-curve-wrap]], [[wip-a00400-curvetool]]
