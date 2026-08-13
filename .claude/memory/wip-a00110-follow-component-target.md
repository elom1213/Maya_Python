---
name: wip-a00110-follow-component-target
description: A00110 Follow 탭 Target 에 메시 버텍스 등 컴포넌트 지원 — worldMatrix 가 없어 위치+노말로 행렬 생성, 프레임 이동 필요 (v01.41)
metadata:
  node_type: memory
  type: project
---

A00110_animTool **Follow 탭 Target 에 컴포넌트(메시 버텍스 등) 지원** (v01.40→**01.41**, 2026-08-13).

**전에는 죽었다**: `_matched_state` 가 `getAttr("mesh.vtx[5].worldMatrix[0]")` 를 부르는데 컴포넌트에는
worldMatrix 가 없어 **ValueError** 로 베이크 전체가 중단. `objExists("mesh.vtx[5]")` 는 **True** 라
앞단 가드를 그냥 통과한다.

**해결** (`_target_matrix`):
- **메시 버텍스** — 위치 = `MFnMesh.getPoint(kWorld)`, 회전 = **정점 노말을 +Y 로 삼는 직교 프레임**
  (A00145 Match 탭과 같은 규약), 스케일 1.
- **그 밖의 컴포넌트(커브 CV 등)** — 위치만 `pointPosition`, 회전/스케일은 소유 오브젝트 worldMatrix.

**마야 함정 2개**
- 컴포넌트 위치는 **`getAttr(..., time=t)` 로 시점 조회가 안 된다**. 디폼되는 메시를 따라가려면
  프레임을 실제로 옮겨(`currentTime`) 읽어야 한다. 컴포넌트 타겟일 때만 옮기고 원래 시간은 복원.
- **`cmds.ls("mesh.vtx[99999]")` 는 에러가 아니라 마지막 정점으로 조용히 클램프**해서 돌려준다
  (실측: `vtx[13]`). 유효성 판정은 **돌려받은 이름이 요청과 같은지**로 해야 한다.

검증: 코어 18 + UI 6 항목([[mayapy-headless-verify]]), 오브젝트 타겟 회귀 포함.
