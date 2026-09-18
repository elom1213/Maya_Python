---
name: wip-a00380-match-by-weight
description: A00380 Match > By Weight (v01.09) — 스킨 웨이트 마스크로 M_j 를 M_tgt 쪽으로, 짝짓기 기본은 joint k -> mesh k
metadata:
  type: project
---

A00380_MeshTool v01.09 (2026-09-18): Match 탭을 하위 탭 **Default**(기존 Match) / **By Weight** 로 나눴다.
코어 `app/core/weight_match_manager.py`.

- `new = cur + mask × Strength × (M_tgt − cur)`, 오브젝트 공간 · 버텍스 인덱스 대응 (블렌드셰이프 웨이트 맵과 같은 결과).
- mask = M_w 스킨 웨이트(`MFnSkinCluster.getWeights` 한 번) 중 짝지은 조인트의 합, 1 로 자름.
- 짝짓기: 사용자의 예시(jnt_01 ↔ M_01)를 따라 **Joint k -> Mesh k** 를 기본으로, **Sum -> every mesh** 를 옵션으로 뒀다 — 요청문만으로는 어느 쪽인지 확정되지 않아 둘 다 넣었다.
- 이동은 Match 의 `MatchTarget` 재사용: `weights` 자리에 소프트 셀렉션 대신 마스크를 넣고 `commit(strength)`.
- 창 크기: 테마 qss 에서 QRadioButton 하나가 245px 라 한 줄에 둘이면 창 폭을 넘는다. `minimumSizeHint` 는 show 직후엔 폴리시 전 값(401)이라 `processEvents` 뒤에 다시 재야 한다(386).

**Why:** 조인트별로 영역을 쪼갠 코렉티브를 만드는 흐름.
**How to apply:** 사용자가 짝짓기 방식을 다르게 원하면(예: 메시마다 조인트 여러 개) 여기부터 고친다. 관련 [[wip-a00380-match-tab]] · [[offscreen-size-needs-theme]]
