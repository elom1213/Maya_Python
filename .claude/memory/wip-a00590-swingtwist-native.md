---
name: wip-a00590-swingtwist-native
description: "A00590_SwingTwistNative v01.00 — MetaHuman SwingTwistEvaluatorNode 를 quatNodes 망으로(골든 2e-13°), Build/Rigs 만 · Convert §9 · Container §10 은 다음 단계, swing blend 1 ≠ 영향 없음"
metadata:
  node_type: memory
  type: project
  originSessionId: 3b72b09f-82c3-4ab7-acb4-add90da912f7
  modified: 2026-11-13T00:00:00.000Z
---

2026-11-03 검토 · 계획서 `JUN_All/docs/plans/A00590_SwingTwistNative_plan.md`. **2026-11-13 v01.00 구현**: 코어 `Framework/core/maya_swing_twist.py`(`build` · 홀더 · `read_holder` · `delete_rig`) + 툴 `tools/A00590_SwingTwistNative`(Build · Rigs 탭). 시험 golden 16/16(원본 플러그인 나란히) · tool 46/46. **GUI 확인 아직.**

**다음 단계(사용자: 급하지 않음)**: §9 Convert(기존 원본 노드 → 망, Restore 포함) · §10 Container(망 하나 = container 하나, 블렌드 publishAndBind, blackBox). 실제 MetaHuman 씬 · DNA export 사용 여부는 §9 때 다시 묻는다.

원본: `~/Documents/maya/modules/MetaHumanForMaya/lib/SwingTwistEvaluatorPlugin/1.3.2/platform-windows/maya-<ver>/lib/*.mll` (2023~2026 있음). 연결 방식은 같은 모듈의 `mh_pose_editor/model/swing_twist.py`.
- 입력 `startJoint`/`endJoint` = 조인트 `.rotate`, `swingBlend`, `twistBlend[i].values`, `fromEnd`. 출력 `swing`, `twists[]`.
- **트위스트 축 X 고정, 오일러 XYZ 고정(rotateOrder 무시), jointOrient 무시.**
- 수식 = UE RigLogic `TwistSwingJointsEvaluator.h`: twist = normalize(x,0,0,w), swingOut = invTwist * slerp(inv(q*invTwist), I, sb), twist_i = slerp(base, I, tb_i), base = invTwist 또는 fromEnd 면 twist(end)(역회전 아님).
- ★ **블렌드 의미**: twist 0 = 시작 트위스트 상쇄, 1 = 회전 0. **swing 0 = 시작 회전 전체 상쇄, 1 = 트위스트만 상쇄(invTwist, 0 이 아님)** — 처음엔 "1 = 영향 없음" 이라 잘못 적었다(11-13 시험에서 발견).
- quatNodes 함정: `quatSlerp.input2Quat` 기본값 (0,0,0,0) → identity 로 쓰려면 W=1 을 직접. 기본 angleInterpolation = Shortest(원본과 같음). joint.rotate → eulerToQuat.inputRotate 는 unitConversion 없이 직결.
- `.ma` 의 `requires` 는 `-nodeType ...` 줄과 `"quatNodes"` 가 다른 줄로 나뉜다(문자열 검사 주의).

**Why:** 사용자가 에픽 플러그인 의존을 없애려 한다.
**How to apply:** 다음 단계는 계획서 §9 · §10. ★ Pose Editor DNA export 는 `ls(type="SwingTwistEvaluatorNode")` 로 찾으므로 변환 씬에선 swing/twist 가 빠진다 → Restore 필요. [[maya-2023-compat]](코어 sin/cos 없음 → quatNodes 사용)
