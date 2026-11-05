# Anim Key Tool
# 02.22  Pin 켜짐(Pinned) = 연한 빨강 - 공용 Framework/qt/pin_style (A00240_PathTool 과 같은 색).

# 02.23  Follow 탭 `Point` 체크박스 - Maintain Offset 의 위치를 pointConstraint 처럼(target 이 돌아도 공전 안 함).
#        끄면 예전 그대로 parentConstraint 처럼. Maintain Offset + Translate 일 때만 켤 수 있다.

# 02.24  Follow 탭 `Maintain Offset` 기본 켜짐(예전엔 꺼짐).

# 02.25  View > Graph Focus `Layer curves` 콤보 - 애니메이션 레이어가 있을 때 그래프 에디터의 레이어 필터
#        (View > Animation Layer Filter)를 Selected / Active / Active+Selected / All 로 걸고, 세로(Fit value)
#        맞춤도 **그 필터로 보이는 커브만** 잰다. 예전엔 `keyframe -q -name` 이 활성 레이어 커브만 돌려줘
#        Layer1 선택 시 ±200 에 맞추는데 화면엔 베이스 ±400 도 겹쳐 보였다. 기본 Selected(없으면 활성 → 전부),
#        `Keep` 은 GE 설정을 건드리지 않고 그대로 따른다. 레이어 없는 씬은 영향 없음.

# 02.26  Bake > Counter Layer 탭 신설 - global_ctl 만 든 레이어(lyr_glo)가 바꾼 자식(발)의 **월드** 위치·회전을
#        lyr_glo 뮤트 상태와 같게 되돌리는 보정 additive 레이어를 만든다. 레이어를 뮤트해 worldMatrix 를 스냅샷
#        -> xform -ws -m 으로 로컬 T/R -> setKeyframe -animLayer -value 역산(누적 모드 · 가중치 · override 는 마야가).
#        긴 구간(1000+ 프레임)은 200 프레임 청크로 스냅샷해 메모리가 구간 길이와 무관. 잠긴 · 컨스트레인트 채널은
#        건너뛰고 경고, 구간 밖은 identity 키, 바뀌지 않은 오브젝트는 키 없음. 계획서
#        docs/plans/A00110_animTool_V02_counter_layer_plan.md, 회귀 tests/test_counter_layer.py.

# 02.27  Bake > Merge Layers 탭 신설 - 애니메이션 레이어를 **프레임 구간 [Start, End] 안에서만** 병합
#        (`a + b => b` 기존 레이어 / `=> 새 레이어` / `a + Base => Base`). 마야 Merge Layers 의 본체인
#        `bakeResults -destinationLayer X -resolveWithoutLayer a b` 를 그대로 쓰되 `-time s:e -preserveOutsideKeys` 로 구간만 굽고,
#        마야가 소스를 지우던 자리에서 소스의 구간 안 기여를 중화한다(additive = 구간 키 삭제 + identity 키 step,
#        override = weight 를 구간에서 0 으로 계단 키). 경계 s-1 / e+1 은 `setKeyframe -insert` + `keyTangent fixed`.
#        Base 가 대상이면 임시 additive 레이어를 맨 아래에 굽고 base 커브에 접는다(`-destinationLayer BaseAnimation` 은
#        소스 커브를 지운다). 정수 프레임은 전부 동일(1e-15), 구간 밖은 반 프레임까지 동일, 구간 안 프레임 사이는 bake
#        보간(마야 자체 병합도 같다). 대상 weight≠1 · lock · mute · solo · 자식 레이어 · Base→새 레이어 · override 대상에
#        없던 채널은 거부. Verify(병합 전후 채널 값 비교) · Smart bake(근사, 경고) · Selected objects only · 진행 팝업.
#        계획서 docs/plans/A00110_animTool_V02_layer_range_merge_plan.md, 회귀 tests/test_layer_range_merge.py.

# 02.28  Transfer > Layer `Cut Keys to Layer (Move)` 가 **최종 평가값(월드 위치·회전)을 보존**한다(`Keep Result` 체크, 기본 ON).
#        사용자 관찰대로 Base 에만 키가 있는 ctl 을 Base -> a 로 옮기면 월드가 달라졌다(a -> b 도 실측으로는 어긋남).
#        원인 ① 커브를 다 지우면 blend 노드 입력(Base 는 맨 아래 `inputA`, 레이어는 그 노드 `inputB`)에 지우던 순간의
#        값이 정적으로 남아 계속 더해진다 -> identity(0 · multiply 스케일 1) 로 되돌린다(override 소스는 멤버에서 뺌).
#        ② 대상이 커브 없이 들고 있던 정적값(Base 정적값 · additive 멤버 정적값)을 붙여넣기가 덮는다 -> 붙여넣은 키에
#        합성(`keyframe -r -vc` / `scaleKey -vs`). 구간 이동은 Merge Layers 와 같은 경계 규칙(소스 `s-1`·`s`·`e`·`e+1`
#        insert fixed + identity step 키, 대상 바깥 정적값 키) - 정수 프레임 전부 동일, 구간 안팎 반 프레임 동일.
#        정확히 안 되는 경우는 로그 `Not exact:` 에 이유(대상에 이미 키 · weight≠1 · by-layer 회전에 0 아닌 회전 합성 ·
#        override 소스 구간 · 비수치 채널). Copy 는 예전처럼 값 그대로. 회귀 tests/test_layer_key_move.py 68/68.

# 02.29  Bake > Counter Layer `Hold` 모드 - Everywhere(기존) / **Stationary spans only**. 글로벌 레이어가 이동할 때
#        발이 **땅을 짚어 정지하던 구간만** 월드 고정하고, 움직이는 구간이 그 차이를 흡수해 최종 위치(End)는 레이어 결과대로.
#        레이어 뮤트 스트리밍으로 정지 구간(포즈 변화 < Still tolerance, Min span) -> 앵커(Touchdown/Middle/Lift-off) 포즈를
#        구간 목표로 -> 사이는 By travel(이동량 비례)/Ease/Linear 로 델타 보간(위치 더하기 · 회전 월드 후곱 slerp) ->
#        Start·End 델타 0(걸친 구간은 앵커 경계 강제, 전구간 정지는 제외 경고) -> 기존 청크 쓰기(보정 레이어만 뮤트).
#        `Preview Spans` 는 레이어 없이 구간만 로그. Step 은 이 모드에서 무시. 채널 일부만 키를 찍을 때 xform 이 건드린
#        나머지 채널을 되돌림(정적 채널 보호). 실제 씬(ZIHAN 두 발) 구간 오차 1.7e-6 · 범위 밖 0 · 1000f 10.5 s.
#        계획서 docs/plans/A00110_animTool_V02_counter_layer_stationary_plan.md, 회귀 tests/test_counter_layer.py.

# 02.30  View > Graph Focus `Frame margin (±)` 기본값 80 -> **30**(사용자 요청). 코어 상수
#        graph_view_manager.DEFAULT_FRAME_MARGIN 하나로 스핀박스 초기값 · GraphFocusManager 폴백을 맞춤. 범위 · 동작은 그대로.

# 02.31  View > **Layers** - 씬의 애니메이션 레이어 목록(에디터 순서 · 자식은 부모 아래 · BaseAnimation 맨 아래).
#        행을 고르면 그 레이어가 선택(하나면 활성)되어 그래프 에디터(필터 Selected)가 그 커브를 보인다.
#        Mute / Solo / Lock 체크, `Graph Editor: Selected Only / All Layers` 버튼, 보이는 동안 1.5 s 마다 마야 쪽
#        변화 따라가기(레이어 변경 이벤트가 없어 QTimer 비교). Curve > Filters 처럼 **Expand** 로 별도 창.
#        core/anim_layer_manager.py (LayerMergeManager.layer_info 재사용), tests/test_anim_layers.py.

# 02.32  Pin(Always on Top)이 켜져 있으면 Expand 로 뺀 창(View > Layers · Curve > Filters)도 다른 창 위에 머문다
#        (공용 MOD_expand_qt_v01.set_stay_on_top - 떠 있는 창에 바로, 다음에 띄우는 창에도). 사용자 요청.

# 02.33  Expand 창(View > Layers · Curve > Filters)은 **Pin 과 무관하게 늘 다른 창 위에**(생성 때 WindowStaysOnTopHint).
#        v02.32 의 "Pin 을 따라가기" 는 그래프 에디터를 클릭하면 뒤로 숨는다는 보고 → 창을 만들 때 플래그를 준다.

# 02.34  View > Graph Focus `Auto-Focus on Selection` 토글이 ON 이면 연한 빨강(공용 pin_style, Pin 과 같은 색). 사용자 요청.

# 02.35  Hot Key > Main 에 `Animation Layers > Delete BaseAnimation` - MEL `delete BaseAnimation;` 과 같은 결과.
#        A00030_quickTool_V02 v02.09 에 넣었던 것을 사용자 요청으로 옮겼다(A00030 에서는 v02.10 에 뺐다).
#        AnimLayerManager.delete_root() : 루트(animLayer -q -root)를 cmds.delete - 자식 레이어 · blend 노드 ·
#        레이어 커브 삭제, Base 커브 재연결. undo 로 레이어가 안 돌아와서(mayapy 실측) 확인 팝업, 지운 뒤 View > Layers 갱신.

# 02.36  Bake > Locator (새 하위 탭) - `LOC + Anim`: 리스트(TSL)의 오브젝트마다 로케이터 `<이름>_LOC` 를 월드에 만들고
#        Start ~ End 동안 월드 위치 · 회전(+ 선택 Scale)을 베이크. 마야에서 쓰던 `_SmartLayer` 의 LOC + Anim 을 새로 만든 것.
#        구간 = 공용 timeRange(Get Current · Get Sel Range) + Get Timeline. 진행 팝업(공용 progress) - bakeResults 한 번 +
#        MDGMessage 시간 변경 콜백으로 프레임마다 게이지. 임시 컨스트레인트 삭제 · 오일러 필터 · 실패 시 정리 · undo 한 번.

# 02.37  Bake > Locator - `Constrain Objects to Locators` 그룹(기본 끔): 베이크 뒤 각 로케이터 -> 원본 오브젝트 컨스트레인트.
#        Parent(기본) · Point · Orient · Scale, Parent 와 Point/Orient 는 서로 배타. 오프셋 없음(구간 안 월드 그대로, 실측 1e-15).
#        잠긴 축 · 키 아닌 구동 축은 그 축만 skip, scale 은 pairBlend 가 없어 키 있는 축도 skip(마야 Constrain > Scale 과 같음).

# 02.38  View > Layers - 공용 확대 / 축소(Framework MOD_viewZoom_qt_v01) 적용: 기본 150%, 글자 · 행 높이 · 체크박스가 함께 커진다.
#        `Zoom [-] 150% [+]` + Ctrl + 휠, 배율 기억. Mute / Solo / Lock 은 칸 어디를 눌러도 토글(행 선택은 안 바뀜). Expand 창 440x600.

# 02.39  Hot Key > Main > Hold 에 `Layer Blend Key` 옵션(기본 끔) - Shift+A 가 Hold 에 더해 고른 레이어에
#        (현재 - N) 레이어 멤버 keyable 채널 전부 = 그 시점 레이어 값(커브 평가 / blend inputB 정적값, 커브에 직접 써서 덮어쓰기),
#        현재 프레임 = Pose Key 탭 체크 축(Pose Key 와 같은 setKeyframe -animLayer -> 최종 값이 Pose 값) 키.
#        레이어를 만들거나 멤버로 넣지 않는다(없음 · 잠김 · 비멤버는 경고 후 건너뜀). Hold 와 독립, undo 한 번.
#        UI 값은 HoldLayerManager.settings 로 push(핫키는 UI 를 못 읽는다) + optionVar 복원.
#        core/hold_layer_manager.py, 계획서 docs/plans/a00110_hold_layer_blend_plan.md,
#        회귀 tests/test_hold_layer_blend.py 29/29 · test_hold_layer_blend_ui.py 11/11.

# 02.40  Layer Blend Key 버그 수정 - 컨트롤러가 레이어에 있어도 Shift+A 가 레이어 키를 **조용히** 안 찍던 문제.
#        원인: DEV 리로드는 같은 깊이 모듈을 sys.modules 등록 순서로 reload 한다. v02.38 이 로드된 세션에서 툴을 다시 열면
#        hotkey_manager 가 hold_layer_manager 보다 먼저 reload 되어 옛 HoldLayerManager 를 붙잡음 -> UI 는 새 클래스에 설정,
#        핫키는 옛 클래스(enabled=False)를 읽어 아무 메시지 없이 건너뜀(mayapy 재현). 수정: 설정 원본을 optionVar 로
#        (update 가 쓰고 apply 가 읽음), run_hold 는 호출 때 모듈 속성으로 클래스 조회, Layer Blend 예외는 뷰포트에 에러 한 줄,
#        레이어 미선택은 'no layer chosen' 경고, 레이어 콤보는 펼칠 때 목록 새로 읽기(창을 연 뒤 만든 레이어).
#        회귀 test_hold_layer_blend 33/33(RL1 리로드 순서) · _ui 12/12.

# 02.41  Key > Pose Key `Use current values` 체크박스(기본 끔) - 체크된 축에 입력 값 대신 **지금 프레임의 현재 값**으로 키
#        (키 없이 움직여 둔 값도 그대로 키, 켜면 값 칸 비활성). 켜져 있으면 Shift+A Layer Blend Key 의 현재 프레임 키도
#        Pose 값 대신 현재 값(최종 값이 그대로 남게 setKeyframe -animLayer). 값은 run_hold 가 **Hold 전에** 읽는다
#        (Hold 가 커브를 바꾸면 움직여 둔 값이 사라지므로). 설정은 optionVar use_current 로 기억.
#        회귀 test_hold_layer_blend 41/41 · _ui 16/16.

# 02.42  Layer Blend Key 대상 = **마야에서 지금 선택한 오브젝트만** 명시(사용자 요구 - 레이어에 든 다른 오브젝트엔 키 금지).
#        HoldLayerManager.selected_objects(): ls -sl -objectsOnly 에서 animLayer · objectSet · character 노드 제외
#        (세트 · 캐릭터에 setKeyframe 하면 멤버 전체로 퍼진다). run_hold 는 누른 순간 선택을 한 번 읽어 capture / apply 에 같은 목록.
#        뷰포트 메시지에 키를 찍은 오브젝트 이름. mayapy 에서는 v02.41 도 선택 오브젝트에만 찍혔다(재현 안 됨) - 방어 + 확인용.
#        회귀 test_hold_layer_blend 51/51(SEL: 멤버 3개 중 A 만 선택 x 레이어 · 세트 · 캐릭터 섞임) · _ui 16/16.

# 02.43  Layer Blend Key 보기 게이트 `Run only when viewing`(기본 BaseAnimation) - 지금 보고 있는 레이어가 정확히 그 레이어
#        하나일 때만 Layer Blend 가 돈다. AnimLayer1 을 보며 그 커브 구간 키를 골라 Shift+A(= AnimLayer1 Hold) 할 때 끼어들지
#        않게(사용자 요구). 보고 있는 레이어 = 레이어 에디터 선택 -> 없으면 preferred -> 없으면 루트. 여럿 보면 건너뜀.
#        Hold 는 그대로, Layer Blend 는 `skipped - viewing '...'` 한 줄. 저장값 "" = 루트, optionVar view_layer.
#        회귀 test_hold_layer_blend 63/63(VG) · _ui 19/19.

# 02.44  Pose Key `Use current values` 를 **축마다** (사용자 요구) - 전역 체크박스 대신 행마다 `Current` 체크박스.
#        켠 축만 지금 값, 나머지 축은 입력 값(켠 행은 값 칸 비활성). Layer Blend Key 도 축마다 따른다(capture 도 그 축만).
#        설정 use_current(bool) -> current_axes(축 목록, optionVar JSON). 옛 use_current=1 은 체크된 축 전부 current 로 옮겨 읽음.
#        회귀 test_hold_layer_blend 69/69(UC1b · UC-ADD/OVR 3 · UC6~8) · _ui 19/19.

# 02.45  Pose Key `Current` 기본 켜짐 = rotate Y · translate X · translate Z (사용자 요구, 저장값이 없을 때).
#        hold_layer_manager.DEFAULT_CURRENT_AXES 하나로 UI 초기값 · load_settings 기본을 맞춤. 회귀 70/70 · _ui 19/19.

# 02.46  ① Pose Key `Current` 를 켠 축은 **축 체크가 꺼져 있어도 키를 찍는다**(키 축 = 체크 ∪ Current). 사용자 보고:
#        Layer Blend Key 로 AnimLayer1 에 찍힌 키를 보면 Current 축에 키가 없다 - v02.44~45 는 체크 ∩ Current 만 current 로
#        다뤄 기본값(체크 rx rz ty / Current ry tx tz)에서 Current 축이 대상에서 빠졌다. Pose Key 버튼 · capture · apply 모두.
#        ② 툴을 열면 View > Graph Focus `Auto-Focus on Selection` 기본 ON(사용자 요청).
#        회귀 test_hold_layer_blend 73/73(UC6 · UC10~12) · _ui 21/21(U20 · U21), 창 띄우는 기존 시험 5개 통과.

# 02.47  Layer Blend Key 기준 프레임 = **그래프 에디터에서 고른 키 구간 [a, b] 의 a** (사용자 요구). 키는 a(Pose / Current) 와
#        a - N(레이어 값). a 는 Hold 전에 읽는다(range_start - Hold 가 (a, b] 를 지우므로), 고른 키가 없으면 현재 프레임.
#        Current 값 = a 시점 값: 현재 시간이 a 가 아니면 undo 기록을 끈 채 시간을 a 로 옮겨 읽고 되돌린다(values_at).
#        mayapy 실측 - 레이어가 있으면 getAttr -time · MDGContext 는 Base 값만, currentTime -update false 는 옛 값.
#        setKeyframe -animLayer -v 의 additive 역산은 키 시간 기준이라 그대로 a 에 찍는다. 회귀 81/81(RA0~7) · _ui 21/21.

# 02.48  Bake > Fix Sliding 탭 신설 - 리스트 오브젝트마다 월드 속도(선택 축) -> 스무딩 -> Threshold(최대 속도의 %) 아래 연속 프레임 =
#        정지 구간 [a, b]. 이웃 구간 틈 <= G(기본 4) 면 합치고(대안 B), 길이 > M 인 구간만, 구간마다 시간순으로 "그 구간 T/R 키를 고르고
#        Layer Blend Key 켠 채 Shift+A" 를 한다(Hold = 보기 레이어 커브, Layer Blend = Hot Key > Main 설정, force). 블렌드 시작은 앞 구간 끝에서
#        자르고(대안 A), 구간 끝 b 에도 같은 레이어 값 + flat(대안 D). 셋 다 끄면 순수 Shift+A 재현(시험으로 1e-9 대조).
#        `_debug_speed` 노드에 speed / smooth / threshold / result(적용 뒤 재샘플) 커브, undo 밖. Preview Spans, 진행 팝업, optionVar 기억.
#        KeyframeManager._hold_curve / hold_range, HoldLayerManager.apply(force, ramp_start, hold_end). _SmartLayer 는 툴팁만 참고.
#        실측: KANA 씬(6830 f) 발 IK 둘, 191 구간, 34 s, 구간 안 월드 속도 0. 계획서 docs/plans/a00110_fix_sliding_plan.md,
#        회귀 tests/test_fix_sliding.py 30/30 · test_fix_sliding_ui.py 11/11.

# 02.49  Bake > Fix Sliding 업데이트(사용자 요청 4건) - ① 디버그 노드를 TSL 오브젝트마다 하나 `<이름>_debug_speed`
#        (어트리뷰트 speed / smooth / threshold / result + source / info, v02.48 단일 `_debug_speed` 는 지움) ② 그래프 에디터 커브 색
#        흰 / 밝은 하늘 / 빨강 / 초록 (animCurve.useCurveColor + curveColor) ③ [a-N, a] 키를 찍을 Layer 콤보 + Frames before (N) 를
#        탭에서 고른다(처음 값 = Hot Key > Main, 펼칠 때 목록 갱신, Hot Key 설정은 안 바뀜) ④ 공용 Expand 로 별도 창(늘 위).
#        FixSlidingManager.run(layer=, offset=), HoldLayerManager.apply(layer=, offset=). 회귀 test_fix_sliding 36/36 · _ui 15/15.

# 02.50  Fix Sliding 크래시 수정 (MayaCrashLog261104.1716 / .1749 - 두 번째 이후 실행, 디버그 커브가 그래프 에디터에 떠 있음):
#        AnimUISlice.dll TanimCurveCallbackManager::uiPainter ACCESS_VIOLATION. 진행 팝업의 processEvents 로 그래프 에디터가
#        다시 그릴 때, undo 를 끈 채 지운 디버그 노드의 해제된 커브를 읽었다. ① 디버그 노드 · 커브를 지우지 않고 재사용(MFnAnimCurve.remove
#        로 키만 비우고 addKeys - cutKey -clear 는 커브 노드까지 지워서 안 씀) · 옛 `_debug_speed` / 리스트에 없는 노드는 안내만
#        ② 커브를 고치는 단계에선 게이지를 단계 끝에만(이벤트 루프 안 돌림) ③ 그 동안 그래프 에디터 setUpdatesEnabled(False)
#        ④ 시작할 때 키 선택 비우기. 회귀 test_fix_sliding 40/40 · _ui 15/15, KANA 두 번 연속 실행 노드 · 커브 재사용 확인.

# 02.51  Bake > Bake 를 구간 [s, e] 만 구울 때 **구간 밖 기존 키 보존** (사용자 보고: 컨스트레인트를 걸고 [10, 50] 만 구우면 그 밖의 키가 지워짐,
#        오브젝트는 BaseAnimation + 다른 레이어에 키). 실측 - 레이어 멤버 채널에서 bakeResults -time -preserveOutsideKeys 는 Base 커브를
#        [s, e] 키만 남기고 바꾸고(구간 밖 소실) 합성값을 Base 에 써 위 레이어를 이중 계산. -> 레이어 오브젝트는 bake_layered:
#        컨스트레인트 켠 채 매 프레임 샘플 -> 채널마다 대상 레이어(덮는 맨 위 override, 없으면 Base) 커브의 [s, e] 안 키만 지우고
#        (s-1 / e+1 모양 보존 키 + 이웃 탄젠트 fixed) setKeyframe -animLayer 대상 -value (마야 역산). 다른 레이어 커브 그대로.
#        또 bakeResults -smart 는 레이어 없이도 구간 밖 값을 바꿨다 -> smart = dense bake + 구간 안만 Douglas-Peucker 로 키 줄이기
#        (Tolerance = 채널 단위 절댓값, linear 탄젠트). filterCurve -simplify 는 허용오차를 안 지켜 안 씀. 키가 없던 채널은 마야 기본대로
#        구간 밖에서 구운 끝값을 잇는다(컨스트레인트를 거는 순간 pairBlend 입력이 0 이라 원래 값을 되살릴 수 없음).
#        회귀 tests/test_bake_layers.py 19/19.

VERSION = "02.51"
LAST_UPDATE = "2026-11-04"
