---
name: wip-a00400-shape-transform
description: A00400_CurveTool Display > Transform — 커브 셰이프(CV)를 각 커브 피벗 기준으로 scale/move/rotate (v01.18)
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
  한 칸에 친 값을 켜 둔 다른 축에 복사(되먹임 방지로 `blockSignals`).
- 검증: 코어 23항목 + 오프스크린 Qt UI 20항목 (mayapy 2024). 검증 방식은
  [[cmds-scale-rotate-pivot-is-world]] 참고 — 마야 명령 결과와 CV 단위로 대조했다.
