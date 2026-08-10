---
name: wip-a00145-attr-name-matching
description: A00145 Match from Source — 이름 유사 어트리뷰트 검색(토큰 역색인 + IDF). 1000x1000 = 0.15s (v01.21)
metadata: 
  node_type: memory
  type: project
  originSessionId: ee81a66a-5136-4bb8-b44a-7fa187164cdb
  modified: 2026-08-10T02:10:01.788Z
---

A00145_RigConnect **Connect 탭 Destination 패널의 `Match from Source`** (v01.20→**01.21**, 2026-08-10).

소스 어트리뷰트 각각에 대해 이름이 가장 비슷한 destination 어트리뷰트를 찾아 **소스 순서 그대로**
목록 맨 위로 올리고 선택한다. `connect_attrs` 가 `src[i] ↔ dst[i]` 를 **순서로** 짝지으므로 그대로
Connect 로 이어진다. 옵션: `Unique`(기본 ON) / `Min`(coverage 하한, 기본 0.40).

구현: `app/core/attr_match.py` — **maya import 없는 순수 파이썬**(DCC 없이 단독 테스트/벤치마크 가능).
알고리즘과 복잡도 근거는 [[attr-name-matching-token-index]] 참고.

- 찾은 것 = 목록 앞으로, 나머지는 원래 순서대로 뒤에. destination 필터는 자동으로 비운다
  (선택이 필터에 가려지면 `visible_selected` 에서 빠져 연결 대상에서 사라진다).
- 소스에서 아무것도 선택 안 했으면 **보이는 소스 전체**를 질의로 쓴다.
- 동점 후보가 더 있으면 `ambiguous` 플래그 → 로그에 표시(이름만으로는 못 가렸다는 뜻).
  예: `translateX` 는 `rotatePivotTranslateX` 와 coverage 가 똑같이 1.0 이고 가산점으로 갈린다.

검증: 요청 예시 그대로 · 순서 보존 · camelCase↔snake · unique · 문턱 미달 보고 · 폴백 ·
브루트포스 교차검증 · 1000/2000/5000 벤치마크 + UI 스모크(매칭→실제 connectAttr 까지) 전부 통과.
