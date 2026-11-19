# Changelog — A00630_MotionPathEditor

## v01.02 (2026-11-19)

- **[Fix] Edit Path 를 켜면 편집은 되는데 버튼이 연한 빨강이 안 되던 것** (마야 GUI 에서만).
  켜는 순간 마야가 "툴이 바뀌었다" 를 알리는데, 그때 `currentCtx()` 는 아직 이전 툴이다. v01.01 은 알림을 받자마자 판단해
  "편집 툴 아님" → 방금 켠 버튼을 다시 껐다(편집 툴은 켜진 채라 끌기는 됐다).
  이제 알림은 확인을 **idle 로 미루기만** 하고(마야가 전환을 끝낸 뒤 판단), 편집 컨텍스트 이름은 마야가 실제로 붙인 이름으로 비교한다.
  `Q` · 다른 툴로 나가면 버튼이 꺼지는 것은 그대로.
- 시험 `test_ui` 29 : GUI 의 순서(알림 때는 이전 툴 → idle 에 편집 툴)를 그대로 재현 - v01.01 코드로는 실패함을 확인. (mayapy 의 `evalDeferred` 는
  미루지 않고 바로 실행해서, 시험에서는 GUI 처럼 줄에 쌓는 대역으로 바꾼다.) **마야 GUI 확인 아직.**

## v01.01 (2026-11-19)

- **[Fix] 키를 끌면 에러** `[FAIL] Drag : function takes exactly 4 arguments (2 given)` 후 취소되던 것. 마야 2024 API 2.0 의
  `M3dView.viewToWorld` 는 결과를 돌려주지 않고 **넘긴 `MPoint` / `MVector` 를 채운다** — 인자 2개로 불렀다(v01.00 은 이 경로를 헤드리스로 돌려 보지 못했다).
  새 시험 `tests/test_edit_context.py` 19 : 누름 → 끌기 → 놓기 · 박스 선택 · Shift/Ctrl · Y 축 · 오른쪽 버튼 취소를 **마야와 같은 함수 모양의 가짜 뷰**로 끝까지 돌린다.
- **[UI] Range > Custom 에 `Get Current` · `Get Sel Range`** — A00110 과 같은 공용 범위 위젯(`JUN_mod_timeRange_qt_v01`). Get Current = 그 칸을 현재 프레임으로,
  Get Sel Range = 그래프 에디터 · 타임 슬라이더에서 고른 키의 처음 · 끝으로 두 칸을 함께. Custom 일 때만 켜지고, **실제 범위가 바뀔 때만** 다시 굽는다.
- **[UI] Edit Path 가 켜져 있으면 버튼이 연한 빨강** (공용 `pin_style`). `Q` 나 다른 마야 툴로 바꿔 편집이 꺼지면 버튼도 꺼진다(`ToolChanged` 이벤트).
- 시험 7종 126항목(`test_ui` 26). **마야 GUI 확인 아직.**

## v01.00 (2026-11-19)

- **첫 버전** — 계획서 `docs/plans/A00630_MotionPathEditor_plan.md` 의 0단계(실측) + 1단계(위치 경로 표시 + 키 드래그).
- 고른 오브젝트 · 조인트의 **프레임별 회전 피벗 월드 위치**를 뷰포트에 경로로 그린다: 선 · 프레임 점(간격 = 속도) · 키 점 · 현재 프레임 점 · (옵션) 프레임 번호.
  메시에 가려지지 않게 x-ray 로 그린다.
- **Edit Path**: 키 클릭 · Shift/Ctrl · 박스 선택, 선택 키 드래그(평면 View / Ground / 축 X · Y · Z) → translate 키 값이 바뀌어 애니메이션이 고쳐진다.
  여러 키 · 여러 경로를 함께. 부분 키(그 프레임에 다른 축 키가 없음)는 처음 움직일 때 **모양을 지키며** 키를 채운다. 잠긴 축은 그대로.
  **드래그 한 번 = undo 한 번**(채운 키까지). 오른쪽 버튼 = 드래그 취소.
- **속도**: 부모 공간(`parentMatrix`)만 시간 문맥으로 한 번 굽고, 자기 translate 는 애님 커브를 직접 평가한다 → 편집 때 씬을 다시 평가하지 않는다.
  실측(mayapy 2024, 1,000 프레임): 키 하나 바꾼 뒤 갱신 **0.002초** 대 마야 Editable Motion Trail **0.15초**, 드래그 한 번 갱신 3.4 ms.
  처음 만들기(굽기)는 Motion Trail 과 비슷하다(0.14 ~ 0.19초).
- 그래프 에디터 편집 · undo/redo 에 경로가 따라온다. 부모 · 컨스트레인트 애니메이션을 바꿨으면 **Refresh**.
- 잠금(이유를 로그 · 표시): translate 가 컨스트레인트 · 표현식 등으로 구동, 애니메이션 레이어 · pairBlend(아직 지원 안 함), 세 축 모두 lock.
- 그리기 노드는 **씬에 저장되지 않고 undo 큐에도 들어가지 않는다**. 저장 직전에 잠깐 지워 파일에 플러그인 `requires` 줄도 남지 않는다 → 툴 없이도 파일이 그대로 열린다.
- 블렌더 애드온 *Editable Motion Paths*(GPL-3.0-or-later)의 아이디어를 **독자 구현** — 코드는 쓰지 않았다.
- 시험(mayapy): `test_path_math` 19 · `test_anim_channels` 15 · `test_edit_session` 21 · `test_watcher` 20 · `test_ui` 18 · `test_picking` 13, 실측 `bench_motion_path.py`.
  **뷰포트 그리기 · 마우스 편집은 마야 GUI 확인 아직.**
