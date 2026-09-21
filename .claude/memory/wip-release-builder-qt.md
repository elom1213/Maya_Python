---
name: wip-release-builder-qt
description: dev/release_builder_QT — 툴을 골라 릴리즈 폴더로 복사하는 개발용 Qt 창. v01.02 에 목록 필터 · 공용 로그창 · 아이콘(작업 표시줄 AUMID 포함)
metadata:
  node_type: memory
  type: project
---

`JUN_All/dev/release_builder_QT` — 툴을 체크해 **릴리즈 폴더로 복사**하는 개발용 Qt 창
(`dev/build_release.py` 의 후신). 배포 대상이 아니라 개발 도구라 `tools/` 가 아닌 `dev/` 에 있다.
복사 로직 `app/core/release_builder.py` 는 **Qt 비의존**.

**v01.02 (2026-09-21, 사용자 요청 셋)**

- **목록 필터** — 공용 [[framework-filter-widget]] `JUN_mod_filter_qt_v01`. 툴이 **66개**라
  눈으로 찾는 게 일이었다.
- ★ **체크와 필터는 따로 논다** (Qt 는 숨긴 항목의 체크를 유지한다):
  `Select All` / `Clear` 는 **보이는 것에만** 걸고, `Release` 는 **가려진 채 체크된 것도
  내보내되 개수를 로그로 알린다.** 체크는 명시적 의사표시라 없던 일로 만들지 않되 모르고
  나가지도 않게 — `A00145_RigConnect` Attribute 탭과 같은 판단.
  `Refresh` 뒤에는 `flt.refresh()` 를 불러 **필터 글자를 지킨 채** 다시 먹인다.
- **로그창**을 공용 [[framework-log-widget]] 로 교체. ★ 공용 위젯의 `append()` 는
  **HTML 을 해석**하므로, 경로와 `=` 구분선이 들어가는 이 로그는 **`appendPlainText`** 로 쓴다.
- **아이콘** 신규 (`icon/release_builder_QT.svg|.png|.ico`) — 열린 상자 + 위로 나가는 화살표.
  이 툴은 **터미널 실행**이라 [[standalone-taskbar-icon-method]] 를 그대로 따랐다:
  각 크기를 **SVG 에서 직접 렌더**(축소 금지) → **가장 큰 프레임을 base** 로 `.ico` 저장 →
  `QApplication` **앞에서** `SetCurrentProcessExplicitAppUserModelID`. 새
  `app/config/app_meta.py` 가 아이콘 경로와 AUMID 를 들고 있다.
  - 래스터라이즈는 **mayapy + PySide2 QSvgRenderer** 로, `.ico` 조립은 **시스템 python +
    Pillow** 로 했다 — **mayapy 에는 Pillow 가 없다**(시스템 python 에는 12.2 가 있다).

검증: 오프스크린 Qt **30항목**. 문서 `docs/release_builder_QT.md`(신규).
실제 릴리즈 복사는 안 돌려 봤다(목적지가 외장 드라이브 경로).
