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

VERSION = "01.03"
LAST_UPDATE = "2026-11-19"
