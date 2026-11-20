# -*- coding: utf-8 -*-
# Motion Path Editor (A00630)
# 01.00  첫 버전 (계획서 docs/plans/A00630_MotionPathEditor_plan.md 1단계) — 고른 오브젝트 · 조인트의 프레임별 회전 피벗
#        월드 위치를 뷰포트에 경로(선 · 프레임 점 · 키 점 · 현재 프레임)로 그리고, Edit Path 에서 키를 클릭 · 박스 선택 ·
#        드래그(View / Ground / X / Y / Z)하면 translate 키 값이 바뀌어 애니메이션이 고쳐진다. 드래그 한 번 = undo 한 번.
#        부모 공간(parentMatrix)만 시간 문맥으로 한 번 굽고 자기 translate 는 애님 커브를 직접 평가 - 편집 때 씬을 다시 평가하지 않는다
#        (1,000 프레임: 키 하나 바꾼 뒤 갱신 0.002초 대 마야 Motion Trail 0.15초). 그리기 노드는 씬에 저장되지 않는다.
#        블렌더 애드온 Editable Motion Paths(GPL-3.0)의 아이디어를 독자 구현 - 코드는 쓰지 않았다.

# 01.01  드래그 에러 수정 - 키를 끌면 "[FAIL] Drag : function takes exactly 4 arguments (2 given)". 마야 2024 API 2.0 의
#        M3dView.viewToWorld 는 결과를 돌려주지 않고 넘긴 MPoint / MVector 를 채운다(OUT 인자) - 인자 2개로 불렀다.
#        편집 컨텍스트 흐름 시험 추가(가짜 뷰가 마야와 같은 모양이라 이런 호출 실수를 잡는다).
#        Range > Custom 에 A00110 과 같은 공용 범위 위젯(Get Current x2 · Get Sel Range), 실제 범위가 바뀔 때만 다시 굽기.
#        Edit Path 가 켜져 있으면 연한 빨강(공용 pin_style), Q · 다른 툴로 바꾸면 버튼도 꺼진다(ToolChanged).

# 01.02  Edit Path 를 켜면 편집은 되는데 버튼이 연한 빨강이 안 되던 것. 켜는 순간 마야가 "툴이 바뀌었다" 를 알릴 때
#        currentCtx() 가 아직 이전 툴이라, 그 즉시 판단한 v01.01 이 방금 켠 버튼을 다시 껐다(GUI 에서만).
#        이제 알림은 확인을 idle 로 미루기만 하고(evalDeferred), 컨텍스트 이름은 마야가 실제로 붙인 이름으로 비교한다.

# 01.03  애니메이션 레이어 - 툴 창 `Animation Layer` 목록(Base + 씬 레이어)에서 편집 레이어를 고르면 그 레이어의 키를 보여 주고
#        끌면 그 레이어 커브만 바뀐다. 경로는 늘 모든 레이어를 합친 실제 움직임. 블렌드 = weightA·아래 + weightB·레이어(실측) →
#        최종 translate 는 편집 레이어 값에 1차식 → 정확한 역산. 레이어 가중치(뮤트 · 솔로 · 가중치 애니)는 parentMatrix 와 함께 굽는다.
#        잠금: 레이어에 없음 · 레이어 lock · 효과 없음(뮤트 · 가중치 0 · 위 override). 레이어에 커브 없던 축은 상수로 커브를 만든다.
#        레이어 커브를 만든 편집을 undo 하면 마야가 블렌드 체인을 다시 계산하지 않아 낡은 위치가 남았다 → 표시 명령
#        junMotionPathDirty 를 묶음 맨 앞에 넣어 undo · redo 끝에 대상 + 블렌드 노드를 dgdirty.

# 01.04  Speed 탭 (계획서 docs/plans/A00630_MotionPathEditor_speed_graph_plan.md G0~G5) - 경로의 속도 그래프
#        (Speed / Position / Acceleration, 범위 Whole Path / Selected Keys / Around Current) 와 그 위 조작:
#        오른쪽 드래그 = Smooth 브러시(Speed: 경로 모양 · 키 프레임 유지, 타이밍만 / Shape: 경로 모양의 울퉁불퉁함),
#        곡선 끌기 = 그곳 빠르게 · 느리게, 키 선 끌기 = 키 시간 이동(포즈 전체), 빈 곳 = 스크럽. 획 하나 = undo 하나.
#        목표 움직임 → 애님 커브 refit(마야 Bezier 골든 1e-11, 기울기 최소제곱 + 필요한 곳만 키 추가, 가중 탄젠트 정확 분할).
#        Whole Pose = 같은 시간 왜곡을 rotate · scale 에도. 칠하는 동안 뷰포트에 원래 경로 회색 점선 + 새 프레임 점.
#        툴 창을 Path / Speed 탭으로 (tabFit).

# 01.05  그래프에서 획 · 끌기 뒤 Ctrl+Z / Z 를 눌러도 그래프가 되돌아가지 않던 것. 그래프 빈 곳 스크럽이 cmds.currentTime 을
#        마우스 이동마다 불렀는데, 스크립트의 currentTime 은 **부를 때마다 undo 하나**가 쌓인다(실측) - 획 뒤에 그래프를 조금만 훑어도
#        Ctrl+Z 가 획이 아니라 시간 변경만 한 프레임씩 되돌렸다. 스크럽을 API MAnimControl.setCurrentTime 으로(undo 큐 밖, timeChanged 는
#        그대로). 같은 프레임이면 부르지 않는다. 획 · 곡선 끌기 · Smooth Range 자체는 원래 undo 하나씩이었다(진단 시험).
#        그래프 키 선 끌기(키 시간 이동, 포즈 전체)를 없앴다 - 필요 없는 조작(사용자). 키 선 위 왼쪽 드래그도 스크럽.

VERSION = "01.05"
LAST_UPDATE = "2026-11-20"
