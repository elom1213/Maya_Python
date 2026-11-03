---
name: wip-a00590-swingtwist-native
description: "MetaHuman SwingTwistEvaluatorNode 는 quatNodes 망으로 완벽 재현된다(실측 1e-13) — 노드 사양 · 수식 · 계획서 위치, 구현 전 사용자 확인 대기"
metadata:
  node_type: memory
  type: project
  originSessionId: 3b72b09f-82c3-4ab7-acb4-add90da912f7
  modified: 2026-11-03T08:31:59.608Z
---

2026-11-03 검토 완료, 계획서 `JUN_All/docs/plans/A00590_SwingTwistNative_plan.md`. **구현은 아직**(툴 위치 · MetaHuman 테스트 씬 · DNA export 사용 여부 · quatNodes 허용을 사용자에게 확인 중).

원본: `~/Documents/maya/modules/MetaHumanForMaya/lib/SwingTwistEvaluatorPlugin/1.3.2/` (노드 하나). 연결 방식은 같은 모듈의 `mh_pose_editor/model/swing_twist.py`.
- 입력 `startJoint`/`endJoint` = 조인트 `.rotate` (**도 단위**, unitConversion 자동), `swingBlend`, `twistBlend[].values`, `fromEnd`. 출력 `swing`, `twists[]`.
- **트위스트 축 X 고정, 오일러 XYZ 고정(rotateOrder 무시), jointOrient 무시.** `cmds.affects` 는 None 인데 평가는 정상.
- 수식 = UE RigLogic `TwistSwingJointsEvaluator.h`: twist = normalize(x,0,0,w), swingOut = invTwist * slerp(inv(q*invTwist), I, sb), twist_i = slerp(base, I, tb_i), base = invTwist 또는 fromEnd 면 twist(end)(역회전 아님). **blend 0 = 완전 상쇄, 1 = 영향 없음.**
- 재현: eulerToQuat → quatNormalize(X,W) → quatInvert → quatProd → quatSlerp → quatToEuler. 원본 대비 행렬 3e-15 · 오일러 값 3e-13°(같은 오일러 가지), x=w=0 특이점도 0.

**Why:** 사용자가 에픽 플러그인 의존을 없애려 한다.
**How to apply:** 구현할 때 계획서 §4~7 대로. ★ Pose Editor DNA export 는 `ls(type="SwingTwistEvaluatorNode")` 로 찾으므로 변환 씬에선 swing/twist 가 빠진다 → Restore 기능 필요. [[maya-2023-compat]](코어 sin/cos 없음 → quatNodes 사용)
