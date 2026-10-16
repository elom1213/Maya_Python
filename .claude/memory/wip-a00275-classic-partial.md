---
name: wip-a00275-classic-partial
description: A00275 Weights > Classic Native = selected vertices only (v01.36) - selection rules for Joints to Joints / Meshes to Meshes
metadata:
  type: project
---

2026-10-16 v01.36: `Weights > Classic` 의 **Native** 엔진이 선택 버텍스만 처리한다 (Kangaroo 는 손대지 않음).

- 선택 파싱은 Transfer 탭 것(`weight_transfer_manager.parse_target_selections`) 재사용 - 엣지/페이스는 버텍스로, 소프트 셀렉션은 falloff.
- Joints to Joints: `_native_move_columns(vtx_ids, soft)` 가 선택 버텍스만 get/setWeights.
- Meshes to Meshes: 판단은 **To 메시 기준**. To 에 버텍스 → 부분(skinCluster 유지, `_transfer_one_native(surface_association=...)`),
  To 통째 → 전체, 선택 안 한 To → Skipped. **어느 To 에도 컴포넌트 선택이 없으면 예전처럼 전부 전체** (From 메시 버텍스만 고른 경우 포함).

**Why:** 사용자 요청 "선택한 버텍스만 웨이트 전이". 미선택 쌍을 건너뛰는 규칙은 내가 정한 것 - 사용자 피드백이 오면 여기 고칠 것.
**How to apply:** Classic 부분 전이를 바꿀 때 Transfer 탭 코드와 공유됨을 의식([[wip-a00275-transfer-tab]]). GUI · 소프트 셀렉션은 미확인.
