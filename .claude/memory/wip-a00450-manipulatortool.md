---
name: wip-a00450-manipulatortool
description: "A00450_manipulatorTool - 매니퓰레이터 축 굵기 슬라이더. manipOptions 는 전역 하나뿐, lineSize 는 1.0 하한, 굵기(lineSize)와 히트(linePick)는 별개"
metadata: 
  node_type: memory
  type: project
  originSessionId: 064559b4-a50c-475d-865d-675d82033aad
  modified: 2026-08-18T08:36:35.723Z
---

`JUN_All/tools/A00450_manipulatorTool` (v01.00, 2026-08-18 신규, arch B PySide, brown_dark).
이동/회전/스케일 매니퓰레이터 축 굵기를 슬라이더로 라이브 조절 + Reset.

**마야가 주는 것은 `cmds.manipOptions` 하나뿐**(mayapy 2024 실측):
`lineSize` 2.0 / `linePick` 4.0 / `handleSize` 30.0 / `scale` 1.0 / `forceRefresh`.

- **`lineSize` 는 1.0 미만이 전부 1.0 으로 잘린다**(0 도 −1 도). 상한은 사실상 없음(200 OK).
  `handleSize`/`scale` 은 0 을 **무시**(기존 값 유지). → 쓴 뒤 반드시 **되읽어서** UI 에 반영.
- **⚠️ 도구별 굵기는 마야에 없다.** `manipMoveContext`/`manipRotateContext`/`manipScaleContext`
  에는 크기 플래그가 없고(activeHandle 류뿐) `manipOptions` 는 **전역**이라 세 도구가 값을 공유한다.
  → 값을 셋으로 들고 있다가 `scriptJob(event=["ToolChanged", ...])` 로 **도구 전환 순간 전역에 밀어 넣어**
  "도구별 굵기"를 흉내낸다(`ManipState`). 활성 줄은 UI 에 `▸` 로 표시.
- **컨텍스트 이름은 회전만 대문자**: `moveSuperContext` / **`RotateSuperContext`** / `scaleSuperContext`
  → 소문자로 낮춰 부분 일치. 컨텍스트는 **GUI 마야에서만 생성**되어 headless 에선 `currentCtx()` = None,
  `cmds.scriptJob(event=...)` 도 **예외가 아니라 `None`** 을 돌려준다(반환값으로 실패 판정할 것).
- **굵게 한다고 잘 집히지 않는다**: `lineSize` = 그려지는 두께, `linePick` = **실제 클릭 히트 반경**.
  "매니퓰레이터가 잘 안 집힌다" 가 목적이면 `linePick` 을 같이 올려야 한다.

관련: [[qdoublespinbox-keyboard-tracking]] (슬라이더 스핀박스), [[mayapy-headless-verify]],
[[pin-for-maya-cmds-tools]], [[prefer-pyside-for-new-tools]].
문서 `JUN_All/docs/A00450_manipulatorTool.md`.
