---
name: wip-a00145-component-followers
description: A00145 Match — Followers 에 컴포넌트(버텍스/CV)를 담아도 매칭. matchTransform 은 컴포넌트를 인자로 못 받는다
metadata:
  type: project
---

A00145_RigConnect **Match 탭의 Followers 에 컴포넌트**(메시 버텍스 `mesh.vtx[i]`, CV, 엣지,
페이스)를 담을 수 있다 (v01.35, 2026-08-31). 타겟은 종류를 안 가리고 그 **월드 위치**로 점을 옮긴다.

**Why:**
- `cmds.matchTransform(comp, tgt)` 는 **컴포넌트를 오브젝트로 세지 않는다** →
  `At least one source and one target object is needed to match transforms. Found 1.`
  타겟 쪽은 종류별로 갈라 놨는데(vertex/mesh/cluster/snapshot) **팔로워 쪽에 그 분기가 없어서**
  버텍스 팔로워가 늘 이 에러로 죽었다. 컴포넌트 팔로워는 `xform` 경로로 따로 가야 한다.
- **점이 여럿 걸린 컴포넌트(edge/face)에 절대 좌표를 주면 `xform` 이 그 점들을 한 자리로 뭉갠다.**
  중심 → 타겟의 **차이만큼 상대 이동**(`xform -ws -r -t`)해야 형태가 남는다. 점 하나면 절대 지정.
- 점에는 회전·스케일·부모가 없다. 조용히 무시하면 사용자는 왜 안 도는지 모른다 → notes 에
  **`NOTE_PREFIX`("note: ")** 표식을 붙여 UI 가 `[skip]` 이 아니라 `[note]` 로 찍는다
  (notes 채널이 하나뿐이라 정보성 줄이 실패처럼 보였다).

**How to apply:**
- 코어: `app/core/match_manager.py` — `_is_component()` · `_target_position()`(종류 무관 위치 1개:
  transform=rotatePivot, mesh=centroid, cluster=pivot, vertex/component=그 점, snapshot=캐시값) ·
  `_match_pos_component()` · `_match_one()` 맨 앞의 컴포넌트 팔로워 분기.
- 팔로워 종류를 판정할 때는 **스냅샷을 먼저** 거른다(`@cache ...` 텍스트에 `[` 가 들어 있다).
- 다른 툴에서도 "선택한 것을 어디에 맞춘다" 를 만들 때 **팔로워가 컴포넌트일 수 있는지** 먼저 본다.
- 관련: [[wip-a00145-match-one-to-many]] · [[wip-a00145-match-cache]] · [[pointposition-points-only]]
