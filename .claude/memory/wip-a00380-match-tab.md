---
name: wip-a00380-match-tab
description: "A00380_MeshTool v01.01 Match tab — Kangaroo Geometry>Match 재현(인덱스 대응 버텍스 스냅 + soft falloff), 코어 headless 검증, Maya 실기 테스트 대기"
metadata: 
  node_type: memory
  type: project
  originSessionId: 69c25012-610a-4113-b9c9-4458ca7059e9
  modified: 2026-07-23T02:03:41.611Z
---

A00380_MeshTool v01.00→**01.03** — **Match 탭**(v01.01) + **Auto-load 편집 원상복구 버그 수정**(v01.02)
+ **Match 흐름 단순화**(v01.03). **DONE (코어 headless 통과 + Maya 실기 확인 + pushed).**

**v01.03 흐름 단순화**: 사용자 요청 — "Load Target Selection 없이 메시만 선택하고 Apply Match" 하면 되게.
Target 박스(lb_match_target/btn_match_load/btn_match_clear) 제거. Apply(또는 Weight 슬라이더 sliderPressed)
시점에 `_match_build()` 가 **현재 씬 선택**으로 세션을 즉석 생성. **백그라운드 scriptJob 없음** → v01.02
clobber 위험 재도입 안 함. Weight 라이브 미리보기 유지(슬라이더 잡는 순간 스냅샷). Apply 는
`self.match_session or self._match_build()` 로 미리보기 세션 재사용 or 신규. 확정 후 세션 None(다음 Apply 는
새 선택). update_match_state/on_match_load/on_match_clear 삭제, 위젯 상시 활성.

**v01.02 버그 수정 (중요)**: "A00380 을 띄워둔 채 씬 메시의 버텍스를 손으로 옮기면 편집이 원상복구됨."
원인 = Peak 탭 **Auto load** scriptJob 이 선택 변경마다 `on_load`→`discard_preview`→`session.restore()` 를
**무조건** 호출. restore 가 로드 시점 스냅샷(base_tweaks)을 `.pnts` 에 다시 써, 슬라이더를 안 건드려도
사용자 수동 편집을 덮어씀(v01.00 부터 잠복). **해결**: `_preview_dirty` 플래그 — amount≠0 미리보기를
쓸 때만 True, load/commit/restore 후 False. `discard_preview` 는 dirty 일 때만 restore. Match 도 동일
(`_match_preview_dirty`). mayapy 로 근본원인·수정 재현 검증(test_clobber): restore 가 편집 덮어씀 확인 →
가드 시 보존 → 재스냅샷이 편집 포착 → 실제 미리보기는 여전히 제거. **UI 는 headless 불가라 마야 실기 확인.**

**무엇**: [[kangaroo-plugin-external-readonly]] 의 Geometry > Match(`setModelVerts`)를 Kangaroo 없이 재현.
리스트업한 **From 메시의 같은 인덱스 버텍스 위치**로 현재 선택한 메시의 버텍스를 이동. 소프트 셀렉션
falloff 반영. 대응은 closest-point 가 아니라 **버텍스 인덱스**(두 메시 토폴로지 동일 가정).

**수식**: `final_local = orig_local + softw·weight·(from_local - orig_local)`. weight 0~1(전체 블렌드),
softw=소프트셀렉션 가중치. World 모드는 From 을 getPoints(kWorld)로 읽고 대상의
`inclusiveMatrixInverse()`로 역변환 → 대상 버텍스가 From 의 월드 위치에 안착. Object 모드는 로컬 직접 매칭.

**핵심 설계**: Peak(`peak_manager`)의 공용 헬퍼(`_undo_disabled`, `_selection_map`, `_dag_path`,
`_soft_weights`, `_contiguous_runs`, `_shape_of`)와 preview/restore/commit + `shape.pnts` 구간 setAttr
모델을 **그대로 재사용**(match_manager 가 import). Peak 과 유일한 차이 = 이동량: 로드 시점에
`delta[i]=(from_local-orig_local)` 를 버텍스별로 얼려두고 미리보기에서 `weight×softw`만 곱한다.
tweak 누적 방식이라 `new_tweak = base_tweak + delta·weight·softw`, weight=1·softw=1이면 orig 상쇄되어
정확히 from_local 에 안착.

**UI**: main_window 에 build_match_tab + on_match_* 핸들러. From=TSL(`JUN_mod_tsl_qt_v01`, 첫 항목 사용),
Target=현재 선택(Load Target Selection, auto-load 없음), 옵션 World space/Respect soft, Weight 슬라이더(0~1,
기본 1.0)+스핀박스, Apply/Reset. **탭 전환 시 양쪽 미확정 미리보기 discard**(둘 다 pnts 에 써서 겹침 방지),
close 에서도 discard. Peak 세션과 독립(`self.match_session`, `self._match_syncing`).

**검증**: match_manager 코어 mayapy headless 9개 시나리오 통과 — world/object 매칭, weight 0.5 블렌드,
restore, 단일 undo, 부분 선택, **소프트 falloff**, 토폴로지 불일치(overlap만 이동+skip 보고), From 자기제외.
**UI 위젯 구성은 mayapy 스탠드얼론 크래시(exit 127)로 헤들리스 불가 → 마야 실기 확인 필요**([[wip-a00110-stagger-offset]] 와 동일 한계).

**파일**: `app/core/match_manager.py` 신규, `app/ui/main_window.py`(탭+핸들러+탭전환/close discard),
`app/config/version.py`(01.01/2026-07-23), `docs/A00380_MeshTool.md`(3-2 Match 절 + 구현메모).

관련: [[mayapy-headless-verify]], [[undo-chunk-by-default]], [[ui-text-english-only]],
[[prefer-pyside-for-new-tools]], [[push-includes-tool-guide-docs]].
