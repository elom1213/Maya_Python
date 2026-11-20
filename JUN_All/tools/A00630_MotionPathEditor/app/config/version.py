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

# 01.06  Speed 탭 Frames 에 Custom - 공용 Start / End / Get Current / Get Sel Range(Path 탭 Range 와 같은 위젯)로
#        [Start, End] 구간만 그래프로 본다. 경로 범위로 자르고, 안 겹치면 그래프 자리에 안내. 값은 optionVar(graph_start · graph_end).

# 01.07  키를 끌면 "[FAIL] Drag : module 'maya.cmds' has no attribute 'junMotionPathDirty'". 마야를 켠 채 툴만 새 버전이 되면
#        (DEV 리로드 · 새 버전 복사) 처음 읽힌 v01.00~02 플러그인이 그대로 남는다 - ensure_plugin 이 "이미 읽힘" 이면 손대지 않았다.
#        플러그인에 PLUGIN_VERSION("1.4") · COMMANDS 를 두고, 툴 창을 열 때 읽힌 버전 · 명령을 비교해 다르면 그리기 노드를 지우고 다시 읽는다.
#        undo 큐에 옛 플러그인 명령이 있으면 마야가 내려놓기를 거부한다(실측 "still in use") → 그때만 undo 큐를 비우고 로그로 알린다.
#        **플러그인 파일을 고치면 PLUGIN_VERSION 을 올릴 것.**
#        (같은 날 보충) 첫 판은 마야 GUI 에서 "Could not load the plugin" 으로 창이 안 열렸다: 같은 경로에서 다시 읽으면 새 코드가 도는데도
#        `pluginInfo -version` 은 처음 값 "1.0" 을 계속 돌려준다(실측) → 교체 뒤에도 옛것으로 판정. 이제 읽힌 코드에 묻는 명령
#        junMotionPathVersion 으로 비교한다(PLUGIN_VERSION "1.5"). 중간에 실패한 창을 닫을 때 'speed_panel' 없음 에러도 막았다.

# 01.08  Acceleration 그래프도 스무딩 - 브러시 Smooth Acceleration (retime.AccelSmoother): 점들을 시간 축 가우스 평균 쪽으로 당긴다
#        (가속도 = 위치의 2차 차분을 직접 줄인다, 되밀지 않음 - 모양 · 타이밍이 함께). refit 허용 오차 1/5(위치 오차의 2차 차분이 가속도 잡음).
#        Show 를 Acceleration 으로 바꾸면 브러시도 저절로 이것, 나오면 그 전 브러시로. 실측(칠한 구간): 최대 0.057 → 0.017, 평균 −67%.
#        그 전에는 Acceleration 그래프를 칠하면 Speed/Shape 브러시가 돌았다 - Smooth Speed 는 꺾인 곳을 빨리 지나가게 해 최대 가속도를
#        0.057 → 0.197 로 키웠고, Smooth Shape 는 큰 호를 지켜 10% 밖에 못 줄였다.

# 01.09  프레임 점 고르기 + 폴오프 (매니퓰레이터 · 폴오프 계획서 docs/plans/A00630_MotionPathEditor_manipulator_falloff_plan.md G1) -
#        Edit Path 에서 키뿐 아니라 프레임 점도 클릭 · 박스로 고른다(같은 자리면 키 먼저, Frame dots 를 끄면 안 고른다).
#        Edit 줄 `Falloff` · Radius(프레임, 경로를 따라 잰 거리) · Curve...(공용 falloff 커브 팝업, 기본 Smooth). 범위의 점 · 선이
#        가중치 색(노랑 1 → 주황 → 빨강 0)으로 칠해진다. 뷰포트에서 b 톡 = 켜기 / 끄기, b + 좌우 끌기 = 반경(Ctrl+Shift + 끌기도 같다).
#        b 는 마야 핫키(소프트 셀렉션 반경)로 가지 않게 편집 툴이 켜져 있을 때만 앱 이벤트 필터가 먹는다(G0-2 GUI 실측).
#        폴오프 선은 색 단계마다 lineStrip (G0-1: mesh(kLineStrip) 은 x-ray 가 안 먹어 메시에 가려진다). 플러그인 1.6.
#        고른 점을 폴오프로 끌기 · 프레임 점 끌기는 다음 버전(G2) - 지금은 로그로 안내만.

# 01.10  프레임 점 · 폴오프 끌기 (계획서 G2) - 프레임 점을 골랐거나 폴오프가 켜져 있으면 끌기가 deform: 고른 점 = 1, 둘레는 가중치만큼.
#        끄는 동안 미리보기(원래 경로 회색 점선 + 새 경로), 놓을 때 Speed 탭과 같은 refit 으로 키에 쓴다(키 프레임 유지 · 필요한 곳만 키 추가,
#        범위 밖 불변, 레이어는 편집 레이어만). 경로 여럿이어도 Ctrl+Z 한 번. 키만 고르고 폴오프를 끄면 예전 키 끌기(끄는 동안 바로 따라옴).
#        끄는 기준 = 누른 픽셀 광선과 끌기 평면의 교점(점 자체로 하면 안 움직인 클릭도 0.02 cm 튀어 키를 썼다).
#        [Fix] v01.09 폴오프 색 선 · 경로 선이 메시에 가려졌다(사용자 GUI) - VP2 x-ray 는 점에만 먹고 3D 선은 전부 가린다 →
#        선(경로 · 폴오프 · 원래 경로)을 그릴 때마다 화면 픽셀로 투영해 2D 로(screen_strips, 7,000 점 약 6 ms). 플러그인 1.7.

# 01.11  매니퓰레이터 (계획서 G3) - Edit Path 에서 고른 점들의 무게중심에 이동 · 회전 기즈모(화면 크기 고정, 화면 2D 로 그려 메시에 안 가림).
#        Move: 축 화살표 · 평면 사각형 · 가운데(= Drag in 평면/축), Rotate: 축 고리 · 바깥 화면 고리. 고른 점 = 1, 폴오프 범위는 가중치만큼
#        (회전은 각도 x 가중치). 축 World / Path(접선 · 위 · 옆). 뷰포트 w / e = Move / Rotate (이 툴일 때만 먹는다). Shift / Ctrl 클릭은 늘 점.
#        키만 + 폴오프 끔 + 이동 = 예전 키 끌기(끄는 동안 오브젝트가 따라옴), 그 밖은 deform(미리보기 → 놓을 때 refit, undo 한 번).
#        refit 커브 평가를 벡터화 - 매 프레임 키 6,000 개 커브에서 놓기 986 → 240 ms (구간마다 Python 루프였다). 플러그인 1.8.

# 01.12  Speed 탭 + 폴오프 (계획서 G4) - Speed 탭에도 Edit Path(Path 탭 버튼과 같은 편집 툴 하나, 늘 같은 상태). 뷰포트에서 끄는 동안
#        그래프가 라이브로 따라온다(관리자 미리보기). 고른 점의 폴오프 [a, b] 를 그래프 배경에 가중치 색 띠로, Frames > Falloff = [a, b] ± 반경.
#        고른 점이 있으면 Smooth Range = 그 폴오프 범위만 가중치만큼 위치 스무딩(Smooth Shape / Acceleration 결과를 w 로 섞음, 범위 밖 그대로,
#        Smooth Speed 브러시면 Shape 로 대신). 기즈모 굵기 1.5 배(사용자 요청). 플러그인 1.9.

# 01.13  Path 탭 `Drag in` 줄을 숨김(사용자: 필요 없다 - 매니퓰레이터 축 · 평면이 대신). 코드 · 설정은 그대로(main_window.SHOW_DRAG_IN),
#        숨긴 동안은 View 로 움직인다(예전에 고른 Y · Ground 가 안 보이게 계속 먹지 않도록, 저장값은 지우지 않음).

VERSION = "01.13"
LAST_UPDATE = "2026-11-20"
