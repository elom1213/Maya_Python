---
name: wip-a00330-token-tab
description: "A00330_NamingTool v01.07 (2026-09-17) — 상위 탭 Rename(Token / Set Rename), Token 탭 = 칸 수 자유 토큰(Custom/Numbering) + Profile json. Numbering 개수가 세는 대상을 정한다. 마야는 숫자로 시작하는 이름의 숫자를 조용히 지운다"
metadata: 
  node_type: memory
  type: project
  originSessionId: 5782f0ec-e7f6-4339-aa79-6790d10548f6
  modified: 2026-09-17T07:44:04.752Z
---

`A00330_NamingTool` **v01.07** — 사용자 요청: Rename 탭을 만들어 Naming Dyn(→ **Token**) · Set Rename 을 하위 탭으로,
Token 칸마다 규칙 콤보(A00480 Export Naming 처럼), Add/Delete Token 으로 원하는 자리에 칸 추가·삭제 + 가로 스크롤,
규칙을 A00145 Attribute > Create 같은 Profile(json)로.

**설계에서 고른 것 (요청에 없던 결정)**
- **Numbering 개수 = 세는 대상**: 1 개 = 전체 노드 순번, 2 개 = 오브젝트 / 오브젝트 안 노드(레거시 Index1/Index2 그대로),
  3 개 이상 = 실행 안 함(셀 대상을 지어내지 않았다). 사용자가 "3번째 번호" 를 원하면 여기서 규칙을 새로 정해야 한다.
- 칸 고르기 = 칸 머리 checkable 버튼(배타 QButtonGroup). Add = 고른 칸 **오른쪽**, Delete = 고른 칸, 마지막 한 칸은 남김.
- 프로파일은 **칸을 고치면 즉시 저장**(A00145 와 같음), New = 지금 칸 복사. `data/` 는 **gitignore**(A00145/A00340 과 같이 PC 별),
  없으면 코드가 레거시 규칙 `Default` 를 만든다.
- 빈 Custom 은 건너뜀(`__` 없음), 네임스페이스 보존(레거시 rename_dynamics 는 루트로 옮겼다).

**실측 (Maya 2024)**: `cmds.rename` 은 잘못된 이름을 에러 없이 바꾼다 — `'01_a' -> '_a'`(앞 숫자 삭제), `'a-b' -> 'a_b'`.
→ `token_ops.validate` 가 Custom 은 `[A-Za-z0-9_]`, 숫자로 시작하는 이름은 막는다.

**Qt 함정 두 개**
- 테마 qss 에 `QPushButton:checked` 가 없는 테마(brown_dark)는 고른 버튼이 **안 보인다** → 버튼별 stylesheet 로 강조.
- 가로 전용 QScrollArea 는 sizeHint 를 오버라이드해도 **레이아웃이 테마 전 높이를 캐시해 8px 잘렸다** →
  안쪽 위젯 LayoutRequest/Polish 때 `setFixedHeight(inner + hbar + 2*frame)` 로 직접 고정(`TokenScrollArea`).
  오프스크린 창은 화면(800x600)보다 크면 `show()` 가 sizeHint 로 키우므로 가로 스크롤 검증은 `win.resize(min 폭)` 뒤에.

검증: mayapy 61항목(Default = 레거시 rename_dynamics 결과, 프로파일 전 흐름, 스크롤·최소 폭 불변). 마야 GUI 확인 전.
관련: [[wip-a00330-set-rename]], [[qt-exclusive-radio-uncheck-ignored]], [[offscreen-size-needs-theme]], [[wip-a00480-filetool]]
