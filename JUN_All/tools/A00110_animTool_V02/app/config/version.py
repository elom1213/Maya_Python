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

VERSION = "02.32"
LAST_UPDATE = "2026-10-30"
