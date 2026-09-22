---
name: launcher-buttons-follow-current-version
description: A00370_ToolLauncher 버튼은 옛 버전 폴더를 계속 가리켜도 에러가 안 난다 — 새 버전을 만들면 프로파일 JSON 도 함께 옮길 것
metadata:
  type: feedback
---

이 저장소는 새 버전을 **새 폴더**(`_V02`, `_V03`)로 만들고 옛 폴더를 **지우지 않는다**.
그래서 `A00370_ToolLauncher` 의 버튼은 가만히 두면 **옛 폴더를 계속 가리킨 채 남는다.**

**Why:** 링크가 깨지지 않으니 **아무 에러도 나지 않는다.** 버튼은 잘 눌리고 창도 뜬다 —
사용자만 조용히 옛 툴을 쓰게 된다. 스스로 드러나지 않는 종류의 썩음이다.

**How to apply:** 툴에 새 버전 폴더를 만들거나 툴을 다른 툴로 이식하면, 같은 작업에서
`A00370_ToolLauncher/data/profiles/*.json` 의 버튼도 함께 옮긴다.
버튼 이름에 버전을 붙여(`uvTool_V02`) 어느 쪽이 열리는지 화면에서 보이게 한다.

**판단 기준** — "더 새 폴더가 있다" 만으로 옛 툴이라고 단정하지 않는다.
두 폴더가 다 살아 있는 경우가 있다. 각 툴의 **문서·메모가 무엇을 현행으로 적는지**로 가른다
(예: "이후 작업은 V02 에서 한다", docs/README 의 "탭 재분류 전 · 보존").
보조 신호: 옛 폴더의 마지막 실질 변경이 Framework 일괄 작업뿐이면 방치된 쪽이다.

프로파일은 상대경로라 **git 추적 대상**이다 — 여기를 고치면 모든 PC 의 기본값이 바뀐다.

2026-09-22 에 밀린 5개를 정리했다: `meshDoctor`(→ [[wip-a00380-meshdoctor-tab]] 로 이식돼 삭제) ·
`uvTool`→`_V02` · `BSTool`→`_V02` · `AnimTool`→`_V02` · `jointTool_V02`→`_V03`.
검증은 런처 자신의 `tool_launcher.launch()` 로 전 버튼을 눌러 보면 된다([[mayapy-headless-verify]]).
