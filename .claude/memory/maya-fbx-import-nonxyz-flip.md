---
name: maya-fbx-import-nonxyz-flip
description: Maya FBX importer flips rotation keys of non-XYZ rotateOrder joints (uses XYZ Euler-equivalent formula) - all 3 quaternion modes; fix = rewrite curves from raw FBX keys
metadata:
  type: project
---

마야 2024 FBX 임포터(플러그인 2020.3.4)는 회전 키를 이전 키에 가까운 동치 오일러로 바꿀 때 **rotateOrder 를 무시하고
XYZ 동치 `(x+180, 180-y, z+180)`** 을 쓴다. XZY 등 비 XYZ 조인트에서 값이 ±180 근처를 넘나들면 **자세 자체가 틀린다**
(Vicon 모캡 `BCM_01_004.fbx`: CHOEUN Hips 1-5493f, RightArm 3707-6285f, 월드 최대 200cm). `FBXImportQuaternion`
euler · resample(기본) · quaternion 셋 다 틀리고, 끄는 옵션이 없고, 틀린 구간이 연속이라 Euler Filter 로도 못 고친다.
블렌더 경유는 방향은 맞지만 키 감소로 최대 1.27cm 손실.

**Why:** 2026-10-27 mayapy 실측(FBX 직접 파싱 정답 비교 · 전수 조사). 계획서 `JUN_All/docs/plans/A00480_FileTool_fbx_exact_import_plan.md`.

**구현(2026-10-27):** A00480_FileTool v01.13 Import > FBX `Mocap FBX Import (Exact Rotation)` · `Fix Scene From FBX`,
코어 `Framework/core/maya_fbx_exact.py`(+ `fbx_binary` · `euler_math`). 마야 GUI · Maya 2023 실기 확인 아직.

**How to apply:** 모캡 FBX 가 마야에서 이상하게 들어오면 이 버그부터 의심하고 위 기능을 쓴다. 해법은 임포트(euler 모드) 뒤 원본 `Lcl Rotation` 키로
커브를 `MFnAnimCurve.addKeys` 로 다시 쓰고, 언랩은 순서별 동치 `(first+180, 180-middle, last+180)` + 2π 로 한다.
이 PC 의 numpy 는 Maya 번들이 아니라 사용자 site-packages 라 in-Maya 코어는 numpy 없이. 관련 [[fbx-export-selected-scope]]
