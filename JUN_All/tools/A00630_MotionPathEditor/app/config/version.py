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

VERSION = "01.01"
LAST_UPDATE = "2026-11-19"
