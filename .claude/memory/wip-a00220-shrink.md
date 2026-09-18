---
name: wip-a00220-shrink
description: "A00220_BackupTool v01.15 — Pin 옆 Shrink 토글, 공룡만 남기고 창 788→155px. 숨길 그룹 안의 위젯은 레이아웃 사이를 옮겨서 살린다"
metadata: 
  node_type: memory
  type: project
  originSessionId: 5782f0ec-e7f6-4339-aa79-6790d10548f6
  modified: 2026-09-18T00:18:27.244Z
---

`A00220_BackupTool` **v01.15** (2026-09-18) — `Pin` 왼쪽에 **`Shrink`** 체크형 버튼(같은 72x28).
켜면 Target Files · Settings · Control · Log 를 `hide()` 하고 창 세로를 줄인다(실측 **788 → 155px**,
가로 350 그대로). 화면에 남는 버튼은 `Shrink`(라벨 `Shrunk`) 와 `Pin` 뿐이고 백업은 계속 돈다.

**핵심 — 공룡은 숨길 `Control` 그룹 안에 있다.** 그룹을 숨기면 공룡도 사라지므로, 줄이는 동안
공룡을 **창 최상위 레이아웃 index 1 로 옮기고**(`removeWidget` → `insertWidget`) 되돌릴 때 원래
자리(`_dino_index`)로 돌려놓는다. **복제가 아니라 이동**이라 애니메이션·타이머가 끊기지 않는다
([[framework-expand-widget]] 과 같은 결론).

**숨긴 뒤 `layout().invalidate()` + `activate()` 를 해야 창이 줄어든다** — 안 하면 옛 최소 높이에
막힌다(이 툴의 Settings 접기 `_on_settings_toggled` 가 같은 이유로 같은 짓을 한다).
복귀는 `sizeHint` 가 아니라 **줄이기 전 높이(`_full_height`)** 로 — sizeHint 로 돌리면 파일 목록이
늘어나 크기가 달라진다. 접어 둔 Settings 는 섹션만 `show()` 하므로 접힌 채로 남는다.

검증: 오프스크린 PySide6 21항목(버튼 자리·크기, 감춘 위젯, 남은 버튼 둘, 높이, 왕복 복원,
접힌 Settings 유지, 반복 토글, shrink 중 Pin) + `QT_QPA_PLATFORM=windows` + `WA_DontShowOnScreen`
으로 **실제 폰트 캡처**해 눈으로 확인. 마야와 무관한 standalone 툴이라 mayapy 불필요.
관련: [[wip-a00220-pin]], [[wip-a00220-dino-save-pulse]]
