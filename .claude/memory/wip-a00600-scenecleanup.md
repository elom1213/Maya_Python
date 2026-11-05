---
name: wip-a00600-scenecleanup
description: A00600_SceneCleanup - 체크한 항목대로 씬 정리(레이어 · 애니 레이어 루트까지 · Hypershade Delete Unused), 항목 레지스트리
metadata:
  type: project
---

2026-11-05 v01.00 새 툴. 항목 = `app/core/cleanup_items.ITEMS` 에 클래스 하나씩(UI 는 ITEMS 를 읽는다), 정리 함수는
공용 `Framework/core/maya_cleanup.py`. 창을 열 때마다 전부 체크(기억 안 함 - 사용자 요구 "모두 체크").

- 사용자 결정: 머티리얼 정리 = **Hypershade Delete Unused Nodes 와 똑같이** → MEL `MLdeleteUnused` 그대로(mayapy 는 `source "MLdeleteUnused.mel"` 필요).
- 사용자 결정: **BaseAnimation 이 마야에 안 보이게** → `animLayer -q -root` 를 delete. 자식만 지우면 BaseAnimation 이 홀로 남는다.
  레퍼런스 애니 레이어가 있으면 루트를 못 지움 → 경고. 지운 뒤 Layer Editor 는 `updateAnimLayerEditor("AnimLayerTab")`.
- A00210 `ref_importer` 의 같은 규칙 코드는 아직 공용 모듈로 안 옮김(다른 툴 수정이라 요청 시).
- 시험 33/33, **GUI 확인 아직**. 새 항목 후보는 사용자가 계속 추가 예정.

**Why:** 사용자가 정리 항목이 계속 늘어난다고 함 → 항목 추가가 UI 수정 없이 되도록.
**How to apply:** 새 항목 요청 = 클래스 + ITEMS 한 줄 + maya_cleanup 함수 + 시험. 관련 [[wip-a00110-layer-range-merge]] (애니 레이어 합치기는 A00110).
