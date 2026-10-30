---
name: wip-a00110-anim-layers
description: A00110_animTool_V02 v02.31 View > Layers - 씬 애니메이션 레이어 목록 · 행 클릭 = 선택 + 활성(preferred 는 마야가 안 꺼 줘 직접 하나로) · Mute/Solo/Lock 체크 · Graph Editor 필터 버튼 · Expand 별도 창 · 레이어 변경 이벤트가 없어 QTimer 폴링
metadata:
  type: project
---

**A00110_animTool_V02 v02.31 (2026-10-30) View > Layers** — 사용자: "씬의 애니메이션 레이어가 리스트업되고 어떤 레이어를 볼지 선택,
Curve > Filters 처럼 Expand 로 따로 창". `app/core/anim_layer_manager.py` + `main_window._build_layers_page`, 시험 `tests/test_anim_layers.py` 33.

- **목록 순서** = 레이어 에디터: root 직계 `animLayer -q -children` 은 바닥부터라 **뒤집어** 맨 위부터, 자식 레이어는 부모 아래 들여쓰기(QTreeWidget),
  BaseAnimation 맨 아래. 상태는 Merge Layers 의 `LayerMergeManager.layer_info` 재사용 + `preferred`.
- **행 클릭 = 어느 레이어를 볼지**: `animLayer -e -selected` 로 선택, 하나면 활성(preferred). ★ **마야 `preferred=True` 는 다른 레이어의
  preferred 를 끄지 않는다**(실측: L2 활성 뒤 L1 preferred=True → 둘 다 True) → 툴이 전 레이어를 돌며 하나로 맞춘다. 전부 해제는 마야에 반영 안 함.
  그래프 에디터가 그 레이어 커브만 보이려면 필터가 `selected` → `Graph Editor: Selected Only` 버튼(`GraphViewManager.apply_editor_layer_filter`).
- **Mute / Solo / Lock** = 체크 열(`setCheckState` 는 열마다 따로 → Base 는 Lock 열에만 체크박스). BaseAnimation mute/solo 는 거부.
- ★ **레이어 변경 이벤트가 없다** — `scriptJob(listEvents=True)` 에 anim layer 이벤트 없음(standalone 에서는 None) → 보이는 동안
  1.5 s `QTimer` 로 `snapshot()`(이름 · depth · 플래그 · 선택 · 활성) 비교해 새로고침. `isVisible()` 아니면 건너뛴다(탭이 숨으면 비용 0).
- Expand = 공용 `JUN_mod_expand_qt_v01`(이동이라 트리 한 벌, `tw.window()` 가 확장 창으로 바뀌고 collapse 로 복귀) — [[framework-expand-widget]].
- GUI 확인 아직. 관련: [[wip-a00110-layer-range-merge]] [[wip-a00110-graph-focus]] [[animlayer-no-global-selected-query]]
