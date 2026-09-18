---
name: wip-a00240-shrink-anim
description: "A00240 Shrink(350x78 = A00220 줄었을 때 가로 · 세로 절반) + 파일 트리 애니메이션(v01.11) — 버튼 옆 자리, 줄었을 때만 여백 2px, 다 자라면 타이머 정지"
metadata: 
  node_type: memory
  type: project
  originSessionId: 8fc27b42-f7ec-4155-b340-da985ee075b0
  modified: 2026-09-18T01:23:00.346Z
---

A00240_PathTool — Help 메뉴 + **Shrink**(v01.10): 탭·메뉴 바를 감추고 **350 x 78**.
기준은 A00220_BackupTool 이 줄었을 때 350 x 155 (green_mid 오프스크린 실측, [[wip-a00220-shrink]]).

**파일 트리 애니메이션(v01.11, 2026-09-18)** — `app/ui/file_tree_anim.py` `FileTreeAnimWidget`.
파일 0 → 0.5초 뒤 파일 1 셋 → 0.5초 뒤 파일 2 셋, 한 단계 0.25초 ease-out(위치 · 연결선 · 투명도를 진행값 하나로).
- 자리는 버튼 **옆**(아래면 그릴 높이 20px). 줄었을 때만 창 여백 11→2px 로 190 x 74, 한 행 10.6px.
- 다 자라면 타이머 정지, Shrink 켤 때마다 처음부터. 색은 테마 글자색(공룡과 같은 방식).
- 테스트용 `set_elapsed(sec)` / `visible_icons()` 가 있다 — 시각별 캡처로 눈 확인한다.

**Why:** 사용자가 계획서를 받고 "계획대로 진행" — 확인 5가지는 전부 추천안으로 정했다.
**How to apply:** 속도·반복·색을 바꿔 달라면 `FileTreeAnimWidget` 클래스 상수(STEP_DELAY/UNFOLD)와 `paintEvent` 색만 보면 된다.
