---
name: wip-a00240-shrink-anim
description: "A00240 Shrink(v01.10, 350x78 = A00220 줄었을 때 가로 · 세로 절반) + 파일 트리 애니메이션은 계획서 단계, 확인 5가지 대기"
metadata: 
  node_type: memory
  type: project
  originSessionId: 8fc27b42-f7ec-4155-b340-da985ee075b0
  modified: 2026-09-18T01:17:45.673Z
---

A00240_PathTool v01.10 (2026-09-18): Help 메뉴 + **Shrink** — 탭·메뉴 바를 감추고 **350 x 78**.
기준은 A00220_BackupTool 이 줄었을 때 350 x 155 (green_mid 오프스크린 실측, [[wip-a00220-shrink]]).
애니메이션 자리 `anim_area` 는 버튼 **옆**(아래로 두면 그릴 높이 20px) → 172 x 56.

**다음 (v01.11)**: 파일 트리 자라나는 애니메이션 — `docs/plans/A00240_PathTool_shrink_animation_plan.md`.
7행을 56px 에 넣는 게 제약 → 줄었을 때만 여백 2px(한 행 10px) · 7x9 픽셀 아이콘 추천.
사용자 확인 대기: 다 자란 뒤 정지/반복, 여백 2px 안, 펼침 0.25s, 색(테마 글자색), 켤 때마다 재생.

**Why:** 사용자가 "Shrink 를 만들고 애니메이션 계획서를 작성해" — 애니메이션 구현은 아직 요청 전.
**How to apply:** 애니메이션 요청이 오면 계획서 6장 답을 먼저 확인하고 `app/ui/file_tree_anim.py` 로.
