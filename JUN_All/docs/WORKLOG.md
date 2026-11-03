---
title: 작업 일지 (WORKLOG)
aliases: [WORKLOG, 작업일지, devlog]
tags: [worklog, maya-python]
updated: 2026-11-03
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
| 2026-10 | [`worklog/2026-10.md`](worklog/2026-10.md) | 14일 |
| 2026-09 | [`worklog/2026-09.md`](worklog/2026-09.md) | 16일 |
| 2026-08 | [`worklog/2026-08.md`](worklog/2026-08.md) | 18일 |
| 2026-07 | [`worklog/2026-07.md`](worklog/2026-07.md) | 18일 |
| 2026-06 | [`worklog/2026-06.md`](worklog/2026-06.md) | 12일 |

---

## 2026-11-03 (오늘)

> [!summary] A00510_release_builder **v01.04 마야 UI 테마 오염 수정 + `Run_ReleaseBuilder.bat` · 아이콘 바로가기** `#A00510_release_builder`
- 요청: "__dragDrop_A00510 툴을 마야에서 쓰니 마야의 모든 UI 가 이 툴의 UI 와 유사하게 변한다. 마야 UI 가 변하지 않도록. 그리고 실행 bat 파일과, 그 파일의 아이콘도 평소에 보이도록."
- 원인: `launch.run()` 이 마야 안에서도 `ThemeManager.load_theme_dev(app, ...)` 로 qss 를 **QApplication(=마야)** 에 입혔다. 덤으로 launch import 만으로 AUMID 를 지정해 마야 프로세스의 작업 표시줄 ID 도 바꿨다.
- 수정: 앱 전역(qss · 앱 아이콘 · AUMID)은 이 프로세스가 앱을 만들 때만, 마야 안에서는 `load_theme_to_widget(win)` 로 창에만. 다시 누르면 이전 창을 닫는다.
- bat: `Run_ReleaseBuilder.bat` — PySide6/2 있는 64비트 파이썬을 찾아 pythonw 로 실행(설치 없음). `.bat` 은 아이콘을 못 가지므로 `make_shortcut.py` 가 툴 아이콘 + AUMID 를 박은 `Release Builder.lnk` 를 같은 폴더에 만든다(공용 `shell_integration.create_shortcut`, 절대 경로라 gitignore, 스탬프로 바뀔 때만 재생성).
- 오프스크린 검증: 마야 상황(앱 선존재)에서 앱 qss · 다른 위젯 · AUMID 그대로, 창에만 qss · standalone 은 앱 qss 후 정상 종료 · bat `--no-launch` 로 바로가기 생성 확인. **실제 마야 GUI 확인 아직.**

> [!summary] A00210_FileManager **v01.43 Maya > Reference `Delete Display Layers` · `Delete Anim Layers`(기본 ON) + 탭 스크롤 제거** · Framework tabFit **PySide6 수정** `#A00210_FileManager` `#Framework`
- 요청: "각 탭 세로 길이를 줄이든 UI 에 맞게 조절되든 스크롤로 보지 않게. Maya / Reference 탭에 선택한 씬의 모든 레이어, 애니메이션 레이어를 지우는 체크박스(기본 둘 다 체크)."
- 원인: v01.42 의 탭 높이 자동 맞춤이 **PySide6 에서 한 번도 돌지 않았다** — `MOD_tabFit_qt_v01` 이 `int(QSizePolicy.Policy)` 로 TypeError → 매번 `fit skipped`. `_enum_int()` 로 고침(PySide2 동작 그대로).
  덤으로 `tabs_scroll` 안 탭의 hfw 보정 오차(Export 가 File Manager 높이로 열림)도 고침. 롤아웃 시험 **31 툴 · 134 검사 · 0 실패**.
- 축소: 공용 `MOD_fileTree_qt_v01` 에 `tree_hint_height`(기본 None = 그대로), A00210 의 리스트 · 트리 · 표 sizeHint 를 짧게, File Manager Settings 한 줄 절약.
  실화면 실측(작업 영역 2560x1552) File Manager 1480 → 1348 · Reference 987 · Export 1363, **모든 탭 스크롤바 없음.**
- 레이어: `ref_importer.delete_display_layers` / `delete_animation_layers` — 임포트 · 네임스페이스 뒤, 저장 전. 레퍼런스로 남는 것의 레이어는 건너뜀. 애니 레이어는 루트 삭제(`delete BaseAnimation;` 과 같음).
  mayapy 2024 실측: 디스플레이 3 · 애니 4 삭제, 남은 레퍼런스 레이어 `K:KEEP_LYR` 유지, 오브젝트 · Base 커브(0, 3) 유지. A00210 시험 32/32 · 50/50. **실제 파일 GUI 확인 아직.**

> [!summary] A00130_ControlRig_V02 **v02.30 Match 표 체크박스 — 체크된 행만 Match, 나머지 세트는 그대로** `#A00130_ControlRig_V02`
- 요청: "Match 탭 목록마다 체크박스, 체크된 것만 Match, 안 된 것은 방치. 기본은 전부 체크, 모두 체크 / 모두 해제 버튼."
- 구현(UI 만, `match_manager` 는 그대로): 행 0열 체크박스 + `Check All` · `Uncheck All` · `n / m checked`. `on_match` 가 체크된 행만 `match_manager.apply` 에 넘긴다. 체크 해제는 (조인트, 세트_wanted) 키 집합으로 기억해 표를 다시 그려도 유지. 다중 선택 전파는 공용 `JUN_mod_checkTree_qt_v01`.
- IK 세션은 체크와 무관하게 `D01_IK_handle` 전체 — 해제된 세트가 IK 체인이면 닫을 때 폴 평면 맞춤으로 움직일 수 있다(문서 §4.1e 에 명시).
- mayapy 2024 오프스크린 **13/13** (해제 행 원점 유지 · 체크 행 이동 · 갱신 후 유지 · Uncheck All 무동작 · Check All · 다중 전파). **마야 GUI 확인 아직.**

> [!summary] A00110_animTool_V02 **v02.35 Hot Key > Main `Animation Layers > Delete BaseAnimation` — MEL `delete BaseAnimation;` 과 같은 결과** · A00030_quickTool_V02 v02.10 에서 제거 `#A00110_animTool_V02` `#A00030_quickTool_V02`
- 요청: "delete BaseAnimation 이 mel 명령이 친 것과 같은 결과가 되도록 버튼을 추가." → 처음엔 A00030 v02.09 에 넣었다가 "A00110_animTool_V02 / Hot Key / Main 에 이식하고 A00030 에서 빼" 로 옮겼다. A00030 v02.10 은 코드가 v02.08 과 같다(이력만 남김).
- 구현: `AnimLayerManager.delete_root()` — 루트를 `animLayer -q -root` 로 찾아(이름을 박지 않음) `cmds.delete`. 마야가 자식 레이어 · blend 노드 · 레이어 커브를 지우고 Base 커브를 다시 직접 연결한다. UI 는 Hot Key > Main 의 새 `Animation Layers` 그룹 버튼 + 확인 팝업(기본 No), 지운 뒤 View > Layers 갱신. 되돌릴 수 없어 단축키는 걸지 않았다.
- mayapy 실측: 레이어 3단에서 mel 과 **남은 노드 · 프레임 1/5/10 값 · tx 입력 연결이 같다**. 이 삭제는 **undo 로 레이어가 돌아오지 않아서**(standalone, undo 켠 상태) 팝업을 둔다. 시험 `tests/test_anim_layers.py` **46/46**(D1~D6 추가). **마야 GUI 확인 아직** — 팝업 · GUI 에서의 undo.

---
