---
title: 작업 일지 (WORKLOG)
aliases: [WORKLOG, 작업일지, devlog]
tags: [worklog, maya-python]
updated: 2026-08-13
---

# 작업 일지 (WORKLOG)

git 커밋 기록을 근거로 하루 작업을 요약한다. 최신 날짜가 위.

> [!info] 보기
> Obsidian 에서 `JUN_All/docs` 를 vault(또는 폴더)로 열면 속성/태그/링크가 동작한다.
> 굵게/링크가 별표째 보이면 소스 모드이므로 `Ctrl+E` 로 읽기/라이브 프리뷰 전환.

---

## 2026-08-13 (오늘)

> [!summary] `A00400_CurveTool` **탭 2개로 분리 + Line Width 탭** (v01.00→01.01)
- **요청**: 기존 기능은 첫 탭에 그대로 두고, 두 번째 탭에서 TSL 에 리스트업한 커브의 **씬 표시 굵기**를
  슬라이더로 조절. 목적은 **씬에서 커브가 잘 보이고 잘 집히게** 하는 것.
- `nurbsCurve.lineWidth` 를 쓴다(실측: float, 기본 **-1 = 마야 전역 설정 사용**, min/max 없음,
  **Maya 2019+** 에서만 존재, mesh/locator 셰이프에는 없다). **표시 전용**이라 형상·히스토리·렌더 무관.
- 슬라이더(0~10, 0.1 단위)와 스핀박스를 양방향 동기화하고 **드래그 중 실시간 반영**. 값이 바뀔 때마다
  undo 가 쌓이지 않도록 **`sliderPressed` 에서 청크를 열고 `sliderReleased` 에서 닫아** 드래그 한 번 =
  undo 한 스텝(테스트로 고정).
- `Apply` / `Get`(첫 커브 값 읽기) / `Use Maya Default (-1)`. 커브가 아님·구버전·잠김/연결은
  **사유와 함께 스킵**하고 나머지는 계속.
- 로그창은 두 탭이 공유하고 리스트는 탭마다 따로 둔다(굵기 조절 대상과 방향 정렬 대상이 다를 수 있다).
- 검증(mayapy 2024): 코어·UI 28항목 — 기본값/설정/역읽기, 셰이프 이름 입력, 메시·잠김 스킵,
  **탭 분리 후 기존 Create·Reverse 회귀**, 슬라이더↔스핀박스 동기, 드래그 undo 1스텝, 빈 리스트 방어. #A00400


## 2026-08-12

> [!summary] `A00145_RigConnect` **Constraint 탭 `Maintain Offset` 기본 ON** (v01.27→01.28)
- MEL 원본을 따라 기본 unchecked 였으나, 실제 리깅 작업은 거의 항상 오프셋 유지가 전제라
  매번 체크하는 손이 갔다. `Constrain > Constraint` 하위 탭의 체크박스만 기본값을 ON 으로 바꿨다.
- 다른 탭의 동명 옵션(`Skin Weight`, `Connect Closest`)은 손대지 않았다. #A00145

> [!summary] `A00170_driverTool` **Edge Loop 피드백 — 조인트 반경 확정 + 컨트롤러 계층** (v01.14→01.15)
- **① 조인트 반경**: `joint -radius` 로 넘긴 값이 화면 크기와 달라 보인다는 피드백. 실측해 보니
  `.radius` 는 입력값과 **정확히 같았다**(단위·부모 스케일·`jointDisplayScale` 무관 — 헤드리스 확인).
  뷰포트에 그려지는 크기가 **`Display > Animation > Joint Size` 전역 배율**과 곱해진 값이라 달라 보인 것.
  그래도 요청대로 생성·부모 지정 후 **`setAttr(.radius)` 로 한 번 더 못 박고**, 툴팁·문서에 표시 배율을 명시했다.
- **② 컨트롤러 계층**(체크박스, **기본 ON**): 널이 조인트를 직접 끌지 않고
  `null > _con > _ctl > _tgt` 를 만들어 **`_tgt` 가 조인트를 컨스트레인트**한다.
  `_con`/`_tgt` 는 널 그룹, `_ctl` 은 **A00145 Match 탭과 같은 Sphere 커브**(조인트 반경 ×1.5).
  세 노드 모두 `parent -relative` 로 **로컬 0** 이라 널 자리에 정확히 겹치고, ctl 을 움직이면
  커브가 준 위치 **위에 오프셋**이 얹힌다.
- 이름은 널 인덱스를 물려받는다(`loopDrv_null_01_con/_ctl/_tgt`) — 널이 여럿이라 인덱스 없이는 충돌한다.
- Sphere 포인트는 A00145 에서 **반지름 1 로 정규화해 복사**했다(툴끼리 import 금지 — 릴리스 패키지).
- 조인트를 꺼도 컨트롤러는 만들 수 있고, 그때도 Joint Radius 가 컨트롤러 크기를 정한다.
- 검증: 신규 24항목(반경 3종·전역 배율 무관·계층/제로아웃/크기·tgt 구동·ctl 오프셋·off 회귀) +
  기존 코어 34 · UI 30 통과. #A00170

> [!summary] `A00170_driverTool` **AttachCrv 하위 탭 — 엣지 루프에서 드라이버 셋업 한 번에** (v01.13→01.14)
- **요청**: AttachCrv 를 하위 탭 둘로 나눠 `Default` 는 기존 기능 그대로 두고, 새 탭에서
  ① 엣지 루프 집합 저장 ② 버텍스 집합 저장 ③ 루프→커브 + 버텍스 자리에 널 생성 + 커브에 어태치를
  한 번에 ④ 체크박스(기본 ON)로 널을 따라가는 조인트까지 생성.
- **조립**: 커브 생성은 `A00400_CurveTool` 방식(연결 성분별 `polyToCurve(form=2, ch=True)`),
  어태치는 이 툴의 `attach_curve.build_attach_to_closest` 를 그대로 호출한다. **A00400 을 import
  하지는 않았다** — 릴리스 빌더가 툴 하나 + Framework 만 복사하므로 툴끼리 물리면 패키지가 깨진다.
- **커브가 여럿일 때**: 널마다 `nearestPointOnCurve` 로 거리를 재 **가장 가까운 커브**에 붙인다.
  위/아래 입술 루프를 한 번에 처리해도 섞이지 않는다. norCrv/POCI 세트는 커브마다 하나씩.
- **조인트는 parent 대신 `parentConstraint`** — 스켈레톤 계층(`<prefix>_jnt_grp`)을 따로 둬야
  그대로 스킨·익스포트할 수 있다. 어태치가 끝난 **널의 최종 위치**에 만든다.
- 저장한 엣지/버텍스는 리스트 위젯으로 펼치지 않는다(루프 하나가 수십~수백 개) — 요약 라벨 +
  Select/Clear. A00275 Expand Bind 와 같은 방식.
- 검증(mayapy 2024): 코어 34 + UI 27 항목. 닫힌 루프 → 주기적 커브, 널이 버텍스 자리에 정확히,
  메시 정점을 옮기면 커브→널→조인트까지 따라오는 것, 루프 2개 분리 어태치, 조인트 off,
  degree 3 / orient off, 방어 케이스. **기존 Default 탭의 Attach·Distribute 회귀도 함께 통과**. #A00170

> [!summary] `Framework` **`extendToShape()` 패턴 일괄 정리 — 셰이프 확정 공용 헬퍼** (툴 6종 수정)
- **동기**: 앞선 Expand Bind 버그와 **같은 원인**이 다른 툴에도 복붙돼 있었다. `extendToShape()` 를
  쓰는 곳을 전부 훑어(9곳) 위험도를 나눠 고쳤다.
- **하드 에러 계열**(웨이트 API 로 흘러 `kInvalidParameter` 로 죽음): `A00275` Transfer/Migrate,
  `A00270` 네이티브 조인트 이동.
- **조용히 틀리는 계열**(예외 없이 **다른 셰이프**를 읽고 씀 — 더 위험): `A00145` Match 좌표 읽기,
  `A00180` 정점 읽기/쓰기, `A00280` 토폴로지 비교, `A00300` 스캔/수정.
- **해결**: [`Framework.core.maya_shape`](Framework_maya_shape.md) 신설 —
  `shape_path/shape_dag/vertex_count/deformed_shapes/drives_shape`. 셰이프를 추측하지 않고
  **디포머가 실제로 변형하는 셰이프**(`cmds.deformer -q -g`, 모든 디포머에서 동작)로 확정한다.
  9곳을 전부 이 헬퍼로 바꿨다(A00275 의 `shape_of` 도 여기로 위임).
- **덤으로 같은 계열 2건**: 소프트 셀렉션 매칭이 컴포넌트의 트랜스폼을 하나의 셰이프로 좁히다 빗나가던
  것 → 트랜스폼 아래 **메시 셰이프 전부와 대조**. `copySkinWeights` 가 셰이프 여럿인 트랜스폼에서
  `-destinationSkin` 을 요구하며 실패하던 것 → **셰이프를 선택**해 넘긴다(실측으로 해결책 확인).
- 검증: 헬퍼 12 + 호출부 회귀 10 + 기존 A00275 스위트 116항목 + 단일 셰이프 스모크 8항목 통과.
  버전: A00145 01.27 / A00180 02.05 / A00270 01.02 / A00275 01.12 / A00280 01.02 / A00300 01.04. #Framework

> [!summary] `A00275_skinTool_V01` **[Fix] Expand Bind 의 `kInvalidParameter: Object is incompatible with this method`** (v01.10→01.11)
- **증상**: blendShape 를 먹인 뒤 skinCluster 로 바인드한 메시에서 Expand Bind 실행 시 위 경고로 실패.
- **원인**(재현으로 특정): 셰이프를 `MDagPath.extendToShape()` 로 잡고 있었다. 이 함수는 **첫 번째
  non-intermediate 셰이프**를 고를 뿐이라, 한 트랜스폼 아래 메시 셰이프가 여럿이면(blendShape 타겟
  셰이프를 같은 트랜스폼에 정리해 둔 리그, 머지/임포트 잔재 등) **스킨이 안 걸린 셰이프**를 집는다.
  그 경로로 `MFnSkinCluster.getWeights` 를 부르면 마야가 정확히 저 에러를 낸다.
  (blendShape 자체는 무죄 — 단순 blendShape→skin 히스토리는 재현되지 않았다.)
- **덤으로 발견**: 셰이프가 여럿인 트랜스폼에 `polyEvaluate(v=True)` 를 걸면 정수가 아니라 요약
  **문자열**이 돌아와 뒤에서 `TypeError` 로 터진다.
- **해결**: `shape_of()` — **skinCluster 가 실제로 변형하는 셰이프**(`skinCluster -q -geometry`)를 골라
  좌표·인접·컴포넌트·웨이트 IO 가 전부 같은 경로를 쓴다. `vertex_count()` 는 항상 셰이프 기준.
  웨이트를 읽기 전 "이 스킨이 이 셰이프를 변형하는가" 를 확인해 **원시 API 에러 대신 설명이 있는 에러**를
  낸다. 저장 시 컴포넌트가 셰이프 이름으로 오면 그 셰이프를 기억하고, 새 skinCluster 도 셰이프에 건다.
- 검증: 셰이프 해석 회귀 15항목 신규 + 코어 44 · 루프 24 · UI 33 회귀 통과. #A00275

> [!summary] `A00275_skinTool_V01` **Expand Bind 에 엣지 루프 입력 — 밴드 전체가 루프 비율 유지** (v01.09→01.10)
- **요청**: 조인트가 앉아 있는 **엣지 루프**를 툴에 알려 주면 웨이트 균등 배분에 더 도움이 되는지,
  된다면 입력 UI 를 만들어 달라. (루프는 저장된 버텍스 집합 안에 포함된 루프)
- **먼저 도움이 되는지 실측**했다. 11×7 격자(루프 1줄 + 밴드 6줄, 조인트 2개, 반경 10)에서 조인트 0 의
  웨이트가 **루프 줄 `1.0/0.9/0.8/0.7/0.6/0.5`** 인데 **루프+3 줄은 `1.0/1.0/1.0/1.0/0.75/0.5`** 였다.
  루프에서 멀어질수록 "바깥으로 나간 거리" 가 반경을 잡아먹어 **먼 조인트의 falloff 가 먼저 0** 이 되고,
  결국 부드럽게 섞이지 않고 딱딱하게 갈라진다 → **필요한 정도가 아니라 밴드 바인드에는 사실상 필수**.
- **해결**: 루프를 주면 계산을 두 방향으로 나눈다. **루프를 따라** = 조인트 사이 분배(호 길이),
  **루프에서 멀어지며** = amount 만 감쇠(`Across width`, 0 이면 Soft Select 값). 루프 전체를 시작점으로
  하는 **다중 소스 Dijkstra 한 번**으로 "루프에서 떨어진 거리 + 가장 가까운 루프 버텍스(anchor)" 를 얻고,
  비율은 **anchor 의 루프 위 호 거리로만** 낸다 → 밴드 7줄 전부 `1.0/0.9/0.8/0.7/0.6/0.5` 로 일치.
- **입력 UI**: `Store Edge Loop from Selection` + Select/Clear + 요약 라벨. 엣지를 골라도, 그 버텍스를
  골라도 되고, 한 줄로 안 이어지면(갈래·끊김·조각) 이유를 붙여 거절한다. **열린/닫힌 루프 자동 판별**,
  닫힌 루프는 **감아 도는 짧은 쪽** 거리로 재서 시작 정점 근처가 어긋나지 않는다.
  `Fit to Joints` 도 루프가 있으면 **루프 위 간격**으로 잰다(밴드 가로지르는 지름길에 안 속는다).
- 검증: 루프 24항목 신규 + 기존 코어 44 · UI 33 회귀 통과. 루프 없이 갈라지던 결과를 **회귀 테스트로
  고정**해 두었다. #A00275

> [!summary] `A00275_skinTool_V01` **Expand Bind 탭 — 루프 위 조인트에 고르게 바인드** (v01.08→01.09)
- **요청**: Kangaroo `SkinCluster > ClosestExpand` 로 입술·눈 같은 **원형 엣지 루프**에 조인트를 배치해
  바인드하면 **조인트 사이 웨이트가 고르지 않다**. 엣지 개수와 거리에 따라 균등하게 깔리게 해 달라.
  더불어 버텍스 집합/조인트 집합 저장 버튼, falloff 커브 + 모드 UI(`ref/ref_01.png`), Blend, Soft Select.
- **원인**(Kangaroo `weights.py` 를 읽어 확인) — `bindToClosestVertexAndExpand` 는 조인트 사이 경로를
  **토폴로지 등간격**(`fT = (p+1)/(len(iPath)-1)`)으로 섞고, 바깥은 **루프 개수**로 b-spline 감쇠시킨다.
  **실제 엣지 길이를 전혀 보지 않아** 간격이 조금만 불규칙해도 한쪽으로 쏠린다.
- **방식**: 조인트별로 저장 집합 안의 최근접 버텍스를 seed 로 잡고 → **엣지 길이를 누적한 측지 거리**
  (Dijkstra) → `거리/반경` 을 falloff 커브에 → **버텍스마다 조인트들 사이에서 정규화**.
  선형 커브면 두 조인트 사이가 정확히 `d2/(d1+d2)` 라 간격이 불규칙해도 거리에 비례한다.
  탐색을 **저장 집합 안으로 제한**해 윗입술 falloff 가 아랫입술로 새지 않는다.
- **Falloff mode 3종** — `Surface(엣지 길이)` / `Topology(엣지 개수)` / `Volume(직선)`. 세 모드 모두
  **조인트가 아니라 그 최근접 버텍스에서부터** 잰다(요청 문구 그대로 — 조인트가 표면에서 떠 있어도
  자기 버텍스는 웨이트 1 로 시작).
- **coverage 를 따로 둔 이유** — 정규화만 하면 반경 끝에서 웨이트가 1 → 0 으로 뚝 끊겨 **커브 모양이
  무의미**해진다(단일 조인트에서 특히). `coverage = min(1, 커브값 합)` 을 곱해, 조인트 **사이**는 1 을
  유지하고 바깥으로만 빠지게 했다. 덕분에 `Blend` 의 **최댓값이 정확히 Blend** 가 된다.
- **Blend** — 다른 인플루언스가 있는 버텍스는 `Blend × coverage` 만 가져가고 나머지는 기존 쪽이 비율대로
  유지. 다른 인플루언스가 **없으면** 남길 곳이 없어(합이 1 이 아니면 마야가 재정규화) 항상 1.
- **버텍스 집합은 리스트 위젯으로 안 만들었다** — 입술 한 덩이가 수천 개라 창이 느려진다는 요청을 반영해
  요약 라벨 + Select/Clear 로. 재선택은 연속 id 를 `vtx[a:b]` 로 묶어 던진다.
- **Falloff 커브 위젯** 신규(`app/ui/falloff_curve_widget.py`) — `gradientControlNoAttr` 는 cmds 전용이라
  PySide 창에 못 쓴다. 드래그/추가/삭제 + Interpolation 4종 + 프리셋 6종. **그리기와 바인드 계산이 같은
  함수**(`core/falloff.py`)라 화면과 결과가 어긋나지 않는다.
- 검증(mayapy 2024 headless): 코어 44 + UI 28 항목 전부 통과. 닫힌 루프(24분할·조인트 4개)에서
  `1.0/0.833/0.667/0.5/0.333/0.167/0` 균등 램프 + 0번 정점을 넘어가는 wrap 확인.
  성능 25,921 버텍스 / 조인트 20개 **0.60s**(순수 파이썬, numpy 무의존). #A00275

> [!summary] `A00145_RigConnect` **Target Replace → Target Edit : constraint 타깃 추가 / 삭제** (v01.25→01.26)
- **요청**: 임의의 parent/point/scale constraint 의 **타깃을 나열**해 고른 것을 **삭제**하고, 씬에서 고른
  오브젝트를 다른 리스트에 담아 **원하는 constraint 에만 타깃으로 추가**하는 기능.
- 새 탭을 만들지 않고 **`Target Replace` 하위 탭을 `Target Edit` 으로 확장**했다 — 교체·추가·삭제가
  `Constraints` + `Targets` + `New Target` 이라는 **같은 입력 세 개**를 쓰기 때문. 탭이 6개로 늘면
  560px 창에서 탭 바가 더 좁아지고, 같은 리스트를 두 벌 채워야 했을 것이다.
- **작업 범위 = Constraints 리스트에서 고른 항목**(아무것도 안 고르면 전체). "원하는 constraint 만"
  요구를 세 동작 공통 규칙으로 두고, `[INFO] using n picked constraint(s) of m` 로 범위를 로그에 남긴다.
  `List Targets` 와 편집 후 자동 갱신도 같은 범위를 따라 **목록 = 지금 버튼이 건드릴 범위**가 된다.
- **연결을 직접 끊지 않고 Maya 명령을 쓴다** — `cmds.<type>Constraint(tgt, driven, e=True, remove=True)` /
  `cmds.<type>Constraint(newTgt, driven, mo=True)`. 손으로 `target[i]` 연결을 끊으면 weight 별칭과 빈 멀티
  인덱스가 남는다. (교체는 기존대로 연결만 rewire — 노드 이름·weight 연결 보존이 목적이라 결이 다르다.)
- **마지막 타깃을 지우면 Maya 가 constraint 노드까지 지운다**(실측). 기본은 *건너뛰고 경고*,
  `Delete the constraint when its last target is removed` 를 켜야 실제로 지운다. driven 은 마지막 값 유지.
- **Keep in place (remove)** — 옛→새 타깃 델타가 없어 기존 교체 로직을 못 쓴다. 남은 타깃들의 offset 을
  **현재 포즈 기준으로 다시 굽는다**: 각 타깃이 *혼자서도* 삭제 전 월드 행렬을 만들게 맞추면 weight 가
  어떻게 섞이든 블렌드 결과가 같은 행렬이라 정확하다. point/scale/orient 는 공유 `.offset` 을 쓰는 기존
  보정 함수를 재사용. **Add 는 Maya 의 `maintainOffset` 이 이미 같은 일을 한다**(실측 확인).
- 추가 시 `Added target weight` 스핀박스 값으로 weight 지정, 이미 있는 타깃/driven 자신은 건너뛰고 경고.
  `maintainOffset`/`weight` 를 안 받는 타입(geometry/poleVector)은 플래그를 떼고 재시도 후 로그로 알림.
- 검증(mayapy 2024 headless): 코어 30항목(추가·중복·트랜스폼 확장 / 삭제 후 제자리 유지 — parent·point·
  scale·orient·aim·geometry / 마지막 타깃 가드·삭제 / 무관 constraint 방치 / 다중 삭제 / 예외 3종) +
  UI 14항목(탭 라벨, 선택 범위 한정 추가, 스핀박스 weight, 목록 자동 갱신, 필터로 가려진 선택 제외) 전부 통과. #A00145

---

## 2026-08-11

> [!summary] `study` **AdvancedSkeleton MetaHuman Animator 의 Connect / Bake 알고리즘 분석** (문서)
- **동기**: UE 5.7 에서 커브가 베이크된 MetaHuman 페이셜 애니메이션을 마야 페이셜 컨트롤러에 옮기려고
  `Connect Face Animation` + `Bake to standard Face Controls` 를 썼는데 의도대로 안 붙는 경우가 있어,
  두 버튼의 동작을 먼저 알아야 했다. 대상: `0020_maya_plugin/0040_AdvancedSkeleton` (AS **6.801**).
- **Connect** — 씬의 `root_CTRL_expressions_*` **애님커브 노드를 복제**해 MetaHuman ControlPanel 컨트롤
  (`CTRL_L_brow_down` 등)의 `translateY/X` 에 `connectAttr`. 매핑은 **하드코딩 104개 × L/R** 이 전부.
- **Bake** — 패널 → SDK → `blendWeighted` 그래프를 역추적해 **상류가 `bwCTRL_*`/Emotions/Phonemes 인
  애님커브만** 새 blendWeighted 로 합산 → 임시 transform `.tx` 에 물려 `bakeResults` → **이름을 역파싱**해
  AS 표준 컨트롤(`ctrlBrow_R.translateX`)에 `pasteKey`.
- **정확히 안 되는 이유 3층** — ① MetaHuman 의 board→raw 가 다대다라 **역매핑 자체가 근사**,
  ② 커버리지 104개(주석이 명시적으로 버리는 항목: `eyeLowerLid*`, `eyeUpperLidUp`, `eyeWiden`,
  `jawClench`, 목/삼킴, 치아, 혀 roll 등), ③ **양방향(±) 병합 휴리스틱의 손실** —
  `|v|<0.001` 키 제거 → 탄젠트 전부 선형화 → 음수쪽 ×(-1) → `pasteKey -option merge`.
  **0 구간이 사라져 선형 보간**되므로 **UE 압축 커브처럼 키가 듬성하면 치명적**(MHA 원본은 매 프레임 키라 영향 작음).
  루프가 `$z=1` 부터라 **첫 키는 절대 안 지워져** 첫 프레임 값이 0으로 덮이는 경우도 있다.
- **코드 버그 확인** — `tongueTwistRight` 가 음수 분기(`*Right*`)에는 들어가는데 `$target` 지정 줄이 없어,
  proc 스코프 변수에 남은 직전 값(`CTRL_C_tongue_bendTwist_translateY`)으로 pasteKey 된다 →
  **혀 twist 키가 혀 bend 커브를 오염**시킨다. 올바른 값은 `..._translateX`.
- **조용히 실패하는 지점**(로그 없음) — 베이크 범위가 `playbackOptions min/max` 라 타임라인 밖은 잘림 /
  목적지 이름을 `<컨트롤>_<사이드>_<어트리뷰트>` **3토큰 역파싱** 후 `getAttr -settable` 실패 시 무음 skip /
  애님 레이어·컨스트레인트·락이면 무음 skip / `delete -staticChannels` 로 상수 채널 소실 /
  **Bake 가 내부에서 `DeleteAnimation` 을 불러 머리 애니메이션까지 지운다**(머리 연결은 Bake 이후에) /
  끝나고 `ctrlBox.limits` 가 0 으로 남는다. → `// N copied` / `// N baked` 두 숫자가 유일한 검증 수단.
- 문서에 진단용 MEL 스니펫 8종, 권장 작업 순서 11단계, **전체 104행 매핑표**, 자체 툴 설계 메모
  (양방향은 잘라 붙이지 말고 `up - down` 을 매 프레임 합성)를 정리.
  같은 코드가 `AdvancedSkeleton.mel` / `panel.mel` / `picker.mel` **3곳에 바이트 동일 사본**으로 있다.
  [study/AdvancedSkeleton_MetaHumanAnimator_connect_bake_분석](study/AdvancedSkeleton_MetaHumanAnimator_connect_bake_분석.md) #study #MetaHuman

> [!summary] `A00110_animTool` **Key Edit 하위 탭 재편 + Fill Keys(구간 전 프레임 키 채우기)** (v01.39→01.40)
- **요청**: ① Pose Key · Euler Filter 를 Key Edit 하위 탭으로. ② 선택 오브젝트의 **키 가능 + 채널박스
  노출** 어트리뷰트를 나열하고, 고른 채널의 구간 모든 프레임에 키를 찍는 탭 추가. 이미 키가 있으면
  방치, 없으면 지금 값으로. **키를 찍을 애니메이션 레이어도 고를 수 있게.** UI 는 A00145 Connect 참고.
- 최상위 8→**6탭**(Key Edit / Copy Key / Mirror Key / Bake / Follow / Graph Focus), Key Edit 하위는
  **8탭**(Move Keys / Fill Keys / Pose Key / Graph / Offset & Hold / Stagger / Euler / Delete All).
  하위 탭이 늘어 창 기본 폭 520→620.
- **Fill Keys** — 어트리뷰트 목록은 `listAttr -keyable -visible -unlocked`(채널박스에만 보이고 키는
  못 찍는 채널은 제외). 여러 오브젝트는 합집합, 실행 시 없는 채널은 조용히 건너뛴다.
  구간은 공용 `MOD_timeRange_qt_v01`, 레이어는 콤보(`(current)` = 마야가 평소대로).
- **핵심 함정 (mayapy 실측)** — 대상 커브가 이미 있으면 `setKeyframe(insert=True)` 가 모양을 그대로
  보존해 완벽하다(오차 1.8e-15). 그런데 **커브가 없으면 insert 는 조용히 아무것도 안 한다**
  (반환 0, 커브 미생성). 특히 "레이어는 있는데 그 채널 커브가 아직 없는" 흔한 상황이 여기 걸린다.
  그래서 그 경우엔 `getAttr(plug, time=f)` 평가값으로 키를 찍는다.
- **값은 쓰기 전에 전부 미리 구한다** — 레이어 커브에 키가 하나 생기면 그 레이어 기여가 달라져 이후
  프레임 평가값이 흔들릴 수 있다. 계산과 쓰기를 번갈아 하면 흔들린 값을 그대로 굳히게 된다.
- `setKeyframe(animLayer=L, value=V)` 는 레이어 커브에 V 를 그대로 쓰는 게 아니라 **최종 평가값이 V**
  가 되도록 역산해 넣는다 → 평가값을 그대로 넘기면 레이어에서도 모양 유지. 채널이 레이어에 아직
  없으면 `animLayer(e=True, attribute=)` 로 먼저 넣는다.
- 성능: insert 경로는 프레임 단위로 여러 plug 를 한 번에 넘겨 호출 수를 (프레임×채널)이 아니라
  (프레임)으로 줄였다. 전체는 `undo_chunk` + `suspend_refresh`.
- 검증: 코어 10개 그룹(어트리뷰트 필터·insert 경로·값 경로·구간 밖 보존·레이어 3종·다중 오브젝트·
  방어·레이어 목록) + UI 6개 그룹(탭 구성·위젯·목록/필터·실행/재실행·레이어 지정·방어) 전부 통과.
  기존 하위 탭 테스트도 갱신해 통과. #A00110


> [!summary] `A00110_animTool` **Key Edit 탭의 접이식 섹션을 하위 탭으로** (v01.38→01.39)
- **요청**: Key Edit 탭의 하위 접이식 항목들을 모두 하위 탭으로. A00145_RigConnect 의 Constrain 탭 참고.
- 접이식 섹션 5개(Move Keys / Graph Editor / Offset & Hold / Stagger Offset / Delete All Keys)를
  중첩 `QTabWidget` 으로 바꿨다. A00145 와 같이 `KEY_EDIT_PAGES` 테이블 + `_build_sub_tabs()` 구성,
  짧은 라벨 + 전체 이름은 탭 툴팁 + `ElideRight`.
- **A00145 를 그대로 베끼면 안 되는 지점이 하나 있었다** — 이 툴은 창 높이를 콘텐츠에 맞춰 자동으로
  늘리고 줄인다(`_fit_window`). A00145 처럼 각 페이지를 `QScrollArea` 로 감싸면 스크롤 영역이
  콘텐츠와 무관한 sizeHint 를 가져 그 자동 맞춤이 깨진다. 그래서 스크롤 대신 상위/하위 페이지를
  **모두 `JUN_mod_fit_tab_page_v01`** 로 뒀다 — 숨은 페이지가 sizeHint 0 을 보고해야
  `QStackedLayout` 의 "모든 페이지 중 최댓값" 규칙에 안 걸린다.
- 하위 탭 전환에도 상위 탭 전환과 같은 규칙(`grow_only=True`)으로 창을 맞춘다.
- 섹션별 시그널 연결을 각 페이지 빌더 안으로 옮겨 페이지가 자기 완결적이 됐다.
  위젯 이름(`le_start`, `sld_stagger`, `delall_tsl` …)은 그대로라 핸들러/매니저는 손대지 않았다.
- 검증: 하위 탭 구조/라벨/툴팁 · **5개 페이지 위젯 속성 전수 존재 확인** · 전 탭 전환 ·
  Move Keys 실제 키 이동 · Stagger 슬라이더 구동 · 핫키 토글 ·
  **창 자동 맞춤(438→749→420 실측)** 전부 통과. #A00110


> [!summary] `A00145_RigConnect` **개수가 달라도 되는 만큼 연결 — 에러로 중단하지 않음** (v01.24→01.25)
- **요청**: Source/Destination 어트리뷰트 개수가 서로 달라도 오류 때문에 연결이 도중에 막히는 일이
  없게. 개수가 다르면 **적은 쪽만큼만 연결하고 남는 어트리뷰트는 방치**.
- 예전에는 `len(srcAttr) != len(dstAttr)` 이면 **아무것도 연결하지 않고** `ValueError` 였다. 이제
  `min(개수)` 만큼 앞에서부터 짝지어 연결하고 남는 것은 그대로 둔다. 오브젝트 수도 같은 규칙
  (패턴 1의 브로드캐스트는 원래대로 모든 대상 obj 사용).
- 요청의 "연결 도중 오류" 를 넓게 받아 **개별 `connectAttr` 실패도 치명적이지 않게** 했다.
  잠긴/읽기 전용/타입 불일치 어트리뷰트를 만나도 거기서 멈추지 않고 나머지를 계속 연결한 뒤,
  실패한 것만 따로 보고한다(실측: 가운데 것만 잠갔을 때 앞뒤 2개는 정상 연결).
- **조용히 넘기지 않는다** — 남은 어트리뷰트/오브젝트와 실패 목록을 **이름까지** 로그에 찍는다.
  안 그러면 "왜 일부만 연결됐지?" 가 된다. `connect_attrs` 반환이 `(count, mode)` →
  `(count, mode, report)` 로 바뀌었다(호출부는 UI 한 곳).
- 패턴 분기도 정리했다. 기존 패턴 2(양쪽 attr 1개)는 패턴 3의 특수 경우라 같은 루프로 합치고
  라벨만 구분한다. **개수가 맞는 기존 입력의 동작은 그대로**(회귀 테스트로 확인).
- 여전히 예외가 나는 경우는 입력이 아예 빈 때뿐(오브젝트 목록 없음/어트리뷰트 미선택).
- 검증: attr 5vs3 · 3vs5 · obj 3vs5 · 브로드캐스트+불일치 · 중간 잠금 실패 후 계속 · 기존 동작 회귀 ·
  빈 입력 예외 · UI 로그 + 기존 A00145 스위트 7종 전부 통과. #A00145

> [!summary] `A00145_RigConnect` **Connect 하위 탭에 역방향 연결 추가 (Destination → Source)** (v01.23→01.24)
- **요청**: Connect 하위 탭이 Source 어트리뷰트 → Destination 어트리뷰트 한 방향뿐인데, **반대 방향
  (Destination → Source)** 연결도 있어야 한다.
- 두 방향 버튼을 **나란히** 두어 어느 쪽이 드라이버인지 화살표로 읽히게 했다
  (`Source  ->  Destination` / `Destination  ->  Source`). 로그에도 방향을 함께 찍는다.
- 코어(`connect_attrs`)는 손대지 않았다 — **인자 순서만 뒤집으면** 3가지 브로드캐스트 패턴까지
  그대로 뒤집혀 적용된다. UI 에 `_connect_in_direction(from_role, to_role)` 하나만 두고 두 슬롯이
  그것을 감싼다.
- **함정**: 방향을 기본 인자로 받는 단일 슬롯에 `clicked` 를 직접 연결하면, `clicked` 가 넘기는
  `checked`(bool)가 방향 인자로 들어갈 수 있다. 그래서 방향별 얇은 슬롯 2개로 감쌌다.
- 역방향에서는 코어의 실패 메시지 `(src N, dst M)` 이 헷갈린다("src" 가 Destination 개수를 가리킴).
  **`(driver N, driven M)`** 으로 바꿔 방향 중립으로 만들었다.
- `Connect 52 Facial Target` 은 요청 범위가 아니라 Source → Destination 한 방향 그대로 두고 문서에 명시.
- 검증: 버튼/툴팁 · 정방향 · **역방향(값이 실제로 반대로 흐르는지 getAttr 로 확인)** · 브로드캐스트
  반전 · 로그 방향 표기 · 개수 불일치 방어 + 기존 A00145 스위트 6종 전부 통과. #A00145

## 2026-08-10

> [!summary] `A00420_Wrapper` **버텍스 가이드 + 목록↔씬 선택 연동 + Order** (v01.02→01.03)
- **요청**: ① `Add Source` / `Add Target` 이 커브뿐 아니라 **버텍스**도 받게, ② 목록에서 소스/타깃을
  고르면 **씬에서도 그 커브·버텍스가 선택**되게.
- **가이드 종류 자동 판정**(`detect_kind`) — 커브 / 버텍스 `.vtx[]` / CV `.cv[]` / 로케이터를 받는다.
  **메시 오브젝트를 통째로 고른 경우는 일부러 거부**한다. 그대로 받으면 피벗 한 점이 조용히 가이드로
  들어가 결과가 이상해지는데 원인을 찾기 어렵다(엣지·페이스도 위치가 한 점으로 안 정해져 제외).
- **종류를 양쪽 따로 보관** — 한쪽씩 담다 보면 한쪽은 커브, 다른 쪽은 버텍스인 행이 생긴다. 커브는
  샘플 N 개, 점은 1 개라 짝이 안 되므로 **`curve / point mismatch`** 로 표시하고 사유와 함께 건너뛴다.
- **목록 → 씬 선택** — **누른 칸**이 무엇을 고를지 정한다(Source 칸=소스, Target 칸=타깃, Info 칸=양쪽).
  **On / Flip 체크박스 칸은 씬 선택을 건드리지 않는다** — 체크하려다 선택이 바뀌면 곧바로 다음
  `Add Source` 가 엉뚱한 것을 담기 때문. 지워진 노드는 걸러내고, 행 삭제 중에는 동작을 막았다.
- **Order 체크박스** — **컴포넌트는 Maya 가 인덱스 순서로** 주므로 버텍스를 여러 개 담으면 짝이 의도와
  다르게 맺힌다. 공용 TSL(`MOD_tsl_qt_v01`)에 **공개 헬퍼**(`acquire/release/is_order_tracking`)를 추가해
  **같은 전역 refcount 를 공유**한다 — 각자 `selectPref` 를 켜고 끄면 한 창이 닫힐 때 다른 창의 순서
  추적까지 끊긴다. 창이 닫히면 우리가 켠 경우에만 되돌린다.
- **함정(새로 확인)** — 컴포넌트의 선택 순서는 **"선택 이벤트" 단위**로만 기록된다. pref 를 켜 두어도
  `cmds.select([vtx70, vtx10, vtx40])` 처럼 **한 번에 리스트로** 고르면 `ls(orderedSelection)` 이
  **인덱스 순서**를 준다. 하나씩 클릭(`select(add=True)` 를 차례로)해야 순서가 잡힌다. 실사용은 문제가
  없지만 **헤드리스 테스트는 `add=True` 로 나눠 골라야** 한다. 오브젝트는 한 번에 골라도 순서 유지.
- 검증: mayapy 헤드리스 — `detect_kind` 7종, 버텍스 3쌍 담기, 메시 거부, 커브↔점 mismatch 표시 및
  Wrap 건너뜀, 커브 3쌍 + 버텍스 1쌍 실제 래핑, 칸별 씬 선택(Source/Target/Info/On) · 다중 행 ·
  지워진 노드 · 삭제 중 안전, Order on/off 순서 검증, TSL 과의 refcount 공유 + TSL 회귀,
  기존 테스트 5종 전부 통과. #A00420 #Framework

> [!summary] `A00145_RigConnect` **Connect / List Connected / Connect Closest 를 Connect 탭의 하위 탭으로** (v01.22→01.23)
- **요청**: 앞선 Constrain 탭처럼, 이 세 탭도 상위 `Connect` 탭의 하위 탭이 되도록.
- 세 탭 모두 "연결" 작업이라 최상위에 따로 있을 이유가 없었다. 최상위가 **6탭 → 4탭**
  (`Match / Constrain / Connect / Attribute`)으로 줄고, Connect 안에 `Connect / List Connected /
  Connect Closest` 가 들어간다.
- Constrain 것과 골격이 같아 **`_build_sub_tabs(pages)` 공통 헬퍼로 추출**했다. 두 그룹 모두
  `CONSTRAIN_PAGES` / `CONNECT_PAGES` 테이블 + 이 헬퍼로 만들어진다.
- 빌더 이름을 `_build_*_tab` → `_build_*_page` 로 정리. 기존 `_build_connect_tab` 은 그룹 빌더가
  되고, 어트리뷰트 연결 화면은 `_build_connect_page` 가 됐다.
- **이중 스크롤 주의** — 기존 Connect 화면은 스스로 `QScrollArea` 를 반환했다. 하위 탭은 `_scrolled()`
  로 한 번 더 감싸므로, 페이지는 평범한 `QWidget` 을 반환하도록 고쳤다(테스트로 이중 스크롤 없음 확인).
- Source/Destination 섹션은 **동시에 봐야 하는 짝**이라 접이식 그대로 뒀다.
- 검증: 최상위 4탭 · Connect 하위 3탭 구조/툴팁/개별 스크롤/이중 스크롤 없음 · 전 탭 전환 ·
  위젯 속성 전수 존재 확인 · Connect(Match from Source→연결) / List Connected / Connect Closest /
  Attribute 실제 동작 회귀 + 기존 A00145 스위트 5종 전부 통과. #A00145

> [!summary] `A00145_RigConnect` **Constrain 탭의 접이식 섹션을 하위 탭으로 전환** (v01.21→01.22)
- **요청**: Constrain 탭 안의 `Constraint` / `Skin Weight to Constraint` / `Group Create` 등이 접이식으로
  위에서 아래로 쌓여 있는데, 이걸 **하위 탭으로 옆에 나열**되게.
- 기능이 5개로 늘면서 원하는 것을 보려면 접었다 폈다 해야 했다. 이제 `QTabWidget` 중첩으로
  `Constraint / Skin Weight / Group Create / Transfer / Target Replace` 5개 하위 탭이 되고, 탭 하나에
  기능 하나만 보인다.
- 빌더 5개를 `CollapsibleBox` → 일반 탭 페이지(`QWidget` + `QVBoxLayout`)로 바꿨다. 이 파일의 다른 탭
  빌더와 같은 관용구가 됐고 이름도 `_build_*_box` → `_build_*_page` 로 정리. `CollapsibleBox` 자체는
  Connect 탭의 Source/Destination 이 계속 쓰므로 남는다.
- 탭 라벨은 창 폭(560)에 맞춰 줄이고 **전체 이름은 탭 툴팁**으로, 폭이 모자라면 `ElideRight` 로 말줄임.
  탭 전체를 감싸던 스크롤 영역은 **하위 탭별 스크롤**로 옮겨, 창을 줄여도 위젯이 겹치지 않는다.
- 검증: 하위 탭 구조/라벨/툴팁/개별 스크롤 · 전 탭 전환 · **5개 페이지의 위젯 속성 전수 존재 확인** ·
  Matrix 모드 토글 연동 · Constrain/Group Create/Target Replace 실제 동작 회귀 + 기존 A00145 스위트
  4종(target replace, match from source, attr_match, UI) 전부 통과. #A00145

> [!summary] `A00420_Wrapper` **Add Source / Add Target — 소스와 타깃을 따로 리스트업** (v01.01→01.02)
- **요청**: `Add Source` / `Add Target` 버튼을 만들어 소스와 타깃을 **따로** 담을 수 있게.
- **담는 규칙** — "**비어 있는 칸을 위에서 아래로 먼저 채우고, 남으면 그만큼 행을 새로 만든다**".
  소스 N 개를 담고 타깃 N 개를 같은 순서로 담으면 **행 순서대로 짝**이 맺힌다. 개수가 안 맞아도
  나중에 모자란 쪽만 더 담으면 **빈 칸부터 이어서** 채워진다(행이 무의미하게 늘지 않는다).
- **한쪽만 찬 행을 1급 상태로** — `GuidePair` 에 `is_complete()` / `missing_side()` / `set_side()` 를
  두어 반쪽 행을 정상 상태로 다룬다. 표시는 `< empty >` + Info 칸 `waiting for source/target`.
  샘플링(`build_control_points`)과 미리보기(`build_preview`)는 반쪽 행을 **조용히 넘기지 않고**
  `Guide row N has no target` 처럼 **몇 번째 행의 어느 쪽이 비었는지** 알리고 건너뛴다.
- 타깃이 소스보다 많아 짝 없는 행이 생기면 경고. 반쪽 행에 **Swap** 을 걸면 반대 칸으로 옮겨진다
  (스왑이 빈 칸도 그대로 맞바꾸므로 별도 분기 없이 동작). 커브 아닌 선택은 무시하고 개수를 알린다.
- 기존 **Add Curve Pair**(소스→타깃 순서로 한 번에)는 그대로 두어 두 방식 중 고를 수 있다.
- 검증: mayapy 헤드리스 — 소스 먼저/타깃 먼저 양쪽 순서, 개수 불일치(3소스 2타깃 → 이어붙이기),
  타깃 초과 시 행 증가 + 경고, 반쪽 상태로 Wrap 하면 건너뛰고 이유 로그, 완성 후 래핑 결과 검증,
  커브 아닌 선택/빈 선택, 반쪽 행 Swap, Add Curve Pair 회귀 + 기존 테스트 4종 전부 통과. #A00420

> [!summary] `A00420_Wrapper` **Swap — 선택한 가이드 쌍의 Source / Target 맞바꾸기** (v01.00→01.01)
- **요청**: 커브를 거꾸로(타깃 → 소스 순으로) 골라 리스트업했을 때 둘을 바꾸는 버튼. 단, **리스트업된
  것 중 선택한 행만**.
- 이름뿐 아니라 **UUID 도 함께 맞바꿔** 리네임된 커브도 계속 따라간다(헤드리스로 리네임 후 확인).
- 행의 성질인 **On / Flip 체크는 유지**하고, 이전 샘플링에서 계산해 둔 방향·시작점 정보(**Info** 칸)만
  더 이상 유효하지 않으므로 지운다. 행 표시는 저장된 이름이 아니라 **UUID 로 되찾은 현재 이름**을 쓴다.
- 선택한 행이 없으면 아무것도 하지 않고 알린다 — 전체를 조용히 뒤집는 쪽이 더 위험하므로
  (A00110 Euler Filter 의 "키를 안 골랐으면 실행 안 함"과 같은 판단).
- 검증: mayapy 헤드리스 — 부분 선택(0·2행만) 스왑, 무선택 시 무동작, 두 번 스왑 = 원위치,
  On/Flip 보존, 스왑 후 실제 래핑이 올바른 방향으로 붙는지, 리네임 후 UUID 추적 전부 통과. #A00420

> [!summary] `A00420_Wrapper` **신규 툴 — 커브 가이드로 다른 토폴로지 메시를 래핑** (v01.00)
- **요청**: Wrap3D 의 일부 기능. 토폴로지가 다른 두 메시에서 A 를 B 형태로 맞추되, 가이드를
  Wrap3D 의 `SelectPointPairs`(낱개 **포인트**)가 아니라 **커브 쌍**으로. 얼굴이면 입술·눈두덩·코
  라인처럼 특징이 "선"으로 잡히므로 커브 몇 개로 대응을 만든다.
- **가이드** — 짝지은 두 커브를 **호 길이 등간격으로 같은 개수 샘플링**해 i 번째끼리 대응. 커브 1개 =
  대응 포인트 24개(기본). cv 개수·degree 가 달라도 된다. **Snap** 옵션으로 샘플을 각 메시 표면
  최근접점에 당겨 "표면 → 표면" 대응으로 만든다. 점으로 못 박고 싶은 곳은 **Point Pair** 로 추가.
- **커브 쌍의 두 가지 사고를 자동 해결** — ① 진행 **방향** 반대, ② 닫힌 커브(눈·입 루프)의 **시작점(seam)**
  불일치. 두 커브를 각자 중심/크기로 **정규화**(메시 크기·위치가 달라도 비교 가능)한 뒤 정/역 × 시작점 N
  후보 중 오차 최소 조합 선택. **Show Guide Links** 로 샘플끼리 잇는 선을 그려 래핑 전 눈으로 확인.
- **2 단계 파이프라인** — ① **TPS 워프**(3D 커널 `phi(r)=r`)로 특징을 맞추고, ② 타깃 표면 최근접점으로
  **반복 투영**(비강체 ICP)해 세부를 붙인다. 투영만 하면 윗입술 정점이 아랫입술로 끌리고, 워프만 하면
  가이드 없는 볼·이마가 안 붙는다 → 두 단계가 한 짝. 투영 **변위**를 라플라시안으로 스무딩(Relax)해
  스파이크·뒤집힘을 막고, **Max distance / Normal angle limit** 로 안쪽 면에 붙는 것을 막는다.
- **함정** — `MMeshIntersector.create(node, matrix)` 에 **월드 행렬을 넘겨도 결과는 오브젝트 공간**이다
  (headless 확인). intersector 는 항등으로 만들고 좌표 변환은 numpy 로 통째 처리 → 행렬 변환이 파이썬
  루프 밖으로 나간다. 최근접점 20,000 회 **`MMeshIntersector` 0.6s vs `MFnMesh.getClosestPoint(kWorld)`
  4.9s (8 배)**. 컨트롤 포인트가 겹치면(커브 끝이 만나거나 가이드 교차) TPS 행렬이 특이해져 폭발 → 격자
  반올림으로 미리 병합.
- 쓰기는 `shape.pnts` **구간 setAttr**(A00380_MeshTool 과 동일)이라 undo 가 정확하고 히스토리·스킨이
  걸린 메시에서도 동작. 출력은 **New mesh(복제, 기본) / In place** + **Amount** 블렌드.
  가이드 커브 생성은 **A00400_CurveTool 재사용**(Curve from Edges).
- 검증: mayapy 헤드리스 — API 공간/성능 확인, 비선형 형태 차이(달걀형 변형구), 방향 반전 + 시작점
  회전 자동 정렬, 워프만/투영 포함, In place, 스킨 걸린 메시, 가드 옵션, Amount 블렌드, 겹친 컨트롤
  포인트 병합, UUID 리네임, UI 스모크(로드/추가/체크박스/미리보기/래핑/에러 경로) 전부 통과.
  **Maya 실사용 확인 완료.** 성능: 소스 32,222 정점 / 타깃 39,802 정점, 투영 8 회 → 총 0.98 초.
  (`e63199f`) #A00420

> [!summary] `A00145_RigConnect` **Connect 탭 Match from Source — 이름이 비슷한 어트리뷰트 찾기** (v01.20→01.21)
- **요청**: 오브젝트 A 의 어트리뷰트에 대해 오브젝트 B 의 어트리뷰트 중 글자가 유사한 것을 **A 의 순서대로**
  찾아 리스트업. 어트리뷰트가 1000개 이상일 수 있으니 빨라야 하고, **O 표기법으로 복잡도를 문서화**.
- **왜 편집 거리를 안 쓰는가** — 모든 쌍의 편집 거리는 `O(n·m·L²)`. n=m=1000, L≈25 면 6억 회 문자 연산
  이라 파이썬에선 분 단위다. 정확도도 낮다 — `brow_up` vs `lod0_mesh_body_brow_up` 은 길이 차 때문에
  편집 거리상 "많이 다른" 문자열이지만 사람이 보기엔 같은 것을 가리킨다.
- **토큰 역색인 + IDF** — 이름을 구분자와 camelCase 경계에서 토큰으로 쪼개고(`browUp` ↔ `brow_up` 매칭),
  후보 전체를 한 번만 훑어 `토큰 → 후보` 역색인을 만든다. IDF `log(1+m/df)` 덕에 `lod0` `mesh` `body`
  처럼 모든 후보에 있는 토큰은 가중치가 0 에 가까워 **공통 접두어를 사람이 지정할 필요가 없다**.
  점수는 coverage(질의 IDF 중 후보가 설명하는 비율) 주도 + precision·연속·접미·부분문자열·길이 가산점.
- **정확한 가지치기** — 포스팅을 드문 토큰부터 읽다가 남은 토큰들의 IDF 합이 `Min × 질의 IDF 총합` 에
  못 미치면 멈춘다. 그 뒤 토큰만 공유하는 후보는 문턱을 넘을 **수 없으므로** 정답을 놓치지 않는다.
  보일러플레이트 토큰의 거대한 포스팅 리스트를 아예 안 읽는다 → 평균 g 341→121, 시간 절반.
- **복잡도** `O(m·L + n·(g·t + g·log k))`, 최악 `O(n·m·t)`. 실측: 1000×1000 **0.15s**(질의당 0.12ms),
  5000×5000 2.63s. 브루트포스 difflib 대비 **약 145배**.
- **함정** — 폴백(토큰이 안 겹칠 때 쓰는 difflib)의 비율은 coverage 와 **척도가 다르다**. 무관한 이름도
  0.45 가 흔해서(`identification` vs `wibble_frobnicate`) 같은 문턱으로 비교하니 엉뚱한 매칭이 통과했다.
  0.5→0, 1.0→1 로 재스케일해 같은 문턱값이 양쪽에서 같은 뜻을 갖게 했다.
- 찾은 것을 destination 목록 맨 위로 **소스 순서대로** 올리고 선택 → `connect_attrs` 가 `src[i]↔dst[i]` 를
  순서로 짝지으므로 곧바로 Connect 로 이어진다. 동점 후보가 있으면 `ambiguous` 로 표시.
- `attr_match.py` 는 **maya import 가 없는 순수 파이썬**이라 DCC 없이 단독 테스트/벤치마크된다.
- 검증: 요청 예시 그대로 · 순서 보존 · camelCase↔snake · unique · 문턱 미달 보고 · 폴백 · 브루트포스
  교차검증 · 1000/2000/5000 벤치마크 + UI 스모크(매칭→연결까지) 전부 통과. (`1c4199c`) #A00145

> [!summary] `A00275_skinTool_V01` **Move Joints 탭 — 메시를 건드리지 않고 조인트 이동 후 재바인드** (v01.07→01.08)
- **요청**: 바인드된 메시에 영향 없이 조인트를 이동·회전한 뒤, 그 자리에서 다시 바인드되게 하는 기능.
  UI 는 A00290_BSTool 의 Edit 토글 방식(켜고 → 고치고 → 다시 눌러 반영). **버텍스별 웨이트는 불변.**
- **원리** — 인플루언스별 스킨 행렬은 `bindPreMatrix[i] * matrix[i]`. 편집 중 이 곱을 **상수로 유지**하면
  조인트가 어디로 가든 출력이 안 변한다. 시작 시점의 `C_i = bindPre_i(0) * world_i(0)` 를 상수로 잡고
  `bindPre_i(t) = C_i * worldInverse_i(t)` 를 인플루언스마다 **multMatrix 한 개**로 건다.
  Edit OFF 는 현재 출력을 정적으로 굽고 임시 노드를 제거 + bindPose 재생성.
- **함정** — `worldInverseMatrix` 를 `bindPreMatrix` 에 **직결하면 안 된다.** 스킨 행렬이 항등이 되어
  메시가 rest 로 튄다. 리그가 바인드 포즈일 때만 우연히 같고 **포즈된 리그에서는 3.6 유닛 점프**(실측).
  위 `C_i` 보정은 포즈와 무관하게 항상 무변화(오차 1e-16).
- **웨이트 불변은 정의상 보장** — `weightList` 를 읽지도 쓰지도 않는다(테스트에서 배열 전체 비교로 확인).
- Cancel 은 시작 시점의 `bindPreMatrix` + 조인트 트랜스폼을 skinCluster 의 `JUN_jointEditBackup`
  문자열 어트리뷰트(JSON)에 저장해 복원. 편집 상태는 UI 가 아니라 **씬(노드)** 에 있어, 툴을 새로 띄워도
  씬을 훑어 편집 중이던 skinCluster 를 되찾는다.
- 기존 **Bind Pose 탭과 순서가 반대**인 기능이라 문서에 차이를 명시(Bind Pose = 변형된 결과를 굳힌다 /
  Move Joints = 변형 없이 옮긴다). Move Joints 는 형상 델타를 굽지 않아 Orig·blendShape 를 안 건드린다.
- 검증: mayapy 헤드리스 — 바인드/포즈 상태 양쪽, skinMethod 3종, 웨이트 배열 전체 동일, Cancel 복원,
  성긴 인덱스, 다중 skinCluster, 잠긴 bindPreMatrix, 노드 잔류 없음, Go to Bind Pose + UI 스모크 전부 통과.
  (`9d1db12`) #A00275

## 2026-08-07

> [!summary] `A00145_RigConnect` **Constrain 탭 Target Replace — 컨스트레인트의 타깃(드라이버) 일괄 교체** (v01.19→01.20)
- **요청**: 여러 컨스트레인트가 쓰는 타깃들을 리스트업하고, 그중 하나(`tgt_A_02`)를 씬의 다른
  오브젝트(`tgt_B_02`)로 바꾸는 기능. 그 타깃을 가진 컨스트레인트만 교체되고, 없는 것은 방치.
- **`List Targets`** — 리스트업한 컨스트레인트들의 타깃 **합집합**을 보여 준다. 항목 뒤 `[n/m]` =
  *m개 중 n개가 이 타깃을 쓴다*, 툴팁에 어떤 컨스트레인트인지 나열. 검색은 공용 Filter.
- **재생성이 아니라 연결 rewire** — 컨스트레인트를 지웠다 다시 만들면 노드 이름, **weight 에 물린
  연결(IK/FK 스위치 등)**, 커스텀 어트리뷰트가 날아간다. 그래서 노드는 그대로 두고 `target[i]` 의
  **입력 연결만** 새 오브젝트로 갈아끼웠다. weight 값·연결·노드 이름·다른 타깃 전부 보존.
- **함정 1** — `listConnections("con.target[0]")` 는 컴파운드 배열 원소에 대해 **None** 을 준다.
  노드 단위로 받아 dest 플러그를 직접 파싱해야 한다. 멀티 인덱스도 `targetList` 순서에 기대지 않고
  들어오는 연결에서 역추적. `targetWeight` 와 컨스트레인트 자신이 소스인 연결(pointOnPoly 의
  `targetU/V`)은 타깃 판정에서 제외.
- **함정 2 (Keep in place)** — offset 규약을 mayapy 로 전부 실측했다. `parentConstraint` 의
  **`targetOffsetTranslate` 는 타깃 스케일을 포함한 전체 행렬**, **`targetOffsetRotate` 는 스케일을 뺀
  순수 회전** — 서로 다른 공간에 산다. 한 행렬로 같이 옮기면 스케일 걸린 타깃에서 driven 이 튄다.
  오일러 순서는 둘 다 **driven 의 `rotateOrder`**. 타깃별 offset 이라 **weight 가 섞여 있어도 정확**.
  나머지는 `point` 덧셈 / `scale` 곱셈 / `orient`·`aim` 은 `O_new = R_before * R_after⁻¹ * O_old`.
  보정 후 driven 월드 행렬을 다시 읽어 검증하고 어긋나면 경고.
- **joint ↔ 트랜스폼** 교체 시 `targetJointOrient`/`targetInverseScale`/`targetScaleCompensate` 를
  끊고 기본값으로 되돌리거나 새로 연결. 셰이프 기반(geometry/normal/tangent/pointOnPoly)은 같은 타입
  셰이프로. 대응 입력을 못 만들면 **아무것도 건드리지 않고** 경고만(부분 파괴 방지).
- 검증: mayapy 헤드리스 — 타입 5종 × rotateOrder 3종 keep-in-place, weight 연결 보존, joint 왕복,
  셰이프 교체, 동명 노드, 방어 케이스 + UI 스모크 테스트까지 전부 통과. (`1d18764`) #A00145

## 2026-08-06

> [!summary] `A00290_BSTool` **Mix Targets — 리깅 메시에서 New mesh 가 안 만들어지던 문제 + Base mesh 라벨** (v01.17→01.18)
- **요청**: 웨이트가 칠해진 리깅 메시에서 `New mesh` 를 골라도 새 메시가 안 생기고
  `could not reach the base (neutral) mesh ... Use the 'new mesh' option instead` 만 뜬다
  (이미 New mesh 를 고른 상태인데도). 그리고 베이스 메시가 무엇인지 보여 주는 QLabel 도 있으면 좋겠다.
- **원인** (mayapy 실측) — 중립을 `input[g].inputGeometry` 의 **상류 노드**로만 찾고 그것이
  메시일 때만 인정했다. 그런데 **정점을 한 번이라도 건드린 메시에는 `tweak` 노드가 끼어** 있어
  `tweak1.outputGeometry[0]` 이 잡힌다. 스킨/래티스가 앞이면 그 노드가 잡힌다 —
  `orig / tweak / skinCluster / 래티스` 4종 중 **3종에서 실패**.
- **해결 (New mesh)** — 플러그가 들고 있는 메시 **데이터**를 직접 읽는다(`MPlug.asMObject()` →
  `MFnMesh`). 상류가 무엇이든 중립을 얻을 수 있어 **항상 만들어진다.** 토폴로지·UV 는 베이스
  메시를 복제해 가져오고 포인트는 명시적으로 세팅. 히스토리/인터미디어트 없이 월드로 뺀다.
- **해결 (Deform it too)** — geometryFilter 는 모두 `input[N].inputGeometry` 로 거슬러 오를 수
  있으므로 **메시가 나올 때까지 따라간다**. `tweak` 은 오프셋을 그대로 통과시키므로 tweak 이 낀
  흔한 리그에서도 이제 동작한다. 옮긴 뒤 **blendShape 이 실제로 받는 중립을 다시 읽어 검증**하고,
  사이 디포머가 오프셋을 바꾸면(포즈된 스킨, 휘어진 래티스) 되돌리고 New mesh 를 안내한다.
- **Base mesh 라벨 추가** — `Base mesh: head_geo (neutral: head_geoShapeOrig)`. 통과시키지 못할
  디포머가 끼어 있으면 주황색으로 경고(`tweak` 은 통과시키므로 경고하지 않는다).
- **검증** — 리그 형태 7종(기본/tweak/스킨 먼저/**포즈된** 스킨/래티스/**휘어진** 래티스/회전 그룹):
  New mesh 는 7종 모두 생성 + 정점 단위 일치 + 히스토리 없음, Deform it too 는 **주장과 실제가
  항상 일치**. 기존 회귀(Base Shape 15 · Mix 코어 26 · 베이스 모드 8 · UI 23) 전부 통과.

> [!summary] `A00290_BSTool` **Mix Targets 탭 신규 — 소스 믹스를 다른 타겟들과 최종 메시에 일괄 반영** (v01.16→01.17)
- **요청**: 소스 타겟 `[a, b, c]` 와 수치 `[1, 0.5, 0.8]` 이 주어졌을 때, **그 셋을 그 비율로 섞은
  만큼** 나머지 타겟들이 변형되게 해 달라. 대상은 체크박스로 고르고 **전체 선택 체크박스**도.
  (이어서) 타겟뿐 아니라 **blendShape 의 최종 메시도** 같은 만큼 변형돼야 한다. 기본 메시는
  **조인트에 웨이트가 칠해진 리깅 메시**를 가정하고, 어려우면 새 메시를 만들어도 좋다.
- **동작 원리** — blendShape 평가가 `base + Σ(weight × delta)` 이므로 **같은 지오메트리의 델타는
  서로 같은 공간이고 그대로 더할 수 있다**(마야가 매 프레임 하는 일). 따라서
  `new_delta = old_delta + Σ(amount × delta(source))`.
- **UI** — 좌우 두 목록(소스 / 대상)을 스플리터로. 소스는 `Set to Selected` 로 배율을 찍으면
  체크되고 이름 옆에 `x0.5` 표시, `Use Scene Weights` 로 씬의 현재 weight 를 그대로 배율에 채운다.
  대상은 `Check All (visible)` 체크박스 하나로 보이는 행 전부 켜기/끄기. **소스로 체크한 타겟은
  대상 목록에서 회색으로 잠긴다**(소스는 절대 수정 안 됨).
- **이 탭만 "체크된 것이 작업 대상"** — 다른 탭은 "보이는 것이 작업 대상"이지만 목록이 둘이라
  필터로 쉽게 가려진다. 체크는 명시적 상태이니 가려져도 적용하고, `Checked: 3 (1 hidden)` 로
  가려진 개수를 항상 보여 준다.
- **최종 메시(Base mesh) 3모드** — 타겟이 "베이스로부터의 오프셋"이라 **베이스를 옮기면 델타를
  그대로 둔 타겟이 따라 움직인다.** 그래서 규칙을 하나로 못박고(*체크한 것은 변형, 안 한 것은
  그대로*) 세 갈래를 명시했다: `Leave it alone` / `Deform it too`(중립=바인드 셰이프를 옮기고,
  체크 안 한 타겟은 델타에서 믹스를 빼 제자리 보정) / `New mesh`(`<base>_mixed` 생성, 리그 무손상).
- **스킨 리깅 메시** — blendShape 이 체인 앞이면 입력이 언제나 `<base>ShapeOrig`(바인드 셰이프)라
  그것을 옮기면 되고 **skinCluster 는 그대로 살아 있다**. 실측: 바인드 포즈에서 보이는 메시가
  정확히 믹스만큼 이동, 포즈 상태에서는 스킨을 타고 변형(리깅 관점에서 올바름).
  베이스 포인트에는 **변환 없이** 더하면 된다 — `output = base + Σ(w×delta)` 라 정의상 같은 공간
  (스킨·origin·회전 8조합 실측).
- **구조** — `app/core/delta_utils.py` 를 새로 뽑아 Base Shape 탭과 저수준 처리(델타 공간, live 타겟
  메시 이동 + 검증/자가 보정)를 **공유**한다. Base Shape 동작은 회귀 15종 전부 통과로 불변 확인.
- **검증** — 코어 26종 + 베이스 모드 불변식 8종 + 스킨 메시 실측 + UI 22종(PySide2 offscreen).
  참고: `QApplication` 은 `maya.standalone.initialize()` **이전**에 만들어야 QWidget 이 안 죽는다.

> [!summary] `A00290_BSTool` **Base Shape — Apply 가 일부 정점만 반대로 스케일하던 문제** (v01.15→01.16)
- **요청**: 스킨 웨이트가 발라진 리깅 메시에서 Base Shape 탭 Apply 를 누르면, Value `0.5` 인데
  **어떤 정점은 의도대로 절반이 되고 어떤 정점은 `1.5` 를 넣은 것처럼** 반대로 커진다.
- **원인** (mayapy 실측) — 델타가 어느 공간에 있느냐는 blendShape 의 **`origin`** 이 정한다.
  `origin=1`(local, `cmds.blendShape` 기본) 이면 타겟 오브젝트 공간이지만 **`origin=0`(world) 이면
  베이스 오브젝트 공간**이다. v01.15 까지는 "항상 오브젝트 공간"이라 보고 델타를 그대로 이동량으로 썼다.
  그래서 타겟과 베이스의 transform 이 다르면(좌우 대칭 타겟의 `scaleX = -1`, FBX 임포트의 `rotateX -90`,
  프리즈한 복제본 …) **어긋난 축의 정점만** 반대로 갔다 — 미러면 X 로 움직인 정점만 뒤집히고 Y/Z 정점은
  멀쩡해서, 정점마다 되기도 하고 반대로 되기도 하는 것처럼 보인다.
- **해결** — world origin 이면 델타를 `base.worldMatrix × target.worldMatrix⁻¹`(3×3 부분)로 **타겟
  오브젝트 공간으로 되돌린 뒤** 이동한다. baked 타겟은 벡터를 그대로 X 배 하므로 공간과 무관(영향 없음).
- **자체 검증 + 자가 보정을 붙였다** — 옮긴 뒤 델타가 정말 X 배가 됐는지 **정점 번호로** 대조하고,
  어긋나면 되돌린 뒤 타겟 정점을 x/y/z 로 밀어 **응답 행렬을 직접 재서** 재시도한다(선형이라 3번이면 3×3).
  그래도 안 맞으면 타겟 메시를 원상복구하고 사유를 로그에 남긴다 — 조용히 틀린 모양을 만들지 않는다.
- **검증** — 공간 조합 11종에서 수정 전 6종 실패(미러는 정확히 ratio +1.5 = 사용자 증상) → 수정 후 전부
  통과. 스킨 리깅 메시 6종, 흩어진 40정점의 압축 컴포넌트 매핑, 안전망 강제 실패 시 원상복구까지 확인.
  19,881 정점 0.19초(검증 포함).

> [!summary] `A00290_BSTool` **Shape Editor — 스핀박스에 숫자를 칠 때 0 이 자동으로 채워지던 문제** (v01.14→01.15)
- **요청**: Expand 로 타겟에 수치를 숫자로 입력하면 **다 치기도 전에 0 이 채워진다.** `0.123` 을 치려고
  `0.1` 까지 치면 `0.100` 이 되고, `0.` 만 쳐도 `0.000` 이 된다. 자동으로 채우지 말고 **친 그대로** 받게 해 달라.
- **원인** (PySide2 실측) — `QDoubleSpinBox` 는 기본이 keyboard tracking **ON** 이라 **키를 누를 때마다
  값을 확정**하고, 확정할 때마다 편집 중인 텍스트를 소수점 자릿수에 맞춰 **다시 쓰며 커서를 옮긴다**
  (`interpretText` → `updateEdit`). 우리 `valueChanged` 핸들러가 되부르는 `_show_weight` 의 `setValue`
  도 같은 일을 한 번 더 한다.
- **해결** — 타겟 행 스핀박스에 `setKeyboardTracking(False)` → **Enter 또는 포커스 아웃에서 한 번만 확정**.
  더해서 `_show_weight` 가 **포커스를 가진(= 지금 타이핑 중인) 스핀박스는 건너뛴다** — 다중 편집이나
  120ms 폴링(`_sync_se_weights`)이 끼어들어도 편집 중인 칸을 덮어쓰지 않는다.
- 슬라이더 드래그 · 다중 선택 동시 편집 · 화살표/휠 스텝은 종전과 동일하게 즉시 반영된다.
- **검증** — mayapy 2024 / PySide2 offscreen `QTest` 실측. `"0.123"` 타이핑 시 tracking **ON** 은
  텍스트 `'0.100'` · 값 `0.1`(증상 재현, `_show_weight` 가드만으로는 안 고쳐진다 — Qt 자체 재포맷),
  tracking **OFF** 는 `'0.123'` · `0.123` · `valueChanged` 1회. `"0."` 부분 입력은 텍스트 유지 · 시그널 없음.
- 문서: `docs/A00290_BSTool.md` 에 "스핀박스에 숫자를 직접 입력할 때" 절 추가.

> [!summary] `A00290_BSTool` **Shape Editor — 키 걸린 타겟의 슬라이더가 실제로 먹게** (v01.13→01.14) — `6080fad`
- **요청**: Expand 로 타겟을 보면 키 애니메이션이 걸린 blendShape 의 슬라이더가 실시간으로 따라오긴
  하는데, **내가 슬라이더를 움직여도 타겟 수치가 조절되지 않는다.** 키가 걸려 있어도 조절되고,
  **Auto Keyframe 설정에 반응해 조절한 값이 현재 프레임의 키**가 되게 해 달라.
- **원인** (mayapy 실측) — v01.07 의 키 타겟 경로는 Auto Key 가 켜져 있으면 `setKeyframe` **하나만**
  냈는데, `setKeyframe` 은 커브에 키를 넣을 뿐 **그 자리에서 plug 값을 갱신하지 않는다**(시간이 다시
  흐르거나 강제 재평가가 있어야 반영). 그래서 드래그해도 메시가 꿈쩍하지 않고, 120ms 폴링이 옛 값을
  되읽어 슬라이더가 애니메이션 값으로 튕겨 돌아왔다.
- **해결** — 키를 찍은 뒤 **`setAttr` 로 값을 즉시 반영**한다. 키 걸린 plug 에 `setAttr` 은 (연결돼
  있어도) **에러 없이** 값을 바꿔 준다. 두 값이 같으므로 서로 싸우지 않는다. Auto Key 가 꺼져 있으면
  키 없이 미리보기만 되고 시간을 이동하면 커브로 복귀(마야 채널박스와 같은 감각) — 예전엔 이쪽도
  화면만 바뀌고 메시는 안 움직였다.
- **애니메이션 레이어 타겟도 살렸다** — 레이어에 넣는 순간 weight 의 직접 소스가 `animCurve` →
  `animBlendNode*` 로 바뀌어 `driven`(비활성)으로 분류됐다. `layered` 상태를 새로 두어 keyed 와
  똑같이 조절되고, 키는 활성 레이어에 찍힌다. 상태는 `free / keyed / layered / driven / locked`.
- **"드래그 중엔 미리보기, 놓을 때 키" 는 일부러 쓰지 않았다** — 그 편이 가벼워 보이지만 실측하니
  더 나빴다. Auto Key 가 켜져 있으면 **마야가 `setAttr` 마다 자체 키를 찍고**, 그 키가 우리 undo
  청크 **밖에** 별도 항목으로 쌓여 Ctrl+Z 가 두 번 필요해진다(setAttr 만 = undo 2회, 키+setAttr =
  1회). 키를 먼저 찍으면 뒤따르는 `setAttr` 이 같은 값이라 마야의 자동 키가 개입하지 않는다.
- **검증** — mayapy 2024 실측 54항목. core 30항목(상태 5분류, autokey ON/OFF 각각의 값·키·스크럽 후
  유지, 같은 프레임 재조절 시 키 갱신, 레이어 키가 베이스 커브 불변, 청크 undo), UI 24항목(PySide2
  실제 위젯으로 드래그·스핀박스·다중 선택·레이어·undo 1회). EM parallel 모드에서도 동일.

> [!summary] `A00110_animTool` **Euler Filter 탭 선택 기반 원버튼** (v01.37→01.38) — `7589ab8`
- **요청**: Euler Filter 탭의 두 입력(대상 리스트 · Start/End 구간)을 **한 버튼이 스스로 감지**해서
  적용해 달라. 예: 컨트롤러 3개를 선택하고 그래프 에디터에서 문제 구간의 키를 드래그로 고른 뒤
  버튼 하나 → 그 구간, 그 3개에 오일러 필터.
- **버튼** — `Euler Filter from Selection`(기존 `Euler Filter in Range` 위). **씬 선택 = 대상**,
  **선택한 키의 앞/뒤 프레임 = 구간**. Anchor 체크박스는 그대로 적용된다.
- **감지 로직은 core 에** — `EulerFilterManager.selected_objects()`(=`cmds.ls(sl=True)`) /
  `selected_key_range()`(=`cmds.keyframe(q=True, selected=True)` 의 min/max). 그래프 에디터의 **키
  선택은 오브젝트 선택과 별개**라 박스 드래그 뒤에도 컨트롤러 선택이 남아 있고, `keyframe(q, sl=True)`
  는 선택된 모든 키의 시간을 **오브젝트·어트리뷰트에 무관하게 전역으로** 주므로 여러 커브에 걸친
  선택도 한 번에 잡힌다.
- **감지 결과를 위젯에 되채운다** — 무엇을 어느 구간으로 처리했는지 눈으로 확인되고, 이어서 Anchor 만
  바꿔 아래 버튼으로 다시 돌려볼 수 있다(씬 선택이 비어 리스트로 폴백한 경우엔 리스트를 덮지 않음).
- **키 미선택이면 실행하지 않는다** — 폴백으로 Start/End 칸 값을 쓰면 "한 번에" 는 되지만, 의도치 않게
  **전 구간**을 건드릴 수 있다. '구간 한정' 이라는 탭의 약속을 깨는 쪽이 더 위험해 경고만 남긴다.
- **mayapy 2024 headless 검증**: 컨트롤러 3개 선택 + 20~40f 키 선택 → 감지 `objects=3`,
  `range=(20,40)`, 구간 안 27키 변경 / 구간 밖 0 / 미선택 컨트롤러 불변. 키·오브젝트 미선택 시
  감지가 각각 `None` / `[]`.

---

## 2026-08-05

> [!summary] `A00110_animTool` **구간 한정 Euler Filter 탭 추가** (v01.36→01.37) — `c7cd7f2`
- **요청**: 마야 그래프 에디터의 `Curves > Euler Filter` 는 선택한 컨트롤러의 **키가 찍힌 전 구간**을
  한꺼번에 처리한다. 회전이 뒤집힌 **일부 구간만** 펴고 나머지는 그대로 두고 싶다.
- **새 탭** — `Euler Filter`(Follow 와 Graph Focus 사이). **TSL 로 대상**을, **공용 timeRange
  위젯(Start/End)** 으로 **구간**을 지정해 그 구간 안의 `rotateX/Y/Z` 키만 편다. 로직은
  `app/core/euler_filter_manager.py` 의 `EulerFilterManager.filter_range()`.
- **직접 구현 대신 마야 필터를 겨냥** — mayapy 2024 headless 로 확인한 결과
  `cmds.filterCurve(filter="euler", startTime=, endTime=)` 는 **구간을 실제로 존중한다**(구간 밖 키가
  안 바뀜). 메뉴 명령이 전 구간을 처리하는 건 필터에 구간 개념이 없어서가 아니라 **MEL 이 구간을
  안 넘겨서**였다. 그래서 오일러 언와인딩(±360°)과 플립 표현 `(θ1+180, 180-θ2, θ3+180)` 선택을
  직접 구현하지 않고 마야의 수식·탄젠트 처리를 그대로 쓴다 — `rotateOrder` 가 `zxy` 여도 결과가
  마야와 일치한다.
- **Anchor 옵션(기본 ON) 이 없으면 정작 원하는 케이스가 안 고쳐진다** — 필터의 기준(앵커)은
  **구간 안 첫 키**이고 그 키는 절대 안 바뀐다. 즉 20f 에서 뒤집힌 걸 고치려고 구간을 `[20-40]` 으로
  잡으면 구간 안 키들끼리는 이미 일관돼 **0 key changed** 가 나온다. 그래서 필터 구간을 **Start
  직전 키까지 뒤로 넓혀** 그 키를 앵커로 삼는다 — 앵커는 값이 유지되므로 **"구간 밖은 그대로"** 를
  지키면서 앞쪽 애니메이션과 매끄럽게 이어진다.
- **결과 보고** — 필터 전/후 값 스냅샷을 비교해 **실제로 바뀐 키 수**를 세고, 구간 한정 필터의
  필연적 결과인 **End 경계 이음매**(`now step at the End boundary`)와 구간 밖 변경(마야 버전 대비
  방어 검사)을 경고로 알린다. 전체는 **단일 undo 청크**.
- **제외 규칙** — `rotateX/Y/Z` 세 축이 다 애님 커브를 가져야 처리한다(오일러 필터는 3축을 한
  묶음으로 봐야 한다). 없으면 사유와 함께 skip. 애님 레이어가 있으면
  `cmds.keyframe(plug, q=True, name=True)` 가 **선택된 레이어 커브 하나만** 돌려주므로 마야 기본
  필터처럼 **작업 중인 레이어에만** 적용된다.
- **검증**: mayapy headless **9 시나리오 통과**(앵커 ON/OFF 차이 · 구간 밖 키 불변 · End 이음매 감지 ·
  회전 커브 없는/씬에 없는 오브젝트 skip · `zxy` rotateOrder · 빈 구간 · undo 청크 · 가드).
  **마야 실기 UI 테스트 대기.** #A00110 #animTool #EulerFilter #filterCurve

> [!summary] `A00120_FKIK` **베이크 구간 UI 를 공용 timeRange 위젯으로 교체** (v01.07→01.08)
- **요청**: 베이크할 구간을 정하는 UI 를 `Framework/qt/MOD_timeRange_qt_v01.py`(`JUN_mod_timeRange_qt`)
  로 교체.
- **교체 대상** — Match / Bake 박스의 손수 만든 한 줄
  `Start [QSpinBox][Get Current]  End [QSpinBox][Get Current]`. A00110 에서 뽑아낸 공용 위젯이
  이미 같은 모양이라, 위젯 하나(`self.bake_range`)로 통째로 대체했다. 이제 A00110 · A00390 ·
  A00410 과 같은 위젯을 쓴다.
- **덤으로 얻은 것: `Get Sel Range`** — 그래프 에디터/타임슬라이더에서 **선택한 키들의 앞·뒤
  프레임**으로 Start·End 를 한 번에 채운다. 구간을 손으로 두 번 입력하던 것이 클릭 한 번이 됐다.
- **걷어낸 코드** — `_init_frame_range()` / `_set_current_frame()` / `_make_get_current_btn()`
  세 헬퍼 제거. 초기값(현재 playback 범위)만 주는 `_playback_range()` 만 남겼다 — 창을 열었을 때
  Start/End 가 재생 범위로 채워지는 동작은 그대로.
- **주의 하나**: QSpinBox 는 **항상 숫자**를 주지만 공용 위젯은 QLineEdit 기반이라 **빈 칸/비숫자면
  `values()` 가 `None`** 이다. `on_bake()` 에 가드를 넣어 그 경우
  `[Warning] Enter a valid Start / End frame.` 만 남기고 아무것도 하지 않게 했다(구간 없이 베이크가
  도는 사고 방지). 위젯 로그는 `log_callback=self.log` 로 툴 로그창에 연결.
- **검증**: `ast.parse` 문법 확인 + 호출부 전수 확인(`sb_start`/`sb_end` 잔존 없음).
  **마야 실기 UI 테스트 대기.** #A00120 #FKIK #timeRange #공용위젯

## 2026-08-03

> [!summary] `A00090_ConnectionBuilder` **규칙 json 을 버전 폴더로 분리 + UI 에서 버전 선택** (v01.04→01.05)
- **요청**: 규칙 json 의 **버전이 다른 상황**에 대응. `v001`, `v002` … 폴더마다 수정된 json 을 두고
  사용자가 UI 에서 버전을 고르게 한다.
- **폴더 구조** — `app/rules_v01/*.json` → **`app/rules/<version>/*.json`**. 기존 8개 json 은
  `git mv` 로 `rules/v001` 로 이동(이력 유지). 작업 폴더에 이미 만들어져 있던 동일 내용의
  `app/rules/v001` 사본은 정리하고 추적본으로 대체. `rules_v01` 안에 `v001` 을 넣는 안도 있었지만
  **이름 중복(v01 안의 v001)** 이라 `rules/` 를 루트로 잡았다.
- **`RuleLoader` 에 버전 개념 추가** — `find_versions()` / `get_version()` / `set_version()` /
  `rule_dir()`. `load` · `load_solver_rule` · `find_all_json` · `load_all` 은 **`version` 인자**를 받고,
  생략하면 현재 선택 버전을 쓴다. 선택 버전이 사라져도 **첫 버전으로 자동 폴백**하도록 `get_version()`
  이 매번 실제 폴더 목록을 확인한다(창을 열어둔 채 폴더를 지워도 죽지 않는다).
- **UI** — Rule 행을 `[Version ▾][Rule ▾][Refresh]` 로 바꿨다. 버전을 바꾸면 Rule 콤보를 다시 채우고
  (같은 이름이 있으면 **선택 유지**), `Create All` / `Connect All` / `Connect Intermediate` 는 전부
  **선택 버전의 json 만** 순회한다. 로그에도 버전을 찍는다.
- **함정 2개**: ① 콤보를 채우는 코드가 `self.log()` 를 부르는데 **로그 위젯이 아직 없으면 크래시** →
  초기 채우기를 `build_ui` 맨 끝(시그널 연결 뒤)으로 옮겼다. ② 채우는 도중 `currentTextChanged` 가
  튀어 재진입하므로 `blockSignals` 로 감쌌다.
- **검증**: 스텁 `maya.cmds` 로 `RuleLoader` 단독 확인 — 버전 스캔/`rule_dir`/8개 rule 로드/
  `load_solver_rule`/없는 버전 지정 시 `ValueError`. **마야 실기 UI 테스트 대기.** #A00090 #RuleVersion #JSON

> [!summary] `A00170_driverTool` **`Attr Search` 를 공용 Filter 로 대체** (v01.12→01.13)
- **요청**: A00170 에도 `JUN_mod_filter_qt_v01` 로 대체할 수 있는 UI 가 있으면 대체.
- **대상 3곳** — Remap Value 탭 Attributes, Stretch 탭의 **Default Distance / Stretch Object** 두 그룹.
  전부 `Attr Search` 입력 + `Search` 버튼이라 같은 패턴이었다.
- **TSL 안의 리스트에 붙였다**: 이 탭들의 Attributes 는 `QListWidget` 이 아니라 **TSL 위젯**이라,
  내부 `tsl.list_widget` 을 공용 Filter 에 넘겼다. 세 곳 모두 빌드가 `selected_items()` 를 쓰므로
  **"보이는 것이 작업 대상"이 그대로 성립** — `visible_selected()` 로 바꾸고 가려진 선택은 로그로 알린다.
  (TSL 의 `get_all_items()` / `selected_items()` 는 숨김을 모른다는 걸 공용 문서에 주의로 적었다.)
- **`Reveal` 버튼으로 기능 분리** — 옛 `Attr Search` 는 ① 일치 항목 **선택** ② 일치가 없으면
  토큰으로 **재질의**(`listAttr(obj.<token>)`) 를 한 버튼이 겸했다. A00145 에서는 ②가 사실상 죽은
  길이라 걷어냈지만, **여기서는 살아 있다** — Filter 는 이미 채워진 목록만 거르므로 애초에
  리스트업되지 않은 `worldMatrix` 같은 어트리뷰트는 못 찾는다. 그래서 ②를 **`Reveal` 버튼으로
  분리**해 기능을 보존했다(언제 재질의가 일어나는지 눈에 보인다). 드러낸 항목이 곧바로 가려지지
  않도록 Reveal 후 필터는 자동으로 비운다.
- **검증**: stub `maya.cmds` + PySide6(+pymel stub) 로 32항목 통과 — 세 곳 각각 부분 일치/대소문자
  무시/일치 없음/Clear/가려진 선택 제외/목록 재구성 후 유지. **테스트가 잡은 것**: Stretch Default 쪽
  TSL 은 **단일 선택**이라 두 개를 동시에 선택할 수 없다 → 선택 모드에 따라 기대값을 나눠 검증.
  **마야 실기 UI 테스트 대기.** #A00170 #Filter #공용위젯 #Reveal

> [!summary] `A00290_BSTool` **두 탭의 검색을 공용 Filter 위젯으로 이전** (v01.12→01.13)
- **요청**: `JUN_mod_filter_qt_v01` 로 A00290 Base Shape 의 검색을 대신하고, 툴 전체를 공용 위젯으로 이전.
- **Base Shape 탭**: `QListWidget` 이라 그대로 붙였다. 자체 구현(`_apply_bs_filter` /
  `_update_target_number` / `_visible_selected_targets` / `on_select_all_targets`)을 전부 걷어내고
  위젯의 `refresh()` · `visible_selected()` · `select_all_visible()` 로 대체 — 동작은 동일.
- **Shape Editor 탭**: 여기가 남겨 뒀던 확장 지점이었다. 목록이 `QListWidget` 이 아니라
  **행 위젯을 쌓은 것**(행마다 Edit 버튼·슬라이더·스핀박스)이라 위젯에 **`rows_provider` 모드**를 추가했다 —
  `() -> [(이름, 위젯), ...]` 콜러블을 넘기면 `setVisible()` 로 행을 숨긴다.
  개수 라벨은 탭과 **확장(Expand) 창 두 곳**에 반영해야 해서 `number_label` 대신
  **`filtered(shown, total)` 시그널**을 받아 직접 쓴다(양방향 필터 동기화도 여기서 유지).
- **이전하면서 덤으로 얻은 것**: 두 탭 모두 **`Clear` 버튼**과 **공백 여러 단어 AND**
  (`brow up` → `browInnerUp`)가 생겼고, Shape Editor 탭에 **`Number: 보이는수 / 전체수`** 가 붙었다
  (예전엔 전체 수만). 공용화의 실익이 바로 나온 사례 — 한 곳을 고치니 두 탭이 같이 좋아졌다.
- **검증**: stub `maya.cmds` + PySide6 로 28항목 통과 — Base Shape 16(부분 일치/대소문자/AND/Clear/
  Number 라벨/가려진 선택 제외/목록 재구성 후 유지), Shape Editor 12(rows_provider 판정, 행 숨김,
  시그널 경유 Number 라벨, `visible_rows`, 행 재구성 후 유지).
  A00145 32항목 + Base Shape core 12항목도 회귀 통과. **마야 실기 UI 테스트 대기.**
  #A00290 #Framework #Filter #공용위젯 #rowsProvider

> [!summary] `Framework` **공용 Filter 위젯 신설** + `A00145_RigConnect` 적용 (v01.18→01.19)
- **요청**: A00290 Base Shape 의 Filter 가 좋다 — **입력하면 일치하는 것만 남고 나머지는 안 보이는**
  그 특성을 `A00145_RigConnect` 의 **Search 버튼** 자리에 적용할 것. 그리고 **앞으로 검색 기능이 있는
  모든 툴을 같은 Filter 로 통일**하고 싶다. 일단 A00145 부터.
- **먼저 공용 위젯으로 뽑았다** — `Framework/qt/MOD_filter_qt_v01.py`(`JUN_mod_filter_qt`).
  A00145 에만 복사해 넣으면 세 번째 툴에서 또 복사하게 되고, "통일"이라는 요청의 목적 자체가 무너진다.
  `attach()` / `refresh()` / `visible_selected()` / `select_all_visible()` + `filtered` 시그널,
  `number_label` 을 주면 `Number: 보이는수 / 전체수` 자동 갱신.
  매칭은 **부분 일치·대소문자 무시**에 **공백 여러 단어 = AND**(`brow up` → `browInnerUp`)까지 넓혔다.
- **A00145 적용** — Connect 탭 **Source/Destination 두 패널** + **Attribute 탭**, 세 곳 모두 교체.
  - 옛 `Search` 버튼은 ① 일치 항목을 **선택**하고 ② 일치가 없으면 검색어로 어트리뷰트를 **재질의**했다
    (MEL 시절 동작). ①은 `Filter` + `Select All` 로 대체. ②는 **부분 일치가 하나도 없을 때만** 도는
    경로라 실질적으로 죽은 길이었고(`List Attributes` 가 전체 재조회 담당) 그대로 걷어냈다.
  - Attribute 탭의 검색은 원래 **조회 인자**(`list_attributes(obj, user_only, search)`)여서 Enter 를
    쳐야 다시 질의됐다 → 이제 전부 받아 와서 **즉시 거른다**. core 시그니처는 그대로 두고 UI 만 안 넘긴다.
- **"보이는 것이 작업 대상" 규칙을 여기서도**: Qt 는 숨겨도 선택을 유지하므로 `Select All` 은
  `select_all_visible`, `Connect Source to Destination` 과 Attribute 복사는 `visible_selected()` 로
  거르고 가려진 선택은 `[INFO] ... hidden by the filter were skipped` 로 알린다.
  (A00210 → A00290 → A00145 로 같은 규칙을 세 번째 적용 — 공용 위젯 문서에 규칙으로 못 박았다.)
- **검증**: stub `maya.cmds` + PySide6 로 32항목 통과 — 위젯 단독 16항목(부분 일치/대소문자/AND 토큰/
  Clear/Number 라벨/`refresh` 전후/가려진 선택), A00145 16항목(src·dst·Attribute 세 곳 각각 필터 표시,
  보이는 선택만 반환, 가려진 선택 제외, Preview 갱신). **마야 실기 확인 완료(2026-08-03).**
- **다음**: A00290 Base Shape 를 공용 위젯으로 이전. Shape Editor 탭은 `QListWidget` 이 아니라
  **행 위젯 목록**이라 그대로는 못 붙는다 — 위젯이 "무엇을 숨길지"를 콜백으로 받도록 확장해야 한다(문서에 기록).
  #A00145 #Framework #Filter #공용위젯 #보이는것이대상

> [!summary] `A00290_BSTool` **Base Shape 타겟 Filter(검색)** (v01.11→01.12)
- **요청**: Base Shape 탭의 Targets 목록에서 **이름으로 타겟을 찾는 검색**. **일부만 쳐도** 잡히게
  (`Inner` → `browInnerUp`).
- **반영**: 목록 위에 **`Filter`** 입력 칸 + **`Clear`** 버튼. 부분 일치·**대소문자 무시**.
  Shape Editor 탭에 이미 있던 Filter 와 **같은 규칙**으로 맞춰 두 탭의 검색 감각을 통일했다.
  `Number` 라벨은 필터 중 **`보이는 수 / 전체 수`**(`Number: 2 / 9`)로 바뀌고,
  `List Targets` 로 목록을 다시 채워도 **필터가 유지**된다.
- **함정 — Qt 는 항목을 숨겨도 선택을 유지한다**: 그대로 두면 **필터에 가려 안 보이는 타겟까지
  Apply 가 먹는다.** A00210 에서 세운 규칙(**보이는 것이 작업 대상**)을 여기서도 지켰다 —
  `Select All` 은 보이는 것만 선택(가려진 것까지 잡는 `QListWidget.selectAll` 대체),
  `Apply` 는 **보이면서 선택된** 것에만 적용하고 가려진 선택은 `[Info] ... were skipped` 로 알린다.
  선택이 전부 가려졌으면 아무것도 안 하고 필터를 지우라고 안내. 선택 자체는 지우지 않으므로
  여러 필터를 오가며 고른 뒤 **필터만 비우면 한 번에** 적용된다.
- **검증**: stub `maya.cmds` + PySide6 로 17항목 통과 — 부분 일치/대소문자 무시, 일치 없음,
  Clear 복귀, Number 라벨, Select All 가시 한정, 가려진 선택 제외(그리고 "Qt 가 선택을 유지한다"는
  전제 자체도 확인), 목록 재구성 후 필터 유지. **마야 실기 확인 완료(2026-08-03).**
  #A00290 #BaseShape #검색 #보이는것이대상

> [!summary] `A00030_quickTool` **`Local Axis ON` / `OFF` 버튼 추가** (V01.14→V01.15)
- **요청**: 그동안 `toggle -localAxis` 를 직접 쳐서 축을 봤는데, 선택한 오브젝트 **전부를 한 번에**
  보이게/안 보이게 하는 버튼이 필요하다. 현재 상태를 진단한 뒤 필요한 것만 바꾸는 방식.
- **`Display` 섹션 + 버튼 2개** — 콜백은 `JUN_cmd_set_local_axis(state)` 하나를 `args=[True/False]`
  로 공유한다. 오브젝트마다 `displayLocalAxis` 를 먼저 읽어 **목표 상태와 다른 것만** 바꾸므로,
  일부만 켜진 섞인 선택도 전부 같은 상태로 정렬된다(토글이 아니라 절대 상태).
- **`toggle -localAxis` 는 쓰지 않았다(mayapy 실측)**: 값은 바뀌지만 **undo 큐에 아무것도 남기지
  않는다.** 청크로 감싸도 빈 청크라서, 버튼을 누른 뒤 Ctrl+Z 를 치면 로컬 축이 아니라 **그 이전
  작업이 취소된다**(테스트에서 joint 생성이 undo 됨). `setAttr` 은 정상적으로 undo 되어 이쪽 채택.
- **선택 해석**: `ls(sl=True, objectsOnly=True)` 로 컴포넌트 선택도 받는데, 이때 나오는 shape 에는
  `displayLocalAxis` 가 **없다**(shape 에 `toggle` 을 걸면 에러도 없이 무시됨). 그래서
  `JUN_fun_resolve_local_axis_node()` 로 **부모 transform 까지 올라가서** 적용한다.
- 여러 오브젝트는 `undo_chunk()` 로 묶어 Ctrl+Z 한 번에 복구. 잠기거나 연결된 어트리뷰트는
  `setAttr` 이 실패하므로 노드 목록을 경고로 보고한다. 섹션이 늘어난 만큼 창 높이 360 → 420.

> [!summary] `A00290_BSTool` **Base Shape Apply 가 되돌아오던 버그 수정** (v01.10→01.11)
- **증상**: Base Shape 탭에서 Apply 로 타겟의 기본 모양을 바꾸면 **그 순간엔 바뀐 것처럼 보이는데**,
  씬을 저장하거나 Shape Editor 탭의 Edit 로 들어가면 **Apply 전 모양으로 되돌아온다.** "어느 순간부터
  안 된다"고 했다.
- **원인(mayapy 로 재현)**: 타겟 메시가 씬에 남아 `inputGeomTarget` 으로 **연결된(live) 타겟**에서는
  `inputPointsTarget` 이 **연결된 메시로부터 매번 다시 계산되는 값**이다. 여기에 `setAttr` 을 하면
  **에러도 경고도 없이** 다음 평가에서 원래 값으로 돌아간다(실측: 99 로 써도 dgdirty 후 5.0 복귀).
  v01.10 까지는 포인트 수가 0 이 아니라는 이유로 **"N target(s) rescaled" 성공 보고만 하고 실제로는
  아무 일도 안 했다.** 뷰포트는 더티 캐시 때문에 잠깐 바뀐 것처럼 보이고, 저장·Edit 처럼 재평가를
  유발하는 순간 원복 — 사용자가 본 그대로다. **baked 타겟(메시 삭제)에서는 정상 동작**이라
  "어느 순간부터"는 타겟 메시를 남겨두는 씬을 쓰기 시작한 시점이었다.
- **수정**: 아이템마다 `inputGeomTarget` 연결로 **live / baked 판정** →
  baked 는 기존대로 `inputPointsTarget` 스케일, **live 는 타겟 메시 정점을 직접 이동**.
  델타가 곧 타겟 메시이므로 이것이 기본 모양을 바꾸는 정공법. in-between 은 아이템마다 다른 메시에
  연결될 수 있어 **아이템 단위**로 판정한다.
- **델타는 오브젝트 공간**(실측): `inputGeomTarget` 이 `worldMesh` 로 연결돼 있어도,
  base/target transform 이 서로 달라도 `delta = 타겟 로컬 − 베이스 원본 로컬` 이다.
  → 정점을 **오브젝트 공간에서** `(X−1)×delta` 상대 이동. 월드로 옮기면 타겟에 회전·스케일이 있을 때
  어긋난다(첫 시도에서 실제로 틀린 값이 나와 확인됨).
- **이동은 `shape.pnts`(tweak) 구간 setAttr** — A00380 peak_manager 와 같은 방식.
  메시 데이터(`vrts`)를 안 건드려 undo 정확, **19,462 정점 6.4초 → 0.17초(약 38배)**.
  `getAttr(".pnts")` 통짜 조회는 "compound with mixed type elements" 로 실패하므로 기존 tweak 은
  `MPlug.getExistingArrayAttributeIndices()` 로 읽는다.
- **검증**: mayapy 12항목 통과 — live/baked 각각 `weight 1.0 모양 == 예전 weight X 모양`,
  저장/재오픈 유지, `sculptTarget` Edit 진입·해제 유지, Ctrl+Z 1회 복귀, in-between 전 아이템 스케일,
  19k 정점 0.166초. **마야 실기 확인 완료(2026-08-03).** #A00290 #BaseShape #blendShape #liveTarget

> [!summary] `A00210_FileManager` **Path Structure 가 파일도 캡처/재생성** (v01.28→01.29)
- **요청**: 지금은 경로(폴더) 구조만 저장/생성한다. **감지된 파일도** 저장·생성할지 정하는 **체크박스**를
  두고 **기본은 체크**. 저장할 때와 생성할 때 모두 사용자가 정할 수 있게. 생성되는 파일은 **0바이트 빈
  파일**이고, `test.ma` 를 잡았으면 `test.ma` 가 아니라 **`test.ma__`** 로 만들어 **원본과 생성물을 구분**.
- **반영** — 체크박스 2개(둘 다 기본 켬)
  - **`Include files`**(Save Structure) — Capture 가 파일 이름도 기록(JSON 에 `files` 추가).
    **이름만 담고 내용은 안 담는다** — "원본 mb/ma 는 공유 대상이 아니다" 라는 이 툴의 원칙 그대로.
    깊이·최상위 체크리스트 규칙은 폴더와 동일. 단 **base 직속 파일은 체크리스트와 무관하게 항상 포함**
    (어느 최상위 폴더에도 속하지 않는 base 자체의 내용물이라서).
  - **`Create files`**(Preview 행, 구 *Show files* 대체) — 기록된 파일을 **트리에 체크박스와 함께** 보여주고
    Recreate 가 생성. 파일 하나만 체크 해제해 건너뛸 수 있다.
- **`Show files` 를 남기지 않고 흡수한 이유**: 예전엔 "표시 전용"이라 별개 토글이어도 됐지만, 이제 파일이
  **생성 대상**이다. 표시와 생성을 따로 두면 *안 보이는데 만들어지는* 항목이 생겨 Depth 규칙과 어긋난다
  → **트리에 보이는 것이 만들어지는 것**으로 통일.
- **표식 `__` 는 확장자 뒤에 덧붙인다**(`test.ma__`). 확장자를 바꾸지 않아 원래 이름을 그대로 읽을 수
  있으면서, 탐색기·DCC 가 이 빈 파일을 진짜 씬으로 열려 하지 않는다. `marked_name()` 은 **멱등** —
  재생성된 트리를 다시 Capture→Recreate 해도 `____` 로 늘지 않는다.
- **기존 파일은 절대 안 건드린다**: 같은 이름이 있으면 덮어쓰거나 비우지 않고 `existing_files` 로만 집계.
  `open(..., "x")` 배타 생성이라 **검사와 생성 사이의 경쟁 상태에서도** 내용이 날아가지 않는다.
- **하위호환**: `files` 키 없는 구버전 JSON → 빈 목록으로 읽혀 **폴더만 재생성**(기존 동작 그대로).
  `recreate()` 반환은 **`RecreateResult`**(폴더/파일 따로 집계)로 바꾸되 `created, existing = recreate(...)`
  2-튜플 언패킹을 유지해 호출부가 안 깨지게 했다.
- **함정(기록)**: `QTreeWidgetItem` 은 **`ItemIsUserCheckable` 을 기본으로 켠 채** 만들어진다(체크 상태를
  안 주면 체크박스가 안 그려질 뿐). 그래서 "체크 가능한가"를 **플래그로 판정하면 루트·표시전용 파일까지
  통과**한다 → 저장해 둔 `rel`/`recorded` 데이터 롤로 판정하도록 고쳤다(테스트가 잡아냄).
- **검증**: core 24항목 + UI 12항목 전부 통과 — 깊이별 파일 캡처(1/2/All), `include_top` 필터, JSON 왕복,
  구버전 호환, `__` 표식·0바이트·재실행 시 내용 보존, 소스 원본 무해, `files=None` 하위호환, 부모 폴더
  자동 생성, 트리 recorded/표시전용 구분, Create files OFF 시 파일 0개.
  **실기 UI 확인 완료(2026-08-03).** #A00210 #PathStructure #파일재생성 #하위호환

---

## 2026-07-30

> [!summary] `A00060_jointTool_V02` **`Match to Sel` 버튼 추가** (v01.03→01.04)
- **요청**: Curve 탭의 `Match to Obj` 는 **TSL 에 리스트업된** 오브젝트/버텍스만 대상으로 동작한다.
  그 **오른쪽에 버튼을 하나 더** 만들어 **지금 선택한** 오브젝트/버텍스로 바로 Match to Obj 를 수행할 것.
  `Order` 가 켜져 있고 버텍스를 여러 개 선택했다면 **고른 순서대로** 처리할 것.
- **반영**
  - `Tool : joint to obj` 의 버튼을 한 행(`QHBoxLayout`)으로: 왼쪽 **`Match to Obj`**(리스트) /
    오른쪽 **`Match to Sel`**(현재 선택). 축 옵션(Connect·Separate, Foward/Secondary axis,
    Secondary axis orient)은 **두 버튼이 공유**한다 — 핸들러를 `_match_to_objs(label, objs)` 로
    묶어 대상만 갈아끼운다. `core` 는 **무변경**(`joints_to_objs` 가 이미 순서 있는 리스트를 받음).
  - 선택 순서는 **공용 위젯에 이미 있는 판정을 재사용**했다. `JUN_mod_tsl_qt_v01._maya_selection()`
    을 **`maya_selection()` 으로 public 노출**(Framework) → `Match to Sel` 은 이걸 호출만 한다.
    Select/Add 버튼과 **정확히 같은 규칙**이라 두 경로가 어긋날 여지가 없다.
  - 빈 선택은 만들지 않고 `[ERR] ... nothing selected`. Order 가 꺼진 채 2개 이상 선택하면
    `[INFO] 'Order' is off` 로 **인덱스 순서로 간다고 미리 알린다**(조용히 다른 순서로 만들지 않음).
- **함정(기록)**: `ls(sl=True)` 는 **컴포넌트를 고른 순서가 아니라 인덱스 순서**로 준다. 5→0→3→1 로
  찍어도 0,1,3,5 다. 게다가 pref 가 꺼져 있으면 `ls(orderedSelection=True)` 도 **에러 없이 조용히**
  인덱스 순서를 돌려주므로, "순서가 되는지"는 반환값이 아니라 **pref 를 조회해** 판단해야 한다.
- **검증**: mayapy 8항목 전부 통과 — pref OFF 면 `ls(os)` 가 `[0,1,3,5]`(함정 재현) / pref ON 이면
  `[5,0,3,1]`, 그 순서대로 **체인이 5,0,3,1 위치로** 생성(루트 1개·길이 4), `Separate` 는 전원 루트,
  오프셋 그룹(+7Y) 아래 오브젝트도 **월드 위치 보존**. **마야 실기 UI 테스트 대기.**
  #A00060 #MatchToSel #선택순서 #Framework

> [!summary] `portfolio` **Epic PoseWrangler 플러그인 패치 내역 정리**(1-6 절 신설)
- **요청**: `PoseDriverConnect/python` 의 git 기록에서 **최초 코드 ↔ 최신 코드** 차이를 분석해,
  이력서 「MetaHuman 기반 캐릭터 리깅 및 커스터마이징 경험」 항목용 서술로 포트폴리오 두 문서에 추가.
- **분석**: 커밋 4개(`699e71e` = 벤더 원본). 실질 변경은 `serializer_v1_2_0.deserialize()` 한 함수.
  원본은 델타 모드 프리셋의 `driven_transforms`(헬퍼/트위스트 코렉티브 조인트)가 **씬에 전부 있다고 전제** —
  rest 매트릭스 수집에서 예외, 델타 복원에서 `current_driven_transforms[name]` KeyError → 헬퍼가 하나만
  없어도 **임포트 전체 실패**(= 커스텀 아바타에 프리셋 재사용 불가). 패치는 ① `cmds.objExists` 필터
  ② 복원 루프 skip ③ driven 0개 솔버는 생성 스킵+로그(껍데기 솔버 방지).
- **반영**: `portfolio_KR.md` / `portfolio_EN.md` 에 **1-6 절**을 1-5(비메타휴먼 아바타 일반화) 뒤에 배치
  — 이 패치가 1-5 의 **전제 조건**이라는 인과가 드러나게. frontmatter `updated` 갱신, 메모리 기록.
  플러그인 포크는 `JUN__PoseDriverConnect` (master=벤더 / dev=내 패치) 로 이미 동기화 상태. #portfolio #MetaHuman

> [!summary] `A00410_SecondaryMotion` **Bone Chain / Bone Root 모드 + 출력 레지스트리** (v01.01→01.02)
- **요청**: `A00390_WindTool` 에서 Bone Chain / Bone Root 를 나눈 것과 **같은 요청**. 기본(연속된 FK 계층)
  을 Chain 모드로 두고, **Root 모드**에서는 TSL 항목들을 각각 **임의의 체인의 최상위 부모**로 보고 자손마다
  기능을 수행할 것. + 훗날 **output 을 curve/node 로 나누는 요청**에 대비해 코드를 준비해 둘 것.
- **확인 결과 — 모드는 이미 있었지만 컨트롤러에서 깨져 있었다**: v01.00 의 `Chain From: List order /
  Hierarchy` 가 그 동작이었는데, Root+Controller 로 돌리면 계층 탐색이 transform 을 전부 담아
  `[ctl_01, ctl_02_offset, ctl_02, ctl_03_offset, ctl_03]` 처럼 **오프셋 그룹까지 체인 노드**가 됐다
  → 그룹에 키가 찍히고 체인 길이가 배로 늘어 **falloff 도 어긋남**. (조인트는 `type="joint"` 필터로 무사)
- **반영**
  - 이름을 A00390 어휘로 통일: **`Mode: Bone Chain / Bone Root`**, core 상수 `MODE_LIST` → **`MODE_CHAIN`**
    (예전 이름은 별칭 유지).
  - **그룹은 지나가되 담지 않는다** — **셰이프를 가진 노드(=컨트롤)만** 체인 노드가 된다(`_is_control`).
    셰이프가 아예 없는 계층(그룹만으로 된 체인)에서는 **필터를 끄고 재시도**하는 폴백.
  - 자식이 없어 체인이 안 된 루트를 로그로 알린다(`empty_roots`, 전엔 조용히 사라졌다).
  - 체인 해석 반환을 **`ChainResolveResult` 객체**로(항목이 늘어도 호출부가 안 깨짐, 3-튜플 언패킹 호환).
- **출력 확장 대비**: **`app/core/outputs.py` 레지스트리** 신설.
  `OutputSpec(id, label, family, apply_fn, needs_solve)` + `register()`, 계열은 `FAMILY_CURVE`(현재
  Layer/Bake Keys) / `FAMILY_NODE`(예약). **`needs_solve=False` 면 프레임별 솔브를 건너뛴다**(노드망은
  프레임 해가 불필요). **UI Output 라디오를 레지스트리에서 자동 생성** → spec 하나 등록하면 UI 에 나타난다.
  `OUTPUT_NODE`("Live Node")를 `implemented=False` 로 예약(호출하면 명확히 거부). 솔버·샘플러·회전
  재구성은 출력 방식을 모른다.
  - 파일에 **노드 출력의 난점**도 적어 뒀다: A00390 의 싸인은 `t` 만으로 값이 정해져 노드망으로 옮길 수
    있었지만, 2차 모션 솔버는 **이전 프레임 속도가 필요한 상태 누적형**이라 적분 표현식/커스텀 노드가 필요하다.
- **검증**: mayapy 신규 21항목 + 기존 3종 스위트(22/10/UI 22) 전부 통과. Bone Root+Controller 가
  **컨트롤만** 잡음(`ctlA_01..04`, 그룹엔 키 없음), 루트 2개→체인 2개 왕복 **6.6e-13**, 조인트 다중
  루트+분기 3체인·공유 노드 중복 없음, Bone Chain 무회귀(첫 프레임 오차 0), 레지스트리 apply/거부 동작.
  **마야 실기 UI 테스트 대기.** #A00410 #BoneRoot #outputs #확장지점

> [!summary] `A00030_quickTool` **`Copy Scene Folder` 버튼 추가** (V01.13→V01.14)
- **요청**: 버튼을 누르면 현재 씬 파일이 저장된 위치를 클립보드에 복사(이후 Ctrl+V 붙여넣기). 이어서
  "파일 이름은 빼고 폴더까지만" 복사하도록 수정 + 창 세로가 짧아 마지막 버튼 아래 Copyright 가 잘림.
- **반영**: 새 **`File` 섹션**에 **`Copy Scene Folder`** 버튼(콜백 `JUN_cmd_copy_scene_path`).
  `cmds.file(q, sceneName)` 로 씬 경로를 얻어 **`os.path.dirname` 으로 파일명 제거 → 저장 폴더만**,
  `os.path.normpath` 로 OS 네이티브(`\`) 경로로 변환 후 **Qt `QApplication.clipboard().setText`** 로
  복사(Maya 밖에서도 붙여넣기). 미저장(untitled) 씬은 경고만. 섹션 추가로 창 높이 **300→360**(Copyright 노출).
- **검증**: mayapy — `cmds.file(q, sceneName)` 미저장 `''` / 저장 시 전체 경로, `dirname`+`normpath` 폴더
  네이티브 경로 확인. 모듈 컴파일 통과. **마야 실기 확인은 셸프 `run(True)` 로**.

> [!summary] `A00410_SecondaryMotion` **셸프 아이콘 제작** (SVG + 32×32 PNG)
- **요청**: 툴 아이콘 제작. 규약대로 `icon/*.svg` → `dev/build_icons.py` 로 32×32 PNG 래스터화.
- **디자인**: 휘어지며 **팁이 되감기는 구슬 체인**(루트만 채운 원 = 부모에 100% 구동). 그 whip 실루엣이
  이 툴이 굽는 lag 이다. 배경/accent 는 저장소 공통(`#2d2d30` / `#ff9e64`).
- **32px 가독성 때문에 4번 고쳤다**(매번 실제 렌더해 이웃 아이콘과 나란히 비교):
  얇은 링크+작은 구슬 → 구슬이 선에 **묻혀 울퉁불퉁**해짐 / 상단 화살표 → 화살촉이 뭉개져 **망치**로 읽힘 /
  점선 고스트 → **스페클로 깨짐** / 세로 rest 선 → 루트 구슬에 붙어 **핀·손잡이**로 읽힘 /
  체인이 가로 6px 만 차지 → 이웃들은 타일 폭을 꽉 쓰는데 답답함. → **요소 2개(굵은 링크 + 큰 구슬)** 로 확정.
  의미 전달(고스트로 before/after)을 조금 포기하고 **가독성을 택한 판단**.
- **주의(기록)**: `dev/build_icons.py` 는 **41개 SVG 를 전부 다시 렌더**한다. 이전에 다른 백엔드로 렌더된
  PNG 12개의 바이트가 바뀌어, 무관한 변경은 되돌리고 이 툴만 커밋했다. #A00410 #icon

---

## 2026-07-29

> [!summary] `A00410_SecondaryMotion` **FK 컨트롤러 원본 포즈 보존 + 팁 회전(dummy bone)** (v01.00→01.01)
- **요청(사용자 실기 테스트)**: ① `ctl_01/02/03` FK 체인에 적용하면 **ctl_02·ctl_03 과 그 하위의 원래
  위치가 보존되지 않는다**(원래 위치에서 애니가 시작되게 할 것) ② **마지막 컨트롤러 ctl_03 에 키가
  안 찍힌다**(다른 것처럼 회전하게 할 것). 세팅: List order / Controller / Substeps 3 / Bake Keys.
- **① 원인 = 코드 버그**: 회전 재구성이 각 노드의 DAG 부모를 **바로 앞 체인 노드로 가정**하고 있었다.
  조인트 체인은 맞지만 FK 리그는 `ctl_01 > ctl_01_offset > ctl_02` 처럼 **중간에 오프셋 그룹**이 껴서,
  **그룹 회전이 컨트롤러 로컬값에 그대로 구워졌다** → 스윙이 0 인 첫 프레임부터 포즈가 깨지고 하위가 어긋남.
  - **수정**: 노드별 **실제 DAG 부모** 월드 회전을 프레임마다 샘플링(`ChainSample.parent_quats` 를
    노드별로 확장)하고, 앞 체인 노드의 월드 델타를 물려준 `parent_orig[i] * q_swing[i-1]` 를 부모로 사용.
    부모가 곧 앞 노드인 조인트 체인에서는 수학적으로 동일 → **무회귀**.
  - **재현/검증**: 그룹 회전 (11,-7,23) 리그에서 ctl_02 첫 프레임 기록값 `[11,-7,23]` → **원본 `[0,0,0]`**,
    ctl_03 위치 오차 2.295 → **4.7e-05**, `blend=0` 하위 자식까지 **5.8e-15**, 시작 프레임 위치 오차 **0**.
- **② 팁 회전**: 팁은 자식이 없어 방향을 못 정한다 → KawaiiPhysics 의 **dummy bone** 처럼 마지막 뼈를
  같은 방향/길이로 한 번 더 연장한 **가상 점**을 붙여 방향을 만든다. `Rotate last node (dummy bone)`
  체크박스(기본 켬), 끄면 v01.00 동작. 검증: 빠른 구동에서 팁 **17.55°** 회전(중간 노드 1.89°).
  가상 점이 체인에 포함되어 **falloff 분모가 바뀌므로** 같은 파라미터라도 v01.00 과 미세하게 다르다(의도).
- **남긴 사항**: 빠른 구동 + Substeps=3 에서 왕복 오차 **4.7e-05**(리그 스케일 대비 ~3ppm). 느린 구동
  4.7e-12 / 조인트 체인 6.2e-08 이고 addKeys·setValue 경로가 동일값이라 기록 문제도 아님 — **원인 미특정**,
  실사용 영향 없음으로 판단해 CHANGELOG·문서에 기록. #A00410 #bugfix #FK #KawaiiPhysics

> [!summary] `A00410_SecondaryMotion` **신규 툴 — FK 체인 관성(2차 모션·찰랑임)을 키로 굽기** (v01.00)
- **요청**: 마야에서 언리얼 **KawaiiPhysics** 같은 체인 관성(부모에서 먼 자식일수록 제자리에 남으려는
  성질)을 키 애니메이션으로 재현. 마야 시뮬 솔버는 **너무 무거움** — 더 빠르고 **실시간**으로 볼 것.
  계획서 요청 → 승인 후 v01.00 제작(+ **조인트 직접 모드** 지원, 이름 `A00410_SecondaryMotion`).
- **판단**: nucleus 계열은 성능 이전에 **작업 흐름**이 안 맞는다(시작 프레임부터 순차 재생 필수 → 스크럽
  불가, 파라미터마다 재재생, 별도 베이크 단계). Jiggle 은 메시 전용, spring 컨스트레인트는 길이/각도
  제어 없음. → **KawaiiPhysics 식 위치기반 스프링 근사를 순수 파이썬으로 직접 구현**.
- **핵심 설계(실측이 결정)**: mayapy 로 20본×300프레임 재보니 솔버 **6ms**, 벌크 키 기록 **7ms**,
  드라이버 샘플링 **13ms**. 즉 **전 구간 재계산이 30ms** → 파라미터를 만질 때마다 **구간 전체를 다시 풀어
  프리뷰 override 레이어에 통째로 다시 굽는다**. 재생은 그냥 커브 재생이라 **런타임 시뮬 없는 실시간**.
  (`setKeyframe` 0.529s vs `MFnAnimCurve.addKeys` 0.007s = **74배** → 벌크 API 고정)
- **구현**: `chain_solver.py`(**maya 비의존** 순수 파이썬: 베를레+감쇠→스프링→**길이 구속**→각도 제한,
  **Falloff 가 관성 다이얼** `stiffness_i = stiffness*(1-falloff*i/(n-1))`), `pose_builder.py`(점→로컬 회전,
  **순수 스윙**이라 트위스트 보존), `scene_sampler.py`(체인 해석 + 1회 샘플링 캐시), `bake_manager.py`
  (프리뷰 레이어 · override 레이어 승격 · 키 굽기).
- **마야 변환 규칙 확정(구현 전 mayapy 검증)**: joint `local = R*JO` → `R = L*JO⁻¹`(**조인트 모드는
  jointOrient 를 벗겨야 함**), transform `local = RA*R`, 공통 `world = local*parentWorld`,
  override 레이어 weight 는 base↔layer **선형 블렌드**(base 50/layer 90 → w0.5 에서 70).
- **검증**: 헤드리스 49항목 통과. **왕복 검증**(기록한 회전으로 계산한 실제 씬 위치 == 솔버 결과)이
  조인트 모드 **9.7e-13**(비자명 JO + rotateOrder 6종 혼합), 컨트롤러 모드 **5.4e-12**(비자명 rotateAxis).
  관성: 팁으로 갈수록 편차 증가(0.59→1.04), 즉발 회전 지연 루트 0 → 팁 2프레임.
  UI 는 stub `maya.cmds` + PySide6 로 27항목(mayapy 는 QWidget 생성 불가).
- **문서**: 계획서 [plans/A00410_ChainPhysics_plan](plans/A00410_ChainPhysics_plan.md),
  사용법 [A00410_SecondaryMotion](A00410_SecondaryMotion.md), `docs/README.md` 등록.
  #A00410 #SecondaryMotion #KawaiiPhysics #PySide #mayapy

> [!summary] `Framework/qt/MOD_tsl_qt_v01` **공용 TSL 에 선택 순서 유지(Order) 추가** — 모든 PySide 툴 공통
- **요청**: 컴포넌트 모드로 버텍스를 여러 개 골라 `Select` 하면 **고른 순서와 무관하게** 리스트업된다.
  선택한 순서를 기억해 그 순서대로 담게 할 것. 항상 켜기 어렵다면 **토글**로 하는 게 맞는지 판단해 제안.
- **원인**: `cmds.ls(sl=True)` 는 컴포넌트를 **인덱스 순서**로 돌려준다(5→0→3→1 로 찍어도 0,1,3,5).
  **오브젝트/트랜스폼은 원래부터 선택 순서를 유지**하므로, 깨지는 건 컴포넌트 한정.
  순서를 얻으려면 Maya 전역 pref **Track Selection Order** 를 켜고 `ls(orderedSelection=True)` 로 읽어야 한다.
- **반영**: 헤더 행(타이틀~Number 사이)에 **`Order` 체크박스** 추가 — **세로 공간 증가 0**.
  ON = pref 를 켜고 Select/Add 가 `ls(orderedSelection=True, flatten=True)` 사용 / OFF = **우리가 켠 경우에만**
  pref 원복(사용자가 원래 켜둔 설정은 보존). TSL 이 여러 개 떠 있어도 **전역 refcount** 로 관리하고,
  위젯이 파괴되면 pref 자동 반납(전역 설정을 남기지 않음). 체크 시 "다시 선택하라" 로그 안내.
- **토글로 한 이유**: ①전역 프리퍼런스라 말없이 켜두면 다른 작업까지 영향 ②pref 는 **켠 시점부터** 기록해서
  항상 켜둬도 "다시 선택" 제약이 안 사라짐 ③순서가 필요 없는 리스트는 인덱스 순이 오히려 읽기 편함.
  순서가 늘 중요한 툴은 `order_default=True`, 씬 노드가 아닌 리스트는 `show_order=False`.
- **API**: `show_order` / `order_default` 생성 옵션, `set_order_tracking()` / `is_order_tracking()`.
  기존 호출부 **75곳을 AST 로 전수 확인** — 위치 인자 2개 이상 사용처가 없어 파라미터 추가로 깨지는 툴 없음.
- **검증**: mayapy 로 실제 Maya 의미론 확인(pref OFF 면 `ls(os=True)` 도 **에러 없이** 인덱스 순서 → 반환값이
  아니라 pref 조회로 판별해야 함 / ON 이면 `vtx[5],0,3,1` 그대로 / 마퀴·해제후재선택·오브젝트+컴포넌트 혼합 정상).
  위젯 배선은 **stub `maya.cmds` + PySide6** 로 26항목 전부 통과 — mayapy 안에서는 `maya.standalone` 이 이미
  `QGuiApplication` 을 만들어 둬 `QWidget` 생성 자체가 불가. **마야 실기 테스트 대기**.
- **문서**: 공용 위젯 문서 [Framework_MOD_tsl_qt](Framework_MOD_tsl_qt.md) 신규 작성(옵션·API·UUID 보관·
  Order 동작·문제 해결), `docs/README.md` 에 **공용 위젯** 섹션 추가.
  #Framework #TSL #selectionOrder #PySide #mayapy

> [!summary] `A00400_CurveTool` **신규 툴 — 메시 엣지 → 커브(그룹별) + Reverse Direction** (v01.00)
- **요청**: `ref_01.mel` 처럼 선택한 메시 엣지에 부착된 커브를 만들되, 여러 엣지 구간을 고르면 **구간마다 커브를
  따로** 만들 것(ref 는 선택 전체를 커브 1개로만 묶음). + TSL 에 담은 커브들의 `cv[0]`/`cv[n]` 위치를 축으로
  비교해 **Reverse Direction** 으로 방향 통일(A00360_SortTool 참고).
- **반영**:
  - **엣지 그룹핑**: 선택 엣지를 **정점 공유 연결 성분별로 그룹**(BFS)지어 그룹마다 `polyToCurve(form=2, degree,
    ch=1)` 로 커브 1개 생성. `polyToCurve` 는 다중 그룹을 선택해도 커브 **1개**만 만들어 직접 그룹핑이 필수였다.
    `ch=1` 이라 커브가 메시에 부착. Name Prefix / Smooth(degree 3) 옵션.
  - **Reverse Direction**: `cv[0]`/`cv[n]` 월드 축값 비교 → `cv[0]` 을 Max end(기본)/Min end 에 오도록
    `reverseCurve`. 이미 정렬/판단 불가(두 끝 동일)/커브 아님은 skip. 대상은 TSL `get_all_nodes()`(UUID-safe).
  - A00360 구조(launch/__dragDrop/app.core/app.ui) 클론, coral_dark 테마. 아이콘 SVG→`dev/build_icons.py` PNG.
- **검증**: mayapy — 떨어진 3 엣지 구간 → 정확히 3그룹/3커브, `reverseCurve` 실제 cv 반전(cv0 Y 0→3),
  cv0_at_max/min 양방향·이미정렬 skip·커브아님 skip·빈선택 에러 전부 통과. **마야 실기 테스트 대기**.

---

## 2026-07-27

> [!summary] `A00390_WindTool` **Node 드라이버별 전체 타이밍 offset(windPhaseOffset)** (v01.07→01.08)
- **요청**: Node 모드에서 노드 한 개당 그 본들이 싸인의 어느 타이밍 값을 갖는지(전체 offset) 조절하는
  어트리뷰트. Bone Root 모드에서 루트들이 지금은 다 같은 타이밍인데 서로 다르게 하고 싶음.
- **반영**: 드라이버에 **`windPhaseOffset`**(전체 위상 타이밍 offset) 어트리뷰트 추가. 노드망이
  `base = windPhaseTime − windPhaseOffset` 를 그룹 공용으로 두고 각 조인트가 `base − i×windOffset`
  사용 → 그 드라이버 전체 타이밍을 시프트. 드라이버마다 다른 값 = 서로 다른 타이밍.
- **UI `Node Offset`**(Node 전용): 드라이버 순번 k 마다 `windPhaseOffset = k×값` 초기화 → **Root 모드
  루트별 자동 다른 타이밍**(0 이면 동일=기존). 이후 각 드라이버 windPhaseOffset 직접 조절 가능.
  (구분: `windOffset`=체인 내 본별 지연, `windPhaseOffset`=드라이버 전체 타이밍.)
- **검증**: mayapy — windPhaseOffset=3 이면 피크 t=3→t=6, Root node_offset=3 이면 rootA/B/C 가 0/3/6 →
  피크 t=3/6/9(서로 다른 타이밍), node_offset=0 동일(무회귀), Node/Curve 회귀 통과. **마야 실기 확인됨(사용자).**

> [!summary] `A00390_WindTool` **Curve / Node 출력 + Node 재생속도(windSpeed) 제어** (v01.02→01.07)
- **Curve / Node 출력 선택**(v01.03): Curve=조인트에 키 굽기(기존). Node=`windPeriod/Amplitude/Offset/
  windSpeed` 어트리뷰트를 가진 **null(로케이터) 드라이버 + 노드망**으로 파형을 **실시간** 재현. 어트리뷰트
  편집이 즉시 반영. **Bone Chain=드라이버 1개, Bone Root=루트 수만큼**. sin 은 정규화 싸인 `animCurveUU`
  LUT(preInfinity/postInfinity enum=3 로 무한 반복)로 구현 — Maya 2023 sin 노드 부재 회피(A00170 Remap
  아이디어). setInfinity 는 UU 커브에 안 먹어 enum 직접 setAttr 필요.
- **재생 속도 제어 반복 수정**(v01.04~01.07, 사용자 피드백 3회):
  - v01.04 `windTime`(시간값) 리타임 — 상수로 두면 애니가 멈춰 폐기.
  - v01.05/06 `windSpeed`(값=속도) — 상수는 라이브(`time*windSpeed`), 키 애니는 위상 역행(찰랑임 뒤집힘).
  - **v01.07 최종**: `windPhaseTime` 을 **`∫windSpeed dt` 적분 표현식**(MEL, 프레임 사다리꼴+소수 잔여
    구간, `getAttr -time` 샘플 → 스크럽 안전)으로 라이브 계산. **windSpeed 를 값으로 바꾸든 키로
    애니메이션하든 버튼 없이 즉시 반영 + 위상 역행 없음**(단조 전진). windSpeed=1 → phaseTime=frame
    (curve 모드와 동일 위상). Apply Speed 버튼 제거(자동).
  - 원리: 속도는 시간의 적분이라 단순 곱셈(time*speed)이면 가변 속도에서 순간 주파수가 음수가 돼 뒤집힌다
    (mayapy: 곱셈 19프레임 역행 vs 적분 0 역행).
- **검증**: mayapy — 사용자 예시 파형, Node 실시간 어트리뷰트/cycle, Bone Root 다중 드라이버, windSpeed
  값·키 애니 자동 반영·역행 없음·소수 프레임 정확, Curve 무회귀. **마야 실기 확인됨(사용자, 단계별)**.

> [!summary] `A00390_WindTool` **Bone Chain / Bone Root 모드 추가** (v01.01→01.02)
- **요청**: 지금은 리스트업한 조인트들에만 적용된다. **Bone Root** 모드를 추가해, 리스트업한 각 조인트를
  체인 루트로 보고 그 조인트의 **자손들마다** Bone Chain 기능을 반복 수행하게.
- **반영**: `Mode` 라디오(Bone Chain 기본 / Bone Root).
  - **Bone Chain**: 리스트 = 한 체인, 리스트 순서 = offset 순번(기존 동작).
  - **Bone Root**: 리스트 각 항목 = 체인 루트 → 그 조인트 + **모든 자손 조인트**(BFS)에 **root 로부터의
    깊이(depth)를 offset 순번**으로 파형 반복. offset 은 루트마다 리셋, 분기 형제(같은 depth)는 같은
    offset, 겹치는 조인트는 처음 것만(중복 방지). 코어 `_chain_from_root`/`_resolve_targets` +
    `apply_wind(mode=...)`.
- **검증**: mayapy — rootA depth0/1/2 → offset 0/10/20, rootB offset 리셋, 분기 형제 동일 위상,
  chain 모드는 자손 무시(무회귀), 내부 0 제거·양끝 앵커 root 모드에도 적용. **마야 실기 확인됨(사용자)**.

> [!summary] `A00390_WindTool` **구간 내부 0 교차 키 제거로 커브 부드럽게** (v01.00→01.01)
- **문제**: 극값 사이 0값 키(주기 절반마다, 예: period 12 → 6·12·18…f)가 있으면 spline 커브가 그
  지점에서 평평/각지게 되어 부드럽지 않다.
- **수정**: 기본으로 **내부 0 교차 키를 빼고 극값(±진폭)만** 남긴다. 대신 구간 **양끝(Start/End)** 에는
  그 지점 실제 싸인 값으로 **앵커 키**를 둬 커브가 구간 밖으로 흘러가지 않게 한다. `Keep zero-crossing
  keys` 체크박스(기본 off)로 예전 동작 복원. `_key_times_values` 가 `{시간:값}` dict 정렬 반환 →
  앵커가 격자 극값과 겹쳐도 중복 없음.
- **검증**: mayapy — 극값(3→40, 9→-40) 유지, 내부 0(6·12·96) 키 제거, 양끝(0·100) 앵커 유지,
  offset 조인트 동일, keep-zero on 시 예전처럼 0 키 생성, period 10 소수(2.5/7.5 유지·5/10 제거).
  **마야 실기 확인됨(사용자)**.

> [!summary] `A00390_WindTool` **신규 — 본 체인에 싸인 파형 키를 찍어 '바람에 일렁이는' 애니메이션** (v01.00)
- **기능**: 리스트업한 본 체인의 회전(또는 이동) 축에 `value(t) = amplitude * sin(2π(t - i*offset)/
  period)` 파형을 키로 찍는다. 키는 **1/4 주기마다**(0, +A, 0, -A …) 찍고 **spline** 탄젠트로 보간해
  싸인 파형을 만든다. `quarter = period/4` 가 소수면(예: period 10 → 2.5, 7.5) **소수 프레임에 키**.
  조인트 순번 `i` 는 위상을 `i*offset` 프레임 미룬다 — A00110 Stagger 와 달리 **offset 은 실수 프레임**.
- **구성**: in-Maya PySide(arch A, A00360 스켈레톤 복제). TSL(`JUN_mod_tsl_qt`) + 구간
  (`JUN_mod_timeRange_qt`, A00110 외 첫 외부 소비처) + Axis 콤보(rotate/translate X/Y/Z) +
  Period/Amplitude/Offset 스핀박스 + Clear-range 옵션. 로직 `app/core/wind_manager.py`(UI 비의존),
  Apply 는 `undo_chunk` 로 한 번에 묶음. 아이콘 SVG→PNG(QtSvg offscreen 렌더).
- **검증**: mayapy — 사용자 예시(rotateX 0~100 p12 a40 o10 → jnt_01 3=40/9=-40/0·6·12=0 매12f 반복,
  jnt_02 +10f·jnt_03 +20f 밀림), period 10 → 2.5/7.5 소수키, 소수 offset 2.5, 재적용 시 키 안 쌓임,
  spline 탄젠트 모두 통과. **마야 실기 확인됨(사용자)**. 참고: Maya 가 회전 키를 라디안으로 저장·복원
  → 30° 가 29.9999996 로 돌아오는 미세오차(회전 키 툴 공통, 표시·동작상 동일).

> [!summary] `Framework/qt/MOD_timeRange_qt_v01` **Start/End 구간 입력 UI 를 공용 위젯으로 승격(모듈화)** + `A00110_animTool` 이 소비 (v01.35→01.36)
- **요청**: A00110 의 `Start [값][Get Current]  End [값][Get Current]  [Get Sel Range]` UI 를
  `Framework/qt` 로 승격해 MOD_tsl_qt 처럼 다른 툴에서도 편하게 쓰도록 모듈화.
- **반영**: 새 위젯 `JUN_mod_timeRange_qt_v01`(별칭 `JUN_mod_timeRange_qt`, `Framework/qt/__init__.py`
  등록). Get Current(현재 프레임 1칸) + Get Sel Range(선택 키 앞/뒤로 두 칸) 내장. maya.cmds 는 lazy
  라 Maya 밖에서도 생성/단위테스트 가능(가짜 `_cmds` 주입). API: `start()/end()/values()`,
  `set_range()`, `set_inputs_enabled()`, `changed` 시그널. 내부 `start_edit`/`end_edit` 를 노출해
  마이그레이션 시 기존 `.text()/.setText()` 참조가 그대로 동작.
- **A00110 리팩터링**: 6개 탭(Move Keys · Stagger · Copy · Mirror · Bake · Follow)이 이 위젯을 쓰도록
  교체. `self.le_*_start = widget.start_edit` 별칭으로 하위 코드 무변경. 툴 내 중복 헬퍼 5개
  (`_make_get_current_btn`/`_selected_key_range`/…) 제거. Bake Custom 모드 토글은
  `bake_range.set_inputs_enabled(custom)` 로 단순화.
- **검증**: 위젯 격리 테스트 21개 통과(Qt 를 mayapy 에서 maya.standalone 없이 offscreen 으로 — 이 조합은
  크래시 없음; maya 경로는 가짜 `_cmds` 로). A00110 모듈 import + 별칭 경유 위젯 생성 OK, 잔여 참조 0.
  MainWindow 전체는 Qt+cmds 동시 필요라 헤들리스 불가 → **A00110 실기 UI 확인 대기**.

> [!summary] `A00110_animTool` **`Get Sel Range` 버튼 — 선택한 키프레임 구간으로 Start/End 한 번에 채우기** (v01.34→01.35)
- **요청**: Get Current(현재 프레임 1칸) 외에, **지금 선택한 키프레임들 중 제일 앞/뒤 프레임**을 찾아
  Start·End **두 칸을 함께** 채우는 버튼이 필요. 예: 어떤 컨트롤러의 6~15f 키를 선택 후 누르면
  Start=6, End=15.
- **반영**: Start/End 가 있는 **모든 탭**(Move Keys · Stagger · Copy · Mirror · Bake · Follow)에
  `Get Sel Range` 버튼 추가. `_selected_key_range()`(`cmds.keyframe(q=True, sl=True)` 의 min/max, 여러
  커브 걸쳐 선택해도 전체 앞/뒤) → `_set_selected_key_range()` 가 두 칸을 채움(선택 키 없으면 경고).
  팩토리 `_make_get_selected_range_btn()` 은 Get Current 과 같은 `lambda *_a` 로 checked 인자 흡수.
  Bake 탭은 `btn_bake_get_range` 로 보관해 **Custom range 모드에서만 활성**.
- **검증**: mayapy — `selectKey(time=(6,15))` → (6,15), 선택 없음 → None. Qt UI 는 헤들리스 크래시라
  로직만 확인. **마야 실기 동작 확인됨(사용자)**.

> [!summary] `Framework/qt/MOD_tsl_qt_v01` **다중 레퍼런스(중복 UUID) 씬에서 리스트→씬 선택이 항상 같은 오브젝트로 잡히던 버그 수정** (공용 TSL, A00110 등 ~18툴 공유)
- **증상**: A00110_animTool Follow 탭 TSL 에 여러 오브젝트를 리스트업하고 하나씩 클릭해도 씬에서는
  **계속 같은 오브젝트**가 선택됨. **단순 씬은 정상**, 같은 마야파일을 **네임스페이스만 달리해 여러 번
  불러온 복잡한 씬**에서만 발생. dev_tsl 에서 TSL 을 UUID 기반으로 바꾼 뒤 생긴 현상.
- **원인**(mayapy 재현): **import 는 UUID 를 새로 재할당(유일)하지만, reference 는 파일의 UUID 를
  그대로 유지**한다. 그래서 같은 파일을 여러 번 레퍼런스하면 네임스페이스가 달라도 대응 노드가
  **UUID 를 공유** → `cmds.ls(uuid, long=True)` 가 여러 노드를 반환하는데 `_node_of` 가 **`found[0]`**
  만 집어, 그 UUID 를 담은 모든 항목이 **첫 노드 하나로만** 해석됐다.
- **수정**: `_node_of` 는 `ls(uuid)` 가 **여럿이면 담을 때의 표시 이름(네임스페이스 포함)으로 하나를
  좁힌다**(`_match_by_text`: `cmds.ls(이름) ∩ found`, 그래도 애매하면 `found[0]` 폴백). UUID 가
  **유일할 때의 동작(리네임/리페어런트 안전)은 그대로**. 아울러 `append_unique` 의 중복 판정을 raw
  UUID → **해석된 현재 경로** 기준으로 바꿔, 공유 UUID 라도 네임스페이스가 다른 복사본은 둘 다
  담기게(예전엔 뒤엣것이 중복으로 잘못 거부).
- **검증**: mayapy 실제 3중 레퍼런스 씬 — `A/B/C:ctrlA` 공유 UUID 3개가 각 네임스페이스로 정확히
  해석 / 유일 UUID 는 리네임+리페어런트 후에도 정확(무회귀) / `append_unique` 3복사본 모두 추가 후
  진짜 중복만 거부 / 단순 씬 정상. Qt+standalone 은 헤들리스 크래시라 위젯 대신 fake stand-in 으로
  실제 메서드 구동 — 마야 실기 확인 대기.

## 2026-07-24

> [!summary] `A00275_skinTool_V01` **Transfer 탭: combine 메시 소프트 셀렉션 수정 + 근접 shell 방치** (v01.06→01.07)
- **배경**: 여러 조각이 하나로 **combine 된 메시**에서 소프트 셀렉션(Volume falloff)으로 전이 범위를 잡으면
  ⑴ `(kInvalidParameter): Object is incompatible with this method` 에러, ⑵ 붙어 있지 않은 **근접 shell**
  까지 함께 전이(방치하고 싶은 부위가 전이됨).
- **수정 ⑴ 소프트 매칭**: `_soft_weights` 가 리치 셀렉션 컴포넌트를 **문자열 경로**로 비교해 combine/rename
  메시에서 매칭이 틀어졌다(리치 셀렉션은 셰이프 DAG 를 준다). 이제 컴포넌트의 **셰이프 MObject 노드**와
  대상 셰이프 노드를 직접 비교(`_shape_node`) + 컴포넌트 접근 try/except + 범위 밖 vtx id 방어.
- **수정 ⑵ 근접 shell 방치**: 소프트 셀렉션을 **하드 선택이 속한 연결 shell(island)로 제한**
  (`_connected_island`). 떨어진 shell 은 전이 대상에서 제외 → **방치**.
- **리그레션 재수정**(첫 v01.07 시도 피드백): 첫 시도가 **셰이프 풀패스 문자열** 비교(실 Maya 에서 여전히
  빈 결과 → 소프트 범위 통째 무시, 하드 버텍스만 전이 = 소프트 안 한 것과 동일)와 **버텍스별 `MItMeshVertex`
  island + 임시복제 `skinPercent`** 부분전이(매우 느림)였다. → **노드 비교** + island 을
  `MFnMesh.getVertices()` **벌크 1회 + 파이썬 BFS** + 부분전이를 **maya.api 벌크 read/setWeights** 마스킹
  으로 재작성.
- **검증**: mayapy — 3,124 버텍스 combine 메시에서 island **0.007s**, 소프트 부분전이 **0.055s**(예전 대비
  대폭 빠름); graded falloff(f=1→완전, 0.5→절반 0.500, 미선택→원본 1.000); 떨어진 shellB 제외; 멀티대상/
  단일/Classic 재통과. 트레이드오프: 부분전이는 벌크 `setWeights` 라 **undo 가 세밀하지 않음**(속도 우선).
  getRichSelection 이 헤들리스에서 비어 소프트 경로는 mock 검증 — 마야 실기 소프트 확인 대기.

## 2026-07-23

> [!summary] `A00275_skinTool_V01` **Transfer 탭: 선택한 여러 대상 메시 모두에 전이** (v01.05→01.06)
- **버그**: Transfer 탭에서 소스를 리스트업하고 씬에서 **여러 메시를 선택**한 뒤 Transfer 를 누르면
  **하나의 메시에만** 전이됐다. 원인은 대상 파싱(`parse_target_selection`)이 선택에서 **첫 메시 하나만**
  반환한 것.
- **수정**: `parse_target_selections`(복수) — 선택을 **대상 메시별로 그룹핑**(통째 선택=전체 전이,
  버텍스 선택=그 메시만 부분 전이, 소프트 falloff 는 메시별). Native 는 대상마다 copySkinWeights+마스킹을
  돌리고 **전체를 한 undo** 로 묶는다(`_transfer_one_native` 추출). Kangaroo 는 `_pSelection=None` 이
  이미 선택 전체를 처리한다.
- **덤 수정**: 소스가 대상 선택에 섞여 있을 때 **풀패스 vs TSL 숏네임 불일치**로 소스를 못 걸러내
  자기 자신에 전이하려다 실패하던 문제 — `_mesh_transform` 이 항상 **풀 DAG 패스**를 반환하도록 정규화.
- **검증**: mayapy 실메시 6케이스 통과(소스1→대상3 모두 전이·undo 일괄취소, 대상1만, 소스 제외,
  통째+부분 혼합, 경고). 기존 단일 대상·Kangaroo 라우팅 재통과. UI 는 헤들리스 크래시라 마야 실기 확인 대기.

> [!summary] `A00380_MeshTool` **Peak: Apply 버튼 제거(조절 즉시 반영) + 슬라이더 홈 스타일** (v01.03→01.05)
- **v01.04 — Apply 버튼 제거(슬라이더 상태가 곧 최종 결과)**: "Apply"·"Reset" 버튼을 없애고, 슬라이더로
  조절한 상태가 **손을 떼는 순간 그대로 최종(undoable) 결과**가 되게. 확정 시점은 슬라이더 놓기
  (`sliderReleased`) · Value 입력 완료(`editingFinished`) · `±` 넛지. `on_apply` 를 `commit_stroke` 로
  옮겨 이 시점마다 호출 → 현재 amount 확정 후 0 으로 리셋+재스냅샷(누적). 코어 `peak_manager.commit`
  무변경. 각 조작이 Ctrl+Z 한 번, 오프셋 지우기는 `0`.
- **v01.05 — 슬라이더 홈(groove) 스타일**: 슬라이더 가로 구간이 어두운 배경에 묻혀 범위가 안 보이던 문제.
  A00290_BSTool Shape Editor 슬라이더처럼 홈을 직접 그린다(Peak 은 중앙 0 양방향 → sub/add-page 같은
  색으로 좌우 균일, 0·양끝 눈금, **coral_dark accent #d08778**). Peak·Match 슬라이더 모두 적용. `SLIDER_STYLE`.
- **검증**: 새 흐름(드래그=preview → 릴리스=commit, 반복)을 코어 레벨 mayapy 로 확인(스트로크 누적·undo
  단위·수축). 슬라이더 스타일은 순수 PySide offscreen 렌더로 홈 가시성 확인. UI 는 헤들리스 크래시라
  마야 실기 확인 대기.

> [!summary] `A00110_animTool` **Stagger Offset: Apply 버튼 제거 + 슬라이더 홈 스타일** (v01.32→01.34)
- **v01.33 — Apply 버튼 제거(값이 곧 결과)**: "Apply Stagger Offset" 버튼을 없애고, 슬라이더/스핀박스로
  맞춘 값이 그대로 최종 결과가 되게. settle 모델(v01.32)이 이미 조작이 멎으면(sliderReleased /
  editingFinished / 350ms 디바운스 / 창 닫기) 값을 undo 큐에 한 항목으로 **자동 커밋**하고 있었다.
  → **버튼 + `on_stagger_apply` 핸들러만 제거**(코어 `StaggerOffsetSession` 무변경). Reset·비누적·탐침 유지.
- **v01.34 — 슬라이더 홈(groove) 스타일**: 슬라이더 가로 구간이 어두운 배경에 묻혀 범위가 안 보이던 문제.
  A00290_BSTool Shape Editor 슬라이더처럼 홈을 직접 그린다(중앙 0 양방향 → sub/add-page 같은 색으로
  좌우 균일, 0 은 중앙 눈금이 표시, blue_dark accent #7f9ec8). `STAGGER_SLIDER_STYLE`.
- **검증**: 코어 settle/undo mayapy headless 20개 재통과, QSS 적용 offscreen 확인. UI 는 헤들리스
  크래시라 마야 실기 확인 필요.

> [!summary] `A00380_MeshTool` **Match 탭 신설**(Kangaroo Geometry>Match 재현) **+ Auto-load 편집 원상복구 버그 수정 + Match 흐름 단순화** (v01.00→01.03)
- **v01.03 — Match 대상 로드 단계 제거**: "Load Target Selection" 버튼/Target 박스를 없애고,
  **씬에서 메시를 선택한 뒤 Apply Match 만 누르면** 되게 했다. Apply(또는 Weight 슬라이더를 잡는 순간)에
  **현재 선택**을 대상으로 세션을 즉석에서 만든다. 백그라운드 scriptJob 없이 사용자 조작 시에만 스냅샷을
  잡으므로 v01.02 에서 고친 clobber 위험을 재도입하지 않는다. Weight 라이브 미리보기는 유지(슬라이더를
  잡으면 그 순간 선택으로 미리보기, Reset 은 원본으로).
- **v01.01 — Match 탭**: 리스트업한 **From 메시의 같은 인덱스 버텍스 위치**로, 선택한 메시의 버텍스를
  이동시킨다(소프트 셀렉션 falloff 반영). [[kangaroo-plugin-external-readonly]] 의 `setModelVerts`
  (Geometry > Match)를 **Kangaroo 없이** 재현. 대응은 closest-point 가 아니라 **버텍스 인덱스** 기준.
  - 수식 `final = orig + softw·weight·(from_local - orig_local)`. World 모드는 From 을 월드로 읽어
    대상의 `inclusiveMatrixInverse()` 로 역변환 → 대상 버텍스가 From 의 **월드 위치**에 안착.
  - Peak(`peak_manager`)의 공용 헬퍼와 preview/restore/commit·`shape.pnts` 구간 setAttr 모델을 **그대로
    재사용**(`match_manager` 가 import). Peak 과 유일한 차이는 이동량(로드 시점에 delta 를 얼려두고
    Weight 만 곱함). UI: From=TSL, Target=현재 선택, World/soft 옵션, Weight 슬라이더(0~1), Apply/Reset.
  - 검증: 코어 mayapy headless **9개 시나리오 통과**(world/object, weight 블렌드, restore, 단일 undo,
    부분 선택, 소프트 falloff, 토폴로지 불일치 skip, From 자기제외).
- **v01.02 — "툴만 띄워둬도 손으로 옮긴 버텍스가 원상복구되는" 버그 수정**: 원인은 Peak 탭 **Auto load**
  scriptJob 이 선택 변경마다 `on_load` → `discard_preview` → `session.restore()` 를 **무조건** 부른 것.
  restore 는 로드 시점 스냅샷을 `.pnts` 에 다시 써, 슬라이더를 한 번도 안 건드려도 **사용자의 수동
  편집을 스냅샷으로 덮어썼다**(v01.00 부터 잠복). 해결: `_preview_dirty` 플래그로 **미리보기가 실제로
  걸려 있을 때만 restore**. 근본 원인·수정 로직을 mayapy 로 재현·검증(restore 가 편집 덮어씀 → 가드하면
  보존 → 재스냅샷이 편집 포착 → 실제 미리보기는 여전히 제거됨). Match 탭도 같은 가드.
  UI 위젯 구성은 mayapy 크래시라 헤들리스 불가 → **마야 실기 확인(Match·Peak·버그수정 모두 정상 동작)**.

> [!summary] `A00275_skinTool_V01` **Classic 엔진 선택 + Transfer 탭 신설 + Transfer 엔진 선택** (v01.03→01.05)
- **v01.05 — Transfer 탭에도 Engine(Native/Kangaroo) 선택**: Classic·Migrate 탭처럼 골라 쓴다.
  Native(기본)는 v01.04 그대로(선택 버텍스·소프트 falloff). Kangaroo 는 `transferSkinCluster`
  (`sFrom`=소스들, `_pSelection=None`=현재 선택 타겟, Closest Point). Kangaroo 선택 시 soft
  falloff 옵션은 Native 전용이라 비활성. 라우팅은 headless 로 확인(플러그인 런타임 미초기화면
  crash 없이 `[Error]`; 실제 Maya 에서 Kangaroo Builder 로드 시 동작).
- **요청 1 — Classic 탭에 Engine(Kangaroo/Native) 선택**: 예전엔 Classic 두 버튼이 Kangaroo 전용.
  Migrate 탭처럼 **Native**(플러그인 무의존)를 고를 수 있게 함. `Joints to Joints` native =
  선택 메시 skinCluster 에서 From 본 컬럼→To 본 컬럼 이동(`maya.api`), `Meshes to Meshes` native =
  rebind + `cmds.copySkinWeights`.
- **요청 2 — Transfer 탭 신설(Kangaroo 무의존)**: Kangaroo 의 *SkinCluster > Transfer* 를 흉내낸 기능.
  **여러 소스 메시 → 현재 선택한 하나의 메시**로 웨이트 전이. **선택 버텍스에만 전이**(필수) +
  **소프트 셀렉션 falloff 반영**, Mode 는 Closest Point 고정. core `weight_transfer_manager.py`.
- **핵심 설계**(Kangaroo 는 읽기 전용 참고만; mayapy 실측):
  - 무거운 최근접-점 계산은 `cmds.copySkinWeights(surfaceAssociation="closestPoint")` 가 처리.
    **소스 메시 여러 개를 함께 선택하면 버텍스별 최근접 소스를 자동 사용**(왼쪽 33/33·오른쪽 33/33 검증).
  - 하지만 copySkinWeights 는 **컴포넌트 제한 미지원 — 항상 메시 전체** 적용(미선택 80개가 다 바뀜 확인).
    그래서 부분/소프트 전이는 before/after 를 bulk 로 읽어 **선택 버텍스는 falloff 로 lerp, 나머지는
    before 로 복원** 후 bulk `setWeights`. 버텍스 선택이 없으면 copy 결과를 그대로 둠(undo 깔끔).
- **검증**: mayapy 헤드리스 — 단일/다중 소스, 부분(버텍스) 전이·미선택 보존, 소프트 falloff 그라데이션,
  Classic native move/transfer, 경고 케이스 전부 통과. (Qt+`maya.standalone` 크래시로 전체 창은
  헤드리스 불가 → core 만 실메시로 검증, UI 는 Maya 확인 대기.)
- **문서**: `docs/A00275_skinTool_V01.md`(Classic Engine·Transfer 탭 사용법+구현 메모) · CHANGELOG 갱신.

## 2026-07-21

> [!summary] `A00290_BSTool` **Shape Editor 탭 대폭 개선** (v01.05→01.10) — 슬라이더 가시성 · 다중 편집 · 키 타겟 편집 · undo
- **v01.06 — 슬라이더 가로 홈(groove) 표시**: 어떤 테마 qss 도 `QSlider` 를 스타일링하지 않아 어두운
  배경에서 홈이 묻혀 **핸들만 보이던** 문제. `WeightSlider` 에 자체 `SLIDER_STYLE` 을 넣어 홈·핸들·
  비활성 상태를 직접 그린다. 중앙 0 인 양방향이라 방향성 fill 없이 **좌우 균일한 한 줄**로.
- **v01.07 — 키(animCurve) 걸린 타겟도 조절 가능**: 예전엔 키가 걸리면 슬라이더/스핀박스가 비활성.
  weight 를 **free / keyed / driven / locked** 로 분류(`weight_state`)해, animCurve 아닌 노드 구동·
  잠금만 비활성으로 남긴다. keyed 편집은 **Auto Keyframe ON → 현재 프레임에 `setKeyframe`**,
  **OFF → `setAttr` 미리보기**(시간 이동 시 커브로 복귀 = Maya 채널박스와 동일). mayapy 로 확인:
  키 걸린 attr 은 `setAttr` 이 재평가 시 되돌아가므로 반영엔 `setKeyframe` 필요.
- **v01.07→08→09 — 타겟 다중 편집(선택 UI 3차 반복)**: 여러 타겟을 골라 한 슬라이더/스핀박스로 동시
  조절. ① v01.07 체크박스 → ② v01.08 **행(칸) 클릭 선택 + accent 하이라이트**(`TargetRow(QFrame)`,
  이름 칸 클릭도 선택; 슬라이더/스핀박스는 자기 클릭 소비 → 편집 방해 없음) → ③ v01.09
  **Shift+클릭 = 범위 선택**(기준점~클릭 사이 전부), **Ctrl+클릭 = 개별 토글**. 헤더 Select All / Clear.
- **v01.10 — 다중 편집 후 Ctrl+Z 가 한 타겟 한 틱(~0.01)만 되돌리던 문제 수정**: 드래그가 매 틱
  타겟마다 `setAttr` 을 내 각각이 별도 undo 였던 게 원인. 조작을 **undo 청크**로 묶음 —
  슬라이더 `sliderPressed`~`sliderReleased` 를 한 청크(첫 변경 때 lazy open), 스핀박스는 한 번을 한
  청크로. 이제 **Ctrl+Z 한 번에 선택했던 모든 타겟(값·키)이 원복**된다.
- **검증**: mayapy 헤드리스 — 코어(`weight_state`/`set_weight` 8케이스), 선택 로직(행 클릭/범위/Ctrl
  토글/undo 제스처 등 fake 위젯으로 다수) 전부 통과. 슬라이더 홈·선택 하이라이트는 순수 Qt 렌더로 확인.
  (Qt 위젯 + `maya.standalone` 은 이 환경에서 크래시해 전체 창은 헤드리스 불가 → 로직은 fake 위젯,
  스타일은 maya 없이 렌더로 분리 검증.)

## 2026-07-20

> [!summary] `A00275_skinTool_V01` **신규 v01.00→01.03** — `A00270_skinMigrate` 기능 + **Bind Pose 탭**(현재 포즈를 새 바인드 포즈로)
- **요청**: 스킨 범용 툴에 `A00270_skinMigrate` 기능을 담고, **조인트를 이동·회전한 현재 상태가
  바인드 포즈가 되는** 기능을 추가할 것. blendShape 등 다른 히스토리가 있어도 동작해야 함.
  "마야에서 간단히 되면 방법만 알려달라" 는 단서 포함.
- **먼저 확인 — 마야 네이티브로는 안 된다**(mayapy 실측):
  - `skinCluster -e -recacheBindMatrices` → `bindPreMatrix` 를 **전혀 바꾸지 않는다**. 무효.
  - `dagPose -reset` → **bindPose 가 갱신되지 않는다**(Go to Bind Pose 가 옛 포즈로).
  - `Move Skinned Joints Tool` → 목적이 다름("메시를 변형시키지 않고 조인트만 이동").
- **구현** — `A00270` 복사(원본 유지) + 새 core `app/core/bind_pose_manager.py`, 3단계:
  ① `bindPreMatrix[i] = 인플루언스의 현재 worldInverseMatrix`
  ② (Keep 모드) `skinCluster 출력 − 입력` 델타를 **체인 헤드 셰이프**에 굽기
  ③ `bindPose`(dagPose) 재생성 + `skinCluster.bindPose` 재연결.
  모드 2종(**Keep current shape** 기본 / **Snap mesh to rest shape**), 메시·조인트 아무거나 선택,
  여러 skinCluster 동시 처리, 전체 단일 undo.
- **v01.01 — 실제 리그에서 보고된 버그 3건 수정**(전부 단순 테스트 씬에선 우연히 통과하던 것):
  - **더블 트랜스폼**: `bindPreMatrix` 인덱스를 `enumerate(skinCluster -q -inf)` 로 매긴 게 원인.
    인플루언스 목록 순서는 `matrix[]` **논리 인덱스와 다를 수 있다**(뺐다 넣은 리그는 `[0,1,3,4,5,6]`).
    → **엉뚱한 조인트 슬롯에 행렬이 들어갔다.** `matrix[i]` 연결에서 매핑을 읽도록 수정.
  - **`(kInvalidParameter)`**: `input[0]`/`outputGeometry[0]` 인덱스 하드코딩 + 비(非)메시 지오.
    대상 shape 으로 이어지는 실제 인덱스를 찾고, 메시가 아니면 안내 후 계속 진행.
  - **`bindPoseXXX` 노드 증식**: 재생성 시 **원래 이름을 물려주도록** 수정.
- **v01.02 — 원인을 툴이 스스로 말하게**: 요약 줄에 `shape NOT kept: <이유>` 를 함께 출력,
  **Diagnose 버튼**(읽기 전용, 디포머 체인을 실제 연결 그대로 출력) 추가, 입력 셰이프 fallback
  (버텍스 수가 같은 intermediate) 추가. 동시에 **체인 워크가 `groupParts` 에서 끊기던 결함**을 수정 —
  디포머는 `input[i].inputGeometry`, `groupParts` 류는 `inputGeometry` **스칼라**를 쓴다.
- **v01.03 — 원인 확정 + 후속**: 실제 리그(`CHN_Face`, 22,644 verts) Diagnose 결과
  **`groupParts` 13개 연쇄**(`face_BS` → `groupParts246`…`235` → `Orig`)에서 워크가 멈춘 것이 확인됨.
  v01.02 수정으로 해결됨을 실측. 라이브 blendShape 타겟 경고에 **실제 weight 값**을 표시하도록 개선
  (상쇄량이 weight 에 **정비례**함을 실측: w 0.25/0.5/0.75/1.0 → 오차 0.103/0.220/0.352/0.498.
  부분 weight 면 **조용히 조금만 틀린** 결과라 값을 봐야 판단 가능). Diagnose 깊이 상한 16→64.
- **구현 함정**(코드 주석·가이드 문서에 기록): 델타를 `MFnMesh.setPoints` 로 구우면 **undo 큐에 안
  올라가** Ctrl+Z 시 `bindPreMatrix` 만 되돌아가고 구운 형상이 남아 **메시가 어긋난 채 방치**된다
  → `pnts` 구간 `setAttr`. 그리고 `pnts` 는 **기존 값에 더해야** 한다(프리즈한 `ty=2` 가 전 버텍스에
  `(0,2,0)` 으로 남아 있는 경우가 흔하다).
- **검증**: headless 5개 스위트 — 두 모드, Go to Bind Pose 복귀, blendShape 스킨 앞/뒤, 메시 트랜스폼
  비원점, 루트 조인트 이동, 다중 skinCluster, **undo 완전 복원**, 성긴 인플루언스 인덱스, nurbs,
  잠긴/연결된 `bindPreMatrix`, bindPose 이름 유지, 지오 인덱스≠0, 라이브 타겟 상쇄량. 전부 통과.
  Maya 에서 실제 아바타로 동작 확인 완료.
- **문서**: `docs/A00275_skinTool_V01.md` 신규(경고 메시지별 대응표 + `shape NOT kept` 대응 순서 포함).

> [!summary] `A00110_animTool` v01.31→01.32 — Stagger Offset **Ctrl+Z 복구** + **슬라이더 + 스핀박스** UI
- **문제**: v01.31 은 미리보기를 undo 큐에 전혀 올리지 않아, 값을 조절한 뒤 **Ctrl+Z 를 눌러도 되돌아가지
  않았다**(대신 무관한 이전 작업이 취소됨). 사용자 요구: 조절 후 Ctrl+Z = **Reset 을 누른 것과 동일**.
- **해결(settle 모델)**: 세션이 `applied`(씬에 보이는 값)와 `settled`(undo 큐에 기록된 값)를 따로 든다.
  조작이 **멎으면**(350ms 디바운스, 슬라이더 놓기/스핀박스 편집 종료 시 즉시) **undo 를 끈 채 `settled` 로
  되돌린 뒤** undo 청크 안에서 `settled → 현재값` 을 한 번에 이동시킨다. undo 는 '역연산을 현재 상태에
  적용' 하므로 이렇게 해야 Ctrl+Z 가 정확히 그 지점으로 온다 → **드래그를 아무리 해도 조작 1회 = undo 1개**,
  첫 조작이면 **Ctrl+Z = 원위치 = Reset**. `restore()` 도 `settle(0)` 로 통일(기록된 게 있으면 되돌리기도
  기록해야 큐가 안 어긋난다).
- **씬 동기화 탐침**: 사용자가 Ctrl+Z 를 누르면 씬은 이전 상태인데 세션은 모른다. 첫 움직이는 항목의
  구간 내 첫 키를 탐침으로 잡아 "있어야 할 자리에 키가 있나" 확인하고, 어긋나면 **되돌리기 시도 없이
  세션만 버린다**(잘못 알고 되돌리면 키가 엉뚱한 곳으로 밀린다). 다음 조작에서 현재 상태로 새 세션.
- **UI**: Offset per Item 을 **슬라이더 + 스핀박스**로 (요청대로 `A00290_BSTool` Shape Editor 패턴 —
  같은 값의 두 얼굴, 어느 쪽을 움직이든 즉시 반영하고 반대쪽을 blockSignals 로 맞춤). 슬라이더 ±60f,
  중앙/양끝 눈금, 더 큰 값은 스핀박스.
- **검증(headless, mayapy)**: undo 시나리오 20개 체크 통과 — 화살표 여러 번 → **1회 Ctrl+Z 로 원위치**,
  드래그 20틱 → undo 항목 1개, 2회 정착 시 단계별 복귀, Reset 자체의 undo, no-op settle 무기록,
  탐침의 외부 undo 감지, 정착 후에도 비누적. 기존 39개 회귀 스위트도 전부 통과.

> [!summary] `A00110_animTool` v01.30→01.31 — Key Edit 탭에 **Stagger Offset**(리스트 순서대로 계단식 키 오프셋) 추가
- **요청**: TSL 에 리스트업한 컨트롤러들의 **원하는 프레임 구간** 키를 **리스트 순서대로 N프레임씩** 밀고,
  **스핀박스로 실시간** 조절할 것. 구간은 기존 Start/End/**Get Current** UI 로 세팅.
  예) ctl_01/02/03 모두 0~5f 키, 구간 0~5f, offset 3 → `[0,5] / [3,8] / [6,11]`.
- **구현**: `app/core/stagger_offset_manager.py` 신규(`StaggerOffsetSession`) + Key Edit 탭에 접이식
  섹션 5번째로 UI(TSL[Reverse 켬] / Start·End+Get Current / Offset 스핀박스 / Reset / Apply).
- **설계 포인트**:
  - **비누적 실시간**: 세션이 지금 적용된 offset(`applied`)을 들고, 스핀박스가 바뀌면 **차이만** 이동.
    i 번째 키는 항상 `[Start+i·applied, End+i·applied]` 에 있으므로 `i·delta` 만 밀면 정확히 맞는다.
    → 3→5→1 로 왕복해도 누적되지 않음.
  - **상대 이동만 사용**: `cmds.keyframe(relative=True, timeChange=)` 만 쓰고 커브를 재생성하지 않아
    **탄젠트·인피니티·애님 레이어 소속이 보존**된다(cutKey+setKeyframe 재생성은 커브 노드가 새로
    만들어져 애님 레이어가 바뀔 수 있어 배제).
  - **undo**: 미리보기는 `undoInfo(stateWithoutFlush=False)` 로 큐에 안 올리고, Apply 는
    **원위치 복원 후** 한 번에 적용(restore-before-commit, A00380 에서 검증한 패턴) → **Ctrl+Z 한 번**.
  - **인덱스 보존**: 씬에 없거나 키 없는 항목은 제외하되 **나머지는 리스트 원래 위치를 배수로 유지**
    (제외 항목 때문에 뒤 항목 배수가 당겨지지 않음).
  - 리스트/구간이 바뀌거나 창을 닫으면 확정 안 한 미리보기는 **자동 원위치**.
- **검증(headless, mayapy)**: 39개 체크 전부 통과 — 사용자 예시 그대로, 비누적(3→5→1), 음수 offset,
  restore, commit 후 **1회 undo 복원**, 구간 밖 키 보존 + 덮어쓰기 경고, 탄젠트/weighted 보존,
  다중 채널 동시 이동, 실수 프레임, 스킵 항목 인덱스 보존, 리스트 역순.
  UI 위젯 구성은 mayapy 스탠드얼론에서 크래시(exit 127)라 헤들리스 검증이 불가해,
  스핀박스 실시간 반영·Reset·Apply·자동 무효화는 **마야에서 직접 확인(정상 동작)**.

> [!summary] `A00370_ToolLauncher` v01.03→01.04 — 버튼 경로를 **상대경로로 저장**해 PC 간 git churn 제거
- **문제**: 버튼이 `path` 에 **절대경로**를 저장하고 프로파일 JSON 이 git 추적 대상이라, JUN_All 위치가
  다른 PC 에서 `Refresh Paths` 를 누를 때마다 모든 경로가 그 PC 기준으로 다시 쓰여 프로파일이 통째로
  바뀌고 병합 충돌이 반복됐다.
- **해결(사용자 제안을 완성)**: 사용자 제안(루트를 별도 파일로 분리 + gitignore)은 방향이 맞지만
  프로파일이 절대경로면 부족 → **버튼 경로 자체를 JUN_All 루트 기준 상대경로(`tools/A000XX`)로 저장**.
  이 값은 PC 무관 동일 → 프로파일 추적·공유해도 안 흔들림. 실제 절대경로는 실행 시점에 이 PC 루트로
  `resolve`. 루트는 런처 실행 위치에서 **자동 감지**, 선택적 오버라이드만 **gitignore 된 `local_env.json`**,
  `active.json`(마지막 연 프로파일)도 gitignore + untrack.
- **구현**: `tool_launcher.to_portable`/`resolve`/`_tools_tail`(rebase_to_root 대체), `prefs.effective_root`/
  `get/set/clear_root_override`/`make_all_portable`(rebase_all_profiles 대체), UI 는 저장 시 `to_portable`·
  사용 시 `resolve`, Environment 박스를 Detect/Browse/**Apply Root**/**Make Paths Portable** 로 개편.
  기존 커밋 프로파일 4종을 상대경로로 마이그레이션. `.gitignore` 에 A00370 `local_env.json`/`active.json` 추가.
- **검증(headless)**: 10개 버튼 전부 상대경로로 저장·resolve·validate OK, `make_all_portable` 재실행 시
  0 changed(=churn 없음), 가상 PC2 루트(`D:\x\JUN_All`)로도 정상 resolve, 외부 절대경로 self-heal.

> [!summary] `A00380_MeshTool` **신규 v01.00** — **Peak 탭**(노말 방향 팽창/수축, 후디니 `peak` 노드 대응)
- **요청**: 선택한 메시를 노말 방향으로 팽창·수축시키는 툴. 마야 기본 방식(컴포넌트 선택 → Move 툴
  `axis = normal`)이 **너무 느린** 문제를 해결하고, **미세하게** 조절할 수 있을 것.
- **구현** — 새 in-Maya PySide 툴(arch B). `app/core/peak_manager.py` + `app/ui/main_window.py`:
  - 메시 통째 / 버텍스·엣지·페이스 선택(엣지·페이스는 자동 버텍스 변환) / **여러 메시 동시** 처리.
  - **슬라이더 드래그 = 실시간 미리보기**, `Apply` 로 확정(**Ctrl+Z 한 번**), `Reset` 으로 미리보기 취소.
  - 미세 조정: **`Range`**(슬라이더 한계, 낮출수록 미세) + **`Step` 과 `-`/`+` 넛지** 버튼.
  - 옵션: 각도 가중 노말, **소프트 셀렉션 falloff 반영**, 선택 변경 시 자동 로드(scriptJob).
  - 노말은 **스냅샷 시점 값으로 고정** — 드래그 중 재계산하면 결과가 자기 자신에게 먹여져 형태가 뭉개진다.
- **성능**(19,462 버텍스, mayapy 실측): `cmds.xform` 버텍스 루프 **약 7.2초**(= 마야 기본 방식) ·
  버텍스별 `setAttr` 6.8초 → **`shape.pnts` 구간(range) `setAttr` 0.10초**. **약 70배**.
- **mayapy 로 확인한 함정 4가지**(전부 조용히 틀리는 종류라 코드 주석·가이드 문서에 기록):
  - ① `MFnMesh.setPoints`(vrts 직접 쓰기)는 미리보기가 5배 빠르지만 **기존 tweak 을 지워서**,
    이후 `setAttr` 이 "지워진 상태"를 undo 기준으로 잡는다 → **Apply 두 번 뒤 Ctrl+Z 가 첫 Apply 까지 푼다.**
  - ② `MPlug.setFloat` 로 `pnts` 를 쓰면 **tweak 이 한 번도 없던 메시**(가장 흔한 경우)에서 **반영이 안 된다.**
    `cmds.setAttr` 이 한 번 들어가야 평가가 트리거된다 → 쓰기를 전부 `setAttr` 로 통일.
  - ③ 미리보기의 undo 끄기는 반드시 **`undoInfo(stateWithoutFlush=False)`**. `state=False` 는
    **기존 undo 히스토리를 통째로 날린다.**
  - ④ commit 은 **스냅샷 값으로 되돌린 뒤** 확정해야 한다. `setAttr` 은 실행 시점 값을 undo 기준으로
    기억하므로, 미리보기 값이 남아 있으면 Ctrl+Z 가 미리보기 상태로 돌아간다.
  - 그 외: `getAttr("<shape>.pnts")` 통짜 조회는 *"compound with mixed type elements"* 로 실패 →
    `MPlug.getExistingArrayAttributeIndices` 로 읽는다(19k 메시 0.02초).
- **검증**: headless(mayapy) **34개 검사 전부 통과** — undo/redo, 히스토리 메시, 스킨 메시, 기존 tweak 보존,
  부분/범위/엣지/페이스 선택, 다중 메시, 소프트 셀렉션, `undo_chunk` 조합, 예외 안전성.
  (UI 자체는 mayapy standalone 에서 `QWidget()` 생성이 죽어 헤드리스 구동 불가 → **Maya 에서 직접 확인 완료**.)
- **문서**: `docs/A00380_MeshTool.md` 신규. 포트폴리오(국/영) 섹션 5 에 A00380 항목 추가.

> [!summary] 포트폴리오 문서 갱신 — `A00170_driverTool` 로 만든 **함수 구동 트위스트·디폼 리그 에셋**(촉수·뱀) 추가
- **대상**: `docs/portfolio/portfolio_EN.md` + `portfolio_KR.md`(국/영 동기화).
- **추가**: 섹션 3 에 상세 서브섹션 **3-1. 함수 구동 트위스트·디폼 리그 에셋**(기존 표는 3-2 로) 신설 —
  A00170 툴로 세운 **실제 리그 에셋**(촉수·뱀)을 어필 문장으로.
  - 계층 드라이버(null)의 T/R/S 에 함수를 **신호처리하듯** 얹고 조인트 체인에 **additive 레이어링**.
  - **체인 트위스트 분배로 splineIK up-vector 한계 극복**(길게 감기고 비틀리는 촉수·뱀에 유효).
  - **매트릭스 컨스트레인트 대비 우위** — 전파 모양을 함수로 설계, 시그모이드 threshold·급격함이
    드라이버 오브젝트의 **씬 어트리뷰트로 실시간 조절/애니메이트**.
  - **언리얼 임포트 레디** — 실제 조인트 체인을 구동하므로 스켈레탈 애니메이션이 임포트되어 의도대로 재생
    (Control Rig 라이브 이식은 아님을 명시). ASCII 다이어그램(신호→함수→드라이버→조인트→FBX→Unreal) 포함.
- **상단 3줄 소개**에 "리그 거동을 튜닝 가능한 수학 함수로 오소링" 한 줄 승격, 표의 A00170 행에도 함수 구동
  스트레치 요약 추가. `updated` 만 2026-07-20 으로(제목 기간·커밋 수 등 큐레이션 통계는 유지).

---

## 2026-07-16

> [!summary] `list_attrs` **List Attributes 에러 스팸 제거** — `A00170_driverTool` v01.11→01.12, `A00145_RigConnect` v01.17→01.18
- **증상**: 오브젝트를 리스트업하고 **List Attributes** 를 누르면
  `getNextFreeMultiIndex.mel line 41: No object matches name: <obj>.<attr>[0]` 에러가 **아주 많이** 출력.
- **원인**: `list_attrs` 가 **모든** 어트리뷰트에 대해 `getNextFreeMultiIndex` 를 호출해 multi 여부를 판정했는데,
  그 MEL 은 non-multi(스칼라)에서 `attr[0]` 을 찾다 실패해 어트리뷰트 개수만큼 에러를 출력했다(Python 에서
  catch 해도 Maya 출력은 남음). 로케이터 하나에 224회 호출 중 **215회 에러**.
- **수정**: `cmds.attributeQuery(attr, node=obj, multi=True)` 로 **조용히** multi 를 판정하고,
  multi 로 확정된 것만 `getNextFreeMultiIndex` 로 자식까지 펼친다. 결과 집합은 **동일**(로케이터 230개 그대로),
  에러는 0. A00170(`app/core/maya_scene.py`) + A00145(`app/core/connect_manager.py`, blendShape 로직 보존) 동시 수정.
  검증(headless): getNextFreeMultiIndex 호출 224→9, 에러 215→0, 결과 set 일치, search 경로 정상.

> [!summary] `A00170_driverTool` v01.07→01.11 — **Stretch 탭 신설** + **additive 오프셋** + **시그모이드**(실시간 어트리뷰트 제어) + **다중 어트리뷰트**
- **요청**: Default Distance 오브젝트의 임의 어트리뷰트(값 `a`)를 remap 함수에 통과시킨 결과를
  Stretch 오브젝트 어트리뷰트의 입력으로 넣는 기능. 원본은 post=Cycle w/ Offset·pre=Constant 였는데
  **pre/post 둘 다 사용자 지정**(기본 Cycle w/ Offset)으로, 탄젠트는 **auto→linear**, 함수는
  기존 `f(x)=x-a+1` 에 더해 **`f(x)=-x+a+1`** 도. 원본 오류·리팩토링 개선 포함.
- **구현** — 새 core `app/core/stretch.py` (`run_build_stretch`) + main_window `Stretch` 탭(`stc_*`):
  - driver `default.attr` → driven `stretch.attr` 의 **set driven key(animCurveUU)**. 키 2개
    `(a, 1)`,`(a+1, 2|0)` → linear 탄젠트 → `setInfinity(driven_plug, pri/poi)`. Default 1개면 1:n,
    아니면 n:n. 함수 콤보 + Pre/Post Infinity 콤보(Constant/Linear/Cycle/Cycle with Offset/Oscillate).
  - **원본 대비 개선**: ① pre/post infinity 사용자 지정. ② 탄젠트 auto→linear. ③ 둘째 키 `2a`→`a+1`
    로 **실제 `f(x)=x-a+1`**(원본 기울기는 `1/a`)이 되게 하고 `a=0`(키 입력 겹침)·`a<0`(기울기 부호
    반전) 깨짐 제거. ④ `setDrivenKeyframe` 2회로 커브 직접 생성(`connectionInfo` 재조회 제거).
    ⑤ 존재/self-drive/스칼라 여부 입력 검증.
  - **검증 사실**(headless mayapy 2024): `setInfinity` 는 **커브 노드가 아니라 plug 대상**일 때만
    적용됨(문자열 `cycleRelative`=Cycle with Offset); setAttr enum 은 `{Constant:0,Linear:1,Cycle:3,
    Cycle w/ Offset:4}`(2 는 빈 값). animCurveUU 의 driver 축은 `keyframe -q -fc`. linear+cycleRelative
    양방향에서 `f(x)=x-a+1`/`-x+a+1` 이 전 구간 정확히 일치. 1:n·n:n·검증 로직 모두 통과.
  - 코어 로직·컴파일·import 체인은 headless 검증 완료. **Maya 실환경 동작 확인됨**.
    가이드 문서(`docs/A00170_driverTool.md`) 4탭으로 갱신.
  - 원본 MEL 의 **Distance 탭**(`distanceDimension` 생성)은 이식하지 않음(요청 범위 밖).
- **후속(v01.08→01.09) additive 오프셋**: 커브를 driven 어트리뷰트에 직접 연결(덮어쓰기)하던 것을,
  사이에 `addDoubleLinear` 오프셋 노드를 끼워 **원래 값 기준 additive** 로 바꿨다.
  `curve.output → addDoubleLinear.input1`, `input2 = original - 1` → `driven = original + (x-a)`.
  f(x) 의 rest 출력 1 을 빼고 original 을 더하므로 **rest 에서 원래 값 보존**, driver 이동 시 그 값에서
  증감(예: `translateX` 원래 1.5 → 1.5 에서 늘거나 줆). original 은 커브 연결 **전에** getAttr 스냅샷.
  검증(headless): disconnect 수술 후에도 커브 infinity 유지, 오브젝트별 서로 다른 original 각각 보존,
  1:n additive 전 구간 일치, 컴파운드(translate) 부분 keying 없이 skip.
- **후속(v01.09→01.10) 시그모이드 함수**: Function 에 `Sigmoid`/`Sigmoid rev` 추가. animCurveUU 대신
  **해석적 노드망**(`multiplyDivide` power `base^exp` + divide + addDoubleLinear)으로
  `driven = tmin + (tmax-tmin)/(1 + base^(±(x-a)+L))` 를 만든다. 사용자 요청 조건: x→-∞ 시 tmax,
  x→+∞ 시 tmin(≥0, 0 밑으로 안 감)에 수렴 + 역방향 + 급격함(밑 e=Sharpness)·threshold 사용자 지정 +
  **`sigmoid(a)=원래 값`**. 마지막 조건을 `L = log_base((tmax-original)/(original-tmin))` 수평이동으로
  정확히 충족(→ plateau 는 리터럴 tmax/tmin, `tmin<original<tmax` 필요, 아니면 그 짝 skip+WARN).
  UI: Function 콤보에 2개 추가, Sharpness/Thresh Min/Max 스핀박스(시그모이드 전용, 선형이면 비활성 /
  infinity 는 반대). 검증(headless): 정상·역방향 exact, 오브젝트별 original 통과, plateau·0 하한,
  범위 밖/ base≤1 검증, 선형 회귀 OK. **base = 1/(1+e^-x) 의 e 값**을 그대로 노출한 셈.
  **Maya 실환경 동작 확인됨**(선형·시그모이드 전부).
- **후속(v01.10→01.11) 다중 어트리뷰트 + 시그모이드 실시간 제어 + 검색 다중선택**:
  ① **Stretch 어트리뷰트 다중 선택** — TSL multi_select, 페어링을 UI 에서 오브젝트(1:n/n:n)×선택
     어트리뷰트로 확장(`build_stretch` 는 인덱스 정렬 zip 으로 단순화). ② **시그모이드 파라미터를
     Default Distance 오브젝트의 어트리뷰트로** 추가(`stretchSharpness`/`ThreshMin`/`ThreshMax`,
     기본값=UI 값) + 노드망에 연결 → 씬에서 실시간 조절. 이를 위해 시그모이드 노드망을
     `driven = tmin + (tmax-tmin)/(1 + ratio·base^(±(x-a)))`, `ratio=(tmax-original)/(original-tmin)=base^L`
     형태로 바꿔(로그 노드 불필요) base·tmin·tmax 가 live 여도 `driven(a)=original` 유지. driver
     오브젝트당 제어 어트리뷰트 한 벌 공유(캐시). ③ **Attr Search 재질의 시 발견된 어트리뷰트 전부 선택**
     (`select_by_texts`, 단일 리스트는 첫 항목). ④ **함수별 파라미터 UI 토글** — Sigmoid 파라미터 행과
     Pre/Post Infinity 행을 각각 컨테이너 QWidget 으로 묶어 통째로 `setEnabled` → **라벨까지 함께** 회색
     처리(선형이면 Sharpness/Thresh Min/Max 비활성, 시그모이드면 Infinity 비활성).
     검증(headless): 다중 어트리뷰트 sigmoid/linear, tmax 실시간 변경 시 3개 네트워크가 각 original 유지하며
     재타겟, 회귀 OK. **Maya 실환경 동작 확인됨.**

## 2026-07-14

> [!summary] `A00145_RigConnect` v01.16→01.17 — **Attribute 탭 신설** + blendShape 타겟 이름 나열(Attribute·Connect)
- **요청**: (1) 임의의 오브젝트에서 원하는 어트리뷰트만 골라 다른 오브젝트에 같은 이름 / 원하는
  접두사·접미사로 새로 만드는 기능을 **새 탭**으로. (2) **blendShape 노드를 소스로 넣으면 타겟
  이름들이 나열**되게 — Attribute 탭은 물론 **Connect 탭의 Destination 에서도** 안 나오던 문제.
- **구현 (1) Attribute 탭** — 새 core `attribute_manager.py`:
  - `get_attr_spec` 이 어트리뷰트 정의를 읽고 `copy_attributes` 가 타겟들에 `addAttr` 로 재생성.
    보존: 타입(double/float/long/short/bool/enum/string/message/doubleAngle/컴파운드
    `double3`·`float3`/multi), min·max·soft min·soft max, default, keyable, 채널박스 표시, hidden,
    enum 이름, `usedAsColor`. `Copy current value`(기본 ON)면 현재 값도 복사.
  - UI: Source(오브젝트 + 어트리뷰트 목록, `User defined only` 기본 ON, 검색, Select All) /
    Targets / `Prefix`·`Suffix` + 실시간 `Preview` / `Copy Attributes to Targets`.
  - **short name**: 이름을 안 바꾼 경우에만 원본 short name 유지. prefix/suffix 로 바뀌면 Maya 가
    새로 만들게 둔다(그대로 쓰면 **다른 어트리뷰트와 충돌**).
  - 컴파운드 **자식은 목록에서 제외**(부모 복사 시 같이 생기고, 자식만 따로는 `addAttr` 불가).
    자식 이름은 부모의 새 이름을 따른다(`tint`→`L_tint_ctrl` 이면 `L_tint_ctrlR/G/B`).
  - 이미 있는 어트리뷰트는 **건너뛰고** `[WARN]` 로그(덮어쓰지 않음). 전체가 undo chunk 하나.
- **구현 (2) blendShape 타겟** — 새 공용 core `blendshape_utils.py`(`is_blendshape` /
  `get_blendshape_targets`), Attribute·Connect 탭이 함께 사용:
  - **원인**: 타겟은 별도 어트리뷰트가 아니라 **`weight[i]` 멀티의 별칭(alias)**. Connect 탭의
    `getNextFreeMultiIndex` 기반 멀티 확장은 **인덱스 0 하나만** 잡아 첫 타겟만 나왔고, Attribute 탭의
    `listAttr(userDefined=True)` 는 `attributeAliasList` 만 돌려줬다.
  - **수정**: `aliasAttr` 에서 별칭을 직접 읽어 **weight 인덱스 순**으로 목록 맨 앞에 놓는다.
    Connect 는 `weight` 원시 멀티를 목록에서 빼고, 순서 유지 중복 제거.
  - **함정**: `attributeQuery` 는 별칭을 부모 멀티(`weight`)로 해석한다 → 그대로 두면 타겟 하나를
    복사해도 컨트롤러에 **`weight` multi 어트리뷰트**가 생긴다. 별칭이면 long/short name 을 타겟
    이름으로, `multi=False` 로 바로잡았다.
- **검증**: **mayapy** — (1) 13종 타입(범위/기본값/enum/컬러/벡터/string/message/multi/채널박스 전용)
  라운드트립 **정의 전부 동일**, prefix/suffix·중복 skip 확인. (2) 타겟 4개 blendShape 에서 Attribute·
  Connect 목록에 타겟 전부 나열, 타겟→컨트롤러 복사(float/multi=False/keyable/값 유지) 후
  `ctrl.smile`→`bs.smile` 연결까지 값 전달 확인. 일반 오브젝트 리스팅 회귀 없음.
  **Maya 에서 UI 동작 확인 완료.** docs 갱신. #A00145 #RigConnect #attribute #blendShape #maya #mayapy

> [!summary] `A00145_RigConnect` v01.15→01.16 — Skin Weight to Constraint, **Parent 외 Scale/Point/Orient 타입 추가**
- **요청**: Constraint 탭의 `Skin Weight to Constraint` 가 parentConstraint 만 만든다.
  parent 를 만들듯 rotate(orient)·scale constraint 도 만들 수 있게 할 것.
- **구현**:
  - `constrain_manager` 에 public 헬퍼 `get_constraint_func(con_type)`(key → `cmds.*Constraint` 함수)
    를 추가하고 기존 `constrain()` 도 이걸 쓰게 해서 **타입 매핑을 한 곳으로** 모았다.
  - `skin_constraint_manager.SKIN_CONSTRAIN_TYPES` = `con_mgr.CONSTRAIN_TYPES` 에서 **`pointOnPoly`
    제외**(메시를 타겟으로 삼는 constraint 라 joint 가중 방식에 쓸 수 없음) → `Parent / Scale / Point /
    Orient`. `con_type="parent"` 기본값이라 기존 호출은 그대로 동작.
  - `con_type` 을 `_apply_weighted_constraint` → `skin_weight_to_constraint` →
    `create_locators_and_constrain` 까지 통과 → `Locators` 버튼도 같은 타입을 따른다.
  - UI: Options 안에 위 `Constraint` 박스와 **동일한 라디오 패턴**(기본 Parent) 추가. 어떤 타입이든
    influence joint 의 **웨이트 배분 방식은 동일**하다.
- **함정**: **`interpType`(Shortest 강제)은 parentConstraint / orientConstraint 에만 있다.**
  point/scale 엔 없어서 무조건 `setAttr` 하면 에러 → `cmds.attributeQuery(..., exists=True)` 로 가드.
- **검증**: **mayapy** 로 3-joint 스킨 큐브를 만들어 네 타입 모두 실행 — 전부 생성 성공, 웨이트가
  `[0.5641, 0.2692, 0.1667]`(합 1.0)로 정규화, `interpType=2` 는 parent/orient 에만 설정됨.
  `Locators`(per-vertex) 경로와 기본값(parent) 하위호환도 확인. **Maya 에서 UI 동작 확인 완료.**
  docs 갱신. #A00145 #RigConnect #constraint #skinWeight #maya #mayapy

---

## 2026-07-13

> [!summary] `A00080_KWI_creator_V03` v01.03→01.04 — Constraints 탭, **씬에 없는 오브젝트 쌍 제외**
- **요청**: Generate & Copy 로 코드를 만들면 마야 씬에 없는 본까지 코드가 생성된다.
  `dyn_necklace_n_[01-10]_0[1-4]` / `[02-11]_0[1-4]` 로 만들 때 `dyn_necklace_n_01_04`,
  `02_04` 가 씬에 없으면 그 쌍 코드는 만들지 말 것.
- **구현**:
  - core `constraint_creator.build_text/create_file` 에 `exists_fn(name)->bool` 옵션 추가 →
    쌍의 **두 본 중 하나라도** `exists_fn` 이 False 면 그 쌍을 제외하고, 제외 목록
    `skipped=[(a,b,[없는 이름]),...]` 을 함께 반환. `exists_fn=None` 이면 필터 안 함(**DCC 비의존 유지**).
  - UI: 체크박스 **"Only generate pairs whose objects exist in the scene"**(기본 ON). 켜져 있고
    마야 안이면 `cmds.objExists` 기반 `exists_fn` 을 주입한다(`_scene_exists_fn`). 제외된 쌍과 없는
    이름을 로그에 출력. 끄면 예전처럼 전부 생성.
- **검증**: headless(python) 필터 로직 + **mayapy** 실제 씬(01_04/02_04 만 안 만든 조인트 씬)에서
  `cmds.objExists` 로 확인 — 없는 본이 낀 2쌍만 제외(40→38), 출력 텍스트에 없는 이름 미누출.
  골든 예시(모두 존재)는 35개 그대로. UI 도움말/CHANGELOG/docs 갱신.
  #A00080 #KWI #constraints #maya #mayapy

> [!summary] `A00080_KWI_creator_V03` v01.02→01.03 — Constraints 탭 브래킷 패턴 **제로패딩** 수정
- **버그**: `dyn_necklace_n_[01-10]_0[1-4]` 처럼 브래킷 안에 리딩 0 을 써도(`[01-10]`) 확장 결과가
  `1_01, 2_01…` 로 **패딩이 빠졌다**. 기대는 `01_01, 02_01…`.
- **원인**: `constraint_creator.expand_pattern` 이 `[01-10]` 을 `int("01")=1` 로 바꾼 뒤 `str(1)="1"` 로
  되돌려 **리딩 0 을 잃었다**. `0[1-4]` 는 0 이 브래킷 밖(리터럴)이라 멀쩡했다.
- **수정**: 브래킷 경계 문자열(`a_str`,`b_str`)을 보고 **한쪽이라도 리딩 0 이면** 두 경계 폭의 최대값으로
  `str(val).zfill(width)` 제로패딩. 리딩 0 이 없으면 `width=0` → 패딩 없음(`[1-10]`→`1..10`, 기존 동작 유지).
- **검증**: `[01-10]_0[1-4]`→`01_01…10_04`(40개), `[02-11]`→`02..11`, 하위호환 `[1-10]`→`1..10`,
  `[01-7]`→`01..07`, 골든 예시 `0[1-7]_0[1-5]`→`01_01…07_05`(35개) 그대로. UI 도움말/CHANGELOG/docs 갱신.
  #A00080 #KWI #constraints #bugfix

> [!summary] `A00370_ToolLauncher` v01.02→01.03 — 버튼 경로 **PC 간 이식**(JUN_All Root + Refresh Paths)
- **요청**: 한 PC 에서 만든 버튼을 다른 PC 에서 쓰면 툴이 안 뜬다. PC 마다 JUN_All 경로가 다르기
  때문(PC1 `G:\...\JUN_All`, PC2 `C:\...\Maya_Python\JUN_All`). JUN_All 경로를 지정하고 `Refresh` 로
  세팅을 재설정해 어느 PC 든 공유·복구할 수 있게.
- **원인**: 버튼은 `path` 에 툴 폴더의 **절대경로**를 저장한다. JUN_All 위치가 다르면 전부 깨진다.
- **핵심 착안**: 런처 자신이 `JUN_All/tools/A00370_ToolLauncher/...` **안**에 있으므로, 이 파일 위치에서
  거슬러 올라가면 **실행 중인 PC 의 JUN_All 루트를 항상 정확히 자동감지**할 수 있다
  (`tool_launcher.jun_all_root()`). 사용자가 아무것도 지정하지 않아도 되는 기본값이 된다.
- **구현**:
  - `Environment` 그룹(컨트롤 최상단) — **JUN_All Root** 필드(자동감지값으로 프리필) + `Browse...` +
    `Detect` + **Refresh Paths** 버튼(`launcher_tab._build_env_group`).
  - **Refresh Paths** → `prefs.rebase_all_profiles(root)`: **모든 프로파일의 모든 버튼**을 이 루트 기준으로
    다시 잡는다. `tool_launcher.rebase_to_root()` 가 경로의 **마지막 `tools` 세그먼트**를 앵커로 잡아
    그 뒤(`A000XX_name/...`)만 떼어 `<new_root>/tools/<tail>` 로 다시 잇는다. `JUN_All/tools` 밖을
    가리키는(=`tools` 앵커 없는) 버튼은 손대지 않고 **skip** 으로 보고. 바뀐 파일만 저장.
  - **자동 복구(self-heal)**: Refresh 를 안 눌러도 `launch()` 가 저장 경로가 깨졌을 때
    `rebase_to_root(path, jun_all_root())` 로 한 번 리베이스해 그게 실제로 있으면 거기서 실행한다.
    → 공유 프로파일이 대체로 그냥 동작.
- **공유 흐름**: 프로파일 JSON(`data/profiles/*.json`)은 repo 로 공유되므로, 한 PC 에서 커밋하면 다른 PC 에서
  pull 후 **Refresh Paths 한 번**으로 그 PC 기준으로 복구된다.
- **검증**: headless(python) — PC1 절대경로→현재 루트 리베이스 정확, `color` 보존, 외부 경로 skip,
  **현재 루트로 리베이스 시 파일 0개 쓰기(무손상)**, 통계(changed/unchanged/skipped/total/profiles) 일치.
  이후 사용자가 마야에서 UI 확인 완료.
  #A00370 #ToolLauncher #PySide #portability

> [!summary] `Framework/qt/MOD_tsl_qt_v01.py` — 공용 TSL 에 **선택형 Reverse 버튼** 추가 + `A00350_ArrayCreator` 적용
- **요청**: 공용 PySide TSL 위젯에 리스트 항목의 정렬 순서를 **통째로 뒤집는 Reverse 버튼**을
  **선택적으로**(원하는 툴만) 넣고, `A00350_ArrayCreator` 에 그 버튼을 켜라.
- **구현 (TSL)**: 생성자에 `show_reverse=False`(기본 꺼짐) 플래그 추가 → Sort 버튼 아래에
  `Reverse` 버튼 생성. `_on_reverse()` 는 `_set_records(list(reversed(self._records())))` —
  Sort 와 같은 **레코드 기반** 재배치라 각 항목의 **UUID(uuid, component) 데이터가 그대로 따라간다**
  (리네임/리페어런트/동명 안전). 기본값이 꺼짐이라 이 위젯을 쓰는 다른 18개 툴에는 영향 없음.
- **구현 (A00350)**: `main_window` 의 TSL 생성에 `show_reverse=True` 만 추가. 배열 요소 순서를 한 번에
  뒤집을 수 있다(체인을 끝→루트로 골랐을 때 등). v01.00→v01.01.
- **검증**: headless PySide — 기본값이면 `btn_reverse` 미생성, `show_reverse=True` 면 순서가 정확히
  뒤집히고(`['a','b','c','d']`→`['d','c','b','a']`) 붙여둔 UUID 데이터가 이동 후에도 보존됨. 전부 PASS.
  #A00350 #ArrayCreator #TSL #PySide #framework

---

## 2026-07-10

> [!summary] `A00290_BSTool` v01.02→01.05 — Shape Editor 탭 **weight 실시간 반영** + **중앙 0 슬라이더** + **Expand 창**
- **요청 1**: 씬에서 타겟 수치를 조정해도 툴에 반영되지 않는다 → 실시간으로 따라오게.
- **원인**: Maya 는 어트리뷰트 변경을 Qt 에 알려 주지 않는다. 기존엔 `Refresh` 를 누르거나 노드 리스트가
  바뀔 때만 `getAttr` 로 읽어 채웠다.
- **구현 (v01.03)**: `QTimer` 폴링 `120ms` (`_sync_se_weights`). 채널박스·어트리뷰트 에디터·애니메이션
  재생·다른 스크립트 등 **값을 바꾼 주체와 무관하게** 동작한다.
  - **함정 — 되쓰기**: `setValue` 는 `valueChanged` 를 발화해 `on_se_weight_changed` 로 되돌아온다.
    막지 않으면 방금 씬에서 읽은 값을 씬에 **다시 쓰고**, 잠금/구동된 weight 는 **매 틱 경고 로그**가 쌓인다.
    → `blockSignals` 로 막아 **씬 → UI 단방향** 유지.
  - 폴링은 **Shape Editor 탭이 보이고 표시할 행이 있을 때만** 돈다(`_update_se_timer` +
    `showEvent`/`hideEvent`/`closeEvent`). 포커스가 있는(입력 중인) 위젯과 표시 자릿수(`decimals=3`)
    아래의 미세한 차이는 건드리지 않는다.
- **요청 2**: 숫자 대신 **중앙이 0 인 가로 막대**로 좌/우 조절.
- **구현 (v01.04)**: `WeightSlider` — 중앙 `0`, 오른쪽 끝 `+1`, 왼쪽 끝 `-1`(양 끝·중앙에 눈금).
  `QSlider` 는 정수만 다루므로 **1000배 스케일**로 매핑(해상도 `0.001`). 스핀박스(`-10~10`)는 유지하고
  **양방향 동기화**(`_show_weight`) — 어느 쪽을 움직이든 씬에 쓰고 반대쪽을 맞춘다. 창 폭 460 → 580.
- **함정 — 폴링의 "값 같으면 건너뛰기" 판정**: 잠금/구동된 weight 의 슬라이더를 밀면 씬에는 안 쓰이는데,
  스핀박스만 보고 판정하면 **스핀박스는 씬과 일치**하므로 건너뛰어 **슬라이더만 잘못된 위치에 영영 남는다**.
  → `WeightSlider.shows()` 를 더해 **두 위젯을 모두** 보고 판정. 잠긴 weight 를 밀면 다음 틱에 원위치.
  (범위 밖 weight 는 슬라이더가 끝에 붙되, 클램프된 값이 씬에 되쓰이지 않는다.)
- **요청 3**: 탭 안의 `Targets` 칸이 좁다 → 별도 창으로 크게 보는 `Expand` 버튼.
- **구현 (v01.05)**: `TargetsWindow` (`BS Tool - Targets`, 기본 `640x900`). **행을 복제하지 않고
  스크롤 영역(`se_scroll`) 자체를 옮긴다** — 행 위젯이 그대로라 Edit 토글·슬라이더·폴링이 전부 살아
  있고 두 벌을 동기화할 일이 없다. 닫으면 저장해 둔 `se_scroll_index` 로 탭의 **원래 자리**에 되끼운다
  (옮긴 동안엔 숨겨 둔 자리 표시자 라벨이 그 칸을 지킨다).
  - 확장 창에도 `Filter`/개수 표시. 탭 쪽 필터와 **양방향 동기화**(값이 같으면 쓰지 않아 `textChanged`
    가 서로를 부르며 맴돌지 않는다).
  - **폴링 조건 확장**: 확장 창이 떠 있으면 본 창이 가려지거나 다른 탭이어도 계속 돈다(타겟이 화면에
    있으니까). 본 창을 닫으면 확장 창도 함께 닫아 스크롤 영역을 되돌린다(고아 창 방지).
- **검증**: Maya 쪽은 mayapy + maya.standalone(외부 `setAttr` 반영 / 애니메이션 구동 weight 의 현재 프레임
  평가값 / 잠긴 weight 읽기 / 노드 삭제 시 예외 없음), Qt 쪽은 일반 python + PySide6(되쓰기 없음 /
  포커스 보호 / eps 스킵 / 슬라이더 매핑·클램프 / 되울림 없음 / 잠긴 weight 복구 / 재부모화 후 원래
  인덱스 복원 · 반복 시 레이아웃 순서 유지 · 행 생존 · 필터 동기화) 전부 PASS.
  **mayapy standalone 에서는 `QApplication` 생성이 크래시**해 한 프로세스로 못 합치고 스위트를 분리했다.
  #A00290 #BSTool #blendShape #PySide #QTimer #mayapy

> [!summary] `Framework/qt/MOD_tsl_qt_v01.py` — **TSL 항목을 UUID 로 보관**해 이름 기반 씬 선택 실패를 제거 (브랜치 `dev_tsl`)
- **발단**: `A00145_RigConnect` Constraint Transfer 의 좌/우 TSL 에 **이름은 같고 계층만 다른** 오브젝트를
  각각 담으면 **한쪽만 씬 선택이 안 된다**.
- **진단 (mayapy 로 재현)**: `Select` 버튼이 쓰는 `cmds.ls(sl=True, fl=True)` 는 짧은 이름이 아니라
  **최단 고유 경로**(`grpA|pCube1`)를 준다. 그래서 **담는 시점에는** 동명이인이어도 선택이 잘 된다
  (그룹을 통째로 duplicate 해 모든 계층 이름이 겹쳐도 OK). 실패는 **저장된 이름이 낡았을 때**만 난다:
  - 담은 뒤 리네임/리페어런트 → `No object matches name`
  - 담은 뒤 같은 이름 노드가 하나 더 생김 → `More than one object matches name`
  두 경우 모두 `_on_selection_changed` 의 **`except Exception: pass` 가 예외를 삼켜서** 아무 일도 안
  일어난 것처럼 보였다(원인 추적 불가).
- **구현**: 표시 텍스트는 그대로 두고 씬 노드인 항목에 **`(uuid, component)` 를 `Qt.UserRole + 1` 에 병행
  보관**. 행 클릭 시 `cmds.ls(uuid, long=True)` 로 **현재 경로를 되찾아** 선택. 예외 삼킴 제거 →
  삭제된 항목/선택 실패를 로그로 안내. `append_unique` 의 중복 판정도 **UUID 우선**으로 (기존엔 텍스트
  기준이라 **이름만 같은 다른 오브젝트를 같은 것으로 보고 버렸다** — 별개 버그).
  하위호환 위해 `get_all_items()` 는 계속 텍스트 반환, 신규 `get_all_nodes()` / `selected_nodes()` 추가.
- **함정 1 — 노드가 아닌 리스트**: 어트리뷰트명/파일명/노드 타입명을 담는 4곳(A00040 `name_tsl`,
  A00150 `attr_tsl`, A00170 `rmp_attr_tsl`, A00310 `sel_types_tsl`)은 UUID 가 없다 → 이름 폴백,
  씬에 없는 이름이면 선택 시도 자체를 안 한다(조용히 무시).
- **함정 2 — 컴포넌트**: `cmds.ls("<uuid>.vtx[0]")` 는 **파싱 에러**다. 그래서 **노드 UUID + 컴포넌트
  접미사**를 따로 보관했다가 선택 시 재조립 → A00145 `tsl_skin_verts` 도 폴백이 아니라 UUID 이점을 받는다.
- **함정 3 — 재정렬이 UUID 를 날린다**: Up/Down/Sort 가 `set_items(get_all_items())` 로 리스트를 다시
  만든다 → `(텍스트, UUID)` 레코드 단위로 옮기도록 수정.
- **함정 4 — `rowsInserted` 폭증**: `set_items` 를 `addItem` 루프로 바꾸면 model 의 `rowsInserted` 가
  항목 수만큼 발생해, 그걸 듣는 A00150/A00160/A00170/A00290 의 훅이 여러 번 호출된다 →
  기존처럼 `addItems` 한 번 + `setData` 로 유지.
- **검증**: mayapy + maya.standalone (mayapy 에서 `QApplication` 생성은 크래시 → stub 항목으로 해석 로직
  검증). 동명이인 각각 해석 / 리네임·리페어런트 추적 / 삭제 시 None / 컴포넌트 리네임 추적 /
  비-노드 문자열 무시 전부 PASS. **Maya 실동작 확인은 아직**(공용 위젯이라 18개 툴 영향).
  #Framework #TSL #UUID #PySide #A00145 #mayapy

> [!summary] `A00030_quickTool` V01.11→V01.13 — **Pin(always on top) 추가 + Anim Tool UI 제거** (+ `Framework/qt` 공용 헬퍼)
- **요청**: Quick Tool 에 pin 기능 추가, Anim Tool 에 해당하는 UI 는 삭제. (직전에 작업해 둔 V01.12
  `Cluster Each` 버튼도 함께 커밋)
- **함정 — maya.cmds 창은 Qt 창처럼 pin 할 수 없다**: 이 툴은 아키텍처 (A)라 `cmds.window` 로 만든다.
  `cmds.window` 에는 최상단 고정 플래그가 없어서 A00110/A00220/A00340 의 `self.setWindowFlag(
  Qt.WindowStaysOnTopHint, ...)` 패턴을 그대로 못 쓴다.
  → `MQtUtil.findWindow(<창 이름>)` → `wrapInstance` 로 창의 **Qt 핸들을 QWidget 으로 감싼 뒤** 같은
  플래그를 토글한다. 플래그를 바꾸면 창이 숨는 Qt 특성 때문에 뒤에 `show()` 재호출은 동일하게 필요.
- **공용화**: 이 다리 역할을 `Framework/qt/maya_window.py` 에 **`maya_ui_widget(ui_name)`** 로 추가
  (`findWindow` → 없으면 `findControl`). 기존 `maya_main_window()` 와 `wrapInstance` 임포트
  (shiboken6/shiboken2 폴백)를 `_wrap_instance()` 로 공유. **다른 maya.cmds 툴에 Pin 을 붙일 때 재사용.**
- **UI**: Qt 툴들은 우측 상단 `Pin`/`Pinned` 토글 버튼이지만, cmds 레이아웃에서 우측 정렬 버튼을 만들려면
  `rowLayout` 을 덧대야 해서 창 최상단 **`Pin (always on top)` 체크박스**로 넣었다.
- **제거**: `Anim Tool` 섹션(rotate X / rotate Z / translate Y 입력 + `Rotate X Z to zero`), 콜백
  `JUN_cmd_anim_rot_x_z_to_zero`, `JUN_mod_tfg` 임포트, `btn_specs` 항목, `idx_anim_rot_x_z_to_zro`.
  창 높이 450 → 300(버튼 높이는 기존 `450/40` 유지). `Update window` 의 `JUN_cmd_update_window_for_anim`
  은 이름만 anim 이고 `playbackOptions` 토글이라 **남겼다**.
- **문서**: 가이드 문서가 없던 툴이라 `docs/A00030_quickTool.md` 신규 작성 + `docs/README.md` 목록 등록.
  #A00030 #quickTool #pin #alwaysOnTop #mayacmds #Framework

> [!summary] `A00300_meshDoctor` v01.02→01.03 — **Target Meshes 리스트 선택 → 씬 선택 연동**
- **요청**: `Target Meshes` 에 리스트업된 오브젝트를 고르면 씬에서도 선택되게. 공용
  `Framework/qt/MOD_tsl_qt_v01.py` 에 이미 있는 기능이니 참고할 것.
- **구현**: `lst_targets.itemSelectionChanged` → 씬 선택(`cmds.select(..., replace=True)`).
  공용 위젯의 `_on_selection_changed` 와 같은 동작이되 **노드를 되찾는 방식이 다르다** — 공용 위젯은
  리스트에 담긴 **이름 문자열**로 선택하지만, A00300 은 항목의 `Qt.UserRole` 에 **UUID** 를 보관하므로
  `cmds.ls(uuid, long=True)` 로 현재 DAG 경로를 얻어 선택한다(중복 이름 씬에서 엉뚱한 메시를 잡지 않음.
  기존 `_listed_nodes()` 와 동일한 방식). 선택이 비면(Remove/Clear 직후) 씬 선택은 건드리지 않고,
  씬에서 사라진 항목은 로그로 안내.
- **정리**: CHANGELOG 에 누락돼 있던 **v01.02**(Target Meshes 리스트 + Summary 테이블) 항목도 함께 채움.
  #A00300 #meshDoctor #TSL #UUID #PySide

> [!summary] `A00290_BSTool` v01.01→01.02 — **`Shape Editor` 탭 신규**: 마야 기본 Shape Editor 대체
- **요청**: 마야 Shape Editor 는 가끔 원하는 타겟을 트리에 노출하지 않아 **Edit 버튼조차 없어** 수정을 못 한다.
  blendShape 노드를 골라 **모든 타겟을 리스트업**하고 타겟마다 Edit 버튼을 만들어, 이후는 기본 Shape Editor 와
  똑같이 동작하게 해달라.
- **구현**: 새 탭(탭 1) + `core/shape_editor_manager.py`(`ShapeEditorManager`). 타겟은 `aliasAttr` 에서 직접
  읽으므로 마야가 감추는 타겟도 전부 나온다. 타겟마다 `Edit` 토글 + weight 스핀박스, 이름 `Filter`, `Refresh`,
  `Exit Edit Mode (all blendShapes)`. Edit 진입 시 weight 1.0 (이전 값 백업) · `envelope` 1.0 · 베이스 메시 선택,
  해제 시 weight 원복. 노드당 한 타겟만 편집(마야와 동일) — 다른 타겟을 켜면 이전 것 자동 해제.
  뷰포트 HUD(`updateBlendShapeEditHUD`)도 갱신. 창을 닫으면 열린 편집 모드를 모두 해제(= 결과 확정).
- **함정 1 — `setAttr` 로는 편집 모드가 안 걸린다**: 처음엔 `scripts/others/setSculptTargetIndex.mel` 을 근거로
  `<bs>.inputTarget[g].sculptTargetIndex` 를 `setAttr` 했다. 어트리뷰트 값은 바뀌어 **편집 모드처럼 보이지만**,
  디포머가 버텍스 편집을 가로채도록 세팅하는 일은 **`sculptTarget` 커맨드**가 한다. 그래서 조각한 결과가
  베이스 shape 의 tweak(`.pnts`)으로 들어가 **원본 메시가 수정**됐다.
  → 쓰기는 `cmds.sculptTarget(bs, e=True, target=<idx|-1>)`, **읽기만** 어트리뷰트.
  (`sculptTarget -q -target` 은 `None` 을 돌려줘서 조회에 못 쓴다. 위 mel 은 이미 sculpt 세팅이 끝난 뒤
  인덱스만 옮기는 용도였다.)
- **함정 2 — `clicked` 시그널 인자**: `clicked(bool checked = false)` 는 인자 없이 발화될 수 있어
  `lambda checked, ...` 가 `TypeError: missing 1 required positional argument`. `*_a` 로 흘리고 위젯에서
  `isChecked()` 를 직접 읽는다. `QDoubleSpinBox.valueChanged` 도 PySide2 에 `(QString)` 오버로드가 있어 동일 처리.
- **함정 3 — Edit 버튼 색이 안 바뀜**: 테마 qss 의 `QPushButton:hover`/`:pressed` 가 pseudo-state 규칙이라,
  클릭 직후(마우스가 버튼 위) 테마 색이 다시 덮는다. 버튼 자신의 스타일시트에 hover/pressed 까지 지정하고
  라벨도 `Edit` ↔ `Edit ON` 으로 바꿔 상태를 명확히 했다.
- **검증**: `Maya2024/bin/mayapy.exe` + `maya.standalone` 헤드리스로 스피어 2타겟 blendShape 을 만들어 매니저를
  직접 호출 — 수정 전엔 `base.pnts[5]=(0,0,2)`(원본 훼손), 수정 후엔 `deltas[0]` 에 `(0,0,2)` 기록 + `pnts` 는 0.
  weight 원복(0.25), 타겟 전환 시 이전 타겟 자동 해제, `Exit Edit Mode (all)` 후 편집 노드 0 개까지 확인. 마야 실동작도 OK.
  #A00290 #blendShape #ShapeEditor #sculptTarget #PySide #mayapy

> [!summary] `Framework/styles` 전체 — **비활성(disabled) 위젯 표현을 테마 qss 로 이관** (+ `A00260` v01.06→01.07)
- **요청**: A00260 에서 한 "비활성 UI 를 흐리게" 처리를 **같은 종류의 qss 파일 전부**에도 적용할 수 있는지.
  (※ 그때는 qss 를 고친 게 아니라 `main_window.py` 안의 로컬 `DISABLED_QSS` 를 그룹박스에만 덧댔던 것)
- **문제**: `Framework/styles/*.qss` **14 개 전부 `:disabled` 규칙이 없었다.** `QLabel { color: #e6e6e6 }` 같은
  평면 규칙이 비활성 상태까지 적용되면서 Qt 기본 회색 처리를 덮어써, `setEnabled(False)` 를 해도 그대로 밝게 보임.
- **구현**: 각 테마의 **기존 팔레트를 배경 쪽으로 블렌딩**해(텍스트 55%, 버튼/보더 60%, 입력 50%) 테마별 비활성
  색을 계산하고, 14 개 qss 끝에 `:disabled` 블록 추가 — `QLabel`/`QCheckBox`/`QRadioButton`/`QGroupBox(::title)`,
  `QPushButton`, `QLineEdit·QTextEdit·QPlainTextEdit·QListWidget·QSpinBox·QComboBox`,
  `QCheckBox·QRadioButton::indicator(:checked)`. 색 하드코딩 없음.
- **함정**: `dark.qss` / `red.qss` 는 원래 `QCheckBox::indicator` 를 **스타일링하지 않는다**. 비활성 상태에만
  `::indicator` 규칙을 주면 Qt 가 네이티브 렌더링을 버려 **체크 표시가 사라진다** → 두 파일에서는 체크박스
  인디케이터 규칙을 빼고 라디오만 남김(주석으로 이유 명시). 라디오는 14 개 전부 원래 스타일링돼 있어 안전.
- **정리**: `A00260_ConstraintConverter` 의 로컬 `DISABLED_QSS` 제거(다크 색 하드코딩이라 라이트 테마에서 어긋남)
  → 이제 테마가 담당. version 01.07.
- **검증**: PySide6 offscreen 으로 `ThemeManager.load_theme_to_widget()` 을 태워 14 개 테마 전부
  **qss 파싱 OK + 렌더링 픽셀에서 비활성 라벨 색이 활성과 다름**을 확인(14/14). 초기에 뜬 `Could not parse
  stylesheet` 는 원본 파일의 `@STYLES@` 토큰을 로더 없이 먹여서 난 것으로, 기존 문제도 내 변경 탓도 아니었음.
  #Framework #qss #theme #disabled #PySide

> [!summary] `A00260_ConstraintConverter` v01.05→01.06 — **Position / Rotation 노드도 접힌(collapsed) 형태로 출력**
- **요청**: v01.05 로 만든 Position / Rotation 노드가 UE 에서 **핀이 다 펼쳐진 채** 붙는다.
  `ref_/sample_position_close.py` 처럼 접힌 형태로 나오게 할 것.
- **분석**: `sample_position.py`(펼침) ↔ `sample_position_close.py`(접힘) 의 차이는 **딱 두 줄** —
  `Parents` 컨테이너와 `Filter` 컨테이너의 `bIsExpanded=True`(6칸 들여쓰기). 컨테이너 **안쪽**의
  `Parents.N` / `Child` 의 `bIsExpanded=True` 는 접힌 형태에도 그대로 남는다. Parent 템플릿(`A0001`)은
  원래부터 이 규칙이라 손댈 필요 없음. Rotation 의 `AdvancedSettings` 컨테이너도 이미 `bIsExpanded` 없음.
- **구현**: `A0005_Src_position_node.py` / `A0006_Src_rotation_node.py` 에서 컨테이너 레벨
  `bIsExpanded=True` 두 줄 제거(각각 `TArray<FConstraintParent>` 앞, `FFilterOptionPerAxis` 앞).
- **검증**: `ConstraintConverter.build_text()` 결과가 `ref_/sample_position_close.py` 와 **바이트 동일**,
  Rotation 은 `sample_rotate.py` 에 같은 두 줄을 제거한 접힘 변환본과 **바이트 동일**. Parent 회귀 없음.
  py_compile 통과. version 01.06, 가이드 문서 갱신.
  #ConstraintConverter #UnrealEngine #ControlRig #template

> [!summary] `A00260_ConstraintConverter` v01.04→01.05 — **Position / Rotation 컨스트레인트 노드 + 축(X/Y/Z)별 필터**
- **요청**: 지금은 UE **Parent Constraint** 노드만 생성한다. 드롭다운으로 **Position / Rotation** 노드도
  같은 방식으로 생성하게 하고, **Translate/Rotate/Scale 을 축(X/Y/Z) 단위로 체크**할 수 있게 할 것.
  Position/Rotation 은 각각 Translate/Rotate 행만 활성화되고 나머지는 선택 불가.
  레퍼런스: `ref_/sample_position.py`, `ref_/sample_rotate.py`
  (`dyn_pants_btmL_01_01` ← `thigh_twist_02_l` 0.8 / `thigh_twist_01_l` 0.2, X 축만 필터).
- **분석**: 세 노드는 Child / Parents(타겟+웨이트) / bMaintainOffset / Weight 구성이 같고 **두 가지만 다르다** —
  ① `Position` 은 `AdvancedSettings`(InterpolationType) 핀 자체가 **없다** ② `Parent` 의 `Filter` 는
  `Translation`/`Rotation`/`Scale` **3중첩**(각 `bX/bY/bZ`)인데 `Position`/`Rotation` 은 **단일 `bX/bY/bZ`**.
  `Rotation` 은 `Position` + AdvancedSettings(구조체 `RigUnit_RotationConstraint_AdvancedSettings`).
  Parents 배열(`A0002`/`A0003`)은 셋이 동일해 그대로 공용.
- **구현**: 신규 템플릿 `0010_src/A0005_Src_position_node.py`, `A0006_Src_rotation_node.py`(샘플에서 기계적으로
  추출). `A0001`(Parent) 의 채널 단위 placeholder `{{TRANS_FILTER}}` 등을 **축 단위**(`{{TRANS_X}}`…`{{SCALE_Z}}`)로
  분리. `node_builder.py` 에 `NODE_TYPES` 스펙 테이블(채널 / interp 핀 유무 / 노드 이름 접두사) + `NodeBuilder`
  가 `node_tmpl` 하나 대신 `node_tmpls` dict 를 받고 Parent 면 3벌 필터·나머지는 단일 `FILTER_*` 를 채움.
  `ConvertOptions` 에 `constraint_type` + 축 플래그 9개(`trans_x`…`scale_z`) + `axes(channel)` 헬퍼.
  `constraint_converter.py`/`tool_path.py` 는 템플릿 3종 로드 + 접두사를 타입에서 가져옴.
  UI: `Constraint Type` 드롭다운 + Filter **3×3 그리드**, 타입 전환 시 안 쓰는 행/Interpolation Type 비활성화,
  해당 채널 축이 전부 꺼져 있으면 자동으로 X/Y/Z 켜기(+Convert 가드).
- **비활성 표현**: `setEnabled(False)` 는 되는데 **눈으로 구분이 안 됨** — `Framework/styles/*.qss` 17 개 모두
  `:disabled` 규칙이 없어 `QLabel { color: #e6e6e6 }` 같은 평면 규칙이 비활성 상태까지 덮어쓰기 때문.
  프레임워크 전체를 건드리지 않고 **옵션 그룹박스에만** `DISABLED_QSS`(라벨/체크박스/콤보 `:disabled` 색 +
  인디케이터)를 `setStyleSheet` 으로 덧댐. 창 전체에 걸면 `launch.py` 의 `ThemeManager.load_theme_to_widget`
  이 나중에 덮어쓰므로, 부모 테마보다 우선하는 **자식 위젯** 스타일시트로 건다.
- **검증**: 샘플 데이터로 `ConstraintConverter.build_text()` 결과가 `sample_position.py` / `sample_rotate.py` 와
  **바이트 동일**(round-trip, 노드명·Position 좌표 제외), Parent 축별 필터 3벌 값 확인, py_compile 통과,
  **Maya 실기 확인 완료**(비활성 표현 포함). version 01.05, 가이드 문서 갱신.
  #ConstraintConverter #UnrealEngine #ControlRig #template #qss

---

## 2026-07-09

> [!summary] `A00145_RigConnect` v01.14→01.15 — **Connect Closest 의 cluster handle 위치 버그 수정**
- **증상**: `Driven` 에 **클러스터 핸들**, `Driver` 에 (계층 안의) 조인트를 넣고 `Get Closest` 를 누르면
  결과가 기대와 다르게 나옴.
- **원인**: `app/core/maya_scene.py` 의 `world_position()` 이 `xform -ws -t`(transform 의 translate)만
  읽는데, **`clusterHandle` 은 transform.translate 가 `(0,0,0)`** 이고 실제 중심은 shape 의 `origin`
  (아이콘/rotate pivot 위치)에 있다 → 클러스터 후보가 **전부 월드 원점**으로 계산되어 거리가 사실상
  "driver ↔ 원점" 으로 동일해지고 greedy 1:1 매칭이 **리스트 순서대로** 짝지어짐. (driver 조인트가 다른
  조인트의 자식인 것 자체는 `-ws` 가 계층을 반영하므로 원인이 아님)
- **구현**: `PIVOT_BASED_SHAPES = ("clusterHandle",)` 상수 추가. `world_position()` 이 해당 shape 를 가진
  노드(또는 shape 자체)를 만나면 ① shape 의 `.origin` 을 transform 의 world matrix 로 곱해 월드 좌표 산출
  → ② 실패 시 `xform -ws -rp` → ③ 그래도 실패 시 기존 `-ws -t` 로 폴백. 헬퍼 `_pivot_based_shape()` /
  `_transform_of()` / `_local_to_world()` 추가. `find_closest`·`match_closest_pairs` 가 모두
  `world_position` 을 쓰므로 **`Get Closest` 와 `Connect` 가 함께 수정**됨.
- **검증**: py_compile 통과 + **Maya 실기 확인 완료**. version 01.15, 가이드 문서 Connect Closest 절 갱신.
  #RigConnect #ConnectClosest #cluster #bugfix #rigging

> [!summary] `A00145_RigConnect` v01.13→01.14 — Constrain 탭 **Constraint Transfer** 신규(걸린 constraint 를 다른 오브젝트로 이관)
- **요청**: 이미 걸려 있는 constraint 를 다른 오브젝트에 걸리도록 **옮기는** 기능. 왼쪽 TSL 에 constraint,
  오른쪽 TSL 에 오브젝트를 리스트업 → 실행하면 **어떤 종류의 constraint 든** 원본을 지우고 **세팅이 같은**
  constraint 를 오른쪽 오브젝트에 재생성. **Maintain offset 유지**로 명령 전후 원본/신규 오브젝트 모두
  위치·회전 불변. **UUID 기반**(동명 오브젝트 안전).
- **구현**: 신규 코어 `app/core/constraint_transfer_manager.py` — `transfer_constraints(constraint_names,
  object_names)`. `_read_constraint`(nodeType 로 `getattr(cmds, ctype)`, `targetList`/`weightAliasList`+getAttr
  weight/부모=driven/aim 벡터·worldUp/parent·orient interpType 수집, 전부 UUID) → `_recreate`(타깃+새 driven 으로
  `cmd(*targets, driven, maintainOffset=True)`, MO 미지원 타입은 예외 시 MO 없이 재시도, weight/aim/interpType
  복원). 순서: **새 constraint 먼저 생성**(원본 살아 있는 동안) → 원본 `delete` → 원본 driven 월드행렬 복원(대상에
  자기 자신 없을 때). 왼쪽 항목이 트랜스폼이면 `listRelatives(type='constraint')` 로 자동 확장. 매핑: 오른쪽 1개면
  전 constraint→그 오브젝트, 개수 같으면 1:1, 아니면 min+경고. UI(`_build_constraint_transfer_box`, 접이식 기본
  접힘, 좌 Constraints/우 Apply To 두 TSL + Transfer 버튼), 핸들러 `on_transfer_constraint`, core `__init__` 등록.
- **검증**: 전 파일 py_compile 통과 + **Maya 실기 확인 완료**(constraint 이관 후 원본/신규 오브젝트 위치·회전
  불변, MO 유지). version 01.14, 가이드 문서 `A00145_RigConnect.md` Constrain → Constraint Transfer 절 추가.
  #RigConnect #ConstraintTransfer #maintainOffset #UUID #rigging

> [!summary] `A00145_RigConnect` v01.12→01.13 — Constrain 탭 **Group Create** 오프셋 노드 옵션 확장(zero-out)
- **요청**: (신규 `A00380_HierarchyTool` 로 만들려다) 이미 존재하는 **Constrain 탭 > Group Create** 기능에
  다음을 추가: ① 접미사(**Suffix**)를 사용자 지정(`zro` 등, zero-out 의미) ② 패딩 있는 번호(01, 02) ③ 오프셋
  노드 **개수** 지정 ④ 노드 **타입**을 기본 그룹 또는 **선택 오브젝트와 동일 타입**(joint → joint) 선택
  ⑤ 부모뿐 아니라 **자식** 쪽도 동일 방식으로 생성.
- **구현**: `group_create_manager.py` 를 `create_offset_nodes(objects, count, suffix, match_type,
  create_parent, create_child, padding)` 로 확장. Parent 체인(부모↔obj 사이 삽입)에 더해 **Child 체인**(obj↔
  자식 사이 삽입, shape 는 obj 에 유지, 기존 트랜스폼 자식만 가장 깊은 노드 아래로 재부모) 추가. `_make_node`
  가 `group`(빈 그룹) 또는 오브젝트 nodeType(예: **joint** 은 `createNode` + select clear 로 자동부착 방지)으로
  생성, 이름 = `<obj>_<suffix>_<번호(패딩)>`. 전부 `matchTransform`(pos/rot, scale 제외)로 월드 정렬,
  **UUID 기반**은 유지. UI(`main_window._build_group_create_box`)에 **Suffix/Count/Padding**, **Type**(Group/
  Match object type 라디오), **Side**(Parent 기본 on / Child 체크박스) 추가. 구버전 `create_groups()` 는 위임
  래퍼로 남김. `on_group_create` 핸들러가 새 값 전달.
- **후속 수정(같은 날)**: `Match object type` 에서 **커브 등 shape 기반 타입이 그룹으로 만들어지던** 문제 수정
  (`nodeType` 이 transform 레벨에서 `transform` 을 돌려주던 게 원인). `_make_offset_node(source, match_type,
  name)` 로 통합 — **shape 있으면 오브젝트를 복제 후 하위 자식만 삭제·월드로·스케일 1**(curve→curve, mesh→
  mesh), **shape 없으면 같은 nodeType 으로 createNode**(joint→joint), 순수 transform 은 빈 그룹. 노드 타입
  기준은 항상 **원본 오브젝트**(중첩 노드 전부 동일 타입).
- **검증**: py_compile 통과 + **Maya 실기 확인 완료**(joint/curve 등 Match object type 정상, Parent/Child
  양방향). version 01.13, 가이드 문서 `A00145_RigConnect.md` Group Create 절 갱신.
  #RigConnect #GroupCreate #zeroOut #offset #joint #hierarchy

---

## 2026-07-08

> [!summary] `A00370_ToolLauncher` v01.00→01.02 (신규) — 툴 폴더 경로를 담은 버튼으로 JUN 툴을 팝업시키는 숏컷 런처
- **요청**: `A00080_KWI_creator_V03` · `A00260_ConstraintConverter` 처럼 **마야 세팅→언리얼 코드 생성** 툴들을
  각각 셸프 아이콘으로 부르는 대신, **하나의 UI 에서 버튼을 만들어** 누르면 지정 툴이 팝업되는 숏컷 런처.
  `A00340_SelectionTool` 과 유사한 UI/기능(**Profile · Category**)을 갖되, 툴 **폴더 경로만 지정하면**
  그 툴을 쓸 수 있는 **확장 가능** 설계. + 각 버튼에 **그 툴의 아이콘**을 곁들이고(v01.01),
  아이콘을 버튼 **왼쪽 정사각형**으로 크게 배치(v01.02).
- **구현(arch B, A00340 클론)**: 프로파일/카테고리/버튼-색/Color Select/접이식 Controls 스플리터 레이아웃을 이식,
  버튼 데이터는 `objects` 대신 `path` 를 담음. 핵심 로직 `app/core/tool_launcher.py` — `resolve_module(path)`
  로 `(<JUN_All>, "tools.A000XX_name")` 을 뽑아 `importlib.import_module` → `run(reload_module)` 호출
  (= 각 툴 셸프 명령의 일반화). `validate`(폴더+`__init__.py`), `find_icon`(`icon/<폴더명>.png`), Browse 폴더
  선택, Reload-on-launch 체크(기본 ON). 버튼 렌더는 `QHBoxLayout[정사각 아이콘 QLabel(버튼높이), 버튼]`.
  기본 `Default` 프로파일에 `Maya to Unreal` 카테고리로 A00080/A00260 예시 배선. 아이콘(로켓+실행버튼) 제작.
- **검증**: 전 모듈 py_compile, 경로 resolve/validate·find_icon 실폴더 정확, **두 대상 툴 실제 import+run 확인**,
  오프스크린으로 `LauncherTab` 전체 렌더(아이콘 34×34 정사각 좌측 배치)까지 확인. **Maya 실기 확인 완료**(테마
  yellow_light). version 01.02 + 신규 가이드 문서 `JUN_All/docs/A00370_ToolLauncher.md`.
  #ToolLauncher #shortcut #launcher #Profile #Category #신규툴

> [!summary] `A00350_ArrayCreator` v01.00 (신규) — 마야 오브젝트 → UE Control Rig Item Array 노드 텍스트 생성(클립보드)
- **요청**: TSL 에 오브젝트를 리스트업하고 그 순서대로 언리얼 Control Rig **Item Array 노드**(`TArray<FRigElementKey>`)
  텍스트를 생성해 **클립보드 복사**(UE 에 Ctrl+V) + 파일 저장. 요소 **Type**(None/Bone/Null/Control/Curve/Reference/
  Connector/Socket)을 고를 수 있게, **기본 Bone**. 아이콘 제작. 참고: 템플릿 `A0010_Src_Array_node_v01/v02.py`,
  아키텍처 A00080_KWI_creator_V03 · A00260_ConstraintConverter.
- **구현(arch B, A00260 패턴 클론)**: `0010_src` 에 조각 템플릿 3개(node/element decl/element def, `{{KEY}}`),
  `node_builder.py` 가 decl+def+SubPins 를 요소 수만큼 조립, `array_creator.py`(PathManager 0010_src→0020_out,
  파일 저장), `main_window.py`(TSL + Element Type 콤보[기본 Bone] + Node Title + Create→클립보드). v02 는 타입
  카탈로그(단일요소 노드 8개)라 **전역 Type 콤보**(모든 요소 공통)로 구현.
- **검증**: **라운드트립 — v01 의 6조인트/Bone 로 생성 시 v01 과 바이트 단위 완전 일치(204줄)**, 변형 테스트 정상,
  전 모듈 py_compile. **Maya 붙여넣기 확인 완료.** version 01.00 + 신규 가이드 문서 `JUN_All/docs/A00350_ArrayCreator.md`.
  #ArrayCreator #UnrealControlRig #RigVM #텍스트생성 #신규툴

> [!summary] `A00360_SortTool` v01.00 (신규) — 오브젝트를 월드 X/Y/Z·이름·타입 기준 정렬 + 아웃라이너/TSL 순서 재정렬
- **요청**: 선택 오브젝트를 TSL 에 리스트업하고, **월드 X/Y/Z 위치 중 하나**(+이름/타입) 기준으로 정렬해
  **아웃라이너 순서(위→아래)** 를 바꾸는 in-Maya PySide 툴. 아웃라이너 재정렬은 **체크박스 on/off(기본 on)**,
  TSL 리스트도 같은 순서로 재정렬. 위치를 가진 노드면 **조인트·메시·커브·클러스터·디포머** 등 무엇이든 동작.
  참고 MEL: `AriSortOutliner.mel` / `AriSortOutlinerOptions.mel`.
- **구현(arch B, A00060_V02 스켈레톤 클론)**: `app/core/sort_manager.py` — `sort_objects(items, mode, reverse,
  reorder_outliner)`. 위치는 `xform(ws)`, 이름=짧은이름, 타입=(shape nodeType, 이름). 위치 없는 순수 DG 노드는
  크래시 없이 스킵. 아웃라이너 재정렬은 **Ari 슬롯 스왑**(`reorder -relative`)을 이식 — 부모별 그룹으로, 선택
  오브젝트가 원래 차지하던 슬롯을 정렬 순서로 채움(형제만 재정렬 가능한 Maya 제약과 일치). `app/ui/main_window.py`
  — TSL(`JUN_mod_tsl_qt_v01`) + Sort By 라디오(World X/Y/Z·Name·Type) + Reverse/Reorder-in-Outliner 체크 + Sort +
  로그, undo_chunk 로 묶음. 아이콘(`icon/*.svg` + 32px png, 정렬막대+화살표) 제작.
- **검증**: **Maya 실기 확인 완료.** version 01.00 + 신규 가이드 문서 `JUN_All/docs/A00360_SortTool.md`.
  #SortTool #outliner #reorder #worldSpace #AriSortOutliner #신규툴

> [!summary] `A00060_jointTool_V02` v01.02→01.03 — Curve/Divide 조인트를 월드 절대 좌표로 생성(계층 아래 오브젝트 위치 오차 수정)
- **요청**: Curve/Divide 탭의 **Match to Obj / Make Joint Divided** 로 조인트를 만들면, 오브젝트가 어떤 계층
  아래에 있을 때 **원하는 위치에 안 생긴다**. 월드 기준 절대값으로 받아 어떤 계층이든 정확히 생성하도록 수정.
- **원인/수정(모두 `app/core`)**: ① `divide_manager.curves_from_pairs` — `xform` 이 **object-space** translation
  이라 커브/분할 joint 가 로컬 좌표에 생성 → `ws=True` 추가. ② `curve_joint_manager._joint_at_curve_point` —
  `pointPosition`(이미 월드)에 커브 world translation 을 **한 번 더 가산**(이중 가산) → 커브가 원점 아니면 2배
  오차 → 가산 제거 + `xform(ws)` 확정. ③ `obj_joint_manager._joint_at_obj`(Match to Obj) — `joint -p` 가 부모
  체인 아래로 들어갈 때 대비해 생성 직후 `xform(jnt, ws=True, translation=pos)` 로 월드 위치 확정.
- `aim_manager` 는 원래부터 `ws=True` 라 변경 없음. 원점/무계층 케이스는 동작 불변(하위 호환).
- **검증**: **Maya 실기 확인 완료.** version 01.03 + 신규 가이드 문서 `JUN_All/docs/A00060_jointTool_V02.md`(§6) 갱신.
  #jointTool #worldSpace #xform #pointPosition #rigging

---

## 2026-07-07

> [!summary] `A00300_meshDoctor` v01.01→01.02 — 여러 메시 배치 진단 + 메시별 요약 테이블(클릭 시 상세)
- **요청**: 여러 메시를 TSL 에 리스트업하고 한 번에 진단해, 모든 메시의 결과를 **간단하게** 보고 싶다. UI 방식 제안 요청.
- **결정(옵션 '요약 테이블 + 클릭 상세' 선택)**: 창 상단에 **Target Meshes** TSL(Add Selected/Remove/Clear, **UUID 보관**
  → 중복 이름/리페어런트 안전) 추가. **Diagnose Listed**(기존 Diagnose Selected 대체)가 리스트 전체를 진단하고,
  **리스트가 비면 현재 선택**으로 폴백. 결과는 **Summary 테이블**(`Mesh|Status|Issues`, Status 색상 구분, Issues 는
  WARN/FAIL 을 `이름(개수)` 요약)로 보여주고, **행 클릭 → 그 메시의 기존 전체 상세 리포트를 아래 로그뷰에 출력**.
- **구현**: core `mesh_scan.py` 에 `scan_nodes(nodes)`/`_resolve_meshes()` 추가(`scan_selection` 은 이를 재사용).
  `main_window.py` 에 TSL 그룹·Summary 테이블·핸들러(`on_add_selected`/`_listed_nodes`/`_fill_summary`/`_on_summary_row` 등).
  JSON/TXT 리포트는 배치 전체 저장 유지.
- **검증**: **Maya 실기 확인 완료.** version 01.02 + 신규 문서 반영 `JUN_All/docs/A00300_meshDoctor.md`(§여러 메시 한 번에 진단).
  #meshDoctor #배치진단 #SummaryTable #UUID #weightTransfer

> [!summary] `A00210_FileManager` v01.27→01.28 — Path Structure: Recreate 목적지("Recreate To") 칸 + Rename 버튼
- **요청**: Path Structure 탭에서 (1) 저장된 구조 이름을 바꾸는 **Rename** 버튼, (2) Recreate 가 File Manager 탭의
  `Scan Dir` 인지 이 탭의 `Base Folder` 인지 헷갈려서 **재생성 목적지를 따로 지정**하는 UI. UI 방식은 제안 요청.
- **원인/혼동**: 기존 Recreate 는 `<File Manager 탭 Project Root>/<base_rel>` 에 생성 — 어느 경로인지 화면에 안 보였다.
- **구현(옵션1 '베이스 폴더 직접 지정' 선택)**: Saved Structures 그룹에 **`Recreate To` 칸(+Browse)** 추가 —
  체크된 폴더가 이 폴더 **바로 안**에 생성된다. 구조 선택 시 `<Project Root>/<base_rel>`(기존과 같은 경로)로
  **자동 채움**, 다른 곳으로 자유롭게 변경 가능(생성 경로가 항상 노출). 목적지가 없으면 생성 확인. `Rename` 은
  QInputDialog(파일명+내부 name 동기화, 충돌 거부). **Recreate 버튼은 녹색 액센트 + 우측 정렬**로 Refresh/Rename/
  Delete(관리)와 구분(실제로 폴더를 생성하는 동작). core: `path_structure.rename()` 신규, `recreate(..., base_abs=)` 추가.
- **검증**: **실기 확인 완료.** version 01.28 + 문서 `JUN_All/docs/A00210_FileManager.md`(§4-C) 갱신.
  #FileManager #PathStructure #Recreate #Rename #UX

> [!summary] `A00110_animTool` v01.29→01.30 — Graph Focus 자동 확대를 오브젝트 선택에만 엄격히 한정
- **요청**: Graph Focus 의 Auto-Focus 자동 확대가 **컨트롤러를 선택했을 때만** 동작하게. 지금은 애니 작업 중
  컨트롤+`z`(undo)를 눌러도, 그래프 에디터의 키프레임을 하나 선택했다 풀어도 자동 확대가 걸린다.
- **원인**: 마야 `SelectionChanged` 는 씬 오브젝트 선택뿐 아니라 **키 선택/해제·undo** 로도 발생. v01.27 의
  "선택된 키가 있으면 건너뛰기"는 키를 **해제한** 순간(선택 키 0개)을 막지 못했다.
- **구현(`app/core/graph_focus_manager.py` 만 변경)**: 직전에 프레이밍한 **오브젝트 선택 목록**을 캐시
  (`_last_selection`)해두고, `_apply_silent` 에서 `cmds.ls(sl=True, long=True)` 가 실제로 **달라졌을 때만**
  프레이밍(선택이 비면 무시, 기존 키-선택 방어도 유지). `apply_now`(토글 ON/값 변경/Focus Now)도 캐시를 현재
  선택으로 맞춰 재트리거 방지. 키 선택/해제·undo 는 오브젝트 선택이 그대로라 무시된다.
- **검증**: **Maya 실기 확인 완료.** version 01.30 + 문서 `JUN_All/docs/A00110_animTool.md`(§1 changelog, §5.7) 갱신.
  #animTool #GraphFocus #SelectionChanged #AutoFocus

---

## 2026-07-06

> [!summary] `A00145_RigConnect` v01.10→01.12 — Constrain 탭에 Group Create 접이식 추가(오프셋 그룹 _con_NN 삽입, UUID 기반)
- **요청**: Constraint 탭에 접이식 UI 하나 추가. 리스트업된 각 오브젝트에 **위치·회전이 같은 그룹**을 만들어 **오브젝트의 부모와
  오브젝트 사이 계층**에 삽입(그룹명 `<obj>_con_01`, 몇 개 만들지 사용자 지정).
- **구현(v01.11, 새 매니저 `app/core/group_create_manager.py`)**: `create_groups(objects, count)` — 오브젝트당 `Count` 개의
  중첩 오프셋 그룹을 삽입. 각 그룹은 `matchTransform`(position/rotation, **scale 제외**)로 오브젝트 월드에 맞추고, 원래 부모 아래로
  재부모(월드 보존) 후 대상을 그 그룹 아래로. `_con_01` 이 오브젝트 바로 위, 번호가 커질수록 바깥. 오브젝트 월드/기존 계층 유지.
  `CollapsibleBox("Group Create", 기본 접힘)` + 전용 TSL + Count 스핀박스(1~50) + `Create Groups` 버튼(`_build_group_create_box`/`on_group_create`).
- **UUID 기반(v01.12)**: 중복 이름·재부모로 DAG 경로가 바뀌어도 안전하도록, 대상/부모/생성 그룹을 **UUID 로 잡아두고 매번 UUID→현재 경로로
  해석**(`_to_uuid`/`_path`, A00330_NamingTool 패턴). 중복 이름이면 경고 후 첫 매치 사용, 없거나 실패한 항목은 건너뛰고 로그.
- **검증**: `py_compile` 통과. **Maya 실기 검증 대기.** version 01.12 + 문서 `JUN_All/docs/A00145_RigConnect.md`(Constrain > Group Create) 갱신.
  #RigConnect #GroupCreate #offsetGroup #UUID #matchTransform

> [!summary] `A00220_BackupTool` v01.12→01.13 — Always on Top(Pin) 토글 버튼 추가 (A00110 패턴 이식)
- **요청**: `A00110_animTool` 처럼 Pin 기능을 붙여, 필요할 때 이 창을 다른 창들 위에 고정.
- **구현(`app/ui/main_window.py`)**: 창 **우상단 헤더 행**에 체크형 `Pin` 버튼(좌측 stretch + 고정 크기 72×28) 배치.
  `toggle_always_on_top(enabled)` 이 `Qt.WindowStaysOnTopHint` 를 켜고/끄고 라벨을 `Pinned`/`Pin` 으로 바꾼 뒤
  `show()` 재호출(플래그 변경 시 창이 숨는 Qt 특성 회피). A00220 은 standalone Qt 창이라 A00110 과 동일하게 동작.
  기본 OFF(정상 Z-order, opt-in), prefs 미저장(A00110 과 동일).
- **검증**: `py_compile` 통과 + **실기 확인 완료**. version 01.13 + CHANGELOG + 문서 `JUN_All/docs/A00220_BackupTool.md`(§3) 갱신.
  #BackupTool #Pin #AlwaysOnTop #WindowStaysOnTopHint

> [!summary] `A00340_SelectionTool` v01.03→01.04 — 창을 상하 스플리터로 분리 + 컨트롤 4칸(Profile/Create/Color/Log)을 하나로 접었다 펴기 (Maya 실기 검증 완료)
- **요청**: 컨트롤 칸(Profile/Create/Color/Log)과 생성한 버튼 모음을 분리하고, 컨트롤을 접었다 펼 수 있게. (제안 4가지 중
  '상하 분할 + 접기' 채택 → 이후 '각 칸 개별'이 아니라 '네 칸을 한 번에' 접도록 재조정)
- **구현(`app/ui/selection_tab.py`)**: 창을 `QSplitter(Qt.Vertical)` 로 [컨트롤 pane] / [버튼 pane] 분리(핸들 드래그로 비율 조절).
  컨트롤은 Profile/Create/Color/Log 그룹박스 4개를 **하나의 접이식 `Controls` 박스**(신설 `CollapsibleBox` 위젯,
  QToolButton 헤더 ▾/▸)로 묶어 **한 번에** 접었다 편다. 접으면 `_on_controls_toggled` 가 스플리터 위 pane 을 헤더 높이로
  줄여(230→70) 버튼 영역을 넓히고(378→538), 펴면 원위치. 로그창은 이 박스 안으로 이동(기존 하단 Log 그룹 제거,
  `main_window` 가 `log_view` 를 탭에 전달).
- **검증**: `py_compile` + 오프스크린 PySide6 스모크(접이식 박스 1개+그룹 4개, 접기 시 전 그룹 숨김·pane 축소/확대, 펴기
  복원, 색칠 기능 회귀 없음) 통과 + 렌더 PNG 육안 확인, **Maya 실기 검증 완료**. version 01.04 + CHANGELOG + About +
  문서 `JUN_All/docs/A00340_SelectionTool.md` 갱신.
  #SelectionTool #레이아웃 #QSplitter #CollapsibleBox #접기

> [!summary] `A00110_animTool` v01.27→01.29 — Graph Focus 세로축 Fit value 를 값 범위에 꽉 맞추고, 위/아래 여백(%)을 UI 로 조절
- **v01.28 — 여백 없이 꽉 채우기**: Fit value 세로 값 범위에 주던 위아래 10% 여백을 없애, 구간 내 **최댓값이 뷰 맨 위·
  최솟값이 맨 아래에 닿도록**(`animView` minValue/maxValue = vmin/vmax) 값을 최대한 크게 보이게 함(값이 줄어 잘 안 보이던 문제).
  평평한 구간(min==max)만 예외로 최소 여백 유지.
- **v01.29 — 여백을 UI 로 조절**: 가장자리에 딱 붙는 게 부담스러워 살짝 여백을 두고 싶다는 요청에 따라 **`Value margin (%)`
  스핀박스**(기본 10%, 0~100, 5~10% 권장) 추가. 세로 값 범위에 이 %만큼 위/아래 여백을 두고 프레이밍한다.
  `frame_around_current(..., value_pad_pct)` 로 전달, Auto-Focus·Focus Now 공통, 값 변경 시 즉시 재적용.
- **파일**: `app/core/graph_view_manager.py` · `graph_focus_manager.py`(pad_getter 배선) · `app/ui/main_window.py`(스핀박스+핸들러),
  version 01.29, 문서 `JUN_All/docs/A00110_animTool.md`(§5.7 + 이력) 갱신. `py_compile` 통과, **Maya 실기 검증 완료**.
  #animTool #GraphEditor #FitValue #ValueMargin #animView

> [!summary] `A00340_SelectionTool` v01.02→01.03 — 선택 버튼 색을 카테고리 넘나들며 다중 선택해 일괄 적용(Color Select 모드) + 체크 누락 버그 수정 (Maya 실기 검증 완료)
- **요청 변경**: v01.02 의 "카테고리 단위 일괄 색 변경"을, **카테고리를 넘나들며 임의의 버튼을 골라 칠하는** 방식으로 교체.
- **구현(`app/ui/selection_tab.py`)**: `Color` 바에 **`Color Select`** 토글 추가. 켜면 모든 버튼이 체크형이 되어 클릭이 '선택'
  대신 '체크'로 바뀐다. 카테고리와 무관하게 원하는 버튼을 체크한 뒤 **`Apply Color...`** 로 고른 한 색을 일괄 적용,
  **`Clear Color`** 로 해제. 체크된 버튼은 강조 테두리로 표시되고 재렌더/색적용 후에도 체크 유지, 모드 OFF 시 초기화.
  v01.02 의 카테고리 우클릭 `Set/Reset Buttons Colors` 는 제거(개별 버튼 우클릭 `Set Color...`/`Reset Color` 는 유지).
- **버그 수정**: "버튼 2개를 체크했는데 `Apply Color` 를 누르면 *Check one or more buttons first* 팝업"이 뜨던 문제.
  원인은 체크 상태를 `clicked` 시그널로만 내부 집합(`self._checked`)에 쌓는 구조 — 시그널 인자 신뢰도가 환경(Maya
  PySide2)에 따라 갈려 집합이 비어 있었다. **수정**: ① `clicked`→`toggled` 시그널(새 상태를 확실히 전달),
  ② Apply/Clear 시 렌더된 버튼 위젯의 실제 `isChecked()` 를 다시 읽어(`_sync_checked_from_widgets`) 집합을 맞춤 —
  **화면 버튼 상태를 진실의 원천**으로. 시그널이 누락돼도 빈 집합이 되지 않는다.
- **검증**: `py_compile` + 오프스크린 PySide6 스모크(실제 `btn.click()`·시그널 누락 복구·재렌더 체크 유지) 통과,
  **Maya 실기 검증 완료**. version 01.03 + CHANGELOG + About + 문서 `JUN_All/docs/A00340_SelectionTool.md` 갱신.
  #SelectionTool #버튼색 #ColorSelect #다중선택 #toggled #버그수정

> [!summary] `A00110_animTool` v01.25→01.27 — Graph Focus 세로축 Fit value 보정 + 키 선택 후 `f`(Frame Selection) 존중 (Maya 실기 검증 완료)
- **v01.26 — Fit value 세로축이 항상 맞도록**: 세로 값 범위를 **구간 안 키 값**만으로 구해, 현재 프레임 ±margin
  구간에 키가 없으면(멀리 떨어진 두 키 사이) 세로축을 못 맞추던 문제. 이제 애니메이션 커브 `.output` 을 **구간에 걸쳐
  시간별로 평가**(탄젠트 오버슛 포함)해 min/max 를 구하고 구간 내 키 값도 함께 반영 → 키 유무와 무관하게 세로축이 맞는다.
  커브가 많으면 커브당 샘플 수를 줄여 총 평가 횟수 상한(4000) 유지. `app/core/graph_view_manager.py`.
- **v01.27 — 키 선택 후 `f` 를 존중**: Auto-Focus 켠 상태에서 특정 키를 선택해 `f` 로 그 범위만 보려 하면, 키 선택으로
  발생한 `SelectionChanged` 의 지연 콜백이 뒤늦게 현재 프레임으로 덮어써 원하는 프레임(예: 300f)이 아니라 현재
  프레임(400f)으로 튀던 문제. 자동 프레이밍 콜백이 **선택된 키가 있으면 건너뛰도록**(`cmds.keyframe(q, selected, name)`)
  수정. `Focus Now`·토글 ON 같은 명시적 조작은 영향 없음. `app/core/graph_focus_manager.py`.
- **검증**: `py_compile` 통과 + **Maya 실기 검증 완료**(선택 포커싱·Fit value·`f` 존중 모두 의도대로).
  #animTool #GraphEditor #FitValue #FrameSelection #scriptJob

> [!summary] `A00110_animTool` v01.24→01.25 — Graph Focus 탭 신설(선택 시 그래프 에디터를 현재 프레임 ±margin 으로 프레이밍)
- **요청**: 컨트롤러를 선택하면 전체 키 구간(예: 0~6000f)이 다 보이는 대신, 현재 프레임 기준 앞/뒤 80프레임 정도만
  그래프 에디터에 확대해서 보고 싶다(예: 현재 500f → 420~580f). On/Off 토글 + margin 값(80)을 UI 로 지정.
- **구현**: 7번째 탭 **Graph Focus**. `Auto-Focus on Selection` 체크형 토글 버튼이 켜지면 `SelectionChanged` scriptJob 으로
  선택 변경을 감시하다가, 마야 자체 Auto-Frame 뒤(`evalDeferred(lowestPriority=True)`)에 `animView` 로
  `[현재-margin, 현재+margin]` 을 덮어쓴다. `Frame margin (±)` 스핀박스(기본 80, 사용자 지정), `Fit value` 체크로
  세로(값) 축도 구간 내 키 값 범위에 맞춤(기본 ON), `Focus Now` 로 토글과 무관하게 1회 프레이밍. `closeEvent` 에서 scriptJob 정리.
- **파일**: 새 매니저 `app/core/graph_view_manager.py`(프레이밍 로직) + `graph_focus_manager.py`(scriptJob 라이프사이클),
  `app/core/__init__.py` · `app/ui/main_window.py` 배선, version 01.25, 문서 `JUN_All/docs/A00110_animTool.md`(§5.7) 갱신.
- **검증**: `py_compile` 통과. **Maya 실기 검증 대기.**
  #animTool #GraphEditor #animView #scriptJob #SelectionChanged

> [!summary] `A00340_SelectionTool` v01.01→01.02 — 선택 버튼에 커스텀 색 지정(팔레트+스포이드) + 카테고리 일괄 색 변경
- **요청**: 만든 선택 버튼마다 색을 바꾸고 싶다. A00210 lineage 탭의 `Set Color...`처럼 팔레트를 띄우고, 스포이드로
  다른 색을 집어 적용. 가능하면 여러 버튼 색을 한 번에.
- **구현(`app/ui/selection_tab.py`)**: 버튼 dict 에 선택적 `"color"`(hex) 추가. 색이 있으면 `_button_stylesheet()` 로
  배경/테두리/hover/pressed 스타일 적용, 라벨 글자색은 배경 밝기(`_contrast_text_hex`, 휘도>140→검정)로 자동 결정.
  팔레트+스포이드는 A00210 과 동일하게 `QColorDialog.getColor()` 그대로 사용(내장 **Pick Screen Color** = 스포이드).
- **개별**: 버튼 우클릭 → `Set Color...` / `Reset Color`. **일괄**: 카테고리 우클릭 → `Set Buttons Color...`(그 카테고리
  전체 버튼에 한 색 적용) / `Reset Buttons Colors`. 색은 프로파일 JSON 에 버튼별로 저장돼 세션 유지.
- **검증**: `py_compile` 통과. **Maya 실기 검증 대기.** version 01.02 + CHANGELOG + About + 문서
  `JUN_All/docs/A00340_SelectionTool.md` 갱신.
  #SelectionTool #버튼색 #QColorDialog #스포이드 #일괄변경

---

## 2026-07-03

> [!summary] `A00040_file_exporter_V02` v02.04→02.05 — 메시 제외 실패 재진단(레퍼런스 아님) + shape intermediate 를 1순위로
- **재진단**: 제외 메시가 FBX 에 남던 진짜 원인은 "레퍼런스"가 아니라 **메시 transform 이 잠김/연결/컨스트레인**(리그드
  캐릭터에 흔함)이라 `parent -world` 가 실패한 것. 동일 이름 레퍼런스 그룹이 있는 건 무관. v02.02~04 의 "referenced" 라벨이 오분류였음.
- **수정(`app/core/export_ops.py`)**: shape 기반 제외 타입(mesh 등)은 이제 **shape 의 `intermediateObject` 를 켜는 방식을
  1순위**로 사용 — reparent 를 안 쓰므로 잠금/연결/레퍼런스/네임스페이스와 무관하게 항상 제외됨. shape 없는 타입(joint)만
  unparent. `_safe_parent_to_world` 예외 범위 확대(잠김/연결 포함), WARN 문구에서 "referenced" 제거.
- **한계**: 하위 메시는 shape 만 숨기므로 **빈 transform(null)** 이 FBX 에 남을 수 있음(지오는 빠짐).
- **검증**: `py_compile` + parent 실패 시뮬 단독 테스트(메시가 intermediate 로 제외·원복) 통과. **Maya 실기 재검증 대기.**
  문서 §6.1 + CHANGELOG/version v02.05.
  #FileExporter #메시제외 #intermediateObject #locked #connected #재진단

> [!summary] `A00040_file_exporter_V02` v02.03→02.04 — 레퍼런스 메시가 제외 세팅에도 FBX 에 남던 문제 수정
- **버그**: 이름 같은 레퍼런스가 있는 씬에서 메시 제외로 추출 시, 그룹 하위의 **레퍼런스 메시들**이 그대로 남음
  (`[WARN] could not exclude 51 referenced object(s), still in FBX`).
- **원인**: 레퍼런스 노드는 계층 밖으로 unparent 가 금지되어(v02.02 안전장치가 "제외 불가"로 처리) FBX 에 남음.
- **수정(`app/core/export_ops.py`)**: 제외 노드를 ① 통째로 월드로 빼내기 시도 → ② 실패(레퍼런스)하면 그 타입 **shape 의
  `intermediateObject` 를 켜서** FBX 에서 제외(export 후 원복). FBX 는 intermediate shape 를 안 내보내므로 reparent
  없이 레퍼런스 메시 제외 가능. 헬퍼 `_excluded_shapes_of`/`_set_intermediate` 추가. shape 없는 타입(레퍼런스 joint 등)만
  `could not exclude` 경고로 남음.
- **검증**: `py_compile` + 헬퍼 단독 테스트(shape 선별·setAttr intermediate) 통과. **Maya 실기 재검증 대기.**
  문서 §6.1 + CHANGELOG/version v02.04.
  #FileExporter #레퍼런스 #메시제외 #intermediateObject #FBX #버그수정

> [!summary] `A00040_file_exporter_V02` v02.02→02.03 — 씬 최상위로 빼기 / 계층 유지 선택 체크박스 추가
- **요청**: 세트 오브젝트를 씬 최상위로 빼서 뽑을지, 현재 계층을 유지해 뽑을지 고르는 체크박스. 기본은 최상위로 빼기.
  (`grp>joint_01` 에서 joint_01 이 세트면 → `joint_01` 또는 `grp>joint_01` 로 선택 추출)
- **구현**: Export 섹션에 **Move to scene root** 체크박스(기본 ON). core `export_sets/_export_fbx` 에 `keep_hierarchy`
  인자 추가 — 체크 ON 이면 기존처럼 멤버를 월드로 빼냈다 복원, OFF 면 멤버 이동을 건너뛰고 제자리에서 export.
- **원리**: FBX *export selected* 는 조상(부모) 체인은 포함하되 형제 가지는 제외하므로, 빼내지 않으면 부모 계층만 보존됨.
  타입 필터(그룹 하위 mesh/joint 제외)는 두 모드 모두 그대로 동작.
- **검증**: `py_compile` + 오프스크린 UI 스모크(체크박스 기본값·토글) 통과. **Maya 실기 검증 대기.**
  문서 §5·§7 + CHANGELOG/version v02.03.
  #FileExporter #계층유지 #씬최상위 #FBX #옵션

> [!summary] `A00040_file_exporter_V02` v02.01→02.02 — 레퍼런스 오브젝트(동일 이름 네임스페이스) 추출 시 크래시 수정
- **버그**: 레퍼런스로 같은 이름 오브젝트가 생긴 씬(`Test` + `namespace:Test`)에서 `Test` 를 세트에 넣어 추출하면
  `RuntimeError: Referenced objects parented to referenced objects may not be reparented` 로 크래시.
- **원인**: 깔끔한 계층을 위해 멤버를 월드로 빼내는(`cmds.parent(world=True)`) 단계를 Maya 가 **레퍼런스-밑-레퍼런스**
  노드에는 금지한다.
- **수정(`app/core/export_ops.py`)**: `_safe_parent_to_world` 헬퍼로 빼내기를 try/except 감싸고, 실패한 노드는
  **제자리에서 내보내고 복원도 생략**(성공한 것만 moved 로 추적해 복원). 제외 대상이 레퍼런스라 못 빼면
  `[WARN] could not exclude ... still in FBX` 로그. UUID 식별은 그대로라 동일 이름도 안전.
- **검증**: `py_compile` + 오프스크린 UI 스모크 통과. **Maya 실기 재검증 대기.** 문서 §7 + CHANGELOG/version v02.02.
  #FileExporter #레퍼런스 #네임스페이스 #reparent #버그수정

> [!summary] `A00040_file_exporter_V02` v02.00→02.01 — 타입 필터가 그룹 하위 노드에도 적용되도록 수정
- **버그**: Mesh 체크 해제 시 세트에 **직접 든** 메시는 제외되지만, 세트에 든 **그룹 하위**의 메시는 그대로 추출됨.
- **원인**: 타입 판별이 노드 자신·직속 shape 만 검사 → 그룹(transform, shape 없음)은 mesh 로 안 걸려 통째로 유지되고,
  FBX export 가 그룹을 선택하면 하위 메시까지 자동 포함.
- **수정(`app/core/export_ops.py`)**: `_collect_excluded_in_hierarchy` 추가 — 각 멤버 **계층 전체**를 훑어 제외 타입의
  '최상위' 노드를 찾고, export 직전 월드로 빼냈다가 후 원부모 복원(UUID 기반). 그룹은 유지, 하위 제외 타입만 FBX 에서 빠짐.
  로그의 excluded 목록에 그룹 하위 제외 노드도 합산.
- **검증**: `py_compile` + top-most 수집 로직 단독 테스트 통과. **Maya 실기 재검증 대기.** 문서 §6.1/§7 + CHANGELOG/version v02.01.
  #FileExporter #타입필터 #그룹계층 #FBX #버그수정

> [!summary] `A00040_file_exporter_V02` 신규 — 레거시 파일 익스포터를 PySide 로 재작업 + 타입 필터 추가
- **요청**: A00040_file_exporter 를 PySide 로 재작업해 `A00040_file_exporter_V02` 에 생성(아이콘 재사용).
  내보낼 때 **드롭다운 체크로 노드 타입 포함/제외**를 고르고 싶다(지금은 mesh·joint, 나머지는 항상 포함, 확장 가능).
- **구조**: 아키텍처 (B) 관례대로 `app/core/export_ops.py`(로직) · `app/ui/main_window.py`(화면) 분리,
  A00330 을 템플릿으로. 고유 드롭 파일 `__dragDrop_A00040_V02.py`(셸프 라벨 "FileExporterV2"), 테마 blue_dark.
- **포팅**: Export path · Set's Name/File name TSL · 토큰 네이밍(Custom / Set's Name) · 세트별 FBX
  내보내기(월드로 빼내기→export→원부모 복원). 복원 단계는 **UUID 기반**으로 바꿔 동일 이름 오브젝트도 안전.
- **신규 Type Filter**: `Export` 섹션 "Include Types ▾" 드롭다운에 체크 항목(Mesh/Joint, 기본 전부 체크).
  체크 해제=제외, 목록에 없는 타입(curve/nurbs 등)은 항상 포함. Mesh 해제+Joint 유지 → 메시만 빠지고 나머지 전부 추출.
  타입 추가는 `core.FILTER_TYPES` + `_TYPE_MATCHERS` 두 곳만.
- **검증**: 전체 `py_compile` + 오프스크린 스모크(core 파일명 조립·필터 토글 + UI 생성) 통과. **Maya 실기(FBX
  export/reparent) 검증은 대기.** 문서 [A00040_file_exporter_V02](A00040_file_exporter_V02.md) + CHANGELOG/version v02.00.
  #FileExporter #FBX #타입필터 #PySide #재작업 #UUID

> [!summary] `A00220_BackupTool` v01.11→01.12 · `A00240_PathTool` v01.05→01.06 — 두 툴에 작업표시줄 아이콘 적용
- **요청**: A00210 과 같은 방식으로 이 두 standalone 툴에도 아이콘 생성·적용.
- **아이콘 제작**([taskbar_icon_guide.md](taskbar_icon_guide.md) 방식): 각 테마에 맞춘 SVG →
  QtSvg 사이즈별 렌더 → 멀티사이즈 `.ico`(16~256px)+`.png`.
  A00220 = **green_dark, 초록 문서 스택+백업 순환화살표**; A00240 = **purple_dark, 보라 폴더 계층 트리**.
- **배선(각 툴)**: `app/config/app_meta.py`(고유 `APP_USER_MODEL_ID` + dev/exe 경로 해석) 신설,
  `launch.py` 가 QApplication 전에 AUMID 지정 + `app.setWindowIcon`, `main_window` 창 아이콘,
  `build_exe.bat` 에 `--icon`/`--add-data "icon;icon"`.
- **검증**: `py_compile` + 오프스크린 스모크(두 툴 모두 멀티사이즈 아이콘·고유 AUMID·창 아이콘 non-null)
  통과. 각 CHANGELOG/version.py + docs([A00220_BackupTool](A00220_BackupTool.md)/[A00240_PathTool](A00240_PathTool.md)) §2 갱신.
  #BackupTool #PathTool #아이콘 #작업표시줄 #AppUserModelID #PySide

> [!summary] `A00330_NamingTool` v01.00→01.01 — 씬에 동일 이름 오브젝트가 있어도 리네임이 실패하지 않도록 수정
- **버그**: Naming Dyn 탭에 `joint_01`·`joint_03` 를 리스트업하고, 두 루트 밑에 각각 **같은 이름** `joint_02`
  자식이 있는 상태에서 **Naming Dynamics** 실행 시 `RuntimeError: Invalid path ...` 발생.
- **원인**: TSL 이 **short name** 을 저장 → `listRelatives` 로 받은 자손 이름(`joint_02`)이 씬에서 **모호**해
  `cmds.rename("joint_02", …)` 가 어느 노드인지 특정 못 함. 부모를 rename 하면 자식 경로가 바뀌는 문제도 있음.
- **수정(`app/core/naming_ops.py`)**: rename 을 **UUID 기반**으로 전환(`_to_uuid`/`_rename_by_uuid`). rename 전에
  `(UUID, 새 이름)` 배정을 모두 계산하고, UUID 로 **현재 경로를 매번 다시 해석**해 rename → 동일 이름/계층에도 안전.
  `build_hierarchy_groups` 는 입력을 `ls(long=True)` 정규화 + 자손을 `fullPath` 로 수집. 같은 취약점이 있던
  **Copy Name·Quick Rename**(insert/add/change/trim) 도 동일하게 하드닝.
- **검증**: `py_compile` 통과 + Maya 실기 확인 완료(사용자). 문서 [A00330_NamingTool](A00330_NamingTool.md) §7
  갱신 + CHANGELOG/version.py v01.01.
  #NamingTool #리네임 #UUID #동일이름 #버그수정

> [!summary] Standalone Qt 툴 작업표시줄 아이콘 재사용 가이드 문서 작성 (docs/taskbar_icon_guide.md)
- **배경**: A00210 에서 확립한 "작업표시줄 아이콘 만들기" 방식을 앞으로 다른 standalone 툴에도
  재사용하도록 문서로 남김(사용자 요청).
- **내용**: ① SVG→QtSvg 사이즈별 렌더→멀티사이즈 `.ico`(각 사이즈 SVG 직접 렌더·base=최대 프레임
  주의) ② `setWindowIcon` ③ **AppUserModelID 를 QApplication 생성 전 지정**(터미널 python.exe
  아이콘 대체의 핵심) + `app_meta.py`/`build_exe.bat` 배선·체크리스트. Maya 셸프 아이콘([icon_plan.md])과
  맥락 구분·상호 링크.
- **산출물**: [taskbar_icon_guide.md](taskbar_icon_guide.md). 메모리에도 방법 저장.
  #가이드 #작업표시줄 #AppUserModelID #PySide #ico #docs

> [!summary] `A00210_FileManager` v01.26→01.27 — 앱/작업표시줄 아이콘 추가 (터미널 실행 시 python 아이콘 대체)
- **요청**: 이 툴(터미널에서 `python launch.py` 로 실행)의 작업표시줄 아이콘을 적절히 바꾸고 싶다.
- **아이콘 제작**: blue_dark 테마에 맞춘 **파란 폴더 + 기록 카드 + 동기화 뱃지** SVG 를 그려
  (`icon/A00210_FileManager.svg`) QtSvg 로 사이즈별 렌더 → **멀티 사이즈 `.ico`(16~256px)** + `.png` 생성.
- **연결(`launch.py`)**: `app.setWindowIcon` + 창(`main_window`)에도 아이콘 지정. 터미널 실행 시 프로세스가
  `python.exe` 라 그대로면 python 아이콘이 떠서, Windows **AppUserModelID**
  (`Dnable.JUN.A00210.FileManager`)를 QApplication 생성 전에 지정해 앱 아이콘이 작업표시줄에 뜨게 함.
  경로 해석은 dev·PyInstaller 양쪽 대응(`app/config/app_meta.py`), `build_exe.bat` 에 `--icon`/`--add-data` 추가.
- **검증**: `py_compile` + 오프스크린 스모크(아이콘 경로/멀티사이즈/창 아이콘 non-null) 통과. 문서
  [A00210_FileManager](A00210_FileManager.md) §2 + CHANGELOG/version.py v01.27 갱신.
  #FileManager #아이콘 #작업표시줄 #AppUserModelID #PySide #ico

> [!summary] `A00220_BackupTool` v01.10→01.11 — 저장 톡 점프가 Windows 10 에서도 빨간색으로 표시되도록 수정
- **배경**: 대상 파일 저장 순간 공룡이 빨갛게 짧게 톡 점프하는데, **Win11 에선 빨갛게 되지만 Win10 에선
  점프만 하고 색이 안 변함**.
- **원인**: 저장 강조색을 **OS 팔레트 하이라이트**(`palette().highlight()`)에서 가져와서 — 이 색이
  Windows 버전마다 다르다(Win11=빨강 계열, Win10=시스템 파랑 등). 그래서 Win10 에선 빨강이 안 나왔다.
- **수정(`app/ui/dino_widget.py`)**: 팔레트 의존을 버리고 **고정 빨강 `#E53935`**(`_SAVE_ACCENT_COLOR`)
  으로 직접 그린다 → 모든 OS 에서 동일하게 빨간 톡 점프. 점프 타이밍·높이는 그대로.
- **검증**: `py_compile` 통과(실기 확인은 실행으로). 문서 [A00220_BackupTool](A00220_BackupTool.md)
  §5 + CHANGELOG/version.py v01.11 갱신.
  #BackupTool #저장감지 #Windows10 #팔레트 #강조색 #버그수정

---

## 2026-07-02

> [!summary] Kangaroo 스킨 웨이트 전이 코드 심층 분석 문서 작성 (docs/study)
- **요청**: Kangaroo 플러그인이 스킨 웨이트를 전이하는 방식을 코드 집중 분석하고, Maya 기본
  `Copy Skin Weights` 와 뭐가 다른지 정리한 문서를 `docs/study` 에.
- **분석**(외부/읽기전용 코드, 수정 없음): `kangarooTabTools/weights.py`(`transferSkinCluster`·
  `moveSkinClusterWeights`·`intTransferSkinCluster`), `kangarooTools/barycentric.py`
  (`getVertexCoordinates`·`getBarycentricCoords`), `patch.py`(`setSkinClusterWeights` + enum),
  `kt_findClosestPoints.mll`(C++). 핵심: ① "전이"가 실은 **Transfer(메시→메시)** 와
  **Move(조인트→조인트)** 두 기능 ② Transfer = C++ 최근접점 질의 → **면 무게중심 보간**(쿼드 전용
  넓이기반) → **numpy 벡터화**, 멀티소스 per-vertex 최근접 선택, **이름 기반 인플루언스 union/매핑**,
  경계 스무딩·prune·normalize·skinCluster 자동생성 후처리 통합 ③ Maya `copySkinWeights` 와 대응
  원리는 같으나 쿼드 정확도·멀티소스·이름 통합·후처리 통합·본→본 Move 로 차별화.
- **산출물**: [kangaroo_skinWeight_transfer_analysis.md](study/kangaroo_skinWeight_transfer_analysis.md)
  (파일·라인 참조 포함). 기존 [skinWeight_transfer_workflow.md](study/skinWeight_transfer_workflow.md)
  는 워크플로우 관점, 이번 문서는 코드 레벨 심층 분석으로 상호 링크.
  #Kangaroo #skinWeights #Transfer #barycentric #copySkinWeights #코드분석 #docs

> [!summary] `A00110_animTool` v01.23→01.24 — Always on Top(Pin) 토글 버튼 추가 (A00340 패턴 이식)
- **요청**: A00340_SelectionTool 처럼 창을 다른 마야 창 위에 고정하는 Pin 버튼을 A00110 에도.
- **구현(`app/ui/main_window.py`)**: 기존 `setMenuBar` 방식을 **QHBoxLayout 헤더 행**(메뉴 바 좌 +
  Pin 버튼 우)으로 바꾸고, 체크형 `Pin` 버튼(`setFixedSize(72, 28)`) 추가. `toggle_always_on_top()`
  이 `Qt.WindowStaysOnTopHint` 토글 + `show()` 재호출, ON 이면 라벨 `Pinned`·로그 기록. 이 툴은 기본
  정상 Z-order 라 필요할 때만 켜는 방식. A00340 과 동일 패턴이라 위치·크기 불변.
- **검증**: `py_compile` 통과(실기 확인은 마야 `run(True)` 리로드로 예정). 문서
  [A00110_animTool](A00110_animTool.md) v01.24 노트 + version.py v01.24 갱신.
  #animTool #AlwaysOnTop #Pin #WindowStaysOnTopHint #PySide

> [!summary] `A00210_FileManager` v01.25→01.26 — Store Repo / Shared Folder 입력을 한 칸으로 병합(모드별 경로는 각각 기억)
- **요청**: Source Mode(Remote/Local)마다 따로 있던 **Store Repo**·**Shared Folder** 입력 두 칸을
  하나로 병합해도 정상 동작할지 → 정상 동작하면 그대로 반영.
- **판단**: 단순히 "한 칸=한 경로"로 합치면 한 프로파일 안에서 모드를 오갈 때 상대 모드 경로 기억을
  잃는다. 그래서 **입력 칸은 하나로 보이되(라벨이 모드 따라 Store Repo↔Shared Folder 전환) 모드별
  경로는 각각 기억**하는 방식으로 구현 → UI 병합 + 동작·프로파일 호환성 무손실.
- **구현(`app/ui/main_window.py`)**: 데이터 폴더 입력을 `ipf_store_dir` 한 칸으로 통합(로컬 전용
  `ipf_local_dir`/`lbl_local`/`btn_local` 제거). 모드별 경로를 `self._path_values{git,local}` 에 보관,
  Source Mode 전환 시 떠나는 모드로 칸 값 저장→오는 모드 값 로드(`_on_source_mode_changed`). 라벨/
  플레이스홀더/툴팁은 `_apply_source_mode` 가 모드에 맞춰 전환, 데이터 폴더 칸은 두 모드 모두 항상 활성
  (git 전용 Remote/Branch/URL/Pull/Push 만 토글). `_load_prefs_to_ui`/`_collect_prefs` 는 여전히 프로파일
  `store_dir`/`local_dir` 두 키로 저장/복원 → **마이그레이션 불필요**.
- **검증**: `py_compile` 통과(실기 확인은 실행으로 예정). 문서
  [A00210_FileManager](A00210_FileManager.md) 개념표/화면구성/사용흐름 + CHANGELOG/version.py v01.26 갱신.
  #FileManager #SourceMode #StoreRepo #SharedFolder #UI병합 #프로파일호환

> [!summary] `A00340_SelectionTool` v01.00→01.01 — 창을 다른 마야 창 위에 고정하는 Always on Top(Pin) 토글 추가
- **요청**: 툴 UI 가 다른 마야 창들보다 항상 위에 뜨도록 하는 토글 버튼.
- **구현(`app/ui/main_window.py`)**: 체크형 `Pin` 버튼을 **상단 헤더 행**(QHBoxLayout: 메뉴 바 좌 +
  버튼 우)에 배치. `toggle_always_on_top()` 이 `Qt.WindowStaysOnTopHint` 를 켜고/끄고,
  플래그 변경 시 창이 숨는 Qt 특성을 피하려 **`show()` 재호출**. ON 이면 라벨 `Pinned`, 로그에도 기록.
- **버튼 배치 다듬기**: 처음엔 메뉴 바 코너 위젯(`setCornerWidget`)으로 뒀으나 토글 시 위치/크기가
  튀어(코너 geometry 재계산) **헤더 행 레이아웃 + 고정 크기(`setFixedSize(72, 28)`)** 로 변경 →
  `Pin`↔`Pinned` 토글에도 위치·크기 불변, 글씨 잘림 없음.
- **검증**: `py_compile` 통과, **마야 실기 확인 완료**. 문서
  [A00340_SelectionTool](A00340_SelectionTool.md) §사용법 + CHANGELOG/version.py v01.01 갱신.
  #SelectionTool #AlwaysOnTop #Pin #WindowStaysOnTopHint #PySide

> [!summary] `A00220_BackupTool` v01.09→01.10 — 저장 감지(공룡 톡 점프)가 Windows 10 에서도 동작하도록 mtime 폴링 fallback 추가
- **배경**: 파일 저장 순간 공룡이 빨간색으로 짧게 점프하는 애니(`notify_save`)가 **Windows 11 에서는
  되는데 Windows 10 에서는 안 됨**.
- **원인**: 저장 감지가 `QFileSystemWatcher.fileChanged` 신호에만 의존 — 이 신호는 Win10 이나 임시파일
  교체식(atomic replace) 저장에서 안정적으로 발화하지 않아 저장 순간을 놓쳤다(애니 자체는 순수 Qt 라 무관).
- **수정(`main_window.py`)**: **0.5초 mtime 폴링 fallback**(`_save_poll_timer`, 감시 중일 때만 동작) 추가.
  `_start_watching` 에서 mtime 기준선(`_watch_mtimes`)을 잡고, `_poll_saves` 가 변화한 파일을 저장으로 감지.
  기존 watcher(`_on_fs_changed`)와 폴링을 **공통 핸들러 `_on_save_detected`** 로 합치고 **mtime 으로 중복
  발화 제거** → Win11(watcher 정상)에서도 톡 점프는 한 번만. 백업용 `_last_mtimes` 와 감지용 `_watch_mtimes`
  는 별개라 간섭 없음.
- **검증**: `py_compile` 통과, **Windows 10 실기 확인 완료**. 문서 [A00220_BackupTool](A00220_BackupTool.md)
  §5-1 + CHANGELOG/version.py v01.10 갱신.
  #BackupTool #저장감지 #Windows10 #QFileSystemWatcher #폴링 #버그수정

> [!summary] `A00210_FileManager` v01.24→01.25 — Path Structure 트리 다중 선택 체크박스 토글이 반복 클릭에도 선택 유지
- **배경**: v01.24 의 다중 선택 일괄 토글이 **첫 클릭만** 선택을 유지하고, 두 번째 클릭부터 선택이
  한 행으로 붕괴됐다.
- **원인**: `itemChanged`(체크박스 토글)는 마우스 **릴리스** 시점에 발생하는데, 그때는 이미 Qt 가 선택을
  클릭한 한 행으로 붕괴시킨 뒤라, 그 시점 `selectedItems()` 로는 붕괴 전 다중 선택을 알 수 없었음.
- **수정**: 트리 뷰포트에 **이벤트 필터**를 달아 **마우스 누름(press) 시점**(붕괴 전)에 선택을 `_presel`
  로 캡처. 핸들러는 키보드 토글이면 온전한 `selectedItems()`, 마우스면 `_presel` 을 써서 대상 폴더 전체를
  일괄 토글(`_apply_state_to_rels`) 후 `singleShot(0)` 로 선택 복원. 매 클릭마다 press 시점에 (복원된)
  선택을 다시 캡처하므로 반복 클릭에도 유지됨.
- **검증**: `py_compile` 통과, **PySide 실기 확인 완료**. CHANGELOG/version.py v01.25.
  #FileManager #PathStructure #다중선택 #Qt #버그수정

> [!summary] `A00340_SelectionTool` v01.00 신규 — 마야 선택 오브젝트를 **버튼 하나로 다시 선택**하는 in-Maya PySide 툴
- **배경**: A00240_PathTool 처럼 버튼을 자유롭게 추가·삭제·순서변경 하되, **경로 열기 대신 마야 오브젝트를
  다시 선택**하는 툴이 필요했다.
- **개념**: **Selection 버튼**(현재 선택을 캡처 → 클릭 시 그 오브젝트 재선택, 이름변경/삭제된 것은 건너뛰고
  로그) · **Category**(버튼 그룹) · **Profile**(캐릭터/에셋별 버튼 세트, `data/profiles/<name>.json`).
  `Add` 토글 시 현재 선택에 누적.
- **구조**: 구성/편집 흐름(profile→category→button, 우클릭 Move Up/Down·Rename·Delete·Change Category·
  Update/Add Objects)은 **A00240_PathTool**, 마야 연동(launch `run()`·`__dragDrop_A00340.py` 셸프 설치·
  Maya parent 창·blue_dark 테마)은 **A00310_SearchTool** 에서 이식. core 분리: `prefs.py`(순수 JSON, DCC 비의존)
  + `maya_select.py`(capture/select). 아이콘(파란 선택 마퀴+커서) png/svg 제작.
- **검증**: **Maya 실기 확인 완료**. 문서 [A00340_SelectionTool](A00340_SelectionTool.md) + CHANGELOG +
  README 목록 등록. version.py v01.00.
  #SelectionTool #선택 #리깅 #애니메이션 #Maya #PySide #신규툴

> [!summary] `A00210_FileManager` v01.23→01.24 — Path Structure 탭: Preview 트리뷰(파일 토글·Expand) + 깊이/선택 재생성
- **배경**: Path Structure 탭이 ① Preview 를 ASCII 텍스트로만 보여주고 ② Save/Recreate 가 대상 경로의
  **모든 하위**를 통째로 저장·생성해서, 원하는 깊이·경로만 고르기 어려웠음. A00240 PathTool 의 Tree 탭처럼
  트리로 보고, 깊이(정수)와 경로(체크박스)를 골라 재생성하고 싶다는 요청.
- **Preview 트리뷰(feature 1)**: `QPlainTextEdit` → **`QTreeWidget`** 로 교체. **Show files** 체크박스
  (기본 **OFF**, 켜면 로컬 파일시스템에서 실제 파일도 표시 — 확인용, 재생성 대상 아님) + **Expand** 버튼
  (큰 창, 체크 상태 반영). 폴더/파일 표준 아이콘.
- **깊이·선택 재생성(feature 2)**: Save 그룹의 *Recursive* 체크박스 → **Capture Depth** 스핀박스
  (1=최상위만, 0=All)로 교체. Saved 그룹에 **Depth** 스핀박스(표시 겸 Recreate 깊이 제한, 0=All) +
  트리 **폴더별 체크박스**(해제 시 Recreate 제외; 루트=base 는 항상 생성, 체크된 자식의 상위는 자동 생성).
- **다중 선택 일괄 토글**: 트리를 **ExtendedSelection** 으로 바꿔 Shift/Ctrl 다중 선택 → 선택 항목 중
  하나의 체크박스를 누르면 선택된 폴더 전체가 동시에 체크/해제(`_syncing_checks` 재진입 가드).
  Saved Structures **목록 높이 축소**(maxHeight 120, stretch 0)로 남는 세로 공간을 Preview 트리에 배분.
- **core `path_structure.py`**: `PathStructure.max_depth` 필드 추가(구버전 JSON `recursive`→깊이 매핑으로
  하위호환: True=0/All, False=1/top). `_collect_folders(max_depth)` 로 깊이 캡처, `limit_depth()`,
  `build_structure_tree(structure, base_abs, show_files, max_depth)`(폴더 트리 + 실파일 병합),
  `recreate(..., folders=None)`(선택 목록만 생성, 중복 제거).
- **검증**: 변경 `.py` `py_compile` 통과 + 코어 로직 테스트(깊이 캡처/limit_depth/트리 빌드/파일 병합/
  구버전 from_dict/선택·깊이 recreate) 통과. **PySide 실기 확인 완료**.
- 문서: 가이드 [A00210_FileManager](A00210_FileManager.md) §4-C 갱신 + CHANGELOG/version.py v01.24.
  #FileManager #PathStructure #트리뷰 #깊이 #선택재생성 #Qt

## 2026-07-01

> [!summary] `A00220_BackupTool` v01.09 — 상태 공룡에 **저장 감지 순간(강조색 톡 점프)** 표현 추가: 저장 순간 ↔ 백업 순간(360° 스핀) 시각 구분
- **요청**: 공룡이 지금은 '툴 작동 중'·'백업 실시' 두 상태만 표현. Save Delay(v01.08) 로 *저장 순간* 과
  *백업 순간* 이 벌어졌으니, **사용자가 파일을 저장한 순간**을 눈으로 구분할 표현을 추가. → 스타일은
  사용자 확정 **"강조색 톡 점프"**.
- **dino_widget.py**: 스핀(`_spin_t`) 패턴을 미러링한 저장 펄스 상태 `_save_t` + `notify_save()` 추가.
  상수 `_SAVE_TICKS=12`(~0.4s, 자동 점프 18틱보다 스냅)·`_SAVE_PEAK_CELLS=5`(7칸보다 낮게). `_tick`
  우선순위 사다리 `스핀 > 저장 > 점프 > 자동점프`. paintEvent 비-스핀 경로에서 `_save_t` 활성 시
  스프라이트를 **테마 하이라이트색**(폴백 `#4CAF50`)으로 그리고 `_save_offset_px()` 만큼 톡 띄움.
  다리는 점프 포즈. 죽은 코드 `hop()`(v01.06 이후 미사용) 제거.
- **main_window.py**: 저장 감지 핸들러 `_on_fs_changed` 에서 백업 예약 직후 `self.dino.notify_save()`
  호출(감시 중 = Auto Backup 모드에서만). stale hop 주석/헤더 갱신. 버전 01.08→01.09.
- **검증**: 전 파일 `ast.parse` + 오프스크린 PySide6 실제 인스턴스화 단위검증 6/6 PASS(펄스 시작·종료,
  스핀 우선 양보, 저장 점프 높이<자동 점프, 정지 시 초기화, `_on_fs_changed`→notify_save+예약).
- **문서**: [A00220_BackupTool](A00220_BackupTool.md) 5장 Dino 상태표에 '저장 감지=강조색 톡 점프' 행 +
  저장/백업 순간 구분 설명, CHANGELOG 01.09.
  #백업 #UI #공룡애니메이션 #standalone

> [!summary] `A00145_RigConnect` v01.10 — Match 탭에 레거시 `DOOTOOL_PY_TOOL_Match.py` 의 체크박스 옵션(Translation/Rotation/Scale/Parent) 이식
- **요청**: 사내 레거시 `DOOTOOL_PY_TOOL_Match.py`(Doosup Jung, 2018)의 Match 옵션 체크박스를 A00145 Match 탭에
  이식하되, 동작·기본 체크 상태를 원본과 동일하게. 단 **Rotate Order / Rotate Axis 는 제외**(A00145 는 월드 행렬
  기반 매칭이라 무의미).
- **이식 항목/기본값**(원본 준수): Translation(ON) / Rotation(ON) / Scale — world space(OFF) /
  Parent Followers to Targets(OFF).
- **core(`match_manager.py`)**: `match()` 에 `translate/rotate/scale/parent` 인자 추가. transform 타겟은
  `matchTransform` 의 position/rotation/scale 플래그로 켜진 채널만 월드 매칭(원본 xform 방식 대신 rotateOrder-safe
  통일 유지). 원본 Scale(null+scaleConstraint 로 월드 스케일 읽기)은 `matchTransform scale`(월드 스케일 일치)로 대체.
  Parent 는 매칭 완료 후 별도 패스로 `_parent_one`(컴포넌트면 소유 transform 아래로, 자기자신/이미 자식이면 스킵,
  월드 위치 보존). vertex/mesh/cluster/component 특수 처리는 translate/rotate 로 게이팅(둘 다 꺼지면 vertex 샘플링도 스킵).
- **ui(`main_window.py`)**: Match 탭에 "Match Options" 그룹(4개 체크박스, 툴팁) 추가. `on_match` 가 값을 읽어 전달,
  채널 전무 시 경고 후 no-op, 로그에 적용 채널 `[TRSP]` 표기. About/버전 01.09→01.10 갱신.
- **검증**: 전 파일 `ast.parse` + 페이크 `maya.cmds` 로 core 단위검증 10/10 PASS(플래그별 matchTransform kwargs,
  parent→owner, already-child 스킵, count/skip). Maya 실기 대기.
- **문서**: 가이드 [A00145_RigConnect](A00145_RigConnect.md) Match 절에 옵션 설명 추가.
  #리깅 #매칭 #이식 #DOOTOOL

> [!summary] `A00220_BackupTool` v01.08 — Auto Backup 에 **저장 후 지연(Save Delay)** 도입: 크래시로 손상된 파일이 정상 백업을 덮어쓰는 사고 방지
- **문제/진단**: PC 가 사고로 자주 종료되는데, 종료 시점에 저장 중이던 Maya 파일이 **손상된 채 디스크에
  남는다**. 기존 Auto Backup 은 저장을 감지하자마자(~300ms 디바운스) 백업해, 그 손상 파일이 정상 백업본을
  덮어써 버렸다. → **10초 지연**이 해결책이 되는지 진단: 백업 툴이 크래시하는 PC 와 **운명을 함께하므로**,
  저장 후 지연 백업을 in-process 타이머로 예약해 두면 크래시 시 예약 백업도 함께 사라져 손상 파일이
  백업되지 않는다(직전 정상본 보존). "저장 후 N초 생존 = 정상 저장" settle 휴리스틱 — **타당**하다고 판단, 구현.
- **구현**: 저장 감지(`_on_fs_changed`) 시 즉시 복사 대신 **파일별로 `{path: 지금+Delay}` 예약**. 1초 폴링
  `_process_pending_backups` 가 due 지난 파일만 백업(예약 있을 때만 타이머 동작). 지연 중 재저장되면 그
  파일만 재예약(settle). 기존 300ms 디바운스(`_debounce_timer`/`_pending_changes`/`_flush_pending_changes`)
  제거. 주기 Interval fallback 은 그대로.
- **UI/설정**: Settings 에 **Save Delay(sec)** 스핀박스(기본 10, 0~600, 0=다음 폴링에 백업) 추가.
  prefs `save_delay` 영속화(+ 기존 `auto_backup` 도 DEFAULTS 에 명시). 버전 01.07→01.08.
- **검증**: 전 파일 `ast.parse` 통과(표준 라이브러리 로직, standalone). 실사용 검증 대기.
- **문서**: [A00220_BackupTool](A00220_BackupTool.md) 5-1 절에 지연 원리/보완(Version Up) 추가, CHANGELOG 01.08.
  #백업 #크래시복구 #standalone #PySide

## 2026-06-30

> [!summary] `A00170_driverTool` v01.07 — AttachCrv 탭에 **Distribute(균일 분배)** 모드 추가 (`ref_01.mel` 원래 동작 복원)
- **배경**: AttachCrv 탭은 그동안 TSL 의 *기존* 오브젝트를 커브 최근접 지점에 붙이는 동작만 있었다. 원본
  `ref/ref_01.mel`(attachDriverOnCurve, Doosup Jung)에 있던 **"양의 정수 N 만큼 새 오브젝트를 커브에 균일
  배치"** 기능을 추가해 달라는 요청.
- **core(`app/core/attach_curve.py`)**: `build_attach_uniform(curve, count, driver_type, full_range, ...)`
  신규(= `run_attach_uniform`). 파라미터 분배는 ref `makeParameterValueList` 그대로 — `count==1`→구간 중앙,
  **full_range ON**→`division=count-1`(양 끝 정확히 포함, 열린 커브), **OFF**→`division=count`(마지막이 끝
  직전, 주기/닫힌 커브 seam 중복 방지). Locator/Null 드라이버 생성 → `<curve>_<NN>_drv`(0 패딩) 리네임 →
  기존 `_attach_one()` 을 `param=` 인자로 재사용(=None 이면 closest, 값 주면 그 파라미터). 매트릭스 네트워크
  (pointOnCurveInfo→fourByFourMatrix→multMatrix→decomposeMatrix)·orient·norCrv·set 은 Closest 모드와 공유.
- **UI(`app/ui/main_window.py`)**: AttachCrv 탭에 "Distribute new drivers uniformly" 그룹(Count spin /
  Driver Type 콤보 / full-range 체크 / **Distribute Drivers on Curve** 버튼) + `on_atc_distribute` 핸들러.
  orient/Aim Axis/norCrv/set 옵션은 두 모드 공유. About 갱신, 버전 01.06→01.07.
- **검증**: 전 파일 `ast.parse` 통과. Maya 실기 대기.
- **문서**: 가이드 [A00170_driverTool](A00170_driverTool.md) AttachCrv 절에 Distribute 사용법 추가.
  #리깅 #커브어태치 #이식 #PySide

> [!summary] `A00320_ARKitCurveTool` 신규 — Unreal "Add ARKit Curves to Skeleton" 분석 + 재현 코드/가이드 정리
- **배경**: Unreal Content Browser 에서 Skeleton 우클릭 시 나오는 *"Add ARKit Curves to Skeleton"*(선택
  스켈레톤에 ARKit 52 블렌드셰이프 커브 메타데이터 일괄 등록) 기능이 어떻게 구현됐는지 분석하고, 같은 동작을
  **직접 만드는 방법**을 정리해 달라는 요청. (Maya 셸프 툴이 아니라 Unreal 용 참조/이식 코드 모음)
- **분석**: 기능은 엔진 수정이 아니라 프로젝트 플러그인(MANUEditor=메뉴 익스텐더 / MANUAnimationEd=커브 추가
  로직 / MANUAnimation=52개 이름)에 분업 구현. 핵심 API `USkeleton::AddCurveMetaData()` 는 `UFUNCTION` 이
  아니라 **Python/BP 미노출** → 두 접근 제공.
- **코드(`tools/A00320_ARKitCurveTool/`)**: ① **하이브리드(B-2, 권장)** — 얇은 C++ 래퍼
  `MANUSkeletonCurveLibrary.h/.cpp`(52 이름 자체 포함, 외부 모듈 의존 없음)를 BP/Python 에 노출 +
  `add_arkit_curves.py`(실행) + `init_unreal.py`(ToolMenus 우클릭 메뉴 자동 등록). ② **빌드-프리** —
  `nobuild_arkit_curves.py`(API discover + 커브 포함 애니 임포트 / `unreal.AnimationLibrary` 경로, 컴파일 0).
- **바닐라 호환**: 스톡 `unreal` API 만 사용 — 커스텀 엔진 비의존(바닐라 UE 5.5 동작).
- **문서**: 학습 노트 [분석](study/Add_ARKit_Curves_to_Skeleton_분석.md) ·
  [B안 구현가이드](study/Add_ARKit_Curves_B안_구현가이드.md), 가이드 [A00320_ARKitCurveTool](A00320_ARKitCurveTool.md)
  신규 작성, README 인덱스 등록.
  #ARKit #Unreal #스켈레톤커브 #LiveLink #이식 #참조코드

> [!summary] `A00330_NamingTool` v01.00 신규 — 레거시 `JUN_PY_NamingTool_V03_04`(maya.cmds) PySide 이식 + ref_01.mel 3번째 탭 통합
- **배경**: 레거시 네이밍 툴은 절차형 `cmds` UI 2탭(Naming Dynamics, Copy name)이었다. 이를 다른 툴들과
  동일한 **PySide 창 + QTabWidget** 구조로 이식하고, 현장용 빠른 리네임 MEL(`ref/ref_01.mel`)을 **3번째 탭**으로 합쳤다.
- **구조**: `A00310_SearchTool` 컨벤션 그대로 — `__dragDrop_A00330.py`(셸프 설치) / `launch.py`(green_dark 테마) /
  `app/{config,core,ui}`. 리스트 UI 는 공용 위젯 `JUN_mod_tsl_qt_v01` 재사용, 로직은 `app/core/naming_ops.py`(thin UI).
- **탭**: ① **Naming Dyn** — `T1_T2_T3_Idx1_Idx2` 계층 토큰 리네임(Idx1=루트 그룹별, Idx2=항목별 증가, 0 패딩,
  transform 자손만). ② **Copy Name** — Base leaf 이름(+Prefix)을 Targets 에 순서대로 적용. ③ **Quick Rename**(신규,
  `ref_01.mel` 이식) — Front Insert / Change New(+인덱스, 10 미만 0 패딩) / Last Add / `-1 Front`·`-1 Rear` / All Apply.
  모든 작업은 단일 Undo(`undo_chunk`)로 묶음.
- **정정/개선**: 원본 `is 0`(Py3 경고) → `== 0`; 이름 처리 시 네임스페이스(`:`)까지 제거해 rename 안정성 향상.
- **아이콘**: green 테마 네이밍/태그 아이콘 생성(svg + png 64/32).
- **검증**: 전 파일 `py_compile` 통과. 가짜 `maya.cmds` 주입 단위 테스트 **13/13 PASS**(인덱스 패딩·10 경계·
  네임스페이스 제거·계층 transform 필터링·copy 개수 불일치 경고). Maya 실기 대기.
- **문서**: 가이드 [A00330_NamingTool](A00330_NamingTool.md) 신규 작성, README 인덱스 등록.
  #namingTool #리네임 #PySide #이식 #ref이식 #신규툴

> [!summary] `A00040_file_exporter` v01.01→01.03 — 월드 최상위(부모 없음) 오브젝트 내보내기 에러 수정 + 인덱스 정렬/비교 정리 (Maya 실기 검증 완료)
- **배경**: 세트 내보내기 시 멤버가 **다른 오브젝트의 차일드가 아니면**(월드 최상위)
  `get_parents()` 의 `cmds.listRelatives(sel_obj, parent=True)` 가 `None` 을 반환 →
  `[0]` 인덱싱에서 `'NoneType' object is not subscriptable` 로 내보내기 실패.
- **수정(`utility.py`)**: ① `get_parents()` — 부모가 없으면 `None` 으로 표시(`prnt[0] if prnt else None`).
  ② 복원 단계 — 월드 최상위(`None`)였던 오브젝트는 그대로 두고 reparent 건너뜀.
  ③ **인덱스 정렬**: `cmds.parent(members, world=True)` 가 *이미 월드에 있던* 오브젝트를
  반환에서 제외해 `objs_out`↔`parents_origin` 가 어긋나던 문제를, 멤버를 하나씩 월드로 빼내며
  `(새 이름 ↔ 원래 부모)` 짝을 `zip` 으로 유지하도록 재작성. ④ 재부모 루프의 바깥 루프 변수
  `i` 섀도잉 제거, `len(...) is 0` → `== 0` 비교 정정.
- **결과**: 추출 대상이 다른 오브젝트의 차일드든 월드 최상위든 모두 정상 내보내기.
- **문서**: 가이드 [A00040_file_exporter](A00040_file_exporter.md) 신규 작성.
- **검증**: Maya 실기 확인 완료(월드 최상위 오브젝트 내보내기 정상). 헤더/타이틀 v01.03.
  #fileExporter #FBX #export #objectSet #버그수정

---

## 2026-06-29

> [!summary] `A00170_driverTool` v01.05→01.06 — AttachCrv 탭에 norCrv(노멀 커브) 방향 옵션 추가(ref_01.mel 원본 방식)
- **배경**: 원본 `ref/ref_01.mel`(attachDriverOnCurve, by Doosup Jung)은 별도 **norCrv** 직선 커브를
  만들어 커브에 어태치된 오브젝트들의 **up(위) 방향**을 정했다. 현재 AttachCrv 탭은 norCrv 없이 월드 +Y
  시드의 자족 직교 프레임만 썼음. 원본 방식(norCrv)을 옵션으로 추가하고 **기본값으로** 삼고 싶다는 요청.
- **구현(core `attach_curve.py`)**: `build_attach_to_closest(..., use_normal_curve=True, normal_curve_length=1.0)`
  추가. orient + use_normal_curve 면 `_create_normal_curve()` 로 attachCrv 밑에 직선 norCrv(원점→(0,±len,0),
  +X/-X 부호) 1개를 만들어 `matchTransform`(pos+rot) 후 parent. 오브젝트마다 norCrv 용 `pointOnCurveInfo` 를
  하나 더 만들어 **fourByFourMatrix X=attachCrv 접선 / Y=norCrv 접선 / Z=norCrv 노멀**(-X 면 세 행 반전)로 구성
  — ref 노드 구성 그대로. 반환에 `norcrv` 추가(4-튜플). use_normal_curve=False 면 기존 자족 프레임 유지.
- **UI(main_window)**: AttachCrv 탭에 **Create Normal Curve (norCrv)** 체크박스(기본 ON) + **norCrv Length**
  스핀박스 추가. Orient OFF 면 둘 다 비활성(`_atc_sync_orient_enabled`). 빌드 후 생성된 norCrv 이름을 로그에 표시.
  About/가이드 [A00170_driverTool](A00170_driverTool.md) §4.3 갱신.
- **검증**: 변경 `.py`(attach_curve/main_window) `py_compile` 통과(Maya 실기 대기). version.py v01.06.
  #driverTool #AttachCrv #norCrv #리깅 #커브어태치 #이식

> [!summary] `A00080_KWI_creator_V03` v01.01→01.02 — 언리얼 Kawaii Physics Bone Constraints Data Asset 내용 생성 "Constraints" 탭 추가(두 탭 구조)
- **배경**: 언리얼에서 `dyn_asset_side_0[1-7]_0[1-5]` / `dyn_asset_side_0[2-8]_0[1-5]` 두 줄 브래킷
  패턴으로 KawaiiPhysics 제약(Data Asset) 내용을 자동 생성하지만 **가끔 에러**가 나서, Maya 에서 동일
  텍스트를 직접 만들어 클립보드로 복사하려 함.
- **Tab 2 "Constraints"**(신규): `(Chain A, Chain B)` 브래킷 패턴 쌍 입력 → **인덱스 1:1 zip** → 합본.
  **+ Add pair** 로 여러 쌍을 받아 하나의 출력으로 병합. `[a-b]` 는 정수 a..b 로 확장(왼쪽 브래킷이
  바깥 루프), 리딩 `0` 은 리터럴이라 **제로패딩 없음**(단일자리 가정). 두 체인 개수 불일치 시 에러.
  출력 = `(` + `(BoneReference1=(BoneName="A"),BoneReference2=(BoneName="B"))` 콤마결합 + `)`,
  미리보기 + 클립보드 + `0020_out/A020_LDA_constraint_out.py` 기록.
- **Tab 1 "KWI Nodes"**: 기존 노드 생성 UI 그대로. `main_window` 를 **QTabWidget** 로 재구성, 로그는 하단 공유.
- **core/템플릿**(신규): `constraint_creator.py`(`ConstraintCreator`: expand_pattern/build_pairs/build_text/
  create_file), `0010_src/A0202_Src_LDA_constraint_entry.py`(단일 항목 템플릿). `A0201_*` 은 골든 샘플로 보존 —
  예시 단일 쌍 출력이 `A0201`(3501자)과 **정확히 일치** 검증.
- **검증**: 변경 `.py` `py_compile` 통과 + 코어 기능 테스트(단일/다중/불일치/빈입력) 통과, **Maya 실기 확인 완료**.
  가이드 [A00080_KWI_creator](A00080_KWI_creator.md) 신규 + CHANGELOG/version.py v01.02 갱신.
  #KawaiiPhysics #언리얼 #Constraint #DataAsset #텍스트생성

> [!summary] `A00270_skinMigrate` v01.00→01.01 — 레거시 move_skinWeightTool 원본 2버튼 UI 를 "Classic" 탭으로 이식(두 탭 구조)
- **배경**: A00270 은 레거시 `JUN_PY_move_skinWeightTool_v01_04`(외부 `import kangarooTabTools.weights`
  사용) 에서 "스마트 통합"(Transfer+Move 체이닝)만 추려 단일 화면으로 만든 상태. **원본의 2버튼 UI 는 누락**돼
  있었음. 이를 복원해 두 탭으로 재구성.
- **Tab 1 "Classic"**(원본 충실 이식): `From`/`To` TSL + Transfer Mode 콤보 + 버튼 2개 —
  `Joints to Joints (single mesh)`(현재 선택 메시에서 `From[i]→To[i]` 웨이트 이동, Kangaroo
  `moveSkinClusterWeights`, selection 기반) / `Meshes to Meshes`(`From[i]→To[i]` skinCluster 전이,
  Kangaroo `transferSkinCluster`, 인덱스 쌍 루프).
- **Tab 2 "Migrate A → B"**: 기존 v01.00 통합 마이그레이션 그대로. 로그창은 두 탭 공유로 하단 이동.
- **core**(`SkinMigrateManager`): `move_joints_in_mesh`/`transfer_meshes` 추가. Kangaroo lazy import 를
  `_import_kangaroo()` 헬퍼로 공통화(외부 3rd-party 플러그인 — 미존재 시 안내 메시지, 무수정).
- **검증**: 변경 `.py`(skin_migrate_manager/main_window) `py_compile` 통과(Maya 실기 대기). 가이드
  [A00270_skinMigrate](A00270_skinMigrate.md) + CHANGELOG/version.py v01.01 갱신. #skinMigrate #리깅 #스킨웨이트 #kangaroo #이식

> [!summary] `A00120_FKIK` v01.06→01.07 — Bake IK/FK 가 구간 밖/다른 레이어 포즈를 바꾸던 버그 수정(컨스트레인트 제거)
- **증상**: 컨트롤러가 base + 다른 애니메이션 레이어 2곳에 키가 있을 때, base 레이어에서 특정 구간만
  Bake IK 하면 **구간 밖 포즈가 베이크 전과 달라짐**. 원본 `JUN_PY_FKIK_Tool_V02_01` 에는 없던 현상.
- **원인**: `fkik_matcher.bake()` 가 임시 `parentConstraint` + `bakeResults` 사용. 컨스트레인트가
  pairBlend 를 끼워 기존 animCurve 를 분리·머지 → 레이어가 있으면 구간 밖까지 오염. 스냅샷/복원 우회책도
  머지 커브만 봐서 **레이어를 인식 못함**.
- **해결(사용자 요구: 컨스트레인트 0)**: 레거시처럼 **per-frame** 으로 되돌림 — 프레임마다 `currentTime` →
  각 쌍 `cmds.matchTransform(position+rotation)` → follower translate/rotate 키. `setKeyframe` 이 활성
  레이어에만 써서 구간 밖/타 레이어 안전. `matchTransform` 은 **rotateOrder 가 서로 달라도 정확**
  (A00145 Match 탭 방식). `match_transforms` 도 xform rotateOrder 스왑 → `matchTransform` 으로 교체.
  `_snapshot/_restore` 는 의도적 컨스트레인트 경로인 `bake_constraint()`(Bake (Constraint) 버튼) 전용으로 잔존.
- **기능 추가**: Start/End 스핀박스 옆에 **Get Current** 버튼(A00110 패턴) — 현재 프레임으로 각 칸 갱신.
  창 맨 위에 **Help > About** 메뉴 바 추가(QMenuBar, 버전/날짜 + 버튼 동작 요약).
- **검증**: 변경 `.py`(fkik_matcher/main_window) `py_compile` 통과(Maya 실기 대기). 가이드
  [A00120_FKIK](A00120_FKIK.md) §4·5 + version.py v01.07 갱신. #FKIK #리깅 #베이크 #애니레이어 #버그수정

---

## 2026-06-26

> [!summary] `A00170_driverTool` v01.04→01.05 — Remap Value 탭 List Attributes/Search 강화(A00145 방식)
- **배경**: Remap Value 탭의 List Attributes 가 keyable 어트리뷰트만 보여줘 범위가 좁았고, 검색은 현재
  목록 안에서만 선택했다. A00145_RigConnect Connect 탭처럼 더 많은 attr + 검색으로 미리스트 attr 발견을 원함.
- **구현**: `core/maya_scene.py` 에 `MayaScene.list_attrs(obj, search="")` 추가(A00145 connect_manager
  list_attrs 이식) — `listAttr(obj)` 전체, 중첩("." ) skip, multi/compound 는 getNextFreeMultiIndex 로
  판정해 자식 펼침. search 시 `listAttr(obj.search)` 로 재질의. 기존 `list_keyable_attrs` 제거.
- **핸들러**(main_window): `on_rmp_list_attributes` → `list_attrs(first)`(전체). `on_rmp_search_attrs`
  → 현재 목록에 토큰 매칭 있으면 선택, 없으면 `list_attrs(first, token)` 로 재질의해 미리스트 attr
  채움(try/except). Attr Search 툴팁 보강.
- **검증**: 변경 `.py`(maya_scene/main_window) `py_compile` 통과(Maya 실기 대기). 가이드
  [A00170_driverTool](A00170_driverTool.md) §4.1 + version.py v01.05 갱신. #driverTool #리깅 #어트리뷰트 #UX

> [!summary] `A00310_SearchTool` v01.00 신규 — 레거시 Selection + Search 툴 2개를 PySide 탭으로 통합
- **배경**: `~/Documents/maya/2024/prefs/scripts` 의 단일 파일 maya.cmds 툴 `JUN_PY_SelectionTool_V02_01`
  + `JUN_PY_SearchTool_V01_02` 를 한 PySide 툴로 합치고 탭으로 구분해 달라는 요청.
- **구현(arch B, A00170 골격 복제)**: `JUN_All/tools/A00310_SearchTool/` 신설. core(maya.cmds, UI 비의존):
  `maya_scene.py`(선택/계층 펼치기/노드 타입) + `search_select.py`(collect_from_selection / collect_types /
  select_by_types / select_by_token, CONSTRAINT_TYPES 5종). ui `main_window.py`: QTabWidget 2탭(접두사
  `sel_*`/`sch_*`) + 공유 로그 + Help>About + 푸터.
  - **Selection 탭**: Source(Hierarchy/Selected)·Invert 옵션, Types|Objects TSL(Get/List Types),
    Select By Shape(Mesh/nurbsCurve/Joint/Constraint), Select By Type(선택 타입 매칭).
  - **Search 탭**: Search Token + 옵션 + Objects TSL + Search By Token.
- **공용 TSL**: `JUN_mod_tsl_qt_v01` 사용 — 사용자 요청대로 **Sort 버튼 포함**(show_sort 기본값 유지).
  Hierarchy/Selected 를 따르도록 기본 Select 버튼 대신 커스텀 **Get** 버튼(add_button)으로 채움.
- **마무리**: 셸프 설치 `__dragDrop_A00310.py`(TOOL_LABEL "SearchTool"), **아이콘**(svg+png, 리스트+돋보기),
  가이드 [A00310_SearchTool](A00310_SearchTool.md), version.py v01.00. 전 `.py` `py_compile` 통과(Maya 실기 대기). #SearchTool #SelectionTool #UI #신규툴

> [!summary] `A00170_driverTool` v01.03→01.04 — 새 탭 **AttachCrv**(커브 최근접 지점 어태치) 추가
- **배경**: `ref/ref_01.mel`(attachDriverOnCurve, by Doosup Jung)을 이식하되 **동작을 바꿔** 달라는 요청.
  원본은 커브에 *일정 간격*으로 새 로케이터를 어태치 → 대신 **TSL 의 기존 오브젝트들**을 각자
  커브에서 **가장 가까운 지점**에 라이브로 붙인다.
- **구현**: 새 core `app/core/attach_curve.py`(maya.cmds, 자족). 오브젝트마다 임시 `nearestPointOnCurve`
  로 최근접 파라미터 취득 → `pointOnCurveInfo → fourByFourMatrix → multMatrix(* parentInverseMatrix)
  → decomposeMatrix → translate`(옵션 `rotate`). orient 시 접선을 aim 축(+X/-X)에 맞추고 side=T×up,
  up'=side×T(vectorProduct)로 직교 프레임 구성. 부모 계층 안전 + 커브 변형 추종.
- **UI**: `_build_attach_tab()` + 탭 "AttachCrv"(접두사 `atc_*`). Attachment Curve(Get), Objects TSL,
  Orient 체크박스 + Aim Axis 콤보, Build 버튼. `__init__` 에 `run_attach_to_closest` 재노출, About 갱신.
- **세트 옵션**: 체크박스 "Group pointOnCurveInfo nodes into a set"(기본 ON) → 빌드로 생성된 모든
  `pointOnCurveInfo` 노드를 objectSet 하나(`<curve>_atcPOCI_SET`)로 묶음. core 가 poci 들을 모아
  `cmds.sets(...)` 생성, 반환을 `(attached, failed, set_node)` 로 확장.
- **검증**: 변경 `.py`(attach_curve/main_window/core __init__) `py_compile` 통과(Maya 실기 대기).
  가이드 [A00170_driverTool](A00170_driverTool.md) §1·2·4.3 + version.py v01.04 갱신. #driverTool #리깅 #커브 #UI

> [!summary] `A00145_RigConnect` v01.08→01.09 — 모든 TSL 에 **Sort 버튼** 노출
- **배경**: 4탭의 모든 리스트(TSL)가 정렬 버튼 없이 입력 순서로만 쌓여 항목이 많아지면 찾기 불편했다.
- **핵심 관찰**: 공용 위젯 `JUN_mod_tsl_qt_v01` 이 이미 `show_sort` 플래그(기본 `True`)와 Sort 버튼을
  갖고 있는데, 이 툴만 9개 TSL 전부 `show_sort=False` 로 끄고 있었다 → **인자 제거만으로 활성화**.
- **구현**: main_window.py 의 모든 TSL 생성에서 `show_sort=False` 제거(Match·Constrain·Skin·Connect·
  Stream·Connect Closest 탭의 Targets/Followers/Vertices/Objects/Driven/Driver). 공용 위젯의 기본
  Sort(`sorted(get_all_items())`) 동작을 그대로 사용 — 위젯 변경 없음.
- **후속 수정(같은 버전)**: Sort 버튼이 한 줄씩 더해지면서 **Connect 탭**(Source/Destination 두 섹션 +
  큰 버튼 2개가 한 창에 세로로 쌓임)에서 공간 부족 시 TSL 버튼이 창 경계를 침범. → Connect 탭 내용을
  `QScrollArea(setWidgetResizable=True)` 로 감싸 공간이 모자라면 겹치는 대신 스크롤바가 생기게 함.
- **검증**: `main_window.py` `py_compile` 통과(Maya 실기 대기). version.py v01.09 + 헤더 날짜 갱신. #RigConnect #UI #TSL

> [!summary] `A00240_PathTool` v01.04→01.05 — ShortCut 탭 **Path 버튼 순서 변경**(우클릭 Move Up/Down)
- **배경**: 카테고리는 이미 우클릭 Move Up/Down 으로 재정렬되는데, 그 안의 Path 버튼은 만든 순서에 고정돼 있었다.
- **구현**: `_show_button_menu` 맨 위에 **Move Up / Move Down**(+구분선) 추가, 카테고리 내 인덱스로 끝단 자동 비활성.
  `_move_button(cat_name, btn_name, delta)` 가 `cat["buttons"]` 에서 인접 버튼과 자리를 맞바꿔 저장·재렌더 —
  카테고리 재정렬(`_move_category`)과 동일 패턴이라 화면 순서=리스트 순서가 그대로 프로파일 JSON 에 반영된다.
- **검증**: `shortcut_tab.py` `py_compile` 통과(Qt 실기 대기). 가이드 [A00240_PathTool](A00240_PathTool.md) 5절 표/설명 +
  CHANGELOG + version.py 갱신. #PathTool #UI #UX

> [!summary] `A00210_FileManager` v01.22→01.23 — **Source Mode** 추가(Remote Git ↔ Local 공유/NAS 선택)
- **배경**: 팀 협업 시 매번 git push/pull 하는 대신 **NAS 같은 공유 저장소**에 데이터를 두고
  파일 서버가 동기화하도록 하고 싶다는 요구.
- **핵심 관찰**: 데이터 read/write 는 이미 `store_dir`(일반 폴더) 기반이고 git 에 묶인 건 Pull/Push
  레이어뿐. Lineage·Path Structure 탭도 폴더를 직접 읽는다 → **새 동기화 로직 불필요**.
- **구현**: Settings 에 **Source Mode** 콤보(`Remote (Git)`/`Local (Shared / NAS)`)와 **Shared Folder**
  입력 추가. `_effective_store_dir()` 한 곳이 모드에 따라 Store Repo(git)/Shared Folder(local)를 반환,
  `get_store_dir()`·`_make_store()` 가 이를 사용해 **모든 탭이 활성 모드 폴더를 자동으로 따름**.
  local 모드에선 git 입력·Pull/Push 비활성 + 안내. `source_mode`/`local_dir` 은 **프로파일별 저장**.
- **자동 폴더 생성**: `MetaStore.ensure_store()` 추가 → 빈 공유/NAS 폴더라도 첫 저장 시 `records/`·`thumbs/`
  가 함께 생성(`_stamp_and_save` 에서 호출). (lineage/path_structure 저장도 기존 `_ensure_parent` 로 자동 생성.)
- **검증**: 변경 `.py`(main_window/store/prefs) `py_compile` 통과(Qt 실기 대기). 가이드
  [A00210_FileManager](A00210_FileManager.md) 5-C 절 + CHANGELOG + version.py 갱신. #FileManager #협업 #NAS #UI

---

## 2026-06-25

> [!summary] `A00110_animTool` v01.22→01.23 — 확장된 `Get Current` 버튼이 동작 안 하던 버그 수정
- **배경**: v01.22 에서 Follow 외 탭(Move Keys/Copy/Mirror/Bake)으로 넓힌 `Get Current` 버튼이
  눌러도 Start/End 입력이 갱신되지 않았다. Follow 탭 버튼만 정상.
- **원인**: 공용 헬퍼 `_make_get_current_btn` 의 슬롯이 `lambda le=line_edit:` 로 **위치 인자 1개**를
  받는 형태였다. PySide `clicked` 시그널은 슬롯에 `checked`(bool) 인자를 넘기는데, 그 값이 `le` 기본값을
  덮어써 `_set_current_frame(False)` 로 호출 → `False.setText` 로 실패. Follow 버튼은 무인자 람다라 무사.
- **수정**: `lambda *_a, le=line_edit:` 로 checked 인자를 흡수해 모든 탭 버튼이 현재 프레임으로 갱신.
  `app/ui/main_window.py` 만 변경.
- **검증**: 가이드 [A00110_animTool](A00110_animTool.md) v01.23 노트 + version.py 갱신(마야 실기 대기). #anim #UI

> [!summary] `A00300_meshDoctor` v01.00→01.01 — zero_area 판정을 형상품질(q) 기반으로 + Clear Log 버튼
- **배경**: polyCleanup(zeroGeom 1e-05) 후에도 `zero_area_faces` 가 FAIL 로 남고, 선택하면 육안 보이는
  아주 작은 면이 나오는 사례. 트리거는 Maya `it.zeroArea()`. 진짜 슬라이버(케이스 A, Transfer 깨짐)와
  작지만 멀쩡한 면(케이스 B, 오탐)을 구분 못 하던 문제(사용자 메시는 케이스 A).
- **개선**: 절대 면적/`zeroArea()` 의존을 줄이고 **스케일 무관 형상품질** `q=(4π·area)/perimeter²`(`face_quality`)로
  판정. 후보(`zeroArea()` or `area<AREA_TINY 1e-5`) 중 `area<AREA_DEGEN 1e-10` 또는 `q<QUALITY_EPS 1e-2` →
  `zero_area_faces`(FAIL, 슬라이버), 그 외 → 신규 `tiny_faces`(INFO, 결함 아님)로 강등해 오탐 제거.
- **로깅**: 플래그된 면마다 `f<idx> a=<area> q=<q>` 를 샘플로 남겨 JSON/TXT 에서 A/B 육안 구분.
  `Select Zero-Area Faces` 헬퍼도 동일 기준. zero_area 메시지에 "필요한 면이면 closestVertex 모드로" 안내.
- **UI**: 로그뷰 아래 **`Clear Log`** 버튼 추가.
- **검증**: 변경 `.py`(mesh_scan/mesh_fix/main_window) `py_compile` 통과(마야 실기 대기). 가이드
  [A00300_meshDoctor](A00300_meshDoctor.md) 진단노트 "v01.01 적용" + CHANGELOG + version.py 갱신. #메시진단 #스킨 #kangaroo

> [!summary] `A00290_BSTool` v01.00→01.01 — Edit BS 탭에 `Copy every frame`(구간 프레임별 메시 추출) 추가
- **Feat**: `Start`/`End` 구간을 **1프레임마다** 씬에서 **선택한 메시**를 복제(visibility off)해
  `<mesh>_f<frame>`(0 패딩)으로 추출하고 `<mesh>_frames` 그룹으로 묶는다. **키 없이** 현재 씬 애니메이션
  상태를 그대로 캡처(`suspend_refresh` + 종료 시 현재 프레임 원복, 전체 단일 undo).
- **UI**: 구간 입력(`Start`/`End` + `Get Current`)은 A00110 Follow 탭 패턴. 대상은 blendShape 리스트가
  아니라 씬 선택 메시. 로직 `edit_bs_manager.copy_every_frame(meshes, start, end)`.
- **검증**: `py_compile` 통과(마야 실기 테스트 대기). 가이드 [A00290_BSTool](A00290_BSTool.md) +
  CHANGELOG v01.01 + version.py 갱신. #blendShape #페이셜 #UI

> [!summary] `A00110_animTool` v01.21→01.22 — `Get Current` 버튼을 시간범위 탭 전체로 확장
- **Feat**: Follow 탭에만 있던 `Get Current`(현재 Maya 프레임으로 Start/End 입력 채움) 버튼을
  **Key Edit(Move Keys) · Copy Key · Mirror Key · Bake** 탭의 Start/End 에도 추가.
- **구현**: 공용 헬퍼 `_make_get_current_btn(line_edit)` 로 버튼 생성 일원화, 핸들러
  `_follow_set_current_frame` → `_set_current_frame`(범용)으로 변경. Bake 탭은 Custom range 일 때만
  버튼 활성(입력 필드와 동일 토글 `_bake_update_range_mode`). `app/ui/main_window.py` 만 변경.
- **검증**: `py_compile` 통과(마야 실기 테스트는 드롭→셸프 실행으로 확인 대기). 가이드
  [A00110_animTool](A00110_animTool.md) v01.22 + version.py 갱신. #애님 #UI

> [!summary] `A00110_animTool` v01.20→01.21 — Follow 탭: 비-베이스 레이어 베이크가 베이스와 동일한 월드 결과를 내도록 수정
- **증상**: Follow 를 비-베이스 애님 레이어(특히 **additive**)에 구우면 ① 구간 안 위치가 어긋나고 ② 회전이
  베이스와 다르며 ③ **구간 밖 원본 애니메이션이 상수만큼 평행이동**. 베이스 레이어 베이크는 정상.
- **근본 원인(사용자 제공 좌표로 확정)**: `setKeyframe(animLayer=L, value=V)` 는 레이어 커브에 V 를 그대로
  쓰는 게 아니라 **'평가 결과(아래 레이어+이 레이어) = V' 가 되도록 레이어 기여를 역산**해 기록한다.
  → override 는 절대값 `V=F` 를 넘겨 정상이었으나, additive 는 **델타 `V=F−base`** 를 넘겨 평가값이
  `F−base` 만큼 어긋남. 중립 `value=0` 도 `additive=−base` 로 역산돼 구간 밖 오프셋으로 유지됨.
  (보내준 커브 값이 정확히 `additive=−base`, `base_pin=2×원본` 패턴이라 역산 동작이 증명됨.)
- **수정**: override/additive 구분 없이 **항상 절대 로컬값 F 만 기록** → Maya 가 레이어 종류에 맞는 기여
  (additive 회전 합성 포함)를 자동 계산. **델타 계산·base 읽기·회전 합성 캘리브레이션·base-pin 전부 제거**
  (코드 단순화). 구간 밖은 경계(`start-1`/`end+1`)에 **원본 절대값**을 키 → 레이어 기여 0, 레이어 커브
  **Infinity=constant** 고정으로 구간 밖 0 기여 유지(원본 위치 변화 없이 그대로 재생).
- **범위**: `follow_match_manager.py` 만 변경(`py_compile` 통과, 사용자 Maya 검증 완료 "아주 잘 됨").
  가이드 [A00110_animTool](A00110_animTool.md) v01.21 항목 + 트러블슈팅 갱신, version 01.21. #애니메이션 #리깅 #애님레이어

> [!summary] 신규 툴 `A00300_meshDoctor` v01.00 — 메시 진단(읽기 전용) + 안전 원클릭 수정 + 로그 출력
- **목적**: 문제 메시 두 증상 해결 — ①빈 공간 클릭해도 메시 선택됨(=bbox 팽창) ②kangaroo Transfer 시 일부만
  이동/페이스 일그러짐(=토폴로지 손상). 메시를 **읽기 전용 진단**해 JSON+TXT 로그를 `0020_out/` 에 출력하고,
  그 로그를 Claude 가 분석해 근본 원인을 짚는 워크플로.
- **아키텍처**: (B) PySide-in-Maya — `A00110_animTool` 클론(launch/`__dragDrop_A00300`/app core·ui 분리,
  blue_dark 테마, 마야 메인윈도우 parent). 진단 로직은 `maya.cmds` + `maya.api.OpenMaya` 2.0(Maya 2023 호환).
- **진단(`mesh_scan.py`)**: NaN/Inf 정점, 떠돌이(stray) 정점, bbox 팽창, intermediate(orig) shape, 잔여 history,
  non-manifold edge/vertex, lamina/holed/concave/zero-area 페이스, zero-length edge, 겹친(미병합) 정점,
  border edge, 음수 스케일, UV 셋/누락 UV, skinCluster — 각 `PASS/INFO/WARN/FAIL` + 의심 근본원인 매핑.
- **수정(`mesh_fix.py`, 전부 Undo 가능)**: Delete History(deformer-safe), Merge Vertices, Conform Normals,
  polyCleanup(non-manifold+lamina+zero-area+zero-edge), Snap NaN/Stray Verts(정점 삭제 없이 좌표만 복구).
  + 문제 컴포넌트 선택 헬퍼(non-manifold/zero-area face/stray·NaN vert).
- **로그(`report.py`)**: `PathManager(write_dir="0020_out")` 로 `meshDoctor_<scene>_<ts>.json` + `_summary.txt` 출력.
- **문서**: kangaroo Transfer 원리(barycentric)와 **메시를 수정하지 않고 Transfer 하는 법**(`closestVertex` 모드 전환,
  근거 `weights.py:2073-2077`) + **NaN(Not a Number) 정의**까지 가이드에 정리. kangaroo 플러그인은 **읽기 전용 참조, 미수정**.
- **아이콘**: 전용 셸프 아이콘 신규(32×32 ARGB svg+png) — 다크 라운드 배경 + 청록 와이어프레임 메시 +
  우하단 빨간 의료 십자 배지(진단/수리 모티프). GDI+ 렌더, `__dragDrop_A00300` 이 이미 경로 참조.
- **문서 보강**: 가이드에 NaN(Not a Number) / manifold·non-manifold / lamina face 용어 정의 추가.
- **검증**: 신규 `.py` 전부 `py_compile` 통과(마야 실기 테스트는 드롭→셸프 실행으로 확인 대기).
  가이드 [A00300_meshDoctor](A00300_meshDoctor.md) + CHANGELOG v01.00. #리깅 #메시진단 #스킨 #kangaroo

> [!summary] `A00080_KWI_creator_V03` v01.00→01.01 — 합본 클립보드 복사 · Help 메뉴바 · 본 개수 표시
- **Feat: 합본 코드 클립보드 복사.** **Create combined file** 실행 시 base+setting+LD 합본 텍스트만
  `QApplication.clipboard().setText(...)` 로 복사 → 언리얼 AnimGraph 에 바로 Ctrl+V. (개별 파일 내용은 복사 안 함.)
  코어 `KWI_creator.create_combined_file()` 반환을 `out_path` → `(out_path, combined)` 튜플로 변경.
- **Change: Help 버튼 → 메뉴바.** 우상단 `QPushButton("Help")` 제거, `QMenuBar` 의 `Help > How to use`
  액션으로 이동(`layout.setMenuBar`). A00260_ConstraintConverter 의 메뉴바 패턴과 동일.
- **Feat: TSL 본 개수 표시.** `Target bones (Root bones)` 라벨에 현재 개수를 붙여 표시(예: `... : 3`).
  `tsl_bones.model()` 의 `rowsInserted`/`rowsRemoved` 시그널에 연결해 추가/삭제/Clear/Load 어떤 경로로 바뀌어도 자동 동기화.
- **검증**: 수정 `.py` `py_compile` 통과(마야 실기 테스트는 드롭→셸프 실행으로 확인 대기).
  가이드 [A00080_KWI_creator_V03](A00080_KWI_creator_V03.md) + CHANGELOG v01.01 갱신. #언리얼 #KawaiiPhysics #리깅

---

## 2026-06-24

> [!summary] 신규 툴 `A00290_BSTool` — 레거시 BS Tool(maya.cmds) 을 PySide 로 재작성 + Base Shape 탭 추가
- **목적**: `~/Documents/maya/2024/prefs/scripts/JUN_PY_BSTool_V01_01`(maya.cmds UI) 을 **PySide(Qt)** 로 재작성.
  기존 툴의 **Connect BS 탭은 제외**하고 **Edit BS 탭만** 이식, **Base Shape 탭**을 신규 추가.
- **아키텍처**: (B) PySide-in-Maya — `A00270_skinMigrate` 클론(launch/`__dragDrop_A00290`/app core·ui 분리,
  green_dark 테마, 마야 메인윈도우 parent, `QTabWidget` 2탭 + 공용 로그).
- **탭1 Edit BS**: blendShape 노드 TSL(`JUN_mod_tsl_qt`) + `Key every target`(프레임 i=1, i±1=0 으로 타겟 순차 키) +
  `Copy every target`(키 후 프레임마다 베이스 메시 복제→타겟 이름 메시 추출, vis off, `<node>_targets` 그룹).
- **탭2 Base Shape (신규)**: blendShape 를 `<- Set`(노드/메시 선택에서 탐색)→`List Targets` 로 타겟 나열, 선택 타겟의
  **weight=Value 모양을 weight=1.0 기본 모양으로 재정의**. 원리: 결과=`base+weight·delta` 이므로 델타를 **Value 배**
  스케일하면 weight 1.0 이 예전 Value 모양이 됨(0.5→절반, 1.3→과장). 구현은
  `inputTargetItem[*].inputPointsTarget`(pointArray) 직접 스케일, in-between·다중 지오 포함, 단일 undo.
  Value 0 금지, 저장 델타 없는(라이브 지오) 타겟은 스킵+로그.
- **코어 분리**: `blendshape_utils`(타겟 조회/인덱스 매핑/베이스 메시/선택→blendShape) ·
  `edit_bs_manager`(Edit BS) · `base_shape_manager`(델타 스케일) — 모두 UI 비의존.
- **검증**: 신규 `.py` 전부 `py_compile` 통과(마야 실기 테스트는 드롭→셸프 실행으로 확인 대기;
  특히 pointArray get/setAttr 라운드트립 권장). 전용 아이콘(System.Drawing 64x64 png + svg, 페이스 모핑 모티프).
  가이드 [A00290_BSTool](A00290_BSTool.md) + CHANGELOG v01.00 + README 등록. #블렌드셰이프 #페이셜 #리깅

> [!summary] 신규 툴 `A00080_KWI_creator_V03` — KWI Creator 를 마야 내부 실행(PySide)으로 버전업 + 본 TSL 입력
- **목적**: 언리얼 KawaiiPhysics 노드 텍스트 생성기(`A00080_KWI_creator_V02`)를 **마야에서 드래그&드롭으로
  설치/실행**하는 (B) PySide-in-Maya 툴로 버전업. **생성 로직은 V02 와 동일**.
- **V02→V03 차이**: ① standalone PySide 앱 → **마야 내부 실행**(`__dragDrop_A00080` → 셸프 `KWI_V03` →
  `tools.A00080_KWI_creator_V03.run(True)`, 마야 메인윈도우 parent). ② 타겟 루트 본을 파일
  (`A0101_tgtBones.py`)이 아니라 **UI 의 TSL(`QListWidget`)** 로 입력 — 입력란/Add·**Add Selected**(씬 선택)·
  Remove·Clear·**Load Example**. 코어에 `KWI_creator.set_tgt_bones(list)`/`get_default_tgt_bones()` 추가.
- **추가 작업**: 상단 **Help 버튼**(`QMessageBox` 사용 안내 팝업, `exec_()` 로 PySide2/6 호환), **전용 아이콘**
  (PIL 렌더 32x32 png + svg, 앵커바+흔들리는 컬러 비드 체인).
- **검증**: 신규/수정 `.py` 전부 `py_compile` 통과(마야 실기 테스트는 드롭→셸프 실행으로 확인 대기).
  가이드 [A00080_KWI_creator_V03](A00080_KWI_creator_V03.md) + CHANGELOG v01.00 + README 등록. #언리얼 #KawaiiPhysics #리깅

> [!summary] A00280_correctiveFromCache — 실사용 피드백 반영 (v01.00→01.01)
- **Fix: PoseWrangler Route "Target mesh is not skinned" 오탐 제거.** PoseWrangler `create_blendshape`(api.py:1165)의
  skin 검사는 skinCluster 가 **노출 셰이프에 직접 연결**돼 있어야만 통과 — skinCluster 가 디포머 체인 마지막이 아닌
  의상 메시(흔함)에선 스킨돼 있어도 에러. 체크 없는 `create_blendshape_safe`(go default→isolate→duplicate→
  `add_existing_blendshape`)로 대체. invertShape 는 히스토리로 skin 을 찾으므로 결과 동일.
- **Feat: `default` 포즈 코렉티브 생성 옵션.** Options 에 `Include 'default' pose` 체크박스 — ON 이면 default 행도
  자동 체크되고 코어가 스킵하지 않음(기존엔 항상 스킵).
- **Fix: 타겟 이름이 A00090 `rules_v01` 약속을 따름.** default 타겟이 `default` 로 나오던 문제 → 솔버 이름에서
  접두사 추출 `<prefix>_default`(예: `WRK_calf_l_UERBFSolver`→`calf_l_default`). 비-default 포즈는 이미 접두사 포함이라 그대로. 양 Route 공통.
- **Feat: Frame Step 입력.** 포즈→프레임 = `start + index x step`(기본 1). abc 캐시가 포즈당 N프레임 간격(예: 60)으로
  정착되도록 시뮬된 경우 step=60 → 0,60,120… 자동 채움(미정착 프레임 샘플링 방지). 행별 수동 편집 유지.
- **검증**: 변경 `.py` 전부 `py_compile` 통과 + 타겟 네이밍 5케이스 단위 검증(PASS). 마야 실기 재확인 대기.
  가이드 [A00280_correctiveFromCache](A00280_correctiveFromCache.md) + CHANGELOG v01.01 반영. #리깅 #페이셜 #RBF #후디니

> [!summary] A00260_ConstraintConverter — 생성 노드 간 ExecutePin 연결(RigVMLink) 추가 (v01.03→01.04)
- **노드 실행 체인 연결**(`ref_/sample_04.py` 기준): 여러 컨스트레인트를 한 번에 변환할 때 생성된 노드들을
  **생성 순서대로 `ExecutePin` → `ExecutePin`** 으로 잇는 `RigVMLink` 블록을 노드 텍스트 뒤에 덧붙인다 —
  붙여넣으면 노드들이 **실행 체인으로 연결된 상태**가 된다(이전엔 노드만 흩어져 나와 수동 연결 필요).
- **구현**: 신규 템플릿 `0010_src/A0004_Src_link.py`(`{{GRAPH}}`/`{{IDX}}`/`{{SOURCE_NODE}}`/`{{TARGET_NODE}}`) +
  `NodeBuilder.build_links(graph, node_names)` — `node_names[i] → [i+1]` 로 N-1 개(`RigVMLink_0 … RigVMLink_{N-2}`) 생성,
  **노드 1개 이하면 링크 없음**. `ConverterPaths.read_link_tmpl` 경로 추가, `build_text` 가 `blocks + links` 를 결합.
- **검증**: 핵심 4파일 `py_compile` 통과 + `build_links` 단독 실행으로 3노드→링크 2개가 `sample_04.py` 와
  동일 포맷, 0·1노드 엣지케이스 빈 결과 확인. 가이드 [A00260_ConstraintConverter](A00260_ConstraintConverter.md) v01.04 반영. #리깅 #언리얼 #ControlRig

> [!summary] 신규 툴 `A00280_correctiveFromCache` — MetaHuman RBF 의상 주름 코렉티브를 후디니 Alembic 캐시에서 배치 추출
- **목적**: RBF(PoseWrangler) 의상 주름 코렉티브 작업에서, 각 포즈 hold 프레임마다 마야 Shape Editor 로 의상을
  abc 캐시에 **수동 매치**하던 (타겟수×관절수 ≈ 32회) 병목을 제거 → 캐시에서 코렉티브를 **버튼 한 번**으로 일괄 추출.
- **아키텍처**: (B) PySide-in-Maya — `A00110_animTool` 클론(launch/`__dragDrop_A00280`/app core·ui 분리, coral_dark).
- **핵심**: 포즈 프레임에서 캐시 형상 월드 스냅샷 → `go_to_pose` → PoseWrangler `edit_blendshape` 의 EDIT 메시에
  캐시 포인트 복사 → `edit_blendshape(edit=False)` 내부 `cmds.invertShape()` 가 bind(스킨 이전) 델타 생성 + 솔버 자동 와이어.
  토폴로지 동일(캐시==의상) 전제. `UERBFAPI(view=False)` 헤드리스 래핑. 포즈→프레임 = `start + poses().index()`.
- **Route 2종**: `PoseWrangler`(솔버 자동 와이어, 기본) / `Direct invertShape`(타겟 이름만, 와이어는 `A00090_ConnectionBuilder` 위임).
- **UI**: 솔버소스(씬/JSON) + Garment/Alembic + Start Frame + per-pose 테이블(체크/프레임 편집/Status) + 옵션
  (exists Skip/Overwrite, skip-if-delta, **L/R Mirror** 선택) + Generate/Mirror 버튼. 전체 단일 undo + suspend_refresh, 종료 시 default/타임 복원.
- **core**: `pose_wrangler_bridge`/`alembic_cache`/`mesh_transfer`(MFnMesh 월드 포인트)/`corrective_batch_manager`/`solver_source`/`mirror_manager`.
- **효과**: 미러 없이 ~32 수동 매칭 → 0(설정 후 1클릭). L/R 미러 시 왼쪽 ~16만 생성 후 오른쪽 자동(절반).
- **검증**: 신규 `.py` 전부 `py_compile` 통과(마야 실기 테스트는 sample_04.json 솔버+후디니 abc 필요). 전용 아이콘(주름 캐시→RBF 허브).
  계획서 [A00280_correctiveFromCache_plan.md](A00280_correctiveFromCache_plan.md) + 가이드 [A00280_correctiveFromCache](A00280_correctiveFromCache.md) + CHANGELOG + README 등록. #리깅 #페이셜 #RBF #후디니

> [!summary] A00260_ConstraintConverter — 닫힘(접힘) 노드 출력 + 노드 가로 배치(4개마다 줄바꿈) + 리로드 안정화 (v01.00→01.03)
- **닫힘 노드 출력**(`ref_/sample_02_close.py` 기준): 펼침(`sample_01_open.py`)과의 차이가
  세 컨테이너 핀(AdvancedSettings / Parents 배열 / Filter)의 `bIsExpanded=True` **3줄뿐**임을 diff 로
  확인 → 템플릿에서 제거. 붙여넣은 노드가 접힌 채라 길이가 짧다. 닫힘 샘플 입력으로 생성 결과가
  `sample_02_close.py` 와 **381줄 전부 동일** 검증.
- **노드 가로 배치**(`ref_/sample_03.py` 참고): 기존 세로 배치를 가로로 변경 — `col = idx % N`,
  `pos_x = start_x + 340·col`. 한 줄 **4개**를 넘으면 줄바꿈해 아래로(`row = idx // 4`,
  `pos_y = start_y + 280·row`). 간격은 sample_03 의 노드 간 X(약 307)를 참고.
- **리로드 안정화**: 닫힘(템플릿 파일)은 즉시 반영됐으나 배치(파이썬 모듈)는 안 바뀌던 문제 —
  `main_window` 가 import 시점에 옛 `ConstraintConverter` 를 바인딩(같은 깊이 모듈 reload 순서)했기 때문.
  `on_convert`/`_collect_options` 에서 **지역 import**(launch.py 패턴)로 바꿔 리로드 후 최신 클래스를
  잡도록 수정 → 코드 변경 즉시 반영. #리깅 #언리얼

> [!summary] A00145_RigConnect — Connect Closest 탭에 `Get Closest` 버튼 추가 (v01.07→01.08)
- **목적**: Driver 리스트의 각 오브젝트에 **가장 가까운 오브젝트가 무엇인지 발견**하고, 그 결과로
  `Driven` 리스트를 driver 순서대로 미리 채운다.
- **후보 풀**: `Driven` 에 항목이 있으면 그걸 풀로, 비어 있으면 **현재 씬 선택**을 풀로 사용(하이브리드).
  driver 자신은 풀에서 자동 제외(거리 0 회피).
- **핵심 설계**: 매칭을 공용 함수 `match_closest_pairs(drivers, pool)`(driver 순서 greedy 1:1, 쓰인 후보
  제거)로 빼고 **기존 `connect_closest` 와 신규 `find_closest_for_drivers` 가 공유** → 채워진 `Driven` 은
  곧 `Connect` 가 실제 연결할 페어의 **미리보기**가 된다. `connect_closest` 도 이 함수를 쓰도록 리팩터.
- **UI**: Driver TSL 버튼 행에 `Get Closest` 버튼(`add_button`). 핸들러는 `driver -> closest (dist)` 로그
  + 찾은 오브젝트를 **뷰포트에서 선택**해 발견 검증을 돕는다. 거리 기준은 기존과 동일한 월드 피벗 거리.
- **검증**: 변경 4파일 `py_compile` 통과. 실제 매칭/뷰포트 선택 동작은 Maya 런타임 확인 필요.
  가이드 `docs/A00145_RigConnect.md`(Get Closest 설명 + 헤더 버전 v01.08) 갱신. #A00145 #리깅

> [!summary] 신규 툴 `A00270_skinMigrate` — 토폴로지가 다른 두 메시 사이의 스킨 웨이트 전이 + 본 재매핑을 버튼 한 번으로
- **목적**: 외형은 비슷하나 토폴로지가 다른 리깅 메시 A, B 에서 ① A 의 웨이트/본을 B 로 **Transfer** →
  ② B 의 웨이트를 `A_joint_i → B_joint_i` 로 **Move** 하던 수동 2단계(Kangaroo Builder skinCluster 탭)를
  **1-click** 으로 단축. 결과적으로 B 가 자기 본 `[B_joint..]` 에 올바르게 바인드된다.
- **아키텍처**: (B) PySide-in-Maya — `A00110_animTool` 클론(launch/`__dragDrop_A00270`/app core·ui 분리,
  coral_dark 리깅 테마). 전신은 Transfer/Move 를 각각 호출하던 `A00020_move_skineWeightTool`.
- **엔진 추상화 (UI 라디오로 선택)** `SkinMigrateManager.migrate(...)`:
  - `Kangaroo`(기본) — `kangarooTabTools.weights` 의 `transferSkinCluster`(bAutoCreateNewSkinCluster) +
    `moveSkinClusterWeights`(xJoints) 체이닝. 사용자가 수동으로 누르던 두 버튼과 **동일 결과**. 본 매핑은
    A00020 의 검증된 `['{joint}']` list-literal 포맷 사용.
  - `Native` — `cmds.copySkinWeights` + `maya.api` `MFnSkinCluster.getWeights/setWeights`. 플러그인 무의존,
    Move 는 본 1:1 컬럼 이동(per-vertex 최근접/스무딩 없음). setWeights 특성상 세밀 undo 미보장 → 정밀작업은 Kangaroo 권장.
- **입력/검증**: Source A / Target B(`<- Set`) + Joints A(From)/B(To) 두 TSL(행 순서 zip 매핑). 개수 일치·메시·
  joint 존재 검사 + **Strict joint check**(기본 ON, From 본이 A 에 안 묶였으면 에러로 순서/오타 조기 발견).
  옵션: Transfer Mode(기본 Closest Point), Remove unused influences(ON), Select result mesh. 전체 단일 undo 청크.
- **아이콘**: `icon/A00270_skinMigrate.svg`→`build_icons.py`(mayapy PySide2 QtSvg)로 32px PNG 렌더 —
  파랑 메시 A → 초록 메시 B + 화살표(웨이트 마이그레이션) 모티프. (초기 placeholder 가 animTool 과 동일했던 것 교체)
- **검증**: 신규 `.py` 전부 `py_compile` 통과, native 엔진 시그니처를 Maya API 사양에 맞춰 보정(skinCluster
  `unbind` 플래그 부재→`cmds.delete`, create 인자 `inf+[mesh]`, `addElements(list(...))`). 가이드 문서
  [A00270_skinMigrate](A00270_skinMigrate.md) + 계획서 + CHANGELOG + README 목록 등록. #리깅 #스킨

> [!summary] 신규 툴 `A00260_ConstraintConverter` — 마야 컨스트레인트 → 언리얼 Control Rig Parent Constraint 노드 텍스트 변환
- **목적**: 마야 씬의 컨스트레인트 세팅(타겟·웨이트·대상)을 **언리얼 Control Rig 의 Parent Constraint 노드
  텍스트**로 변환해 **클립보드에 복사** → UE 그래프에 `Ctrl+V` 붙여넣기. 출력 포맷 레퍼런스는 UE 에서
  복사한 원본 `ref_/smaple.py`(clavicle_out_l ← clavicle_l 0.6, upperarm_l 0.4) 를 그대로 따른다.
- **아키텍처**: (B) PySide-in-Maya — `A00110_animTool` 클론(launch/`__dragDrop_A00260`/app 분리,
  green_dark 테마). 파일 생성 흐름은 `A00080_KWI_creator_V02`(PathManager + `0010_src`/`0020_out` +
  `{{KEY}}` TemplateEngine)를 따른다.
- **읽기**(씬→데이터) `constraint_reader`: 선택에서 컨스트레인트 수집(노드면 그대로/트랜스폼이면 하위
  `-type constraint`), `targetList`/`weightAliasList` 로 타겟·웨이트, 컨스트레인트 부모로 대상(child)을
  읽어 짧은 이름(네임스페이스·DAG 제거)으로. 지원: parent/point/orient/scaleConstraint.
- **생성**(데이터+옵션→텍스트) `node_builder`: 타겟 개수만큼 Parents 배열을 동적 조립 — 선언/정의는
  인덱스 **내림차순**, 컨테이너 `SubPins` **오름차순**, `bIsDynamicArray=True` 는 **첫 parent 에만**
  (UE 직렬화 형태 재현). 노드명 `ParentConstraint_N` 고유화 + Position Y 오프셋.
- **옵션(UI 전역 적용)**: Translate/Rotate/Scale 필터(기본 Translate 만), Maintain Offset(기본 ON),
  InterpolationType 드롭다운(Average/Shortest, 기본 Shortest). UI: Constraints TSL + 옵션 + Convert + 로그.
- **아이콘**: `icon/A00260_ConstraintConverter.png`(64px) — 타겟 2(녹색)→대상 1(UE 블루) 컨스트레인트
  모티프. drag-drop `ICON_NAME` 이 자동 참조(부재 시 `pythonFamily.png` 폴백).
- **검증**: 샘플 데이터로 생성한 결과가 `ref_/smaple.py` 와 **384줄 전부 동일**, 타겟 1·3개 케이스
  인덱스/SubPins/동적배열 플래그 정상, 신규 `.py` 14개 `py_compile` 통과. 가이드 문서
  [A00260_ConstraintConverter](A00260_ConstraintConverter.md) + README 목록 등록. #리깅 #언리얼

> [!summary] docs 학습 노트 분리 — `docs/study/` 신설 + 스킨 웨이트 전이 워크플로우 학습 문서 작성
- **배경**: `JUN_All/docs/` 루트는 **툴 사용법 안내 문서만** 두기로 정리. 특정 툴 안내가 아닌
  **작업 방법론·기법 학습 노트**를 담을 별도 경로가 필요해 **`docs/study/`** 를 신설(기존 `docs/plans/`
  =개발 계획 과 대칭). 이제 docs 는 3분할 — `docs/*.md`=툴 안내, `docs/plans/`=개발 계획, `docs/study/`=학습 노트.
- **신규 학습 문서** `docs/study/skinWeight_transfer_workflow.md`: 잘 웨이트된 메시 A 의 스킨 웨이트를
  토폴로지가 다른 메시 B 로 옮기는 작업 방식 정리. **Shrink Wrap + Blendshape 로 A 를 B 표면에 공간 정렬 →
  Kangaroo Transfer → 다듬기** 흐름의 원리("전이 정확도 = 공간 오버랩", closest-point 대응)와 우려 지점
  (투영 실패 구역·갭 누출·바인드 포즈·인플루언스 이름 매핑), 개선책(게임용 maxInf/prune/normalize 후처리,
  Geodesic Voxel Bind 보조, 스냅샷, Delta Mush, 구역 분할 전이), 전이 방식 비교표 수록.
  관련 개발 계획 [A00270_skinMigrate](plans/A00270_skinMigrate_plan.md)(Transfer+Move 1-click 툴)와 상호 링크.
- **인프라**: `docs/study/README.md`(작성 규칙 + 문서 목록 표) 신규, `docs/README.md` 에 `study/` 폴더
  안내 + 3분할 요약 추가. #docs #리깅

---

## 2026-06-23

> [!summary] Maya 툴 셸프 아이콘 생성 — Ari 스타일 학습 후 툴별 고유 32×32 아이콘 + drag-drop 연동
- **배경**: Maya 내부에서 도는 모든 툴이 셸프 설치 시 동일 기본 아이콘 `pythonFamily.png` 를 써
  셸프에서 구분 불가. Maya 사용자 아이콘 폴더의 **`Ari*` 9종을 학습**(32×32 ARGB, 다크 차콜 배경 +
  얇은 프레임 + 고채도 단순 도식 글리프)해 같은 톤의 **툴별 고유 아이콘**을 만들었다.
- **대상 20종**(베이스 템플릿·standalone `A00240` 제외, 버전 중복은 현행 우선): A00010_V02·A00020·
  A00030·A00040·A00050·A00060(V01/V02)·A00090·A00110·A00120·A00130·A00140·A00145·A00150·A00160·
  A00170·A00180·A00190·A00200·A00211·A00250. 각 툴 도메인을 상징하는 모티프(스켈레톤·본체인·키프레임·
  FKIK 스위치·NURBS 컨트롤·미러 메시·페이셜 마커·DAG 레인·메모 등)로 디자인.
- **방식**: SVG 작성 → 래스터화. 환경에 SVG 도구가 전무(cairosvg/Pillow/Inkscape 부재)했으나
  **Maya 2024 mayapy + PySide2 `QSvgRenderer`** 로 추가 설치 없이 32×32 ARGB(= Ari 포맷 일치) 출력.
  신규 **`JUN_All/dev/build_icons.py`**(개발 편의 스크립트)가 `tools/*/icon/*.svg` 를 일괄 PNG 로
  렌더(mayapy/QtSvg 우선, svglib/reportlab 폴백). 소스 SVG + 결과 PNG 를 각 툴 **`icon/`** 폴더에
  함께 둬 자기완결(드롭 설치 시 함께 이동)·재생성 가능.
- **drag-drop 연동(전체 처리)**: 기존 `__dragDrop_*.py` 18개의 `ICON_NAME` 을 **툴 폴더 내 아이콘
  절대경로 + 부재 시 `pythonFamily.png` 폴백**(`os.path.exists`)으로 교체(`image1=ICON_NAME` 호출부는
  무수정). drag-drop 이 없던 **A00020·A00030·A00090 은 신규 생성**(고유 베이스네임·`sys.modules.pop`
  충돌방지 규칙 준수, A00090 은 namespace 패키지라 `launch.run` 직접 호출).
- **Icon Label(셸프 라벨) 통일**: drag-drop 22개의 `cmds.shelfButton` 에 `imageOverlayLabel=TOOL_LABEL`
  추가 — Tooltip(`annotation`)과 **동일한 `TOOL_LABEL` 값**(예: `ConnBuilder`·`FKIK_Gen`)을 써 아이콘
  위 라벨과 툴팁이 일치한다(아이콘만으로 부족할 때 식별 보강). 값은 기존 축약 라벨 유지.
- **검증**: 아이콘 21개(A00060 V01/V02 2벌) 전부 **32×32 ARGB** 확인, drag-drop 21개 + build_icons
  `py_compile` 통과, PNG 는 `.gitignore` 대상 아님(추적 OK). 셸프 실설치 동작은 Maya 실행 확인 필요.
  계획서 신규 `docs/icon_plan.md`(Ari 분석·툴별 디자인표·도구체인·와이어링·검증). #Framework

> [!summary] A00110 animTool — Offset & Hold 기본 placeholder 10→20 (v01.19→01.20)
- Key Edit 탭 **Offset & Hold** 의 `Hold` 입력칸 placeholder 기본값을 `10` → `20` 으로 변경(UX 기본값
  조정, 로직 무변경). `version.py` 01.19→01.20. #A00110

> [!summary] Framework/테마 — Qt 툴 21개를 카테고리별 qss 색으로 통일
- **계획서 작성**(`docs/theme_category_unification_plan.md`) 후 적용. 각 툴 `launch.py` 의
  `ThemeManager.load_theme_*(..., "<color>")` 색 인자만 카테고리 표준으로 교체(로직 변경 없음).
- **카테고리→색**: Rigging=`coral_dark`(9), Animation=`blue_dark`(2), Modeling=`yellow_dark`(1),
  Facial=`red`(1), UE/Physics=`purple_dark`(1), Pipeline/Utility=`green_dark`(5), Template=`dark`(2).
- **변경 14건**: A00120/130/140(red)·A00150/170(yellow_dark)·A00160(green_dark)·A00190(blue_dark) →
  `coral_dark`; A00110(coral_dark)→`blue_dark`; A00080(dark)→`purple_dark`;
  A00210/211(blue_dark)·A00240(purple_dark)·A00250(coral_dark)→`green_dark`; A00008(red)→`dark`.
  나머지 7개는 이미 표준색이라 유지. 색 바뀐 13개 툴 `version.py` 패치 +1, 관련 가이드 docs(A00170/
  190/210/240) 테마 표기 갱신.
- **대상 외**: arch A(maya.cmds) 툴(A00000/10/20/30/40/50/60/70)은 `ColorThemeRegistry` 버튼색
  시스템이라 별도(후속). A00100/200/230 은 테마 호출 없음. **검증**: 변경 launch.py `py_compile` 통과,
  전 21개 매핑 재확인. 창 색 육안 확인은 Maya/standalone 실행 필요. #framework #theme

> [!summary] A00110 animTool — Key Edit 탭에 'Delete All Keys' 섹션 추가(v01.17→01.18)
- **Key Edit 탭에 접이식 섹션 'Delete All Keys' 추가**(기존 3섹션 → 4섹션, 기본 접힘). 선택 오브젝트를
  TSL(`JUN_mod_tsl_qt_v01`, `List Selected Objects` 버튼)에 리스트업하고, **리스트 전 항목의 모든
  키프레임을 일괄 삭제**하는 버튼을 둔다. 대상은 씬 선택이 아니라 리스트 항목(기존 Offset & Hold 와 동일 패턴).
- **코어**: `KeyframeManager.delete_all_keys(objects)` 추가 — `cmds.cutKey(clear=True)`(전 구간·전 채널,
  구간삭제와 달리 시간/채널 스코프 미적용), `undo_chunk` 로 Ctrl+Z 1회. 씬에서 사라진 항목은 `objExists`
  로 건너뛴다. 파괴적이라 UI 에 **확인 다이얼로그**(QMessageBox) 추가.
- **검증**: 변경 파일 `py_compile` 통과. 씬 키 삭제 동작은 Maya 실행 확인 필요. #A00110_animTool

> [!summary] A00180 abSymMesh — Mirror Deform 탭 'Selected vertices only' 추가(v02.03→02.04)
- **`Mirror Deform` 탭에 `Selected vertices only` 체크박스 추가**(Snap 탭과 동일 패턴). 체크 시 현재
  선택한 정점에만 미러 결과를 쓰고, 나머지는 anchor(Base / Deformed) 위치를 유지한다. 선택은 Base/Deformed
  어느 쪽이어도 됨(같은 토폴로지, 인덱스만 사용).
- **코어에 `indices` 인자 전파**: `snap_core.mirror_deformation` / `apply_mirrored_offsets`,
  `mesh_io.closest_surface_offsets` 가 `indices` 를 받아 **선택 정점만 계산**(무거운
  `getClosestPoint` 도 선택분만 실행). 출력은 전체 길이, 미선택 정점은 anchor 로 채운다.
- **검증**: indices 의미(선택만 미러·나머지 anchor 유지)를 순수 로직 수치 테스트로 확인, `py_compile` 통과.
  씬 편집 동작은 Maya 실행 확인 필요. #A00180_abSymMesh

> [!summary] A00180 abSymMesh — 탭 구조 + Snap to Sym / Mirror Deform 신규(v02.01→02.03)
- **UI 를 탭 구조로 재편**(`QTabWidget`): 기존 기능을 **`abSymMesh`** 탭으로, 신규 2탭 추가. 로그/푸터는
  탭 공용. 기존 `mesh_io`(벌크 정점 IO·undo 플러그인)·`undo_chunk` 인프라 재사용. 향후 기능도 탭으로 확장.
- **신규 `Snap to Sym` 탭** — 비대칭 메시를 대칭 레퍼런스에 **최근접 스냅**(Houdini nearpoint 이식,
  토폴로지 무관). 신규 **`app/core/snap_core.py`**(공간 격자 최근접 탐색, scipy 비의존, 순수 계산).
  - 모드: **Nearest Vertex**(기본, =VEX nearpoint) / **Closest Surface**(`MFnMesh.getClosestPoint`,
    `mesh_io.closest_surface_points`). Selected-only 옵션, Undo, 월드 공간.
  - **Make Symmetric Reference**(3방식): **Mirror one side**(정점 위치 반사 복사, 토폴로지 유지) /
    **Average both**(양쪽 평균) / **Mirror geometry (cut)**(반 잘라 미러, **토폴로지 재생성**;
    신규 **`app/core/mesh_ops.py`**: 시임 스냅→반대쪽 면 삭제→반사 복제+노멀 뒤집기→`polyUnite`/
    `polyMergeVertex`). Origin(World 0 / Pivot / BBox Center)·Source 면·Seam tol 옵션.
- **신규 `Mirror Deform` 탭** — **변형(deformed−base)을 미러 평면 건너편으로 반사**(Houdini Attribute
  Wrangle 미러 오프셋 이식). base/deformed 는 동일 토폴로지(오프셋은 인덱스로 읽음). **Apply onto =
  Base**(반사, VEX 동작) / **Deformed**(원변형 유지+반대쪽 반사=대칭화) 토글. 결과는 새 메시 출력 +
  Snap 탭 Reference 자동 연계.
  - **Match 방식 2종**: **Nearest Vertex**(`snap_core.mirror_deformation`, =VEX nearpoint) /
    **Closest Surface**(`mesh_io.closest_surface_offsets` — 표면 최근접점 + 면 정점 IDW 보간 →
    wrap/mesh-flow 식 부드러운 전이; 적용은 `snap_core.apply_mirrored_offsets`).
- **진행률 팝업**: 정점 수가 많은 무거운 작업(Snap / Make Symmetric Reference / Mirror Deformation)에
  게이지바 팝업(`QProgressDialog`, `_progress` 컨텍스트 매니저) + **Cancel**. 코어 루프에 `progress` 콜백을
  주기적으로 호출(약 200등분), 짧은 작업은 `setMinimumDuration(400)` 으로 팝업 생략. Cancel 시
  `_ProgressCancelled` 로 루프를 빠져나오며 **씬 편집(복제/setPoints) 전에 중단**해 잔여물이 남지 않게 했다.
- **견고성**: 격자 cell 을 '가장 긴 변' 기준으로 잡아 **평면/박판 메시에서 셸 탐색 폭발(무한 루프) 버그
  수정**, 탐색 반경을 점유 범위로 제한. **NaN/inf 정점 방어**(`_finite`/`count_invalid`로 건너뛰고 경고,
  원점이 NaN 이면 작업 중단).
- **검증**: 순수 로직(최근접 brute-force 대조·미러·대칭화·변형반사·NaN/엣지)을 별도 수치 테스트로 확인,
  변경/신규 파일 `py_compile` 통과. 씬 편집(geometry mirror·setPoints) 동작은 Maya 실행 확인 필요. #A00180_abSymMesh

> [!summary] A00090 ConnectionBuilder — 단일 창 + Mesh/Node 확장 + Create/Create All(v01.03→01.04)
- **단일 창 강제**: `main_window` 에 `WINDOW_OBJECT_NAME`+`setObjectName`, `launch.run` 이 새 창 생성 전
  `QApplication.topLevelWidgets()` 를 돌며 같은 objectName 창을 닫는다(A00145 패턴). 전역
  `window_instance` 가 리셋(리로드)된 뒤에도 이전 창을 확실히 닫아 **창 누적 방지**.
- **`Mesh for blendShape` → `Mesh / Node` 확장**: 입력 노드가 **mesh** 면 Rule `mapping` 이름으로
  blendShape target 복제(+deformer), **그 외(joint/transform/control)** 면 같은 이름의 double attr 생성.
  타입 판단·디스패치는 **신규 `app/core/target_builder.py`**(`TargetBuilder.is_mesh`/`build`)가 담당
  (BlendShapeManager·AttributeManager 는 그대로 재사용, core/ui 분리 유지).
- **버튼 분리**: 기존 `Create targets` → **`Create`**(콤보 선택 rule 1개) / **`Create All`**(`rules_v01`
  전체 rule). 다중 노드(콤마 구분) 지원. 생성 루프를 `undo_chunk` 로 묶음.
- **blendShape 누적(append)**: `BlendShapeManager.create_blendshape` 가 이미 blendShape 가 있으면 새
  target 만 다음 인덱스로 추가(`blendShape -edit -target`). "Create All" 로 여러 rule 의 target 이 한
  blendShape 에 모두 들어가도록 수정(기존엔 두 번째 rule 부터 통째로 skip 되던 문제 해결).
- **검증**: 변경 7개 파일 `py_compile` 통과. 노드 생성 동작은 Maya 실행 확인 필요. #A00090_ConnectionBuilder

> [!summary] A00145 RigConnect — Matrix Constraint 이식(Constraint 탭, v01.06→01.07)
- **레거시 `JUN_PY_MatrixCon_01_01.py`(행렬 컨스트레인트) 기능을 A00145 Constraint 탭에 이식**.
  `Matrix Constraint` 체크 시 일반 `*Constraint` 노드 대신 **`multMatrix`+`decomposeMatrix` 네트워크**로
  구속한다(컨스트레인트 노드 누적 없이 부모공간/오프셋 명시 제어).
- **신규 `app/core/matrix_constraint_manager.py`**(UI 비의존, `(made, errors)` 반환): `multMatrix`
  (offset·`target.worldMatrix`·`follower.parentInverseMatrix`) → `decomposeMatrix` → follower 채널 연결.
- **UI**: Constraint 탭에 `Matrix Constraint` 체크박스 + `Translate/Rotate/Scale` 채널 체크박스(기본 전부 on)
  추가. 체크 시 채널 토글 활성·constraint 종류 라디오 비활성(`_on_matrix_mode_toggled`). `Maintain Offset`
  은 일반 모드와 공유. `on_constrain` 에 분기 추가, `_run`(undo) 재사용.
- **원본 버그/개선 반영**: ① scale 연결이 translate 플래그로 잘못 게이팅되던 버그 수정, ② `maintain_offset`
  미사용 버그 수정(off 면 follower 가 target 에 스냅), ③ **joint 면 jointOrient 역행렬로 rotate 출력만 보정**
  (translate/scale 위치가 회전되지 않게 분리), ④ `parentInverseMatrix[0]` 사용으로 "부모 없으면 단위행렬
  그룹 생성" 분기 제거, ⑤ broadcast(target 1개→다수 follower) 지원, ⑥ 재실행 시 기존 입력 연결 해제·항목별
  예외 수집.
- **검증**: 변경 5개 파일 `py_compile` 통과. 노드 네트워크 실제 동작은 Maya 실행 확인 필요. #A00145_RigConnect

> [!summary] Framework 공통화 — 툴 전수 분석 후 저위험 공용 모듈 2종 승격
- **`JUN_All/tools` 33개 툴을 전수 분석**해 여러 툴에 복붙된 코드 패턴(undo 청크, 파일 탐색기
  Reveal, prefs 영속화, CollapsibleBox 등)을 찾고, 그중 **동작 변화가 없는 저위험 2종만** Framework
  로 승격(나머지는 호출부 API 변경이 커 다음 차수로 보류).
- **신규 `Framework/core/maya_undo.py`** — `undo_chunk()` 컨텍스트 매니저. `cmds.undoInfo(openChunk)/
  closeChunk` 보일러플레이트(여러 툴에 32곳 복붙)를 하나로 통일, 예외 시에도 `finally` 로 chunk 닫기
  보장. **15개 파일·28곳**을 `with undo_chunk():` 로 교체(`try/finally`→`with`, `try/except/finally`→
  `with` 안에 try/except 중첩, 동작 동일): A00110_animTool core 5(keyframe·copykey·offset_hold·pose·
  mirror), A00120 fkik_matcher, A00010_V02 hik_manager, A00200 arkit, A00150·A00160·A00170·A00180·
  A00190·A00145·A00060_V02. `finally` 가 `currentTime` 복원·constraint 정리까지 하는 **복잡 블록 4곳**
  (bake_manager·follow_match_manager·fkik_matcher 2)은 재들여쓰기 위험을 피해 의도적으로 보존(이미
  올바르게 chunk 를 닫음).
- **신규 `Framework/core/file_opener.py`** — `open_path()`(폴더 열기 / 파일 선택 reveal, win·mac·linux).
  A00240_PathTool 의 검증된 구현을 승격하고, A00210_FileManager(main_window·lineage_tab)·A00220_
  BackupTool 이 각자 복붙하던 `explorer /select,` 로직을 이 모듈 위임으로 교체(미사용 `sys`/`subprocess`
  import 정리). A00240 의 기존 `path_opener.py` 는 re-export 1줄로 축약해 호출부 무수정 유지.
- **검증**: 편집한 21개 파일 `py_compile` 통과, `open_path` 임포트·빈/없는 경로 예외 동작 확인.
  순감 105줄(190 추가/295 삭제). Maya 내부 undo 단일스텝 동작은 Maya 실행 확인 필요. #Framework

## 2026-06-22

> [!summary] A00250 SceneMemo — 씬 오브젝트 메모 툴 신규(v01.00)
- **신규 in-Maya PySide 툴**(A00110 기반, B형): 씬의 메시/커브/트랜스폼 등에 **사용자 메모**를
  남기고 씬을 닫았다 다시 열어도 보존, 한국어 입력·사후 편집 가능.
- **저장 방식**: 씬 내부 `JUN_memo_store`(network) 노드의 `junMemoData`(string/JSON)에 **노드 UUID
  키**로 저장 → `.ma/.mb` 안에 들어가 Save As/복사/리네임에도 유지. 노드는 `lockNode` 로 보호.
  `json.dumps(ensure_ascii=False)` 로 한국어 안전. core(`memo_store`/`memo_io`) ↔ ui 분리.
- **기능**: Add Selected / Remove / Save Memo / Search / Clean Orphans / Export·Import(마야 파일 옆
  `JUN_memo/<scene>_memo.json` 사이드카, 백업·공유용). 미저장 씬은 Export 불가.
- **다중 선택 일괄 메모**: 테이블 여러 행 선택 후 Save Memo 하면 선택한 모든 오브젝트에 같은 메모
  일괄 저장. **씬 선택은 행 우클릭 → Select in Scene 메뉴**로 제공(별도 버튼 없음). #A00250_SceneMemo

> [!summary] A00090 ConnectionBuilder — Source/Target 리스트화 + 1→n / n→n batch 연결(v01.02→01.03)
- **MetaHuman RBF 연결 UI 개편**: 단일 `QLineEdit` 입력을 **여러 노드 batch** 처리로 바꿨다.
  - **BlendShape 입력행 제거**(상단 `Mesh for blendShape`/Create targets·`BlendShapeManager` 는 유지).
  - **용어 정리**: *Base→Source*, *Driver→Target*(내부 식별자 `solver_node`/`driver_node` 의미는 유지).
  - **Source/Target 을 재사용 리스트 위젯**(`Framework/qt/MOD_tsl_qt_v01.JUN_mod_tsl_qt_v01`)으로 교체하고
    **좌·우로 나란히 배치**. `Is Solver` 는 Source 컬럼 상단, `Set Attr`/`Del Attr` 는 각 리스트에
    `add_button` 으로 부착(리스트 전체 노드 대상). 모든 버튼 높이 축소.
  - **Pair mode 체크박스**(`n->n (index pair)`): 해제=**1→n broadcast**(첫 Source→모든 Target),
    체크=**n→n index pair**(`Source[i]→Target[i]`, 개수 다르면 `[ERROR]` 후 무동작). Connect All /
    Connect / Disconnect / Validate 가 모두 이 모드를 따른다. n→n 도 선택 rule 1개의 mapping 을 전 쌍에 적용.
  - core(connection/attribute/blendshape/intermediate manager) 무수정 — UI 가 짝마다 단일 rule 로직을
    루프 호출하도록 재사용. 가이드 문서(신규 `A00090_ConnectionBuilder.md`)·plan·version 동기화. #A00090_ConnectionBuilder

> [!summary] A00210 FileManager — 노드 경로 팝업(v01.19) + 세팅 Profile(v01.20) + Log history 편집/삭제(v01.21)
- **Lineage 노드 우클릭 Reveal in File Explorer 동작 정리**(v01.18→01.19): 파일이 이 PC 에 있으면
  예전처럼 탐색기에서 폴더 열고 파일 선택(팝업 없음), **로컬에 없으면**(예: 다른 PC 에서 A00211 로 만든
  그래프) 그냥 실패하지 않고 그 노드 파일의 **경로를 선택·복사 가능한 팝업**으로 보여준다. 메뉴는 노드에
  key 가 있으면 활성(파일이 로컬에 없다는 이유로 회색 처리하지 않음). `node_path_info` 헬퍼 신설.
- **File Manager 세팅 Profile**(v01.19→01.20): Project Root·Store Repo·Scan Dir·Remote·Branch·Remote
  URL·Author·Recursive·Show Recorded Only 등 **사용자 입력 세팅 전체를 이름붙인 프로파일(JSON 1개)** 로
  저장·전환. 상단 **Profile** 그룹(콤보 + New/Rename/Delete), 전환 시 현재 값 **자동 저장** 후 새 프로파일
  로드 + Lineage/Path Structure 목록 새로고침, 창 종료 시 활성 프로파일 저장, 다음 실행 때 복원
  (`active.json`). 저장 위치 `~/.jun_filemanager/profiles/<name>.json`. 구 단일 `prefs.json` 은 첫 실행 시
  `Default` 로 1회 마이그레이션(원본 `.bak` 보존). `prefs.load()/save()` 는 활성 프로파일 대상으로 동작해
  하위호환 유지(A00211 무수정 연동). 가이드 문서·CHANGELOG·version 동기화. #A00210_FileManager
- **Log history 항목 편집/삭제**(v01.20→01.21): Log history 헤더에 **Edit 버튼** 추가 → `Edit Log
  History` 다이얼로그에서 항목별 **author/note 편집·개별 삭제**(timestamp 보존, 구조적 편집). 가이드
  문서·CHANGELOG·version 동기화. #A00210_FileManager

> [!summary] 신규 툴 A00211_RefLineage — 마야 씬 reference 관계 → A00210 Lineage JSON 내보내기(v01.00)
- **현재 Maya 씬의 reference 관계(중첩 포함)를 스캔해 A00210 Lineage 그래프로 내보내는 Maya 내 PySide
  툴 신설**. `cmds.referenceQuery` 로 씬→직속→중첩 reference 트리를 따라가 파일 1개=노드(절대경로 dedup,
  씬은 루트), **참조 대상→참조하는 파일** 방향의 reference 엣지(A00210 규약)로 기록한다. 포맷·설정 단일
  소스를 위해 A00210 의 `lineage`/`store`/`prefs` 모듈을 그대로 재사용 — JSON 포맷이 동일해 Lineage 탭에서
  바로 열린다(키는 project_root 상대, 루트 밖이면 빈 값). 미니 UI(Scan/Export) + 헤드리스
  `export_scene_references()`. Windows 타 드라이브 파일의 `relpath` ValueError 도 '루트 밖'으로 처리.
  가이드 문서(신규 `A00211_RefLineage.md`)·CHANGELOG 동기화. #A00211_RefLineage

> [!summary] A00220 BackupTool — 백업 성공 순간 공룡이 공중에서 360° 회전(v01.06) + Target Files 파일명 표시·Reveal(v01.07)
- **파일이 실제로 백업된 순간을 UI 로 또렷이 표시**(v01.05→01.06): 지금까지는 저장 순간 작은 점프(hop)
  한 번이라 놓치기 쉽고, 변경이 없어 실제로 복사되지 않아도 뛰던 문제가 있었다. `DinoWidget.spin()` 을
  신설해 **공룡이 공중에서 360° 한 바퀴 회전**하도록 하고, `_backup_targets` 에서 **한 개라도 백업에
  성공했을 때(`ok > 0`)만** 트리거(저장 상태 진입만으로는 안 돎). 회전은 스프라이트 중심 기준
  `translate/rotate`, 회전 중 모서리가 잘리지 않게 위젯 세로 여유를 대각선만큼 확보하고 주기 점프를 멈춘다.
  걷기(Active)·서있기(Deactive) 동작은 유지. PySide6 오프스크린으로 24프레임(0~360°) 잘림 없음 검증.
  CHANGELOG·version·가이드 문서 동기화. #A00220_BackupTool
- **Target Files 파일명만 표시 + 우클릭 Reveal**(v01.06→01.07): Target Files 목록을 전체 경로 대신
  **파일명(basename)만 표시**(전체 경로는 `Qt.UserRole`+툴팁에 보존, 백업/중복검사/prefs 는 전체 경로
  사용). 항목 **우클릭 → Reveal in File Explorer** 로 탐색기에서 파일 선택 상태로 열기(win `explorer
  /select,` / mac `open -R` / linux `xdg-open`). CHANGELOG·version 동기화. #A00220_BackupTool

> [!summary] A00210 Lineage — Reference 엣지 · 노드/엣지 색 지정 · 화살표 겹침 분리 · 엣지 종류 변환(v01.16→01.18)
- **A00210_FileManager Lineage 탭 기능 묶음**(v01.15→01.18):
  - **Reference(점선) 엣지**: 마야 파일 간 reference 관계를 계보(parents)와 별도로 표현. Connect Mode
    의 엣지 종류 드롭다운에서 `Reference (dashed)` 선택 후 참조 대상→참조하는 파일로 드래그. 레인/색/
    Auto Layout 에 영향 없고 자체 순환 검사·채운 삼각 화살촉. 노드별 `references` 로 저장.
  - **노드/엣지 색 수동 지정**: 러버밴드로 노드·엣지를 골라 `Set Color...` 로 한 번에 색 지정, `Reset
    Color` 로 기본색 복귀. 엣지 색은 그래프 JSON 의 `edge_colors`(`kind:src>dst`)로 저장(끝점 노드
    삭제 시 정리).
  - **겹치는 화살표 분리**: 같은 두 노드 사이의 계보+reference 화살표가 포개지던 것을 가로로 균등하게
    벌려 각 화살표·화살촉을 구분.
  - **엣지 종류 즉시 변환**: 화살표를 선택한 상태에서 엣지 종류 드롭다운을 바꾸면 선택된 화살표가
    Lineage↔Reference 로 즉시 변환(방향·색 유지, 모양 실선 빈 V↔점선 채운 삼각으로 갱신, 순환 거부).
  - 가이드 문서(A00210)·CHANGELOG·version 동기화. #A00210_FileManager

> [!summary] A00120 FKIK 구간 베이크 시 바깥 키 보존(v01.05)
- **A00120_FKIK 구간 베이크가 베이크 구간 밖의 기존 키를 모두 지우던 버그 수정**(v01.04→01.05):
  0~1000 키가 있을 때 500~600 만 베이크하면 그 밖의 키가 전부 사라졌다. 원인은 임시
  `parentConstraint` 가 걸리는 순간 Maya 가 `pairBlend` 를 끼워 기존 `animCurve` 를 플러그에서
  분리해, `bakeResults` 의 `preserveOutsideKeys=True` 가 바깥 키를 보지 못한 것. 컨스트레인트를
  걸기 **전에** `[start, end]` 밖 키를 값/탄젠트(타입·fixed 각도/가중치)로 스냅샷
  (`_snapshot_outside_keys`)하고 베이크·정리 후 복원(`_restore_outside_keys`)하도록 했다.
  `bake_constraint()` 도 재생 범위 기준 동일 가드 + `preserveOutsideKeys=True` 보강. 복원은
  `suspend_refresh()` 로 감싸 프레임마다 리드로우 안 함. 가이드 문서(신규 `A00120_FKIK.md`)·
  CHANGELOG·version 동기화. #A00120_FKIK

> [!summary] A00110 animTool · A00145 RigConnect — 리스트업 후 창/리스트가 작아지던 문제 수정(v01.17 / v01.04)
- **select 로 오브젝트를 tsl 에 채운 뒤 창 세로가 갑자기 작아지던 문제 수정**. (1) 공유 리스트 위젯
  `Framework/qt/MOD_tsl_qt_v01.py` 에 **최소 높이 바닥값 100px**(`DEFAULT_LIST_MIN_HEIGHT`, 명시값
  없는 리스트에 적용 — A00110 의 모든 리스트가 해당). (2) **A00110**(v01.16→01.17): `_fit_window` 가
  **탭 전환 시에는 grow_only**(늘리기만, 줄이지 않음)로 바뀌어 콘텐츠 짧은 탭을 눌러도 창이 축소되지
  않음(섹션 접기/펴기만 콘텐츠 높이로 축소). 공유 로그창 **maxHeight 160** 추가로 창 재확장 시 로그
  독식 방지. (3) **A00145**(v01.03→01.04): 창 **최소 크기 480×560** 보장(자동 리사이즈 없는 툴이라
  하한만으로 충분, 리스트들은 이미 `list_min_height` 명시). 가이드 문서(A00110)·WORKLOG 동기화.
  #A00110_animTool #A00145_RigConnect

> [!summary] A00145 RigConnect — Locators 자동생성 + parentConstraint Interp Type 고정(v01.04→01.06)
- **parentConstraint Interp Type 고정**(v01.05): constraint 의 `interpType` 을 **Shortest(2)** 로 강제 →
  다중 joint 가중 평균 시 짐벌 튐(회전 보간 폭주) 방지.
- **Locators 버튼 추가**(v01.06): follower 없이 **로케이터를 자동 생성**한 뒤 동일 스킨 웨이트 constraint
  를 적용. *average* = centroid 에 로케이터 1개 / *per-vertex* = 버텍스마다 1개. 생성 로케이터는
  `RigConnect_skinLoc_grp#` 로 그룹화하고 Followers 목록을 자동으로 채운다(신규
  `core/skin_constraint_manager.py`). 가이드 문서·version 동기화. #A00145_RigConnect

> [!summary] A00210 FileManager Lineage 탭 — 중간버튼 팬 범위 무제한화(v01.15)
- **A00210_FileManager Lineage 캔버스 중간버튼 팬이 막히던 문제 수정**(v01.14→01.15): 중간버튼 드래그
  팬은 스크롤바를 움직이는 방식이라 이동 범위가 `sceneRect`(콘텐츠 바운딩 + 여백 200px)에 갇혀, 노드
  영역 바깥 200px 에서 더 끌리지 않았다. (1) 초기 `sceneRect` 여백을 **한 뷰포트 크기 이상**(현재 줌
  배율로 환산, 최소 800)으로 넓히고, (2) `LineageView._pan_by` 신설 — 팬이 경계 600px 안으로 들어오면
  그 방향으로 `sceneRect` 를 계속 키워 노드 바깥으로도 자유롭게 이동(사실상 무한 팬). 다음 렌더에서
  콘텐츠 기준으로 다시 줄어 영구 부풀지 않음. 가이드 문서·CHANGELOG·version 동기화. #A00210_FileManager

## 2026-06-19

> [!summary] 신규 툴 A00240 PathTool — 경로 런처(카테고리·우클릭 편집·순서 변경·집/회사 프로파일) + Tree 탭(경로 트리뷰·깊이/파일/확장자 필터·Expand·우클릭 Reveal·폴더/파일 아이콘, v01.02)·버튼 Change Category(v01.03, standalone PySide6) + A00145 RigConnect Match 탭 신설(MEL Match Tool V05.04 이식·리팩토링, v01.03)·Constrain 탭에 Skin Weight to Constraint 추가(v01.02, 접이식) + A00220 BackupTool Settings 접이식화·창 슬림(v01.03)·스핀박스 화살표 PNG 복구·백업 log.txt(v01.02)·상태 표시를 Chrome Dino 애니메이션으로(v01.04)·Auto Backup 저장 즉시 백업(v01.05) + A00110 animTool Follow 탭 강화(Maintain Offset · 1<-n · Get Current) + A00110/A00120 뷰포트 프리즈(refresh suspend 누수) 수정 & Force Refresh 버튼 + A00210 FileManager Lineage 노드 로그 동기화(v01.08)·노드/연결 삭제 & 다중선택(v01.09)·러버밴드 intersect 선택(v01.10)·File Manager Show Recorded Only 필터(v01.11)·Load Image 시작 경로 thumbs 폴더(v01.12)·Settings Branch 편집형 드롭다운(v01.13)·검색/확장자/Recorded 필터 & 우클릭 Show in File Explorer & Log history Expand(v01.14) + Framework dark 테마 Win10 트리 행 가독성
- **A00230_StartupTool 부팅 시 툴 자동 실행 확장**: 기존 "부팅 시 폴더 팝업" 런처를 **폴더 + standalone
  툴 자동 실행**으로 확장. 신규 부팅 코디네이터 `startup.py` 가 `config/startup.json`(기존 `folders.json` 대체,
  `folders` + 신규 `tools` 배열)을 읽어 폴더를 탐색기로 팝업한 뒤 각 툴의 `launch.py` 를 `pythonw` **분리
  프로세스**로 실행(프로세스 분리로 `tools.<tool>.app.*` 패키지 충돌 없음). 기본 등록: A00210 FileManager ·
  A00220 BackupTool · A00240 PathTool. **새 툴 추가는 `tools` 에 `{ "tool": "A002NN_XXX", "enabled": true }`
  한 줄**(표준 위치 밖은 `launch` 경로 override) — 재설치 없이 다음 부팅에 반영. `install.py` 런처(.vbs)가
  `startup.py` 를 가리키도록 변경(기존 설치자는 `install.py` 1회 재실행). `open_folders.py` 는 폴더 로직 모듈로
  재사용·단독 실행 유지. README 갱신. #A00230_StartupTool
- **A00220_BackupTool Auto Backup = 저장 즉시 백업**(v01.04→01.05): Auto Backup 모드가 *주기 타이머*가
  아니라 *저장 시점*에 백업하도록 변경. 대상 파일을 `QFileSystemWatcher` 로 실시간 감시하다가 디스크에서
  바뀌는 즉시(=저장 순간) 그 파일만 백업. 연속 저장·임시파일 교체식 저장을 다루도록 변경을 ~300ms 디바운스
  후 처리하고 감시 경로를 재등록. 기존 `Interval` 주기 타이머는 감시가 놓친 변경을 잡는 **fallback** 으로 유지
  (mtime 비교로 중복 백업 방지). 실행 중 Auto Backup 토글 시 감시 즉시 시작/정지. 복사 루프를 `_backup_targets`
  로 분리해 주기 사이클·저장 감지가 공용. 안내 문서 동기화. #A00220_BackupTool
- **A00220_BackupTool 상태 표시 = Chrome Dino**(v01.03→01.04): Control 의 상태 글자
  (`Deactive`/`Active...`/`Saving`)를 **Chrome-Dino(T-Rex) 픽셀 애니메이션**으로 교체. 신규
  `app/ui/dino_widget.py` 가 코드 내장 비트맵을 **QPainter 로 그림**(이미지 에셋 0개·테마 무관·exe 번들 불필요).
  Active=제자리 달리기(다리 2프레임 교차 + 바닥 점선 스크롤) + 약 2.6초마다 **포물선 점프**, Deactive=가만히
  서 있음, Saving=`hop()` 으로 1회 추가 점프 강조. 자체 33fps QTimer 구동, 기존 점(...) 타이머(`_dot_timer`)·
  관련 메서드 제거. offscreen PNG 렌더로 4포즈(서기/달리기 A·B/점프) 모양 확인 후 통합. #A00220_BackupTool
- **A00240_PathTool 신규**(v01.00): 자주 쓰는 폴더 경로를 버튼으로 만들어 **클릭 시 탐색기로 여는** standalone
  PySide6 런처. **Create** 그룹의 `Category`(카테고리=`QGroupBox` 생성)·`Path` 버튼 — Path 는 **카테고리·버튼
  이름·경로(Browse)를 한 다이얼로그**(`AddPathDialog`)에서 한 번에 입력. 버튼 클릭=경로 열기(폴더는 그 폴더,
  파일이면 폴더+선택; Win `explorer /select,` 우선·mac/linux 폴백, `core/path_opener.py`). **수정/삭제는
  우클릭 메뉴**(카테고리: Rename/Delete, 버튼: Rename/Change Path/Delete) — 항목이 늘어도 화면 유지. 집/회사
  처럼 **JSON 별로 나뉜 Profile**(상단 콤보 + New/Rename/Delete, 최소 1개 유지, 마지막 활성 기억) 추가 —
  프로파일 1개=JSON 1개로 완전 분리. 저장은 `%USERPROFILE%` 가 아니라 **툴 내부 `data/`**(`profiles/<name>.json`
  + `active.json`), **onefile exe 면 exe 옆 `data/`** 로 분기(임시폴더 휘발 회피), `data/` 는 `.gitignore`.
  구버전 `~/.jun_pathtool/shortcuts.json` 은 첫 실행 시 `Default` 로 자동 마이그레이션. 탭은 `QTabWidget`
  (현재 ShortCut 1개, 확장 대비). core(prefs/path_opener)·ui 분리, 툴 고유 import 경로. #A00240_PathTool
- **A00240_PathTool 버튼 Change Category(카테고리 이동)**(v01.02→01.03): ShortCut 탭에서 **Path 버튼
  우클릭 메뉴에 Change Category** 추가 — 현재 카테고리를 뺀 목록(`QInputDialog.getItem`)에서 대상을 골라
  버튼을 그쪽 끝으로 이동(`_change_button_category`). 대상에 같은 이름 버튼이 있으면 차단, 다른 카테고리가
  없으면 안내. 버튼 데이터(경로 포함) 그대로 옮기고 프로파일 JSON 저장·재렌더. 안내 문서 동기화.
  #A00240_PathTool
- **A00240_PathTool Tree 탭 신설**(v01.01→01.02): 입력 경로를 **트리뷰**(QTreeWidget)로 보여주는 새 탭
  (A00210 Path Structure 의 트리 표시 취지). 옵션: (1) **Depth** 스핀박스(0=All, 변경 시 자동 재빌드),
  (2) **Show files** 체크박스(끄면 폴더만, File Types 자동 비활성), (3) **File Types** 체크 드롭다운(발견 확장자
  중 표시할 것만, A00210 File Manager 와 동일 `_CheckableMenu`), (4) **Expand** 버튼(800×620 큰 창),
  (5) **우클릭 → Reveal in File Explorer**(`path_opener.open_path` 재사용, 메인/Expand 트리 공용). 폴더/파일은
  **QStyle 표준 아이콘**으로 구분. Build 시 모든 파일을 캐시하고 Show files/File Types 는 재스캔 없이 즉시 필터,
  Depth/Path 만 재스캔. 로직은 새 `core/tree_scanner.py`(UI 비의존, `build_tree`/`collect_extensions`)로 분리.
  안내 문서 동기화. #A00240_PathTool
- **A00240_PathTool 카테고리 순서 변경**(v01.00→01.01): 카테고리가 생성 순서로만 쌓이고 순서를 못 바꾸던
  것을, 카테고리 **우클릭 메뉴에 Move Up / Move Down**(양 끝단 비활성) 추가로 자유롭게 재정렬. 화면 순서=
  `data["categories"]` 리스트 순서라 인접 항목과 swap 후 저장·재렌더(`_move_category`), 바뀐 순서는 프로파일
  JSON 에 저장. #A00240_PathTool
- **A00210_FileManager File Manager 탭 검색·필터·탐색기 연동 강화**(v01.13→01.14): (1) **Scan 이 전
  확장자 리스트업** — `.mb`/`.ma` 만이 아니라 모든 포맷(`scanner.scan(extensions=None)`). (2) **File Types
  체크 드롭다운** — 스캔에서 발견된 확장자 중 표시할 것만 체크(All 포함). 여러 개 연속 토글해도 안 닫히는
  `_CheckableMenu`(mouseReleaseEvent 에서 `action.trigger()` 후 닫기 차단), 버튼 라벨에 선택 요약. (3) **Name
  filter** — 목록 위 입력란+`Filter`(또는 Enter)로 제목에 키워드 포함 파일만(대소문자 무시), 빈 값=전체. 적용
  키워드를 입력란과 분리(`_name_filter`)해 다른 필터 토글 시에도 일관. (4) 세 필터(이름·확장자·Recorded)를
  `_apply_file_filter` 에서 **재스캔 없이 중첩** 적용. (5) **우클릭 → Show in File Explorer** — FileTable 에
  컨텍스트 메뉴+`reveal_requested` 시그널, `abs_path` 를 `explorer /select,`(win)/`open -R`/`xdg-open` 으로
  선택 표시(Lineage 탭 reveal 방식 재사용). (6) **Log history Expand** — 상세 패널이 좁아 긴 로그가 안 보이는
  문제로, 라벨 옆 `Expand` 버튼이 전체 폭 리사이즈 가능한 읽기전용 창에 같은 로그를 띄움(스냅샷). 안내 문서
  동기화. #A00210_FileManager
- **A00210_FileManager Settings Branch 편집형 드롭다운**(v01.12→01.13): Settings 의 **Branch** 입력을
  `QLineEdit` → **editable `QComboBox`**(`_BranchComboBox`)로 변경 — 드롭다운을 펼칠 때마다 Store Repo 의
  **실제 git 브랜치(로컬 + 원격추적, 중복 제거)** 를 채워 올바른 이름을 고르게 한다(목록에 없는 이름은 직접
  타이핑도 가능, 첫 clone/fetch 전 대비). `main`/`master` 혼동 같은 브랜치명 불일치로 나던
  `src refspec ... does not match any` push 오류를 줄임. 네트워크 fetch 없이 로컬 ref 만 읽는 새
  `GitSync.list_branches()`(`git branch` + `git branch -r --format`, `origin/HEAD` 류 제외) 추가. 안내
  문서 동기화. #A00210_FileManager
- **A00210_FileManager Load Image 시작 경로 = Store Repo/thumbs**(v01.11→01.12): File Manager 탭의
  **`Load Image...`** 파일 다이얼로그가 홈(`~`) 대신 **Store Repo 의 `thumbs` 폴더**에서 열리도록 변경 —
  거기 이미 저장된 썸네일을 **여러 파일에 재사용**하기 쉽게. Store Repo 미설정·thumbs 폴더 부재 시 홈으로
  폴백(`_thumbs_start_dir`). #A00210_FileManager
- **A00210_FileManager File Manager 탭 Show Recorded Only 필터**(v01.10→01.11): Scan 옆 **Recursive**
  옆에 **`Show Recorded Only`** 체크박스 추가 — 켜면 **record(Save Record)가 있는 파일만** 목록에 남긴다.
  Recursive 스캔으로 수많은 파일이 잡힐 때 **이 툴로 관리(기록) 중인 파일만** 추리는 용도. 마지막 scan 결과를
  원본으로 캐시(`_scanned_entries`)해 두고 `_apply_file_filter`(`has_record` 필터)로 **재스캔 없이 토글 즉시**
  반영, 상태는 prefs(`show_recorded_only`)에 저장. 용어는 툴 기존 어휘(Save Record·Record 컬럼·
  `records/<key>.json`)와 맞춰 **Recorded** 채택. 안내 문서 동기화. #A00210_FileManager
- **A00145_RigConnect Match 탭 신설**(v01.02→01.03): MEL `Match Tool V05.04` 를 **첫 번째 탭**으로
  이식·리팩토링. `Targets`/`Followers` TSL 로 follower 를 target 의 **위치/회전에 매칭**. 핵심 개선:
  (1) **rotateOrder 가 달라도 안전** — MEL 이 follower 의 rotateOrder 를 타깃 것으로 바꿨다 되돌리던
  방식(+ mesh/cluster 분기에서 복원이 누락되던 버그)을 버리고 `cmds.matchTransform`(임시 transform 경유)
  으로 통일. (2) **버텍스 타겟 노말 매칭** — 타겟이 `mesh.vtx[i]` 면 정점 월드 위치로 이동 + follower 의
  **+Y 축을 정점 노말에 정렬**(`maya.api.OpenMaya` `MFnMesh.getVertexNormal`, `_basis_from_normal`).
  (3) **버텍스 개별 리스트업** — 공용 TSL 위젯의 `cmds.ls(fl=True)` 로 `mesh.vtx[0:13]` 가 하나로 묶이지
  않고 정점별 항목으로 들어감. (4) **Create(Locators/Sphere/Cube)** 버튼은 "생성→목록→수동 Match" 가
  아니라 **타겟 수만큼 생성 후 즉시 매칭**하고 Followers 목록을 채움(곡선 데이터는 MEL 그대로 이식).
  (5) mesh→월드 centroid(getPoints 평균)·cluster→월드 rotatePivot 로 위치 매칭(MEL 의 local-space
  rotatePivot 질의 버그 수정), `Swap` 유지, **Blend Shape 버튼 제거**. 로직은 새
  `core/match_manager.py`(UI 비의존)로 분리. 안내 문서(`docs/A00145_RigConnect.md`) 동기화.
  #A00145_RigConnect
- **A00145_RigConnect Skin Weight to Constraint 추가**(v01.01→01.02): Constrain 탭을 **접이식 2섹션**
  (`CollapsibleBox`)으로 — 기존 **`Constraint`(펼침)** + 신규 **`Skin Weight to Constraint`(접힘)**. 선택한
  버텍스의 **스킨 웨이트 비율**대로 영향 joint 들을 constraint weight 로 follower 에 `parentConstraint`
  (예: `hip:0.2/spine_01:0.5/spine_02:0.3` → 그 비율의 weightAliasList setAttr). `Vertices`/`Followers`
  TSL 2개, `Max Influence`(상위 N joint 만 남기고 합=1 정규화, 0=무제한), `Maintain Offset`, **`Per-vertex`
  체크박스** — 해제 시 모든 버텍스 웨이트 **평균**을 전 follower 에 동일 적용, 체크 시 `vertices[i]→
  followers[i]` **1:1**(개수 일치). 로직은 새 `core/skin_constraint_manager.py`(skinCluster 탐색 →
  `skinPercent` 웨이트 조회 → 정규화 → weighted parentConstraint)로 분리. #A00145_RigConnect
- **A00220_BackupTool Settings 접이식화 + 창 슬림 + 스핀박스 화살표 복구**(v01.01→01.03): **Settings 를
  접이식 섹션**(공용 `JUN_mod_collapsible_qt`, A00110 과 동일)으로 바꾸되, 접을 때 **위쪽 파일 목록
  (textscrollList)이 늘어나던 문제**를 수정 — 토글 시 창을 sizeHint 로 재맞추면 늘어난 공간을 expanding
  목록이 흡수하므로, 대신 **본문 높이(`body_height()`)만큼만 창을 줄이거나 늘려** 목록 크기를 고정.
  `resizeEvent` 로 접힘 상태 높이를 추적해 사용자가 직접 창을 키우면 목록은 그에 맞춰 변함. 창을 세로형
  (~350px)으로 슬림화(Save Mode 라디오·분/초를 세로 적층, 스핀박스 폭 축소, 긴 라벨·버튼 단축). **분/초
  스핀박스 화살표가 직사각형으로 보이던 문제**는 테마 qss 가 `::up-arrow/::down-arrow` 를 CSS
  border-삼각형으로 그려 일부 Qt 에서 안 그려진 게 원인 — **9×9 PNG 화살표 아이콘**(`sb_up/down_dark/
  light.png`) `image:` 로 교체(다크=밝은 화살표/라이트=어두운 화살표), light 테마엔 누락됐던 `::up-button/
  ::down-button` 서브컨트롤 정의 추가, 12개 `*.qss` 일괄. `theme_manager` 는 `@STYLES@` 토큰을 qss 폴더
  절대경로로 치환(`_read_qss`)해 실행 위치와 무관하게 아이콘 경로 해석. 백업 1회마다 **`log.txt`** 에
  시각+원본→백업본 한 줄 누적(v01.02). (Max Versions 는 Version Up 모드 전용이라 Overwrite 모드에서
  비활성 — 의도된 동작.) #A00220_BackupTool #Framework
- **A00210_FileManager Lineage 러버밴드 intersect 선택**(v01.09→01.10): 빈 캔버스 드래그 다중선택을
  `ContainsItemShape`(사각형에 **완전히** 든 것만) → **`IntersectsItemShape`**(사각형에 **일부라도 걸친**
  노드·엣지 선택)로 변경 — 큰 노드/긴 화살표도 전체를 감싸지 않고 살짝 걸치면 잡힌다. #A00210_FileManager
- **A00210_FileManager Lineage 노드/연결 삭제 + 다중선택**(v01.09): Lineage 탭에서 **연결선(엣지)도
  클릭 선택**(얇은 곡선용 hit 영역 확대 + 선택 시 흰색·굵게 강조)해 **Delete/Backspace** 로 선택(노드·연결
  혼합)을 **확인 팝업 없이** 삭제 — 연결 삭제는 자식의 해당 부모 링크만 제거, 노드 삭제는 고아 참조까지 정리.
  **빈 캔버스 드래그 = 러버밴드 다중선택**(`ContainsItemShape`), Connect Mode 중엔 러버밴드 off(선 긋기
  집중)·해제 시 복원. **Delete Node** 버튼도 선택 노드를 **일괄(팝업 없이)** 삭제로 변경. #A00210_FileManager
- **A00210_FileManager Lineage 노드 로그 동기화**(v01.08): Lineage 탭 **Node** 패널에 **Log history
  (from record)** 읽기 전용 영역 추가 — File Manager 탭의 Save Record 가 쓰는 `records/<key>.json` 을
  `store.load(node.key)` 로 그대로 읽어 같은 작업 기록을 동일 포맷(`[timestamp] author` + note)으로 표시.
  노드 선택 시·`showEvent`(탭 복귀) 마다 디스크에서 다시 읽어 **File Manager 탭과 동기화**(재클릭 불필요).
  record 매핑 노드에만 표시(planned·루트 밖은 안내문). per-item 회색 foreground 보존 위해 `::item` color 는
  덮지 않음. #A00210_FileManager
- **Framework/styles (dark 테마 트리 행 가독성)**: Windows 10 에서 파일 목록(`QTreeWidget`,
  `alternatingRowColors`)의 **교대 행 배경이 거의 흰색**으로 떠 밝은 글자가 안 보이던 문제 수정. qss 에
  교대행/행 색이 없어 OS 네이티브 팔레트(Win10)가 밝게 칠한 게 원인. `QTreeView/QTreeWidget` 에
  `background #2b2b2b` + **`alternate-background-color #33363c`** + 텍스트/선택(테마 accent)·hover 를
  **명시**해 OS 무관하게 **Win11 처럼** 보이도록 했다. dark.qss + 6개 `*_dark.qss`(blue/brown/coral/green/
  purple/yellow) 일괄 적용(라이트 테마 제외). 이전 탭바·헤더 가독성 수정의 후속(트리 행 누락분). 공용
  Framework 라 dark 테마 전 Qt 툴에 반영. #Framework
- **A00110_animTool / A00120_FKIK 뷰포트 프리즈 수정**(A00110 v01.15→01.16, A00120 v01.03→01.04):
  베이크 시 쓰는 `cmds.refresh(suspend=True)` 는 **씬 전역 토글**이라 복원이 어떤 예외에도 실행돼야
  하는데, A00120 `fkik_matcher.bake()` 의 `finally` 가 임시 컨스트레인트 `cmds.delete()` 를
  `suspend=False` **보다 먼저** 실행 → delete 실패 시 복원이 건너뛰어져 **세션 전체가 프리즈**
  (Graph Editor 커브 편집이 프레임 이동 전까지 반영 안 됨)되는 버그. 전역 상태라 한 번 누수되면 A00110
  도 멈춰 보였다. 공용 컨텍스트 매니저 `Framework/core/maya_refresh.py` 의 **`suspend_refresh()`**
  (복원을 항상 먼저/무조건 보장)로 A00110(`bake_manager`, `follow_match_manager`)·A00120
  (`fkik_matcher`)의 suspend 사용처를 전부 통일하고, `bake_constraint()` 의 임시 컨스트레인트 삭제도
  `finally` 로 이동. A00110·A00120 UI 에 **Force Refresh (Unfreeze Viewport)** 버튼
  (`force_refresh()`) 추가 — 멈춘 세션을 즉시 복구. #A00110_animTool #A00120_FKIK
- **A00110_animTool Follow 탭**(v01.14→01.15): (1) **Maintain Offset** 체크박스 — 타겟↔follower
  의 거리·회전을 유지한 채 추종(`parentConstraint maintainOffset=True` 와 동등)하되, **컨스트레인트
  노드 없이 순수 행렬 연산**으로 구현해 사이클·평가순서 오류를 원천 차단. **Start(구간 시작) 프레임**에서
  페어마다 한 번 `offset = worldMatrix(flw) · worldInverseMatrix(tgt)` 를 측정하고 매 프레임
  `local = offset · worldMatrix(tgt) · parentInverseMatrix(flw)` 로 분해(레거시
  `JUN_PY_MatrixCon_01_01` 의 offsetMat 로직과 동일). 끄면 기존처럼 offset 0(정확히 일치).
  (2) **1<-n** 체크박스 — 켜면 타겟 1개를 모든 follower 가 추종(타겟이 1개가 아니면 경고 후 중단),
  끄면 기존 **n<-n**(인덱스 1:1). (3) **Get Current** 버튼 — Start/End 옆에 각각 두어 현재 Maya
  프레임(`currentTime`)으로 입력란 갱신. 로그에 `mode`(1<-n/n<-n)·`offset`(offset/no-offset) 표기.
  `match_follow(..., maintain_offset, one_to_many)` 로 확장, `_offset_matrix()` 신설,
  `_matched_state(..., offset)` 일반화. 안내 문서(`docs/A00110_animTool.md`) 동기화. #A00110_animTool

---

## 2026-06-18

> [!summary] 신규 툴 A00230 StartupTool — 부팅 시 지정 폴더 자동 팝업(JSON 관리) + A00220 BackupTool — 주기적 자동 백업(standalone PySide) + A00110 animTool Follow 탭(target 추종 베이크) & Offset/Hold 신설→Key Edit 접이식 섹션 재구성 + A00210 FileManager Lineage 탭(파일 브랜치/병합 그래프) & Path Structure 선택 기록(체크한 최상위 폴더만)
- **A00230_StartupTool**: Windows 부팅(로그인) 시 자주 쓰는 작업 폴더들을 **탐색기 창으로 자동 팝업**하는
  순수 Python 유틸리티 신규. 열 폴더는 `config/folders.json` 으로 관리·확장(`path`/`enabled`,
  `open_missing`). 경로는 **환경변수(`%USERPROFILE%` 등)·`~` 확장**을 지원해 **PC 가 바뀌어도 동일**하게
  동작하고, 존재하지 않는 경로는 조용히 skip + 중복 경로 dedupe. `install.py` 가 Startup 폴더에 고유명
  런처(`A00230_StartupTool.vbs`)를 1회 생성 — 로그인 시 **pythonw 로 콘솔창 없이** `open_folders.py`
  실행(런처엔 그 PC 의 절대경로가 박힘). `uninstall.py` 로 제거. JSON 로더는 **전체 줄 `//` 주석**을
  허용해 항목을 삭제 없이 토글 가능. Framework·PathManager 비의존(표준 라이브러리만). #A00230_StartupTool
- **A00210_FileManager**: **Lineage 탭 신설**(v01.02) — 여러 리비전 폴더에 흩어진 파일들
  (.mb/.ma 뿐 아니라 .fbx/.obj 등 **포맷 무관**)의 **브랜치/병합 관계(DAG)** 를 직접 기록하고
  `git log --graph` 스타일 **색상 레인 트리**로 본다.
  **인터랙티브 캔버스**(`QGraphicsView`): 노드 드래그 이동 + **Connect Mode** 로 노드→노드 선 긋기로
  부모 연결(자기연결·중복·**순환 자동 거부**). **레인 색상은 DAG 토폴로지에서 자동 계산**(`compute_lanes`,
  git-graph 컬럼 배정 — 브랜치=다른 색, 병합=레인 수렴), **Auto Layout**(컬럼=레인·행=위상순서, 이후
  드래그 위치 저장). **Planned**("제작 예정") placeholder 노드(점선·반투명). 노드 추가는 폴더
  **스캔(모든 포맷·확장자 필터)**·단일 **Add File**·**Add Planned** 3가지 — 루트 안이면
  project-relative key 로 기존 record/썸네일 자동 링크. 에셋별 이름 그래프 `<store_dir>/lineage/<name>.json`
  저장·기존 Push/Pull 로 git 동기화. core(`lineage.py`, Qt 비의존)/ui(`lineage_tab.py`) 분리,
  `path_structure` 패턴 미러. #A00210_FileManager
- **A00210_FileManager Lineage 보강**(v01.03): (1) **버전업/브랜치 수동 지정** — 노드별
  `relation`(`""`auto/`version`/`branch`) 추가. **Node** 패널 `Relation to parent` 콤보로 같은 부모의
  어느 자식을 **Version-up(부모와 같은 색=메인 라인 상속)** 으로, 어느 자식을 **Branch(강제로 새 레인=다른
  색)** 로 볼지 추가 순서와 무관하게 선택. `compute_lanes` 트렁크 선택을 `version` 최우선·`branch` 제외로
  바꾸되 미지정은 기존 기본(첫 자식) 유지(하위호환), 트렁크 레인을 먼저 예약해 다른 자식이 가로채던 케이스도
  정리. 색은 항상 관계에서 파생(의미↔색 불일치 방지), JSON `relation` 키로 저장·Push 동기화. (2) **캔버스
  탐색** — `LineageView(QGraphicsView)` 서브클래스로 **휠 줌**(`AnchorUnderMouse`, 0.15x~4.0x, 현재
  배율은 `transform().m11()`로 읽어 `fitInView` 후에도 정확)과 **중간 버튼 드래그 팬** 추가(좌클릭·노드
  드래그·Connect Mode 와 비충돌, PySide6/2 좌표 모두 대응). #A00210_FileManager
- **A00210_FileManager Lineage 노드 우클릭 메뉴**(v01.04): `NodeItem.contextMenuEvent` 로 노드 우클릭
  시 **Reveal in File Explorer** 제공 — `key`(project-relative)를 `store.project_root`와 합쳐 절대경로
  복원 후 탐색기로 폴더를 열고 **파일 선택**(Windows `explorer /select,`, macOS `open -R`/Linux
  `xdg-open` 폴백). 경로 해석 가능할 때만 활성(키 있음+루트 설정+파일 존재), planned·루트 밖·사라진 파일은
  비활성+안내. 이후 우클릭 액션을 계속 확장할 수 있는 구조. #A00210_FileManager
- **A00210_FileManager 썸네일 캡쳐 오버레이 검정화면 수정**(v01.05): Capture Region 시 화면이 전부
  검게 덮여 캡쳐 범위가 안 보이던 문제 해결. 원인은 오버레이 위젯에 `WA_TranslucentBackground` 가 없어
  반투명 dim 이 불투명(검정) 배경 위에 칠해진 것. (1) 투명 배경 속성 활성 → 실제 화면이 비쳐 보임,
  (2) 풀스크린 '상태'(`WindowFullScreen`) 제거하고 **가상 데스크탑 geometry** 로 전체 모니터를 덮음
  (풀스크린+반투명이 단일모니터 스냅/합성 깨짐을 유발 — **Windows 10/11 공통** 동작 위해), (3) 선택영역
  표시를 `CompositionMode_Clear`(드라이버 편차) 대신 **선택영역 제외 둘레 4개 영역만 dim** 으로 변경해
  선택영역이 확실히 투명. 결과적으로 Win+Shift+S 처럼 전체는 살짝 어둡고 드래그 영역만 또렷. #A00210_FileManager
- **A00210_FileManager 배포 사용자 데이터 리포 원클릭 동기화**(v01.06): 릴리즈본을 git 으로 받은 사용자가
  데이터(records/thumbs/lineage/path_structures)를 동기화 못 하던 문제 해결. 근본원인 3가지 — (1) `on_pull/
  on_push` 가 읽던 `remote_url` 이 prefs/UI 어디에도 없어 항상 빈 값 → `ensure_repo` 가 clone 못 하고 로컬
  init 만 함, (2) 기본 브랜치 `main` vs 데이터 리포 `master` 불일치, (3) 배포 PC 에 clone 할 기본 store_dir
  없음. 해결: **중앙 데이터 리포 URL/브랜치/기본 clone 경로(`~/.jun_filemanager/JUN_FileManager_data`)를 툴에
  번들**(`app/config/data_repo.py`, release_builder 가 `app/` 통째 복사하므로 자동 포함). prefs 기본값을 번들에서
  채우고 구버전 prefs 는 load 시 브랜치 마이그레이션(main→master), UI 에 **Remote URL** 필드 추가, **Pull
  한 번**에 repo 없으면 기본 경로로 자동 clone→pull. clone 실패 시 **로컬 init 폴백 제거**(인증/권한 오류
  표면화, 끊긴 빈 repo 방지). core(prefs/git_sync)·config(data_repo)·ui(main_window) 분리 유지. #A00210_FileManager
- **A00210_FileManager Path Structure 선택 기록**(v01.07): Path Structure 탭에서 베이스 폴더의 **모든**
  하위 경로를 기록하던 것을, **선택한 최상위 폴더만** 기록하도록 변경. **"Folders to record" 체크리스트**
  (`QListWidget`)에 최상위 하위 폴더를 체크박스와 함께 리스트업하고(Base 변경·Browse·**Scan** 시 채움,
  재스캔 시 기존 체크 이름 기준 보존), **"All" 체크박스**로 전체 선택/해제(전체 기록). **Capture** 는 체크된
  최상위 폴더만 모으고(폴더가 있는데 미체크면 경고), **Recursive** 면 그 하위 트리까지 포함. core 는
  `list_top_level()` 추가 + `_collect_folders()`/`capture()` 에 `include_top` 필터(None=전체, 하위호환).
  로직 `app/core/path_structure.py`, UI `app/ui/path_structure_tab.py`. #A00210_FileManager
- **A00220_BackupTool**: 컴퓨터 비정상 종료 대비 **주기적 자동 백업** standalone PySide6 앱 신규.
  대상 **파일 목록**을 분·초 주기로 각 원본 폴더의 `backup` 하위 폴더에 복사(`{base}_{suffix}{ext}`,
  예 `scene_BU.mb`). 폴더명·접미사(BU) UI 지정, **Overwrite(기본)** / **Version Up**(`_NN`,
  최근 N개만 유지·롤오버) 모드 선택. 상태 표시 `Stat : Deactive` / `Active...`(점 애니메이션) /
  `Saving`. **다음 저장까지 남은 시간 카운트다운**(`Next save in MM:SS`, 1초 갱신, v01.01) 추가.
  설정은 로컬 prefs(`~/.jun_backuptool/prefs.json`)에 영속. core(Qt 비의존)/ui 분리,
  A00210 standalone 구조 준수. #A00220_BackupTool
- **A00110_animTool**: **Follow 탭 신설**(v01.11) — 좌(Target)/우(Follower) 리스트로, 각 follower 가
  같은 인덱스 target 의 **월드 위치·회전(·스케일)과 동일**해지도록 구간 키를 베이크(컨스트레인트 없이
  `parentConstraint(maintainOffset=False)` 와 동등). **rotateOrder 무관** — target `worldMatrix` 를
  follower `parentInverseMatrix` 로 로컬화한 뒤 **follower rotateOrder 로 재분해**(Mirror Key 경로
  재사용). **blend(0~1)** 로 원본↔매치 혼합(위치/스케일 lerp·회전 쿼터니언 slerp)을 **키 값에
  베이크**(레이어 weight=1 유지), 선택된 애니 레이어(override `V=F` / additive `V=F−B`)에 기록.
  로직 `app/core/follow_match_manager.py`, UI 는 재사용 위젯 `JUN_mod_tsl_qt_v01` 2개. 더불어
  선택 레이어 판별을 `cmds.ls(type=animLayer)` 나열 후 레이어별 `selected` 검사로 구현(animLayer 에
  선택 레이어 목록 전역 쿼리가 없음). #A00110_animTool
- **A00110_animTool**: **Offset & Hold 기능 신설 → Key Edit 탭 접이식 재구성**(v01.12→01.14).
  리스트업한 컨트롤러의 키를 **포즈 유지(hold) + 보간(offset)** 구조로 재배치 — 오브젝트 커브들의
  **키 시점 합집합**을 포즈로 삼아 포즈마다 `[start+i·P, start+i·P+hold]`(P=hold+offset) plateau 를
  만들고 사이를 offset 길이로 보간한다. 값은 `getAttr(time=)` 로 샘플링(키 없던 커브도 보간값),
  plateau 안쪽 탄젠트 flat·보간 구간 spline(유지→가속→감속→유지), Start 비우면 오브젝트별 첫 키 앵커.
  로직 `app/core/offset_hold_manager.py`. 처음 별도 탭으로 추가(v01.12)했다가 **Key Edit 탭으로 통합**
  (v01.13), 다시 Key Edit 탭을 **Move Keys / Graph Editor / Offset & Hold 접이식 섹션 3개**로 분리
  (v01.14, Offset & Hold 기본 접힘). 접이식 위젯은 재사용 모듈 `Framework/qt/MOD_collapsible_qt_v01.py`
  (`JUN_mod_collapsible_qt_v01` + 숨김 시 sizeHint 0 인 `JUN_mod_fit_tab_page_v01`)로 분리, 레거시
  `JUN_PY_SelectionTool` 의 `frameLayout(collapsable=True)` 패턴 이식. 섹션 토글·탭 전환 시
  `_fit_window` 가 **창 크기를 현재 탭 콘텐츠에 맞춰 자동 조정**. #A00110_animTool
- **standalone Qt 패키지 충돌 수정**: A00080·A00210·A00220·release_builder_QT 가 모두 최상위
  `app` 으로 import 해, 한 인터프리터(Maya·공용 런처)에서 두 툴을 동시에 띄우면 `sys.modules['app']`
  가 첫 툴로 점유돼 두 번째 툴이 `ModuleNotFoundError`(또는 엉뚱한 창)로 실패하던 문제 해결. launch.py 는
  **툴 고유 경로**(`tools.<tool>.app...` / `dev.release_builder_QT.app...`)로, 내부 모듈은 **상대 import**
  (`from ..core import …`)로 전환 — in-Maya 툴(A00110)·템플릿(A00004/A00008)이 이미 쓰던 규약과 일치.
  4개 툴 동시 로드 검증 완료. A00080·A00210 의 launch/내부 import 경로 전환은 **전용 커밋으로 분리**
  푸시(A00220·release_builder 분은 각 기능 커밋에 포함). #Framework
- **Framework/styles (dark 테마 가독성)**: Windows 10 에서 **탭바·테이블 헤더** 글자가 배경과
  대비가 낮아 안 보이던 문제 수정. qss 에 `QTabBar::tab`/`QTabWidget::pane`/`QHeaderView::section`
  (+hover·corner)을 **명시**(어두운 배경·밝은 글자·테마 accent 테두리)해, OS 네이티브 렌더(Win10/11
  차이)와 무관하게 **Win11 처럼** 보이도록 했다. `dark.qss` + 6개 `*_dark.qss`(blue/brown/coral/
  green/purple/yellow) 일괄 적용, 라이트 테마 제외. 공용 Framework 라 dark 테마 전 Qt 툴에 반영.
  #Framework

## 2026-06-17

> [!summary] 신규 툴 2종(A00210 FileManager·A00010 HumanIK V02) + 윈도우 최상단 정책 개선 + 신규 툴 2종(A00200·Release Builder) + Mirror Key Behavior + 저장소 정리(레거시 아카이빙·포트폴리오 README·FileManager 데이터 분리·브랜치 정리) + A00210 Path Structure 탭
- **Framework/qt**: 모든 Qt 툴 창을 **마야 메인 윈도우에 parent** — 뷰포트 위에는 떠 있되 다른 툴
  창과는 정상 Z-order(밑에 있는 창을 클릭하면 위로 올라옴). `Qt.WindowStaysOnTopHint`(항상 최상단)
  폐기. 공용 헬퍼 `Framework/qt/maya_window.py` 의 `maya_main_window()` 추가, A00110+12개 Qt 툴 및
  A00008 템플릿에 일괄 적용(A00200 은 기존부터 동일 패턴) (`d2b5ad4`) #Framework
- **dev/release_builder_QT**: 릴리스 패키징용 **PySide Release Builder QT** 신규 (`7640a92`) #dev
- **A00200_CSV_tool**: **ARKit 페이셜 CSV import** 신규 툴 + 드래그&드롭 설치(`__dragDrop_A00200`)
  (`3d9ec1e`) #A00200_CSV_tool
- **A00110_animTool**: Mirror Key 탭에 **Behavior 모드**(기본 ON) 추가 — 반대쪽 컨트롤러의 고유
  forward/up 축 방향을 보존하며 미러. 소스의 **로컬 채널 값(translate/rotate)을 타겟에 그대로
  복사**한다(반사·행렬 연산 없음, 반사축 무관). Maya `mirror joints` 의 Behavior 세팅으로 만든
  좌우 축 반전 리그용. 체크박스로 기존 월드 반사(orientation)와 선택, 구간/현재프레임 둘 다 적용.
- **A00110_animTool**: Behavior 가 ON 이면 반사축이 무의미하므로 **Mirror Axis 라디오 비활성**.
- **A00110_animTool**: Mirror 실행(Mirror Selected·Mirror Current Frame)이 **씬 선택과 무관하게
  Source/Target 리스트의 오브젝트만** 대상으로 처리(선택 → `Resolve Pairs`/`Select Source` 로
  리스트 채우기 → 실행으로 단계 분리). (v01.08~01.09) #A00110_animTool
- **A00210_FileManager**: Maya 씬(`.mb`/`.ma`) **버전·작업기록 추적** standalone PySide6 앱 신규 —
  경로 스캔·파일별 작업자/타임스탬프 로그·**화면 영역 캡쳐 썸네일**·기록(records/thumbs) **git
  push/pull**(원본 미푸시). 키는 프로젝트 상대경로(cross-PC), 절대경로 설정은 로컬 prefs. core(Qt/Maya
  비의존)/ui 분리, 사용법 [A00210 가이드](A00210_FileManager.md) (`fd74913`) #A00210_FileManager
- **A00010_humanIKTool_V02**: HumanIK 툴 in-Maya PySide 재작성 신규 (`6ef7f76`) #A00010_humanIKTool
- **.gitignore**: PyInstaller 빌드 산출물(`build/`·`dist/`) 무시 추가 (`fd74913`)
- **저장소 아카이빙**: 레거시·학습 폴더 10개를 `_archive/` 로 이동(`git mv`, 히스토리 보존) —
  `legacy_tools/`(00_Old·00_RUN·01_Modules·01_Modules_Small·02_Modules_Old·03_Modules_Test·
  04_KWI_generator) + `study_notes/`(100_Memo·101_cellular_automata·101_maya_python_technic).
  추적되던 `.pyc` 12개 정리, 레거시→현행 매핑표 `_archive/README.md` 추가 (`5248196`) #archive
- **루트 README**: 채용·상사 대상 **포트폴리오형 루트 `README.md`** 신규 — 한국어 본문 + 영어 요약,
  도메인별 툴 하이라이트·기술 스택·저장소 구조·연락처(이메일/GitHub/Notion·웹 포트폴리오). 스크린샷
  자리 `JUN_All/docs/assets/` (`d73c8c7`) #docs
- **A00210_FileManager 데이터 분리**: 별도 원격(`JUN_FileManager_data`)으로 동기화되는 데이터 폴더가
  부모 트리 안에 **중첩(nested repo)** 돼 있던 임베디드-repo 위험 해소 — 부모 트리 밖으로 이동 +
  `store_dir` prefs 갱신, 부모 `.gitignore` 에 추가해 우발적 gitlink 커밋 방지 (`91949fd`) #A00210_FileManager
- **브랜치 정리**: `Dnable` 을 master 역할 기본 브랜치로 확정. `dev_archive`(로컬+원격)·`master`(로컬)
  삭제, 서버에 없던 `Dnable_bch` 추적 잔상 prune. 이후 일상 작업/푸시는 `dev` 로 일원화 #git
- **A00210_FileManager**: **Path Structure 탭** 신규(v01.01) — 베이스 폴더의 하위 폴더 구조를 JSON 으로
  저장해 다른 PC 와 git 동기화하고 **버튼 하나로 폴더만 재생성**(파일 미생성). 베이스는 project_root
  상대경로로 저장→PC 마다 자기 루트 아래 재생성. **Recursive** 토글(중첩 트리 전체 vs 최상위만),
  이름별 다중 저장, **Capture(미리보기)/Save 분리**, 트리뷰 preview(`build_tree_lines`). 기존 창을
  QTabWidget(File Manager/Path Structure)로 재구성, 로그 공유. 코어(`app/core/path_structure.py`,
  Qt 비의존)/ui 분리 (`4dfa979`) #A00210_FileManager

## 2026-06-16

> [!summary] 신규 병합 툴 2종 + Qt 인프라 정리 + JointTool Aim 재설계
- **A00145_RigConnect**: MEL ConnectionTool V04.02 + A00140 병합(4탭 PySide) 신규 툴, 사용법 [A00145 가이드](A00145_RigConnect.md) (`5592490`, `d1750df`) #A00145_RigConnect
- **A00060_jointTool_V02**: MEL JointTool V05.03 + A00060 병합(4탭) 신규 툴, 사용법 [A00060 V02 가이드](A00060_jointTool_V02.md) (`ec42af1`, `bbb78bd`) #A00060_jointTool_V02
- **A00060_jointTool_V02**: Aim 탭 재설계 — Aim axis 드롭박스(X/Y/Z) + twist-only IK식 정렬(joint 월드 위치 보존·constraint/cycle 제거·레퍼런스 안전, v01.01) (`4c67ac8`) #A00060_jointTool_V02
- **Framework/qt**: 모든 Qt 툴을 `Framework.qt.qt` 래퍼 경유로 일원화 (`f3c8d58`) #Framework
- **deps**: 외부 의존성 관리 중앙화 (`a13792c`)
- **A00110_animTool**: Smart bake 옵션(native `bakeResults -smart`, v01.07) + 비교 문서 (`859299d`, `c0d7db8`) #A00110_animTool
- **dragDrop**: 드롭 설치 파일명 고유화로 셸프 버튼 충돌 해결 (`30f0f09`)
- **A00190_FKIK_General_Tool**: 레거시 FK/IK 툴 PySide 리팩터 (`cab90a6`) #A00190_FKIK

## 2026-06-15

> [!summary] animTool/abSymMesh PySide 강화 + bake 성능
- **A00110_animTool**: Copy Key 탭(v01.03)·Mirror Key 탭(v01.04) 추가 + 문서화 (`f6139ac`, `147fa7f`, `be41423`, `8917cbf`) #A00110_animTool
- **A00180_abSymMesh**: Python/OpenMaya 재구현(속도)·app/ 레이아웃 + PySide UI·동작 문서 (`f01ced1`, `f6f5053`, `4719e56`) #A00180_abSymMesh
- **A00170_driverTool**: RemapVal + SphericalEye 를 탭 툴로 병합 (`96acac4`) #A00170_driverTool
- **A00150_remapVal**: 보간을 enum(Linear/Smooth/Spline)으로 (`2cb49aa`) #A00150_remapVal
- **A00120_FKIK**: per-frame 루프 대신 native `bakeResults` 로 bake (`b83c591`) #A00120_FKIK
- **A00080_KWI_creator**: 결합 파일 출력(base+setting+LD) (`61c459e`) #A00080_KWI_creator
- **dev/reload**: per-tool `reload_for_tool` 추가 + 전 Qt 런처 전환 (`1660c63`)
- **Framework/styles**: 체크박스·라디오 인디케이터 전 테마 가시성 수정 (`acf285e`, `730f8b4`) #Framework

---
