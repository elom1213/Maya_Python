---
name: wip-a00370-shrink-rocket
description: "A00370_ToolLauncher v01.11~12 — Pin 왼쪽 Shrink(272x155, 줄면 Pin 이 Shrunk 아래로) + 줄었을 때 툴 아이콘 로켓이 위로 발사되기를 무한 반복(app/ui/rocket_anim.py)"
metadata:
  node_type: memory
  type: project
  originSessionId: 4a5e2d33-dace-406d-882d-78b18f5530db
  modified: 2026-10-23T01:32:41.979Z
---

A00370_ToolLauncher **v01.11** (2026-10-23) — `Pin` 왼쪽 체크형 **Shrink**(72x28). 켜면 메뉴 바 ·
`launcher_tab`(Controls / Filter / 버튼) · 저작권 줄을 `hide()` → `invalidate/activate` → **272 x 155**
(세로는 [[wip-a00220-shrink]] · [[wip-a00240-shrink-anim]] 과 같고 순서도 같다). 끄면 줄이기 전 크기
(`_full_size`, 가로 · 세로 둘 다)로. 화면만 감추므로 프로파일 · 로그는 그대로.

**v01.12 (같은 날)** — 사용자 요청으로 줄었을 때 **`Pin` 이 `Shrunk` 아래**로 간다. 버튼 둘은
`QGridLayout`(`button_grid`) 에 있고 토글에서 `Pin` 만 (0,1) ↔ (1,0) 으로 옮긴다(removeWidget →
addWidget). 비는 Pin 칸(72 + 간격 6)만큼 가로를 줄여 350 → 272. 로켓 영역 166 x 133 은 그대로.

**로켓 발사 애니메이션** — `app/ui/rocket_anim.py` `RocketAnimWidget`. A00240 `FileTreeAnimWidget`
과 같은 꼴(start / stop / set_elapsed / is_running, 바뀔 때만 update). 헤더 행에서 메뉴 바 자리를
물려받아(`stretch=1`, Expanding) 버튼 왼쪽 166 x 133 을 차지한다.
- 로켓 = 코드 비트맵 11 x 14(`ROCKET`, B 몸체 = 테마 글자색 · W 창문 · F 날개 = 아이콘 svg 코랄
  `#ff7a59` / `#ffb27a`) + 불꽃 두 프레임(`FLAME_FRAMES`, 0.08초마다 번갈아). 칸 크기는
  `min(h // 34, w // 17)` → 155px 창에서 4.
- 한 바퀴 **2.4초**: 점화 0.6(발사대 위, 불꽃 깜빡임 + 좌우 반 칸 떨림) → 상승 1.2(ease-in,
  창 위 바깥까지, 0.08초마다 연기 점 하나 남겨 0.9초에 걸쳐 옅어짐) → 빈 하늘 0.6 → 반복.
- 속도 · 반복을 바꾸려면 클래스 상수 `IGNITION / ASCEND / REST / FLICKER` 만.

검증: 오프스크린 PySide6 29항목 + 시각별 캡처(t=0 · 0.3 · 0.9 · 1.3 · 1.6 · 2.0) 눈 확인.
**마야 GUI 미확인.** 관련: [[wip-a00370-toollauncher]]
