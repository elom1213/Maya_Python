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

VERSION = "02.28"
LAST_UPDATE = "2026-10-29"
