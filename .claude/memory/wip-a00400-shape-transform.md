---
name: wip-a00400-shape-transform
description: A00400 Display > Shape Edit(옛 Transform) — 커브 셰이프를 피벗 기준으로 scale/move/rotate + 선 굵기. 트랜스폼 채널은 불변. v01.21 에 Line Width 탭을 흡수하고 개명
metadata: 
  node_type: memory
  type: project
  originSessionId: bcfa3c1b-bf62-47f4-b38b-70e50bb266e8
  modified: 2026-09-21T02:38:54.502Z
---

`A00400_CurveTool` **Display > Transform** 탭 (v01.17 -> 01.18, 2026-09-21, 사용자 요청).
리스트업한 커브마다 **그 커브의 피벗** 기준으로 셰이프(CV 전체)를 스케일 · 이동 · 회전한다.
코어 `app/core/shape_xform_manager.py`, 화면 `app/ui/shape_xform_tab.py`.

**Why:** 컨트롤 크기·자리·방향을 맞추는 일은 **트랜스폼 채널을 건드리면 안 된다** — 컨트롤은 채널이
0/1 로 깨끗해야 한다. 그래서 CV 를 옮긴다.

**How to apply:**
- 공식은 `new = pivot + T + R * (S * (cv - pivot))` — **스케일 → 회전 → 이동** 순.
  기준점은 트랜스폼의 **rotate pivot**(`getAttr .rotatePivot`), 계산은 **오브젝트 공간**이라 축이
  그 커브 자신의 로컬 축이다. 회전된 좌우 컨트롤에 같은 값을 넣으면 각자 자기 축으로 같은 만큼 변한다.
- 쓰기는 셰이프마다 `cmds.curve(shape, replace=True, point=...)` **한 번**. undo 되고 히스토리 커브에도
  통한다. `MFnNurbsCurve.setCVPositions` 는 undo 큐에 안 남고, `setAttr .controlPoints` 는 히스토리가
  있으면 **트윅**이 된다 (같은 판단이 `smooth_manager` 에도 있다).
- **닫힌(주기) 커브**는 `replace=True` 만으로는 거절 → `periodic=True` + `degree` + `knot` 까지.
  모든 CV 에 같은 변환을 걸므로 뒤쪽 degree 개 복사본도 그대로 따라가 이음매가 안 어긋난다.
- 트랜스폼 아래 셰이프가 여럿이면 **전부 같은 피벗**으로 함께 변환한다.
- UI: Scale / Move / Rotate 세 줄, 줄마다 X/Y/Z 체크 + 값. 끈 축은 중립값(1 / 0).
  **기본은 Scale 만 켬** — 크기만 바꾸려다 위치까지 움직이는 사고를 막는다. Scale 의 `Uniform` 은
  한 칸에 정한 값을 켜 둔 다른 축에 복사(되먹임 방지로 `blockSignals`).
- **v01.19 (2026-09-21, 사용자 요청): 값 아홉 개를 전부 슬라이더로.** 3열 그리드를 **축마다 한 줄**
  (`[v] X [슬라이더] [숫자]`)로 바꾸고 `_AxisSlider` 위젯을 탭 안에 뒀다(`QSlider` 는 정수라
  step 으로 나눠 정수 칸으로 쓴다 — A00450 `slider_row.py` 와 같은 방식).
  - ★ **슬라이더는 자주 쓰는 구간만 덮고**(스케일 0~5 · 이동 ±10 · 회전 ±180) 숫자 칸은 전체 범위
    (±1000 / ±100000 / ±3600) 그대로다. 전체 범위를 슬라이더에 걸면 한 픽셀이 수십 단위라 못 쓰고,
    잘라내면 사용자가 친 값이 조용히 바뀐다 → **범위 밖 값을 치면 슬라이더 범위를 그 값까지 넓힌다.**
    `Reset Values` 가 값과 범위를 함께 되돌린다.
  - 슬라이더는 **값만** 정한다 — 씬은 `Apply to Shapes` 에서만 바뀐다(드래그 라이브 변형 아님).
  - 줄이 꺼졌으면 축 체크박스도 비활성이므로 `_on_axis_toggled` 는 `check.isEnabled()` 를 함께 본다
    (`reset()` 이 축을 다시 켜도 꺼진 줄이 살아나지 않게).
  - 탭 최소 폭은 **826 그대로**(세 줄짜리 안내 라벨이 폭을 정한다), 높이만 496 -> 712.
- **v01.20 (2026-09-21, 사용자 요청): 슬라이더가 씬을 라이브로 바꾼다.** 새 코어
  `ShapeTransformSession` — 세션 시작 때 **CV 원위치**를 잡아 두고, 값이 바뀔 때마다 **원위치에서
  다시** 계산해 **절대 위치**로 쓴다 → 슬라이더를 왕복해도 **누적되지 않는다**.
  undo 는 [[wip-a00110-stagger-offset]] 의 방식 그대로(`undoInfo(stateWithoutFlush=False)` 로
  미리보기는 큐에 안 쌓고, 멎으면 **마지막 기록 상태로 되돌린 뒤** 한 번에 써서 한 항목으로
  기록 = restore-before-commit) → **드래그 한 번 = Ctrl+Z 한 번**.
  - ★ **세션을 닫을 때는 위젯 값이 아니라 `session.applied` 를 확정한다.** 닫는 계기가 보통
    "값이 방금 바뀐 것" 이라, 그 시점의 위젯은 이미 **다음 조작의 값**이다. 위젯을 읽어 기록하면
    엉뚱한 값이 커브에 굳는다(실수로 잡음).
  - ★ **리스트 교체는 TSL 모델 신호**(`rowsInserted/rowsRemoved/modelReset`)로 **즉시** 닫는다.
    `_live_update` 안에서 늦게 닫으면 그 순간 값 칸을 0 으로 돌리면서 **사용자가 방금 끈 값이
    사라진다**(이것도 실수로 잡음). 반대로 씬이 어긋나 세션을 버릴 때는 **값을 건드리지 않는다**.
  - `Live` 체크박스 기본 ON. 라이브 중 `Apply` 는 **또 걸지 않고 확정**(값은 1/0 으로 리셋 —
    안 그러면 다음 세션이 새 원위치에 같은 배율을 또 걸어 두 배가 된다), `Reset` 은 드래그 전
    모양으로 되돌린다(undo 한 스텝). 사용자가 Ctrl+Z 를 누르면 `scene_in_sync()` 탐침(첫 CV 비교)
    으로 알아채고 세션을 버린다.
  - 한 틱 비용(headless): 1커브 0.3ms · 50커브 7ms · **200커브 30ms**. 아주 긴 목록이면 Live 를 끈다.
- 검증: 코어 23항목 + 오프스크린 Qt UI 20항목 + **슬라이더 34항목** (mayapy 2024). 검증 방식은
  [[cmds-scale-rotate-pivot-is-world]] 참고 — 마야 명령 결과와 CV 단위로 대조했다.

**Line Width 흡수 + 개명 (v01.21, 2026-09-21)**

옛 `Display > Line Width` 탭을 이 탭 안으로 넣고 탭 이름을 **`Transform` -> `Shape Edit`** 으로.

- **왜 그 이름인가**: 이 탭이 건드리는 것은 **전부 셰이프 노드**다 — CV 도, `nurbsCurve.lineWidth` 도
  셰이프에 붙어 있고 **트랜스폼 채널은 하나도 안 건드린다.** 옛 이름은 트랜스폼을 만지는 것처럼
  읽혔다. (사용자가 제안한 이름을 그대로 채택했고, 근거를 코드 주석과 문서에 남겼다.)
- **합친 실익**: 커브 목록(TSL)을 **한 번만** 만든다. 예전에는 같은 커브를 두 탭에서 두 번 담았다.
- 굵기 상자는 변환과 **따로 논다** — `Live`/`Apply` 를 거치지 않고 슬라이더에서 손을 떼는 순간
  적용(드래그 한 번 = undo 한 스텝). 그래서 버튼 줄 **아래**에 둔다.
- 파일·클래스도 이름을 맞췄다(`shape_edit_tab.py` / `ShapeEditTab`, `git mv`). 코어
  `shape_xform_manager.py` 는 변환 계산이라 그대로.
