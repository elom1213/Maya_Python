---
name: wip-a00610-pmximporter
description: "A00610_PmxImporter - PMX(MMD) direct import into Maya; user decisions, append(fuyo) order via rotateAxis, Blender mmd_tools golden traps, next steps"
metadata:
  node_type: memory
  type: project
  originSessionId: a9d7bd20-6410-453e-9d1a-03779fdc3ff3
  modified: 2026-11-09T02:41:55.165Z
---

`tools/A00610_PmxImporter` v01.01 (2026-11-09). 계획서 `docs/plans/A00610_PmxImporter_plan.md`(§13 결정 · §14 PMX 의 나머지 데이터 · §15 2차 1단계), 안내 `docs/A00610_PmxImporter.md`.

- **사용자 결정(2026-11-09)**: 이름 = PMX 고유(일본어) 이름 + FBXASC · lambert 고정 · IK 본 생성 · **IK 근사 ikHandle 기본 켬 · 로컬축 jointOrient 기본 켬** · 외곽선/툰/스피어 보류.
- 변환(기준 mb `021_Miyabi/00_01_03_RIG_01_PJ/scenes/0010_Miyabi_base_02.mb` 와 숫자 대조): 위치 `(x,y,-z)×8` cm · UV `(u,1-v)` · 삼각형 `(c,b,a)` · 정점 순서 = PMX.
- **부여(付与) 순서 = 부여 먼저, 자기 회전 나중**(three.js GrantSolver `bone.quaternion.multiply(slerp)` 원문 확인) → 마야는 `rotateAxis = W·Append·W⁻¹`(rotateAxis 가 rotate 보다 먼저). offsetParentMatrix 는 순서가 반대라 버렸다.
- **Blender mmd_tools 는 정답 기준으로 쓸 수 있지만 함정**: 부여를 오일러 TRANSFORM 으로 근사(축 섞이면 0.3 cm 어긋남 → MMD 규칙 직접 검사) · IK 끌 땐 LIMIT_ROTATION 도 끌 것(아니면 레스트 71 cm 어긋남) · `pose_bone.matrix` 대입은 부여를 두 번 넣음 → basis(BoneConverter.convert_rotation)로 포즈. `tests/blender_mmd_reference.py`.
- 텍스처 · 문자열 함정 — [[maya-codepage-nonascii-traps]]. 모델 파일은 저장소에 넣지 않는다(재배포 금지), `A00610_SAMPLE_DIR` · `A00610_BLENDER` · `A00610_CATS_ZIP`.
- 번호 충돌 이력: 다른 세션이 같은 A00610 으로 계획을 3분 먼저 커밋 → 그쪽이 A00620. 새 번호는 커밋 직전에 다시 확인.
- 남은 것: GUI 실기 확인, 이동/로컬 부여 · IK 각도 제한 · 그룹/본/재질 모프 · 물리.

**Why:** CATS(블렌더) → FBX → 마야 손질 과정을 없애려는 툴. **How to apply:** 고칠 때 골든(기준 mb + Blender) 시험을 함께 돌린다.
