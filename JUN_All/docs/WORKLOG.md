---
title: 작업 일지 (WORKLOG)
aliases: [WORKLOG, 작업일지, devlog]
tags: [worklog, maya-python]
updated: 2026-10-01
---

# 작업 일지 (WORKLOG)

git 커밋 기록을 근거로 하루 작업을 요약한다. 최신 날짜가 위.

**이 파일은 현재 월을 담는다.** 지난 달은 [`worklog/`](worklog/) 로 내려간다 —
파일 자체는 늘 이 경로에 있으므로 이 문서를 가리키는 링크는 깨지지 않는다.
트리거와 절차는 [`worklog/README.md`](worklog/README.md).

> [!info] 보기
> Obsidian 에서 `JUN_All/docs` 를 vault(또는 폴더)로 열면 속성/태그/링크가 동작한다.
> 굵게/링크가 별표째 보이면 소스 모드이므로 `Ctrl+E` 로 읽기/라이브 프리뷰 전환.

---

## 지난 달 보관

| 월 | 파일 | 작업일 |
|----|------|--------|
| 2026-09 | [`worklog/2026-09.md`](worklog/2026-09.md) | 16일 |
| 2026-08 | [`worklog/2026-08.md`](worklog/2026-08.md) | 18일 |
| 2026-07 | [`worklog/2026-07.md`](worklog/2026-07.md) | 18일 |
| 2026-06 | [`worklog/2026-06.md`](worklog/2026-06.md) | 12일 |

---

## 2026-10-01 (오늘)

> [!summary] A00480 FileTool · A00330 NamingTool — **토큰 칸을 고쳐도 프로파일에 저장 안 함, `Save` 버튼으로만** (A00480 v01.07->01.08 · A00330 v01.10->01.11)
- 요청: A00480 Naming 에서 프로파일을 골라 칸에 글자를 넣고 툴을 닫았다 열면 고친 칸이 그 프로파일의 기본이 돼 있다(알림 없이). 버튼을 눌렀을 때만 기본이 되게, 누르지 않으면 어떤 프로파일도 바뀌지 않게.
- 원인: 공용 위젯 `Framework/qt/MOD_tokenName_qt_v01.py` 의 `_after_edit()` 가 칸이 바뀔 때마다 `store.save_profile()` 을 불렀다.
- 수정(공용 위젯 — **A00330 Token 탭도 같이 바뀐다**): 자동 저장 제거, Profile 줄 콤보 오른쪽에 **`Save`** (`save_profile()`). 로드 직후 `tokens()` 를 기준으로 잡아 `is_dirty()` — 저장 안 한 변경이 있을 때만 Save 가 켜지고, 고쳤다 되돌리면 꺼진다. 저장 안 한 칸은 프로파일 전환(`[WARN] ... unsaved edits ... were dropped.`) · 창 닫기 때 버려진다. `New` 는 지금 칸을 새 프로파일에 저장(떠나온 프로파일은 그대로).
- 검증(오프스크린 PySide6, 임시 data): 편집 → 위젯 다시 만들기 = 원래 6칸(SK_MANU_CH_Name_Basic_Version) · Save 후 다시 만들기 = 고친 칸 · 되돌리면 dirty False · New 후 편집 → 전환 시 WARN.
- 창 폭: Save 버튼만큼 A00480 창 최소 폭 882 → 954px (mayapy 2024 오프스크린 slate_dark). 원래 맞춘 960 안. 마야 GUI 확인 전.

> [!summary] A00240 PathTool — **Change Profile: 카테고리를 버튼째 다른 프로파일로 이동** (v01.13->01.14)
- 요청: Category 버튼으로 만든 카테고리를 좌클릭하면 `Change Profile` 이 나오고, 고른 프로파일로 그 카테고리와 안의 버튼 전부가 옮겨지게.
- 구현: 카테고리 박스를 좌클릭 콜백을 받는 `_CategoryBox(QGroupBox)` 로 바꿨다(Framework Qt 바인딩에 `Signal` 이 없어 콜백). Path 버튼은 자기 클릭을 소비하므로 **헤더 · 버튼 사이 빈 곳**을 누를 때만 메뉴가 뜨고, 버튼 클릭은 그대로 경로 열기. 같은 항목을 우클릭 메뉴에도 넣었다.
- 이동 로직은 core `prefs.move_category(src, dst, name)` (UI 비의존). 대상에 같은 이름 카테고리가 있으면 **끝에 합치고**, 버튼 이름이 겹치면 **아무것도 안 옮기고** 겹친 이름을 알린다. 저장은 **대상 → 현재** 순(중간 실패 시 사라지지 않고 양쪽에 남게).
- 검증(오프스크린 PySide6, 임시 data 폴더): 좌클릭 메뉴 = `['Change Profile']` · 버튼 클릭은 경로 열기만 · 새 카테고리 이동 · 이름 충돌 시 무변경 + 경고 · 같은 이름 카테고리에 합치기 · 활성 프로파일 유지.
