---
name: wip-a00275-layer-tab
description: A00275 Weights > Layer (v01.22) — 같은 버텍스 순서 메시 N 개의 웨이트를 lock + Blend 로 레이어 합성(위 우선, lock 절대값, 넘친 곳만 잘림, 모자라면 재정규화). setWeights 는 undo 안 됨 → 구간 setAttr, bindPreMatrix 는 소스에서 복사
metadata:
  type: project
---

A00275_skinTool_V01 **Weights > Layer** (v01.21→**01.22**, 2026-09-15). 코어 `app/core/weight_layer_manager.py`,
UI 는 main_window 가 길어서 **`app/ui/layer_tab.py` 위젯 하나**(빌더는 `_build_layer_tab`).
계획서 `docs/plans/A00275_skinTool_V01_layer_tab_plan.md` (2장 식은 폐기된 규칙 ① — 실제는 가이드 문서).

**규칙은 사용자가 정했다(계획서 10장 답).** 위 레이어부터 `c = Blend x lock 웨이트`(절대값)를 넣고,
남은 몫 `cap` 을 넘는 레이어만 `cap/합` 배로 줄인다. 끝에 cap 이 남으면 재정규화. lock 이 0 인 버텍스는
아래 행이 그대로 옮겨진다. 베이스는 lock 없으면 전 조인트, lock 걸면 그것만(+재정규화).
처음 제안한 규칙 ①(남은 몫에 곱하기)은 **메시 2개일 땐 같은 답**이고 3개 이상에서 갈린다 — 사용자는 ② 선택.

- **★ `MFnSkinCluster.setWeights` 는 undo 기록에 안 남는다** — 청크 안에서 써도 undo 가
  "no more commands" (그 전 기록이 있으면 **엉뚱하게 skinCluster 생성을 되돌린다**). "기존 메시 갱신"
  모드가 Ctrl+Z 로 돌아와야 해서 버텍스마다 구간 `setAttr weightList[v].weights[lo:hi]` —
  19,881×8 에 0.57s, undo 0.27s, normalizeWeights on 이어도 값 그대로. **구간은 새 값 + 기존 값 인덱스를
  모두 덮어야** 예전 웨이트가 안 남는다(기존 값은 getWeights 한 번). [[skincluster-weight-index-physical]]
- **★ 새로 바인드하면 지금 포즈가 바인드 포즈** → 포즈 중 Merge 하면 튐. `bindPreMatrix` 를 그 조인트를
  가진 가장 위 레이어에서 복사, `geomMatrix` 는 베이스. 포즈 상태면 생성 시 만든 bindPose 는 떼어 지움.
  포즈 후/포즈 중 Merge 모두 lock=1 영역이 M_01, 0 영역이 M_02 변형과 1e-4 이내 일치.
- 형상은 **베이스 skinCluster 의 input[gi].inputGeometry 를 새 mesh inMesh 에 연결→dgeval→끊기**(rest).
- **★ Lock 트리 항목에 `ItemIsUserCheckable` 을 주면 한 번 클릭에 두 번 토글**(델리게이트가 release 에서
  또 뒤집음). 플래그 없이 체크 상태만 두고 트리 mousePress 에서 직접 전환, 선택된 행 전부 적용, 선택 유지
  ([[qtreewidgetitem-checkable-default-flag]]). Shape Editor 다중 편집 조작과 맞췄다([[wip-a00290-shape-editor-tab]]).
- 검증: 코어 47항목(Q1/Q2/Q3 숫자, 2레이어 전 버텍스 식, 순서 영향, 포즈 Merge 디포메이션, update 듬성한
  인덱스 + undo 정확 복원, 공유 조인트 합산, 비정규 입력, 에러 5종, fallback, 19,881×3 레이어 1.0s)
  + UI 33항목(QTest 실제 클릭: Shift/Ctrl 선택, Lock 칸 한 번 = 선택 전부 한 번 토글·선택 유지, Space,
  필터 보이는 행만, Blend 스핀/슬라이더, Create/Update Merge, Up/Down 시 base 표시).
- **★ `QTreeWidgetItem.setSelected(True)` 는 SingleSelection 이어도 다른 줄을 해제하지 않는다** — 코드로
  줄을 고르면 두 줄이 선택된 채 남아 엉뚱한 레이어가 '현재' 가 됐다. `setCurrentItem` 으로 고른다.
- 실제 마야 GUI 확인은 사용자 몫(대기).
