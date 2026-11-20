---
name: project-c-jun-junction-layout
description: "사용자의 C:\\JUN 정션 구조(PC 간 같은 논리 경로로 마야 레퍼런스) — 계획 단계, 정션 경유 파일은 아직 적음"
metadata:
  node_type: memory
  type: project
  originSessionId: 066c4609-b2f7-4781-b343-f8edfa187d49
  modified: 2026-11-20T05:37:20.111Z
---

사용자는 `C:\JUN` 아래에 정션으로 논리 경로를 만들어, 회사 PC 와 집 PC 에서 같은 경로로 마야 레퍼런스를 걸려고 한다(2026-11-20 검토).
구조: `A000010_PortFolio\A0000NN_<프로젝트>\A000010_RIG` · `A000020_ANIM` = 정션(실제 데이터는 PC 마다 다른 디스크).
`JUN_Src_Rig` · `JUN_MUE` · `JUN_Cage` 도 정션이며, 앞으로 마야 툴처럼 숫자 접두사를 붙여 관리할 예정. A00210_FileManager 로 구조 관리 · 복사 · 싱크를 기대한다.

**2026-11-20 사용자 확인: 정션 경로로 레퍼런스를 제대로 거는 마야 파일은 아직 많지 않다.** → 지금 이름을 바꿔도 깨지는 파일이 적다. 이름을 확정하기 좋은 시점.

**Why:** 이 구조의 가치는 "논리 경로가 바뀌지 않는다"에 있다. 실측으로 `0020_vivian_attack_0010.mb` 는 옛 `C:/JUN/JUN_Vivian/...` 을 참조해 이미 끊겨 있었다. `JUN_Cage` 는 `JUN_Src_Rig` 대상의 하위 폴더를 다시 가리킨다(같은 파일, 경로 둘).
**How to apply:** C:\JUN 구조 변경을 도울 때는 ①확정 뒤 이름 바꾸기 금지(필요하면 옛 이름 정션을 별칭으로 남김) ②데이터 하나에 논리 경로 하나 ③텍스처도 C:\JUN 경유 ④옛 실제경로 파일은 `dirmap` ⑤PC별 정션 지도 json(A00210 후보) 를 기준으로 삼는다. 관련: [[wip-a00210-sync-tracker]] · [[wip-a00240-junction-tab]]
