# Changelog — A00290_BSTool

## v01.10 (2026-07-21)
- **[Fix] 다중 편집 후 Ctrl+Z 가 한 타겟의 마지막 한 틱(~0.01)만 되돌리던 문제** — 이제 **한 번의
  조작(제스처)이 통째로 원복**된다.
  - 원인: 슬라이더 드래그는 매 틱 `setAttr` 을 내는데(선택된 타겟마다 하나씩), 각각이 별도 undo
    엔트리라 Ctrl+Z 가 마지막 하나만 되돌렸다.
  - 해결: 조작을 **undo 청크로 묶는다.** 슬라이더는 `sliderPressed`~`sliderReleased` 전체를 한
    청크(첫 변경에서 lazy open), 스핀박스 등 이산 변경은 그 한 번을 한 청크로 감싼다.
  - 다중 선택·키(setKeyframe) 타겟에서도 **Ctrl+Z 한 번에 모든 타겟의 값/키가 원복**된다.
  - 행 재생성 시 열린 청크가 남지 않도록 안전하게 닫는다.

## v01.09 (2026-07-21)
- **[Add] Shift+클릭 = 범위 선택** — 타겟 A 를 클릭한 뒤 B 를 Shift+클릭하면 **화면상 A~B 사이의
  (보이는) 타겟이 모두 선택**된다(표준 리스트 동작). 기준점(anchor)은 마지막 단일/Ctrl 클릭 행이며
  Shift 로 여러 번 눌러 구간을 늘리거나 줄일 수 있다(역방향도 됨).
- **[Add] Ctrl+클릭 = 개별 토글** — 비연속(떨어진) 타겟을 골라 담을 수 있다(v01.08 의 Shift 토글을
  Ctrl 로 옮김).
- `Select All / Clear` 는 기준점을 리셋한다. 필터로 숨은 행은 범위에서 제외된다.

## v01.08 (2026-07-21)
- **[Change] 다중 편집을 체크박스 → 행(칸) 클릭 선택으로 교체** (v01.07 의 체크박스 제거).
  - 타겟 **행을 클릭하면 그 행만 선택**되고 배경이 accent 색으로 강조된다.
  - **Shift+클릭**으로 여러 행을 추가 선택(다시 Shift+클릭하면 해제).
  - 다중 선택 중 **Shift 없이 다른 행을 클릭하면** 이전 선택이 모두 풀리고 그 행만 선택된다.
  - 선택된 행 중 **아무 슬라이더/스핀박스를 조절하면 선택된 모든 타겟에 동시 적용**(v01.07 동작 유지).
    조작한 행이 선택에 없으면 그 행만 바뀐다.
  - 헤더 버튼: `Check All / Uncheck All` → **`Select All`(필터로 보이는 행) / `Clear`**.
  - 구현: 행을 `TargetRow(QFrame)` 로 만들어 `mousePressEvent` 에서 선택 처리
    (`_on_se_row_clicked`). 슬라이더/스핀박스/Edit 버튼은 자기 클릭을 소비하고, QLabel 은
    클릭을 무시해 부모 행으로 전달되므로 **이름 칸을 클릭해도 선택**된다. 슬라이더 드래그는
    선택을 바꾸지 않아, "여러 개 선택 → 한 슬라이더로 동시 조절" 흐름이 유지된다.

## v01.07 (2026-07-21)
Shape Editor 탭 두 가지 업데이트.

- **[Add] 타겟 다중 편집** — 각 타겟 행 왼쪽에 체크박스가 생겼다. 여러 타겟을 체크한 뒤
  **아무 체크된 행의 슬라이더/스핀박스를 조절(또는 값 입력)하면 체크된 모든 타겟에 같은 값**이
  실시간으로 적용된다. 조작한 행이 체크에 포함되지 않으면 그 행 하나만 바뀐다(단일 편집 유지).
  헤더에 **Check All / Uncheck All**(현재 필터로 보이는 행 대상) 추가.
- **[Change] 키가 걸린 타겟도 조절 가능** — 예전엔 animCurve 로 구동(키프레임)되는 weight 는
  슬라이더/스핀박스가 **비활성**이었다. 이제 편집 가능하다:
  - 마야 **Auto Keyframe 이 켜져 있으면** 변경값이 **현재 프레임에 키로 반영**된다.
  - 꺼져 있으면 **미리보기**로 값이 바뀌고, 시간을 이동(재평가)하면 커브 값으로 되돌아간다
    (Maya 채널박스에서 키 걸린 값을 autokey 없이 만지는 것과 동일).
  - weight 상태를 **free / keyed / driven / locked** 로 분류(`weight_state`)해,
    animCurve 가 아닌 다른 노드로 구동되거나 잠긴 weight 만 비활성으로 남긴다.
  - 다중 편집 + Auto Keyframe 이면 체크한 모든 키 타겟에 한 번에 키가 찍힌다.
  - sculpt Edit 진입은 종전대로 **free weight 만** 1.0 으로 올린다(키/구동 타겟은 손대지 않음).

## v01.06 (2026-07-21)
- **[Fix] Shape Editor 탭 weight 슬라이더의 가로 홈(groove)이 안 보이던 문제** — 핸들만 보이고
  슬라이더의 시작·끝을 알 수 없었다. 원인: 어떤 테마 qss 도 `QSlider` 를 스타일링하지 않아,
  어두운 배경(`#2b2b2b`)에서 Maya 네이티브 홈이 배경에 묻혔다.
  `WeightSlider` 에 **자체 스타일시트**(`SLIDER_STYLE`)를 넣어 홈·핸들·비활성 상태를 직접 그린다.
  - 중앙이 0 인 양방향 슬라이더라, 한쪽에서 채워지는 fill 은 0 에서도 절반이 찬 것처럼 보여
    오해를 준다 → **좌우 균일한 한 줄 홈**으로만 그리고 0 위치는 기존 중앙 눈금이 표시한다.
  - green_dark 테마 accent(`#6f9e80`)에 맞춘 색. 비활성(구동/잠긴 weight, 편집 중)은 회색으로.

## v01.05 (2026-07-10)
- **Shape Editor 탭 — `Expand` 버튼 추가**: 탭 안에서 좁던 `Targets` 영역을 **별도의 큰 창**
  (`BS Tool - Targets`, 기본 640x900, 크기 조절 가능)으로 띄운다. 창을 닫으면 탭의 제자리로 돌아온다.
  - 타겟 행을 **복제하지 않고 스크롤 영역 자체를 옮긴다**. 그래서 Edit 토글 / 슬라이더 / weight
    실시간 폴링이 그대로 동작하고, 두 벌을 동기화할 일이 없다.
  - 확장 창에도 `Filter` 와 타겟 개수 표시. 탭 쪽 필터와 **양방향 동기화**(같은 값이면 쓰지 않아
    `textChanged` 가 서로를 부르며 맴돌지 않는다).
  - 확장 창이 떠 있으면 **본 창이 가려지거나 다른 탭이어도** 폴링을 계속한다(타겟이 화면에 있으므로).
  - 본 창을 닫으면 확장 창도 함께 닫혀 스크롤 영역이 탭으로 되돌아온다(고아 창 방지).

## v01.04 (2026-07-10)
- **Shape Editor 탭 — weight 슬라이더 추가**: 타겟마다 숫자 스핀박스 옆에 가로 슬라이더가 붙는다.
  **중앙이 0**, 오른쪽 끝이 `+1`, 왼쪽 끝이 `-1` (양 끝과 중앙에 눈금). 음수 타겟도 밀 수 있다.
  - 슬라이더와 스핀박스는 같은 weight 의 두 얼굴 — 어느 쪽을 움직이든 씬에 쓰고 반대쪽을 맞춘다
    (`_show_weight` 가 `blockSignals` 로 되울림을 막는다).
  - `QSlider` 는 정수만 다루므로 `WeightSlider` 가 1000배 스케일로 매핑(해상도 `0.001`).
  - 슬라이더 범위(`-1~1`)를 넘는 weight 는 슬라이더가 끝에 붙고 **실제 값은 스핀박스**(`-10~10`)가
    보여 준다. 이때 폴링이 클램프된 값을 씬에 되쓰지 않는다.
  - 잠금/구동된 weight 를 밀면 씬에 쓰이지 않고, 다음 폴링이 실제 값으로 되돌린다.
  - 슬라이더를 **잡고 있는 동안**(`isSliderDown`)은 폴링이 값을 덮지 않는다.
  - 행이 넓어져 기본 창 폭 460 → 580.

## v01.03 (2026-07-10)
- **Shape Editor 탭 — weight 실시간 반영**: 씬에서 타겟 weight 가 바뀌면(채널박스, 어트리뷰트
  에디터, 애니메이션 재생, 다른 스크립트 등) 툴의 스핀박스가 곧바로 따라온다. 이전에는 `Refresh`
  를 눌러야만 갱신됐다.
  - Maya 는 어트리뷰트 변경을 Qt 에 알려 주지 않으므로 `QTimer` 로 `120ms` 마다 다시 읽는다
    (`main_window._sync_se_weights`).
  - 폴링은 **Shape Editor 탭이 보이고 표시할 행이 있을 때만** 돈다(`_update_se_timer` +
    `showEvent`/`hideEvent`/`closeEvent`).
  - 스핀박스에 쓸 때 `blockSignals` 로 `valueChanged` 를 막아 씬으로 **되쓰지 않는다**
    (막지 않으면 잠금/구동된 weight 에서 매 틱 경고 로그가 쌓인다). 씬 → UI 단방향.
  - 사용자가 **입력 중인(포커스가 있는)** 스핀박스와, 표시 자릿수(`decimals=3`) 아래의
    미세한 차이는 건드리지 않는다.

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
