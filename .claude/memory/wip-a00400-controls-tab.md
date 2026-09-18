---
name: wip-a00400-controls-tab
description: "A00400_CurveTool Create > Controls — bs_controls(Brandon Schaal) 이식: 컨트롤 커브 생성 · 색 · 셰이프 교체 (v01.15)"
metadata:
  node_type: memory
  type: project
---

`A00400_CurveTool` **Create > Controls** 탭 (v01.14 -> 01.15, 2026-09-18).
사용자가 마야 셸프에서 `import bs_controlsUI; bs_controlsUI.BSControlsUI().bsControlsUI()` 로 쓰던
`prefs/scripts/bs_controls.py` · `bs_controlsUI.py` 를 옮긴 것. 원본 창의 세 섹션
(Create Controls / Control Colors / Control Shape Replace)을 **순서 그대로** 한 탭에 담았다.
코어 `app/core/control_manager.py`, 화면 `app/ui/controls_tab.py`, 셰이프는 [[framework-control-shapes]].

**Why:** 원본은 `maya.cmds` 창이라 이 저장소 툴들과 로그·undo·테마가 따로 놀았다.

**How to apply:**
- 이식하며 바꾼 것: `cmds.error` -> **로그 경고**(나머지는 계속) · 버튼 한 번 = **undo 한 스텝** ·
  색을 바꿔도 **선택 유지**(원본은 `cmds.select(d=True)` 로 날려서 색을 여러 번 못 바꿈) ·
  `parentConstraint` 걸었다 지우기 -> **`matchTransform`**.
- **색은 셰이프에** 건다(트랜스폼에 걸면 자식이 전부 물려받는다). 색 지정 시 `overrideDisplayType` 을 0 으로
  되돌려야 색이 보인다. `Reset Color` 는 트랜스폼 + 셰이프 양쪽.
- **원본 버그**: 셰이프가 없는 노드를 고르면 `bsResetColor` 가 `shapes` 미정의로 죽는다(`UnboundLocalError`).
  여기서는 `objectType(isAType="dagNode")` 로 걸러 경고만.
- 셰이프 교체는 replacement 1개면 전 타깃, 개수가 같으면 짝끼리, 그 외에는 **거절**(짝을 추측하지 않는다).
  `temp_CRV` · `mirror_GRP` 를 남기지 않는다.
- 이름 규칙(원본 `bsNameCurve`): 빈칸 -> `<obj>_ANIM`, 한 단어 -> 흔한 접미사 치환(`spine_jnt`+`ctl` -> `spine_ctl`),
  `_` 포함 -> 그대로.
- 검증 33항목(mayapy 2024 + 오프스크린 Qt) — **34종 전부 원본과 CV 단위 비교**가 핵심이다.
