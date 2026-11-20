---
name: maya-vp2-xray-and-hotkey-filter
description: VP2 MUIDrawManager — beginDrawInXray 는 점에만 먹고 3D 선(lineStrip · mesh 선)은 메시에 가려진다 → 선은 화면 2D 로 · 컨텍스트 중 마야 핫키(b 등)는 앱 이벤트 필터로 먹어 막을 수 있다 (2026-11-20 GUI 실측)
metadata:
  node_type: memory
  type: project
  originSessionId: 066c4609-b2f7-4781-b343-f8edfa187d49
  modified: 2026-11-20T06:50:58.447Z
---

A00630 매니퓰레이터 · 폴오프 G0 GUI 실측 (마야 2024, 2026-11-20, `tools/A00630_MotionPathEditor/tests/g0_gui_probe.py`).

1. **x-ray 는 점에만 먹는다**: `beginDrawInXray` 안에서 `dm.points()` · `dm.mesh(kPoints, ..., colors)` 는 메시를 뚫고 보이는데
   **3D 선은 전부 메시에 가려진다** — `mesh(kLineStrip)`(G0 프로브) · `lineStrip`(v01.09 사용자 확인) 둘 다. 점마다 색 자체는 된다.
   → **선은 그릴 때 화면 픽셀로 투영해 2D 로**(`mesh2d(kLineStrip)` · `line2d`, 박스 선택 사각형처럼 늘 위에 보인다).
   `frame_context.getMatrix(kViewProjMtx)`(행 벡터) + `getViewportDimensions()`, 카메라 뒤(w<=0)에서 끊는다.
   7,000 점 투영 + MPointArray(리스트 생성자) ≈ 6 ms/그리기. (A00630 v01.10 `screen_strips`. 첫 판은 G0 프로브의 "색마다 points()" 줄을 선으로 착각해
   lineStrip 이면 된다고 적었다 — **프로브는 확인하려는 것 그대로를 그려야 한다**.)
2. **핫키 막기**: `QApplication.instance().installEventFilter(f)` 가 `ShortcutOverride` · `KeyPress` · `KeyRelease` 를
   `QWindow (MayaWindowWindow)` 에서 받는다. 셋 다 `return True`(ShortcutOverride 는 `accept()` 도)로 먹으면 마야 핫키
   (`b` = `artisanModifyUpperRadius_press`)가 **안 돈다** — softSelect 설정 불변. draggerContext 는 키를 못 알려 주므로
   필터가 `b_held` 상태를 들고 press 콜백이 읽는다. **필터는 내 컨텍스트가 `currentCtx()` 일 때만** 먹게 한다.
   (뷰포트 `Tab` 은 MTK 가 따로 가로챈다 — [[maya-viewport-tab-is-mtk]], 이 방법이 Tab 에도 되는지는 모른다.)

**Why:** 둘 다 헤드리스로 못 보고, 1 은 API 설명만 보면 될 것 같아 보이는 함정이다.
**How to apply:** VP2 로 색 선 · 점을 x-ray 로 그릴 때, 컨텍스트 툴에서 글자 키가 필요할 때. 관련 [[maya-loaded-plugin-stays-stale]].
