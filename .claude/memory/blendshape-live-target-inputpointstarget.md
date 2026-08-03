---
name: blendshape-live-target-inputpointstarget
description: live 타겟(inputGeomTarget 연결)에서 inputPointsTarget setAttr 은 조용히 무시된다 — 타겟 메시를 옮겨야 함
metadata: 
  node_type: memory
  type: reference
  originSessionId: 85c8852e-52d8-4514-9afa-b44bf5d7ef96
  modified: 2026-08-03T01:01:42.183Z
---

blendShape 타겟 메시가 씬에 남아 `inputTargetItem[i].inputGeomTarget` 으로 **연결(live)** 돼 있으면,
`inputPointsTarget` 은 **연결된 메시에서 매번 다시 계산되는 값**이다. 여기에 `setAttr` 하면
**에러도 경고도 없이** 다음 평가(dgdirty/저장/sculptTarget 진입)에서 **원래 값으로 되돌아간다**.
타겟 메시를 지운 **baked** 타겟에서는 `setAttr` 이 정상적으로 먹고 저장에도 살아남는다.

**Why:** A00290 Base Shape 의 Apply 가 "적용된 것처럼 보이다가 저장/Edit 하면 원복"되던 원인.
포인트 수가 0 이 아니라 성공으로 집계돼 **성공 보고만 하고 아무 일도 안 하는** 상태였다.
(mayapy 실측: 99 로 setAttr → getAttr 은 99 를 주지만 `dgdirty` 후 5.0 복귀)

**How to apply:**
- 델타를 바꾸려면 **아이템마다** `listConnections(item + ".inputGeomTarget", s=True, d=False, shapes=True)`
  로 live/baked 를 판정할 것. in-between 은 아이템마다 다른 메시에 연결될 수 있다.
- live 면 **타겟 메시의 정점을 직접 옮긴다**. 델타는 `worldMesh` 로 연결돼 있어도, base/target
  transform 이 서로 달라도 **오브젝트 공간**(`타겟 로컬 − 베이스 원본 로컬`)이다 →
  `(factor-1) * delta` 만큼 **오브젝트 공간 상대 이동**. 월드로 옮기면 회전·스케일 있는 타겟에서 깨진다.
- 이동은 `shape.pnts`(tweak) **구간 setAttr** 로(19,462 정점 xform 루프 6.4초 → 0.17초).
  기존 tweak 읽기는 `getAttr(".pnts")` 가 "compound with mixed type elements" 로 실패하니
  `MPlug.getExistingArrayAttributeIndices()` 사용 — [[wip-a00380-meshtool-peak]] 와 같은 패턴.
- `sculptTarget` 은 라이브 메시를 만들지 않는다(`sculptTargetIndex` 만 씀) — Edit 모드 자체가
  원인이 아니라 **재평가를 유발하는 계기**일 뿐이다.

관련: [[wip-a00290-shape-editor-tab]], [[wip-a00380-meshtool-peak]], [[mayapy-headless-verify]]
