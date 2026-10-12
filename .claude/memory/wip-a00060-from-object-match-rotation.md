---
name: wip-a00060-from-object-match-rotation
description: "A00060_jointTool_V03 v03.14 — Create > From Object 의 Match Rotation 체크박스(Separate 만, 기본 꺼짐): 분리 조인트에 오브젝트 월드 회전을 jointOrient 로 주는 방법"
metadata:
  node_type: memory
  type: project
  originSessionId: 042dc05b-37df-4abd-b775-d917cf9a7c8b
  modified: 2026-10-12T01:58:40.384Z
---

2026-10-12 사용자 요청: "From Object 탭의 Separate 상태에서 오브젝트의 회전값과 일치하도록 조인트가 생성되는 체크박스,
기본은 꺼짐" (v03.13 → 03.14).

- UI: Connect / Separate 라디오 줄에 `Match Rotation` 체크박스. **Separate 일 때만 활성**(`QButtonGroup.buttonToggled`),
  Connect 는 체인 방향으로 orient 되므로 무시한다. 기본 꺼짐.
- 코어 `obj_joint_manager.joints_to_objs(..., match_rotation=False)` → `_match_world_rotation(jnt, obj)`:
  `xform(jnt, ws=True, rotation=xform(obj, q, ws, rotation))` 뒤 **`makeIdentity(jnt, apply=True, rotate=True)`** 로
  rotate → jointOrient 에 굳힌다. 루트(월드 부모) 조인트라 월드 오일러가 그대로 jointOrient 가 된다.
  회전·이동된 그룹 아래 오브젝트도 월드 행렬이 일치했다(mayapy 실측). 컴포넌트(`.vtx[n]`)는 회전이 없어 건너뛴다.
- 생성 직후의 `joint -e -oj xyz -sao yup` 는 자식이 없어 0 이라 덮어써도 문제없다.

관련: [[wip-a00060-world-space-joint-pos]], [[wip-a00060-aim-root-mode]]
