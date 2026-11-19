# -*- coding: utf-8 -*-
# Motion Path Editor (A00630)
# 01.00  첫 버전 (계획서 docs/plans/A00630_MotionPathEditor_plan.md 1단계) — 고른 오브젝트 · 조인트의 프레임별 회전 피벗
#        월드 위치를 뷰포트에 경로(선 · 프레임 점 · 키 점 · 현재 프레임)로 그리고, Edit Path 에서 키를 클릭 · 박스 선택 ·
#        드래그(View / Ground / X / Y / Z)하면 translate 키 값이 바뀌어 애니메이션이 고쳐진다. 드래그 한 번 = undo 한 번.
#        부모 공간(parentMatrix)만 시간 문맥으로 한 번 굽고 자기 translate 는 애님 커브를 직접 평가 - 편집 때 씬을 다시 평가하지 않는다
#        (1,000 프레임: 키 하나 바꾼 뒤 갱신 0.002초 대 마야 Motion Trail 0.15초). 그리기 노드는 씬에 저장되지 않는다.
#        블렌더 애드온 Editable Motion Paths(GPL-3.0)의 아이디어를 독자 구현 - 코드는 쓰지 않았다.

VERSION = "01.00"
LAST_UPDATE = "2026-11-19"
