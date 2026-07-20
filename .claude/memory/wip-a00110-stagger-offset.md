---
name: wip-a00110-stagger-offset
description: "A00110_animTool v01.31 Stagger Offset — 리스트 순서대로 구간 키를 계단식 오프셋(스핀박스 실시간), Maya 실기 테스트 대기"
metadata: 
  node_type: memory
  type: project
  originSessionId: 69c25012-610a-4113-b9c9-4458ca7059e9
  modified: 2026-07-20T08:59:44.398Z
---

A00110_animTool v01.30→**01.32** — Key Edit 탭 5번째 접이식 섹션 **Stagger Offset** 추가.
**DONE (headless 39+20 check 통과 + Maya 실기 확인 + pushed).**

**v01.32 — Ctrl+Z 복구 + 슬라이더**: v01.31 은 미리보기를 undo 큐에 안 올려서 조절 후 **Ctrl+Z 가
안 먹었다**(무관한 이전 작업이 취소됨). → **settle 모델**: 세션이 `applied`(씬에 보이는 값)와
`settled`(undo 에 기록된 값)를 따로 들고, 조작이 멎으면(350ms 디바운스 / sliderReleased /
editingFinished) **undo 끈 채 settled 로 되돌린 뒤** undo 청크로 `settled→현재값` 한 번에 이동.
undo 는 *역연산을 현재 상태에 적용* 하므로 이 순서라야 Ctrl+Z 가 정확히 그 지점으로 온다.
→ 조작 1회 = undo 1개, 첫 조작이면 **Ctrl+Z = Reset**. `restore()` = `settle(0)` 로 통일.
**탐침(`scene_in_sync`)**: 사용자가 Ctrl+Z 를 누르면 씬≠세션 가정 → 첫 움직이는 항목(index>0)의
구간 내 첫 키가 `probe_base + index*applied` 에 있는지 확인, 어긋나면 **되돌리기 시도 없이 세션만
버린다**(잘못 알고 restore 하면 키가 엉뚱한 곳으로 밀림). UI 는 슬라이더+스핀박스
(**A00290_BSTool Shape Editor 패턴** — 같은 값의 두 얼굴, blockSignals 로 반대쪽 동기화), 슬라이더 ±60f.

리스트업한 컨트롤러의 `[Start, End]` 구간 키를 **리스트 순서 × Offset** 만큼 계단식으로 민다
(0번 제자리 / 1번 +1배 / 2번 +2배 …). 팔로우스루·웨이브용. 사용자 예시: ctl_01/02/03 모두 0~5f 키,
구간 0~5f, offset 3 → `[0,5] / [3,8] / [6,11]`.

**파일**: `app/core/stagger_offset_manager.py` 신규(`StaggerOffsetSession`), `app/ui/main_window.py`
(섹션 UI + `on_stagger_*` 핸들러 + closeEvent 복원), `app/core/__init__.py`, `version.py`,
`docs/A00110_animTool.md`, `WORKLOG.md`.

**설계 결정(재현 시 지켜야 할 것)**:
- **상대 이동만 사용** — `cmds.keyframe(..., relative=True, timeChange=)`. `cutKey`+`setKeyframe` 로
  커브를 재생성하면 **애님 레이어 소속이 바뀔 수 있고** 탄젠트/인피니티 복원 코드가 필요해진다.
  상대 이동은 그 전부를 마야가 알아서 보존한다. (headless 로 탄젠트·weighted 보존 확인함)
- **비누적 실시간**: 세션이 `applied` 를 들고 **차이(delta)만** 이동. i 번째 키는 항상
  `[Start+i·applied, End+i·applied]` 에 있으므로 `i·delta` 를 밀면 정확히 `[Start+i·new, …]`.
- **undo**: 미리보기는 `undoInfo(stateWithoutFlush=False)`, commit 은 **restore-before-commit**
  → Ctrl+Z 한 번. [[wip-a00380-meshtool-peak]] 에서 검증한 패턴 그대로.
- **인덱스 보존**: 씬에 없거나 키 없는 항목은 제외하되 `entries=[(원래 index, obj)]` 로 **리스트
  위치를 배수로 유지** — 제외 항목 때문에 뒤 항목 배수가 당겨지면 사용자가 예상한 결과와 어긋난다.
- **덮어쓰기**: 구간 밖 키는 밀려온 키에 덮일 수 있어 세션 생성 시 검사→로그 WARNING.
  Apply 결과는 Ctrl+Z 로 복구되지만 미리보기 중 Reset 은 덮인 키를 못 살린다.
- 세션 무효화 훅은 `st_tsl.list_widget.model().rowsInserted/rowsRemoved/modelReset` —
  TSL 의 `set_items` 가 거는 `blockSignals` 는 **위젯 레벨이라 모델 시그널은 그대로 온다**.

**한계**: Qt 위젯 구성은 mayapy 스탠드얼론에서 **크래시(exit 127)** 라 헤들리스 검증 불가.
UI 배선(스핀박스 실시간/Reset/Apply/무효화/close 복원)은 마야에서 직접 확인했고 정상 동작.

관련: [[undo-chunk-by-default]], [[mayapy-headless-verify]], [[ui-text-english-only]],
[[push-includes-tool-guide-docs]].
