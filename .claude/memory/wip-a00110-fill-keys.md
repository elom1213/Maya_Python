---
name: wip-a00110-fill-keys
description: "A00110 Key Edit > Fill Keys — 구간 전 프레임 키 채우기 + Key Edit 하위 탭 재편 (v01.40)"
metadata:
  node_type: memory
  type: project
---

A00110_animTool **v01.39→01.40** (2026-08-11).

**① 탭 재편** — 최상위였던 `Pose Key` / `Euler Filter` 를 Key Edit 하위 탭으로 내렸다.
최상위 8→**6탭**, Key Edit 하위 **8탭**(Move Keys / Fill Keys / Pose Key / Graph / Offset & Hold /
Stagger / Euler / Delete All). 하위 탭이 늘어 창 기본 폭 520→620.
([[prefer-subtabs-over-stacked-collapsibles]] — 이 툴은 스크롤 대신 fit page)

**② Fill Keys (신규)** — 고른 채널의 `[Start, End]` **모든 프레임**에 키를 채운다. 이미 키가 있는
프레임은 방치, 빈 프레임만 지금 값으로 → **애니메이션 불변, 키만 촘촘해진다.**

- 어트리뷰트 목록 UI 는 A00145_RigConnect **Connect 탭 구성**(왼쪽 오브젝트 TSL + `List Attributes`,
  오른쪽 목록 + 공용 Filter + `Select All`). 구간은 공용 `MOD_timeRange_qt_v01`.
- 나열 기준: `listAttr(keyable=True, visible=True, unlocked=True)` — **키 가능 + 채널박스 노출 +
  안 잠김**. 채널박스에만 보이고 키는 못 찍는 채널(`-k false -cb true`)은 제외. 여러 오브젝트는
  **합집합**(첫 등장 순서), 실행 시 그 채널이 없는 오브젝트는 건너뛰고 개수만 알린다.
- **애니메이션 레이어 콤보**: `(current)` = 레이어 인자 미전달(마야가 평소대로) / 레이어 이름 =
  그 레이어에 키. 채널이 레이어에 없으면 자동으로 넣어 준다. `Refresh` 로 재조회.

Maya 쪽 함정(insert 가 커브 없으면 no-op, 값 미리 계산, 레이어 역산)은
[[setkeyframe-insert-needs-existing-curve]] 참고.

검증: 코어 10그룹 + UI 6그룹 헤드리스 통과 ([[mayapy-headless-verify]],
[[qapplication-before-maya-standalone]]).
