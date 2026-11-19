# Changelog — A00630_MotionPathEditor

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
