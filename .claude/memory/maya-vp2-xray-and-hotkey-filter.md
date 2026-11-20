---
name: maya-vp2-xray-and-hotkey-filter
description: VP2 MUIDrawManager — mesh(kLineStrip) 는 beginDrawInXray 가 안 먹는다(점은 됨) · 컨텍스트 중 마야 핫키(b 등)는 앱 이벤트 필터로 먹어 막을 수 있다 (2026-11-20 GUI 실측)
metadata:
  node_type: memory
  type: project
  originSessionId: 066c4609-b2f7-4781-b343-f8edfa187d49
  modified: 2026-11-20T06:50:58.447Z
---

A00630 매니퓰레이터 · 폴오프 G0 GUI 실측 (마야 2024, 2026-11-20, `tools/A00630_MotionPathEditor/tests/g0_gui_probe.py`).

1. **x-ray**: `beginDrawInXray` 안에서 `dm.mesh(kPoints, pts, None, colors)` · `dm.points()` 는 메시를 뚫고 보이는데
   **`dm.mesh(kLineStrip, pts, None, colors)` 는 메시에 가려진다.** 점마다 색 자체는 셋 다 된다.
   → 색 선은 색 단계마다 `setColor` + `lineStrip`/`line` 으로 나눠 그린다.
2. **핫키 막기**: `QApplication.instance().installEventFilter(f)` 가 `ShortcutOverride` · `KeyPress` · `KeyRelease` 를
   `QWindow (MayaWindowWindow)` 에서 받는다. 셋 다 `return True`(ShortcutOverride 는 `accept()` 도)로 먹으면 마야 핫키
   (`b` = `artisanModifyUpperRadius_press`)가 **안 돈다** — softSelect 설정 불변. draggerContext 는 키를 못 알려 주므로
   필터가 `b_held` 상태를 들고 press 콜백이 읽는다. **필터는 내 컨텍스트가 `currentCtx()` 일 때만** 먹게 한다.
   (뷰포트 `Tab` 은 MTK 가 따로 가로챈다 — [[maya-viewport-tab-is-mtk]], 이 방법이 Tab 에도 되는지는 모른다.)

**Why:** 둘 다 헤드리스로 못 보고, 1 은 API 설명만 보면 될 것 같아 보이는 함정이다.
**How to apply:** VP2 로 색 선 · 점을 x-ray 로 그릴 때, 컨텍스트 툴에서 글자 키가 필요할 때. 관련 [[maya-loaded-plugin-stays-stale]].
