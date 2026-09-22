---
name: wip-a00380-meshdoctor-tab
description: A00380_MeshTool v01.14 — A00300_meshDoctor 를 MeshDoctor 탭으로 통째 이식(첫 번째 탭) + 아이콘 새로
metadata:
  type: project
---

2026-09-22, A00380_MeshTool **v01.14**. 옛 `A00300_meshDoctor` 를 **MeshDoctor 탭**으로 옮겼다.
탭 순서는 **MeshDoctor → Peak → Match** (무엇이 잘못됐는지 보고 나서 고치는 순서).

## 이식

`app/core/` 의 `mesh_scan.py` · `mesh_fix.py` · `report.py` 를 **로직 그대로** 복사했다.
바꾼 것은 패키지 경로(`tools.A00300_meshDoctor` → `tools.A00380_MeshTool`) 2곳과 리포트 머리말뿐.
외부 의존이 `Framework.core.maya_shape` 와 자기 패키지밖에 없어 깨끗했다.

★ **충실한 이식인지는 결과로 확인한다** — 같은 씬에서 두 툴의 `MeshScanner.scan_nodes()` 결과를
JSON 으로 덤프해 비교하면 된다(완전히 동일했다). UI 검증보다 이쪽이 이식의 근거가 된다.

## 탭에서 바꾼 것

- 대상 리스트 : 손수 만든 `QListWidget` → **공용 TSL**([[framework-tsl-attach-uuids]]). 이 툴이 이미 쓰고 있었다.
- 상세 리포트 : 공용 로그창이 아니라 **탭 안의 리포트 뷰**. 공용 로그창은 높이 110 의 한 줄짜리
  상태 표시줄이라 수십 줄 리포트를 쏟으면 둘 다 못 읽는다([[framework-log-widget]]).
- 진단 직후 **가장 심한 메시를 자동으로 펼친다**, 표의 행 클릭은 상세 + **씬 선택**.
- 리포트는 이제 `A00380_MeshTool/0020_out/` 에 쌓인다.

## 창 크기

테마를 입히고 잰 최소는 **748 x 805**. 폭을 끄는 것은 MeshDoctor 탭(457)이 아니라 **Match 탭(722)** 이다.
예전 `380 x 520` 은 진작부터 최소보다 작아 Qt 가 늘려 주던 값이었다 → 실측값 `760 x 860` 으로 적었다.
([[offscreen-size-needs-theme]])

## 아이콘

요소 셋 — 누운 와이어프레임 격자(대상) · 버텍스를 노말 방향으로 끌어올리는 화살표(편집) ·
오른쪽 아래 십자 배지(진단). 32px 에서 읽히는지 실제로 구워 확인한다([[new-tool-needs-icon]]).
**`dev/build_icons.py` 는 전 툴의 png 를 다시 쓴다** — 한 아이콘만 바꿀 때는 같은 Qt 렌더 코드
(`QSvgRenderer` → `QImage(32,32,ARGB32)`)를 그 파일에만 돌려 무관한 diff 를 만들지 않는다.

옛 `A00300_meshDoctor` 는 관례대로 **지우지 않고 남겼다**(문서 머리에 이사 안내).
마야 GUI 실기 확인은 아직. 자세한 것은 `JUN_All/docs/A00380_MeshTool.md` §3-4.
