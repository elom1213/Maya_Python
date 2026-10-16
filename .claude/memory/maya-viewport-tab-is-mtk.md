---
name: maya-viewport-tab-is-mtk
description: 마야 뷰포트의 Tab 키는 hotkey 로 못 잡는다 — Modeling Toolkit 이 가로채 nexOpt mayaTabPressCmd 를 실행 (dR_paintPress)
metadata:
  type: project
---

마야 뷰포트에서 선택 · Move · Rotate · Scale 툴일 때 **Tab 은 `hotkey -keyShortcut Tab` 바인딩을 무시**한다.
Modeling Toolkit(`modelingToolkit.mll`)이 먼저 가로채 `nexOpt` 옵션을 실행한다:
`useMayaTabPressCmd`(int) / `mayaTabPressCmd`(기본 `dR_paintPress`) / `useMayaTabReleaseCmd` / `mayaTabReleaseCmd`(기본 `dR_paintRelease`).
(MTK 자기 툴 안에서는 `tabPressCmd` / `tabReleaseCmd` 쪽.) 증상: 스크립트 에디터에 `dR_paintPress; selectPref -paintSelect 1 ...` 만 찍힌다.

**Why:** A00110 v02.19 에서 Tab 을 핫키로 걸었다가 사용자가 "Tab 누르면 dR_paint 로그만 나오고 안 된다" 고 보고(2026-10-16).
이름은 마야 바이너리 문자열에서 찾았다 — 문서에 없다.

**How to apply:**
- Tab 을 툴 명령에 걸려면 `mel.eval('nexOpt -e mayaTabPressCmd "..."')` 로 바꿔 끼우고 닫을 때 되돌린다(`A00110_animTool_V02/app/core/hotkey_manager.py` `TabKeyManager`).
  `nexOpt -e` 는 메모리 값(`-save` 해야 저장)이라 크래시에도 다음 세션은 원래대로.
- **`nexOpt` 는 GUI 에서만 등록된다** — mayapy standalone 에서는 플러그인을 로드해도 `Cannot find procedure "nexOpt"`. 헤드리스 검증은 가짜 저장소로만 가능, 실제 동작은 GUI 확인.
- 누르고 있으면 자동 반복으로 press 가 계속 온다 → 토글류는 release 로 풀리는 held 플래그로 한 번만.
- 관련: [[mayapy-headless-verify]], [[wip-a00110-tab-taxonomy]]
