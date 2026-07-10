# Changelog — A00290_BSTool

## v01.02 (2026-07-10)
- **`Shape Editor` 탭 신규 (탭 1)** — Maya 기본 Shape Editor 의 대체. Shape Editor 에 타겟이
  노출되지 않아 Edit 버튼조차 없는 경우를 대응한다.
  - blendShape 노드를 씬에서 고르고 `Select BlendShape Nodes` → 노드의 **모든 타겟**을
    별칭(`aliasAttr`)에서 직접 읽어 리스트업. 타겟마다 **`Edit` 토글 버튼 + weight 스핀박스**.
  - `Edit` ON → `cmds.sculptTarget(bs, e=True, target=weightIdx)`. 이후 베이스 메시를 조각하면
    그 타겟의 델타로 기록되고, `Edit` OFF(`target=-1`) 하면 편집 결과가 타겟 모양으로 확정된다.
    (`sculptTargetIndex` 어트리뷰트를 `setAttr` 로 직접 쓰면 디포머가 편집을 가로채지 않아
    베이스 shape 의 tweak `.pnts` 로 들어간다 → 반드시 커맨드를 쓴다. 읽기만 어트리뷰트로.)
  - Edit 진입 시 타겟이 보이도록 weight 를 1.0 으로 올리고(이전 값 저장), 해제 시 원복.
    `envelope` 도 1.0 으로 맞춘다. weight 가 잠기거나 다른 노드에 구동되면 로그로 안내.
  - 노드당 한 타겟만 편집 가능(Maya 와 동일) — 다른 타겟 Edit 을 켜면 이전 것이 자동 해제된다.
  - 편집 중인 버튼은 **주황색 + `Edit ON` 라벨**로 표시되고, 해제하면 테마 기본 색/`Edit` 로 돌아온다
    (테마 qss 의 `:hover`/`:pressed` 가 색을 덮지 않도록 버튼 자신의 스타일시트로 pseudo-state 까지 지정).
  - 타겟 이름 `Filter`, `Refresh`, `Exit Edit Mode (all blendShapes)` 제공.
    Maya 뷰포트의 편집 HUD(`updateBlendShapeEditHUD`)도 함께 갱신.
  - 창을 닫으면 씬에 열린 편집 모드를 모두 해제(편집 결과 확정)한다.
  - 로직 `core/shape_editor_manager.py` (`ShapeEditorManager`).

## v01.01 (2026-06-25)
- **Edit BS 탭에 `Copy every frame` 추가**: 정해진 `[Start, End]` 구간을 **1프레임마다** 현재 씬에서
  **선택한 메시**를 복제(visibility off)해 `<mesh>_f<frame>` 이름으로 추출하고 `<mesh>_frames` 그룹으로
  묶는다. 프레임 번호는 구간 전체 동일 자릿수로 **0 패딩**(예: 5–120 → `_f005`…`_f120`).
  키를 걸지 않고 현재 씬 애니메이션 상태를 그대로 캡처한다(`suspend_refresh` + 현재 프레임 원복).
  구간 입력 UI(Start/End + `Get Current`)는 A00110 Follow 탭 패턴을 따른다.
  로직 `edit_bs_manager.copy_every_frame(meshes, start, end)`.

## v01.00 (2026-06-24)
- 최초 버전. 레거시 `JUN_PY_BSTool_V01_01`(maya.cmds) 을 PySide(Qt) 로 재작성.
  `A00270_skinMigrate` 클론, green_dark 테마, Maya 메인 윈도우 parent.
- **탭 1 — Edit BS** (레거시 Edit BS 탭 이식. Connect BS 탭은 제외):
  - BlendShape 노드 리스트(씬 선택 연동, `JUN_mod_tsl_qt`).
  - `Key every target` — 각 타겟을 프레임 i 에서 1, i-1/i+1 에서 0 으로 키(타겟 순차 노출).
  - `Copy every target` — 위 키 후 프레임마다 베이스 메시를 복제해 타겟 모양을 타겟 이름의
    메시로 추출(visibility off) → `<node>_targets` 그룹.
- **탭 2 — Base Shape** (신규):
  - blendShape 노드를 지정하면 타겟 이름을 리스트업(`List Targets` / 선택에서 `<- Set`).
  - 선택 타겟의 **weight=Value 모양을 weight=1.0 기본 모양으로 재정의**.
    예) Value 0.5 → 타겟 절반, 1.3 → 과장. 내부적으로 타겟 포인트 델타를 Value 배 스케일
    (`inputTargetItem[*].inputPointsTarget`), in-between 아이템도 함께 스케일. 단일 undo 청크.
  - 저장된 포인트 델타가 없는(라이브 지오 입력) 타겟은 건너뛰고 로그에 안내.
