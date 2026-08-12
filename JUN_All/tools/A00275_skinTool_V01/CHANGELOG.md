# Changelog — A00275_skinTool_V01

## v01.12 (2026-08-12)
- **[Fix] 한 트랜스폼에 메시 셰이프가 여럿일 때 엉뚱한 셰이프를 잡던 문제** — `MDagPath.extendToShape()`
  는 **첫 번째 non-intermediate 셰이프**를 고를 뿐이라, blendShape 타겟 셰이프를 같은 트랜스폼에 정리해
  둔 리그·머지/임포트 잔재 씬에서 원하는 셰이프가 아닌 것이 나왔다. 웨이트 API 에 넘기면
  `(kInvalidParameter): Object is incompatible with this method` 로 죽고, 지오메트리 읽기/쓰기는
  **조용히 다른 셰이프**를 만졌다.
- 공용 헬퍼 **`Framework.core.maya_shape`** 로 통일했다 — 셰이프를 추측하지 않고 **디포머가 실제로
  변형하는 셰이프**(`cmds.deformer -q -g`)로 확정한다.
- Transfer / Migrate / Expand Bind 의 웨이트 IO 경로가 모두 이 헬퍼를 쓴다. `copySkinWeights` 에는
  **셰이프를 선택**해 넘긴다(트랜스폼을 넘기면 셰이프가 여럿일 때 `-destinationSkin` 을 요구하며 실패).

## v01.11 (2026-08-12)
**[Fix] Expand Bind 에서 `(kInvalidParameter): Object is incompatible with this method`**
— 한 트랜스폼 아래 **메시 셰이프가 여럿**인 리그(blendShape 타겟 셰이프를 같은 트랜스폼에 정리해 둔
경우, 머지/임포트 잔재 등)에서 바인드가 죽던 문제.

- **원인**: 셰이프를 `MDagPath.extendToShape()` 로 잡았다. 이 함수는 **첫 번째 non-intermediate
  셰이프**를 고를 뿐이라, 스킨이 걸린 셰이프가 첫 번째가 아니면 **엉뚱한 셰이프 경로**가 나온다.
  그 경로로 `MFnSkinCluster.getWeights` 를 부르면 마야가 위 에러로 죽는다(실측 재현).
- **해결**: `shape_of()` 를 두어 **skinCluster 가 실제로 변형하는 셰이프**(`skinCluster -q -geometry`)를
  고른다. 스킨이 없으면 non-intermediate 메시 셰이프 중 첫 번째. 좌표/인접/컴포넌트/웨이트 IO 가 전부
  **같은 셰이프 경로**를 쓴다.
- **[Fix] 같은 상황에서 버텍스 수를 못 세던 문제** — 셰이프가 여럿인 트랜스폼에 `polyEvaluate` 를 걸면
  정수가 아니라 요약 **문자열**이 돌아와 뒤에서 `TypeError` 로 터진다. `vertex_count()` 가 항상 셰이프
  기준으로 센다.
- **[Add] 방어** — 웨이트를 읽기 전에 그 skinCluster 가 이 셰이프를 정말 변형하는지 확인하고, 아니면
  **무엇이 어긋났는지 적힌 에러**를 낸다(원시 API 에러 대신).
- **[Change] 저장 시 셰이프 보존** — 버텍스를 저장할 때 컴포넌트가 셰이프 이름으로 오면(셰이프가 여럿일
  때 마야가 그렇게 준다) **그 셰이프를** 기억한다. 어느 셰이프의 버텍스인지가 곧 어디에 바인드할지다.
- **[Change] 새 skinCluster 도 셰이프에 건다** — 트랜스폼 이름으로 넘기면 마야가 엉뚱한 셰이프에 바인드할
  수 있다.
- 검증: 셰이프 해석 회귀 15항목 신규(blendShape 앞/뒤, 여분 셰이프가 첫 번째/마지막, 셰이프 직접 입력,
  스킨 없는 다중 셰이프, 어긋난 skinCluster 가드) + 기존 코어 44 · 루프 24 · UI 33 회귀 통과.

## v01.10 (2026-08-12)
**Expand Bind 에 엣지 루프 입력 추가** — 조인트가 앉아 있는 루프를 같이 저장하면 조인트 분배와
루프 바깥 감쇠가 분리되어, 밴드(여러 줄) 어디서나 루프와 같은 비율이 유지된다.

- **[Add] `Store Edge Loop from Selection`** (+ `Select` / `Clear`) — 엣지 루프를 골라도 되고 그
  버텍스를 골라도 된다. 한 줄로 이어지지 않으면(갈래·끊김) 이유를 붙여 거절한다.
  열린 루프 / 닫힌 루프를 자동 판별하고, 닫힌 루프는 **양쪽으로 감아 도는 짧은 거리**로 잰다.
- **[Add] `Across width`** — 루프에서 **멀어지는 방향**의 반경(0 = Soft Select 값과 동일).
  이 방향은 **비율을 바꾸지 않고 amount 만** 줄인다.
- **[Change] `Fit to Joints`** 가 루프가 있으면 **루프 위 간격**으로 잰다(밴드를 가로지르는 지름길에
  속지 않는다).
- **왜 필요했나** — 루프 없이 영역 전체를 한 거리로 재면, 루프에서 멀어질수록 "바깥으로 나간 거리" 가
  반경을 잡아먹어 **먼 조인트의 falloff 가 먼저 0** 이 된다. 그러면 비율이 부드럽게 섞이지 않고
  딱딱하게 갈라진다(격자 11x7 실측, 조인트 2개 · 반경 10):

  | | col 0 | 1 | 2 | 3 | 4 | 5 |
  |---|---|---|---|---|---|---|
  | 루프 줄 | 1.000 | 0.900 | 0.800 | 0.700 | 0.600 | 0.500 |
  | 루프+3 줄 (루프 없이) | 1.000 | 1.000 | 1.000 | **1.000** | 0.750 | 0.500 |
  | 루프+3 줄 (루프 입력) | 1.000 | 0.900 | 0.800 | 0.700 | 0.600 | 0.500 |

- **구현** — 루프 전체를 시작점으로 하는 **다중 소스 Dijkstra 한 번**으로 버텍스마다 "루프에서 떨어진
  거리 + 가장 가까운 루프 버텍스(anchor)" 를 얻고, 조인트 비율은 **anchor 의 루프 호 거리**로만 낸다.
  루프 버텍스가 저장 집합에 빠져 있으면 대상에 끼워 넣고 몇 개인지 보고한다.
- 검증: 루프 전용 24항목 추가(정렬/열림·닫힘 판별/갈래·끊김 거절/밴드 7줄 비율 유지/across 감쇠/
  감아 도는 분배/Fit) + 기존 코어 44 · UI 33항목 회귀 통과.

## v01.09 (2026-08-12)
**Expand Bind 탭 추가** — Kangaroo `SkinCluster > ClosestExpand` 를 대신하는 바인드.
입술·눈처럼 원을 그리는 엣지 루프 위의 조인트들에 바인드할 때 **조인트 사이 웨이트가
엣지 길이에 비례해 고르게** 깔린다.

- **[Add] 저장식 입력** — `Store Vertices from Selection`(엣지/페이스는 버텍스로 변환) +
  조인트 리스트(`Store Joints from Selection`). 버텍스 집합은 **리스트 위젯으로 펼치지 않는다** —
  입술 한 덩이가 수천 개라 리스트가 창을 느리게 만든다. 요약 라벨 + `Select` / `Clear` 로 다룬다.
  선택 복구는 연속 id 를 `vtx[a:b]` 로 묶어 던진다.
- **[Add] Falloff mode** — `Surface (edge length)` 측지 거리(Dijkstra, 기본) /
  `Topology (edge count)` 홉 수 / `Volume (straight line)` 직선 거리. 세 모드 모두 **조인트에
  가장 가까운 버텍스에서부터** 잰다. 탐색은 **저장된 집합 안으로 제한**해 falloff 가 영역 밖으로
  새지 않는다(입술 안/바깥이 붙어버리는 사고 방지).
- **[Add] Falloff curve 위젯** — 마야 Soft Select 의 커브 편집(ref/ref_01.png)을 PySide 로 재현.
  포인트 드래그/더블클릭 추가/우클릭 삭제, `Interpolation`(None/Linear/Smooth/Spline),
  프리셋 6종. 계산과 그리기가 **같은 함수**(`core/falloff.py`)를 쓴다.
- **[Add] Soft Select 반경** + `Fit to Joints` — 각 조인트의 falloff 가 이웃 조인트에 꼭 닿는
  반경을 재서 넣어 준다(현재 falloff mode 척도로).
- **[Add] Blend** — 이미 **다른** 인플루언스를 가진 버텍스에서 이 조인트들이 가져갈 최대 총량.
  실제로는 `Blend × coverage` 만큼 가져가고 나머지는 기존 인플루언스가 비율대로 유지한다
  (coverage = `min(1, 조인트별 커브값 합)` → 조인트 사이는 1, 바깥으로 갈수록 감소).
  다른 인플루언스가 없는 버텍스는 Blend 와 무관하게 1.
- **왜 Kangaroo 가 고르지 않았나** — ClosestExpand 는 조인트 사이를 **토폴로지 등간격**으로 섞고
  바깥은 **루프 개수**로 감쇠시킨다(실제 엣지 길이를 보지 않는다). 엣지 간격이 조금만 불규칙해도
  웨이트가 한쪽으로 쏠린다. 이 탭은 **거리/반경 → 커브 → 조인트 간 정규화** 라, 선형 커브면
  두 조인트 사이가 정확히 `d2/(d1+d2)` 가 된다.
- 검증(mayapy 2024): 코어 44항목 + UI 28항목. 반지름 12 링(24분할)에 조인트 4개 →
  `1.0 / 0.833 / 0.667 / 0.5 / 0.333 / 0.167 / 0` 균등 램프, 루프가 0번 정점을 넘어 이어지는 것까지 확인.
  성능 25,921 버텍스 / 조인트 20개 = **0.60s**(순수 파이썬, numpy 무의존).

## v01.07 (2026-07-24)
Transfer 탭 소프트 셀렉션 관련 버그 수정(컴바인 메시 + Volume falloff).

- **[Fix] `(kInvalidParameter): Object is incompatible with this method` 에러** — 소프트 셀렉션으로
  전이 범위를 잡고 Transfer 하면 나던 에러.
  - `_soft_weights` 가 리치 셀렉션 컴포넌트를 **문자열 경로**로 비교해 combine/rename 메시에서
    매칭이 틀어졌다(리치 셀렉션은 **셰이프 DAG** 를 준다). 이제 컴포넌트의 **셰이프 MObject 노드**와
    대상 셰이프 노드를 직접 비교하고(`_shape_node`), 컴포넌트 접근을 try/except 로 감싼다. 범위를
    벗어난 버텍스 id 도 걸러낸다(방어).
- **[Fix] 방치하고 싶은 부위까지 전이되던 문제** — 여러 조각이 하나로 **combine 된 메시**에서 소프트
  셀렉션 **Volume** falloff 가 붙어 있지 않은 **근접 shell** 까지 범위로 잡아 함께 전이됐다.
  - 이제 소프트 셀렉션을 **하드 선택이 속한 연결 shell(island)로 제한**한다(`_connected_island`).
    떨어진 근접 shell 은 전이 대상에서 제외 → **방치**된다. island 계산은 `MFnMesh.getVertices()`
    **한 번의 벌크 호출**로 면-버텍스 인접을 만들고 파이썬 BFS 로 확장한다(버텍스별 반복 없음 → 빠름).
- **[Change] 부분 전이 방식(빠른 벌크 마스킹)** — 대상 메시에 copySkinWeights(전체) 한 뒤, 선택 전/후
  웨이트를 **maya.api 벌크 read** 로 읽어 선택 버텍스는 `before + (after-before)*f`(f=falloff) 로
  블렌드하고 미선택은 `before` 로 되돌려 **한 번의 벌크 `setWeights`** 로 쓴다. 대용량 메시에서도 빠르다
  (3.1k 버텍스 combine 메시에서 island 0.007s + 전이 0.055s 측정).

## v01.06 (2026-07-23)
- **[Fix] Transfer 탭이 선택한 여러 대상 메시 중 하나에만 전이되던 문제** — 이제 **선택한 모든 메시**에
  전이한다.
  - 원인: 대상 파싱(`parse_target_selection`)이 선택에서 **첫 메시 하나만** 반환했다.
  - 해결: `parse_target_selections`(복수) — 선택을 **대상 메시별로 그룹핑**해, 통째 선택된 메시는 각각
    전체 전이, 버텍스가 선택된 메시는 그 메시만 부분 전이(소프트 falloff 는 메시별). Native 는 대상마다
    copySkinWeights+마스킹을 돌리고 **전체를 한 undo 로** 묶는다. Kangaroo 는 `_pSelection=None` 이
    이미 선택 전체를 처리한다.
  - 소스로 쓰인 메시가 선택에 섞여 있으면 대상에서 제외한다. 이때 **풀 패스로 정규화해 비교**한다
    (TSL 숏네임 vs `ls -l` 풀 패스가 달라 소스를 못 걸러 자기 자신에 전이하려다 실패하던 것도 함께 수정).

## v01.05 (2026-07-23)
- **[Add] Transfer 탭에도 Engine(Kangaroo / Native) 선택** — Classic·Migrate 탭처럼 골라 쓴다.
  - **Native**(기본) — `weight_transfer_manager`(v01.04). 선택 버텍스·소프트 falloff 지원.
  - **Kangaroo** — `transferSkinCluster`(sFrom=소스들, `_pSelection=None`=현재 선택 타겟,
    iMode=Closest Point). 컴포넌트/부분 전이는 Kangaroo 로직을 따른다. 타겟에 skinCluster 가
    없으면 새로 만들고(`bAutoCreateNewSkinCluster`), 있으면 기존 것을 쓴다.
  - Kangaroo 를 고르면 **soft falloff 옵션은 Native 전용**이라 UI 에서 비활성된다.
  - 라우팅은 headless 로 확인(모듈이 있어도 플러그인 런타임 미초기화면 crash 없이 `[Error]` 반환;
    실제 Maya 에서 Kangaroo Builder 로드 시 동작).

## v01.04 (2026-07-23)
- **[Add] Classic 탭에 Engine(Kangaroo / Native) 선택** — 예전엔 Classic 의 두 버튼이 Kangaroo
  전용이었다. 이제 Migrate 탭처럼 **Native**(플러그인 무의존)를 골라 쓸 수 있다.
  - `Joints to Joints` native = 선택 메시 skinCluster 에서 From 본 컬럼을 To 본 컬럼으로 이동(maya.api).
  - `Meshes to Meshes` native = rebind + `cmds.copySkinWeights`(closestPoint).
- **[Add] Transfer 탭 신설** — Kangaroo 의 *SkinCluster > Transfer* 를 흉내낸 기능이되 **Kangaroo 없이**
  동작한다. **여러 소스 메시 → 현재 선택한 하나의 메시**로 웨이트를 전이한다(`copySkinWeights`
  closestPoint; 소스가 여럿이면 버텍스별 최근접 소스 자동 선택).
  - **선택 버텍스에만 전이**(필수) — 타겟의 버텍스를 선택하면 그 버텍스만 바뀌고 나머지는 원본 유지.
  - **소프트 셀렉션 falloff 반영** — 소프트 셀렉션이 켜져 있으면 falloff 비율로 before~after 를 블렌드.
  - Mode 는 Closest Point 고정(요구대로 단순화). 구현은 `app/core/weight_transfer_manager.py`.
  - 구현 메모(mayapy 검증): `copySkinWeights` 는 컴포넌트 제한을 지원하지 않아 항상 메시 전체에
    적용된다. 그래서 전체 전이 결과(after)와 원본(before)을 bulk 로 읽어, 선택 버텍스만 falloff
    로 lerp 하고 나머지는 before 로 되돌린 뒤 bulk `setWeights` 로 마스킹한다. 버텍스 선택이
    없으면 전체 전이 결과를 그대로 둔다(undo 깔끔). 다중 소스는 selection-based copySkinWeights 가
    **버텍스별 최근접 소스**를 사용함을 확인해 그대로 활용.

## v01.03 (2026-07-20)
실제 리그(`CHN_Face`, 22,644 verts)의 Diagnose 결과로 원인이 확정된 뒤의 후속 조치.

- **원인 확정** — `shape NOT kept` 은 **`groupParts` 13개가 연속으로 이어진 체인**에서 발생했다.
  `face_BS`(blendShape) → `groupParts246` … `groupParts235` → `CHN_FaceShapeOrig`.
  v01.02 이전에는 첫 `groupParts` 에서 워크가 멈춰 입력 셰이프를 못 찾았다.
  v01.02 의 `inputGeometry` 스칼라 처리로 해결된 것이 실측으로 확인됨.
- **[Add] 라이브 blendShape 타겟 경고에 실제 weight 값을 표시** — 어느 타겟이 얼마인지 보여준다.
  상쇄량이 **weight 에 정비례**함을 실측했기 때문이다(weight 0.25/0.5/0.75/1.0 →
  오차 0.103/0.220/0.352/0.498). 부분 weight 에서는 **조용히 조금만 틀린** 결과가 나오므로
  값을 봐야 심각도를 판단할 수 있다.
- **[Fix] Diagnose 의 체인 출력 깊이 상한 16 → 64** — 실제 리그가 14 단계를 썼다.
  상한이 낮으면 리포트가 잘려 원인을 못 본다.

## v01.02 (2026-07-20)
`shape NOT kept` 이 왜 났는지 알 수 없다는 피드백에 대한 대응. **원인을 스스로 말하게** 만들었다.

- **[Add] 요약 줄에 이유를 함께 출력** — `shape NOT kept: <이유>` 형태.
  이제 로그에서 경고 줄을 따로 찾아 짝지을 필요가 없다. 가능한 이유:
  - `input geometry is nurbsSurface ...` — 폴리곤 메시가 아님 → **Snap 모드로 실행**
  - `could not resolve the input (Orig) shape from the deformer chain` — 히스토리 체인이 특이함
  - `input shape ... has a different vertex count (N vs M)` — 입력 셰이프 버텍스 수 불일치
  - `skin input/output vertex counts differ` — 스킨 입출력 버텍스 수 불일치
- **[Add] Diagnose 버튼** (Bind Pose 탭) — 씬을 건드리지 않는 **읽기 전용 진단**.
  지오/인덱스/인플루언스 수 + **디포머 체인을 실제 연결 그대로** 한 줄씩 출력해, 어느 단계에서
  막혔는지 바로 보인다. `shape NOT kept` 이 뜨면 이 버튼을 눌러 확인한다.
- **[Add] 입력 셰이프 fallback** — 체인 워크가 실패하면 같은 트랜스폼 아래에서
  **버텍스 수가 같은 intermediate 셰이프**를 찾아 재시도한다(수가 다르면 고르지 않으므로
  엉뚱한 셰이프에 굽지 않는다). 성공하면 `[Info] ... resolved by fallback` 로 알린다.
- **[Fix] 체인 워크가 `groupParts` / `tweak` 등에서 끊기던 문제** — 디포머는
  `input[i].inputGeometry` 를, groupParts 류는 `inputGeometry` 스칼라를 쓴다. 후자를 처리하지
  못해 체인을 끝까지 못 올라갔다. 또 `outputGeometry` 가 배열이 아닌 노드에 대고
  `getAttr(node.input, mi=True)` 를 불러 예외가 나던 경로도 함께 수정.
- **[Fix] 입력 셰이프와 스킨 입력의 버텍스 수를 굽기 전에 검사** — 다르면 굽지 않고 이유를 알린다
  (예전엔 그대로 진행해 어긋난 결과가 나올 수 있었다).

## v01.01 (2026-07-20)
실제 리그에서 보고된 3건 수정. 셋 다 단순 테스트 씬에서는 우연히 통과하던 것들이다.

- **[Fix] 더블 트랜스폼** — 다리를 45도 돌리고 Update Bind Pose 하면 90도 돌아간 것처럼 어긋나던 문제.
  `bindPreMatrix` 인덱스를 `enumerate(skinCluster -q -inf)` 로 매긴 게 원인이었다. 인플루언스 목록의
  **순서는 `matrix[]` 논리 인덱스와 다를 수 있고**(인플루언스를 뺐다 넣은 리그는 `[0,1,3,4,5,6]` 처럼
  성겨진다), 그래서 **엉뚱한 조인트 슬롯에 행렬이 들어갔다.**
  이제 `matrix[i]` 연결에서 `{논리 인덱스: 인플루언스}` 매핑을 읽는다(`_influence_index_map`).
- **[Fix] `(kInvalidParameter): Object is incompatible with this method`** — 두 가지 원인을 모두 처리.
  - `input[0]` / `outputGeometry[0]` 인덱스 하드코딩 → 대상 shape 으로 이어지는 실제 논리 인덱스를
    찾아 쓴다(`_geometry_index`). 한 디포머가 여러 지오를 변형할 때 터지던 경로.
  - 지오가 폴리곤 메시가 아닐 때(nurbsSurface/curve/lattice) → 예외로 죽지 않고,
    **"`Snap mesh to rest shape` 로 실행하라"** 는 안내를 로그에 남긴다(그 모드는 지오 타입과 무관하게 동작).
- **[Fix] `bindPoseXXX` 노드가 매번 새로 생기던 문제** — 재생성 시 **원래 노드 이름을 물려준다.**
  루트가 여러 개면 한 포즈에 함께 저장한다.
- **[Add]** `bindPreMatrix` 가 잠기거나 연결된 인플루언스는 건너뛰고 **어떤 조인트가 빠졌는지 로그로 안내**.
- **[Add]** `Keep current shape` 를 요청했지만 굽지 못한 경우 결과 요약에
  `bind matrices only - shape NOT kept` 로 정확히 보고한다(예전엔 그래도 "shape kept" 라고 표시했다).

## v01.00 (2026-07-20)
- 최초 버전. **스킨 관련 범용 툴**로, `A00270_skinMigrate` 의 기능을 그대로 담고 **Bind Pose 탭**을 추가했다.
  (`A00270_skinMigrate` 는 그대로 유지된다.)
- **Tab 1 "Classic"** / **Tab 2 "Migrate A -> B"** — `A00270_skinMigrate` v01.01 기능 이식.
  core `SkinMigrateManager` 는 로직 변경 없이 그대로 사용한다.
- **Tab 3 "Bind Pose" (신규)** — 조인트를 이동·회전한 **현재 상태를 새 바인드 포즈로** 만든다.
  이후 마야의 **Go to Bind Pose** 가 이 상태로 돌아온다.
  - **Keep current shape**(기본) — 지금 보이는 변형된 형상이 그대로 새 rest 가 된다. 메시가 눈에 띄게
    움직이지 않는다.
  - **Snap mesh to rest shape** — bindPreMatrix 만 갱신. 변형이 풀려 메시가 원래 형상으로 돌아간다
    (Move Skinned Joints Tool 로 조인트를 옮긴 것과 같은 결과).
  - **Rebuild bindPose node**(기본 ON) — dagPose 노드를 다시 만들고 `skinCluster.bindPose` 에 재연결.
  - 대상은 **메시를 골라도 되고 조인트를 골라도** 된다. 여러 skinCluster 동시 처리, 전체가 단일 undo.
  - **blendShape 등 다른 히스토리가 있어도 동작**한다(스킨 앞/뒤 무관, 히스토리 보존).
- 아이콘: `icon/A00275_skinTool_V01.png` — 스킨된 표면 안의 조인트 체인 + 갱신 화살표.

### 구현 메모 (mayapy 로 검증한 함정)
- 마야에는 이 동작을 하는 단일 기능이 **없다**:
  `skinCluster -e -recacheBindMatrices` 는 `bindPreMatrix` 를 **전혀 바꾸지 않고**,
  `dagPose -reset` 은 **bindPose 를 갱신하지 못한다**(Go to Bind Pose 가 옛 포즈로 감).
- 그래서 ① `bindPreMatrix[i] = 인플루언스의 현재 worldInverseMatrix`
  ② (Keep 모드) `skinCluster 출력 - 입력` 델타를 **체인 헤드 셰이프**에 굽기
  ③ bindPose 노드 재생성 + 재연결 — 3단계를 직접 수행한다.
- 델타를 굽을 때 **`MFnMesh.setPoints` 를 쓰면 안 된다** — undo 큐에 안 올라가서 Ctrl+Z 시
  bindPreMatrix 만 되돌아가고 구운 형상이 남아 **메시가 어긋난 채 방치**된다. `pnts` 구간 `setAttr` 사용.
- `pnts` 는 반드시 **기존 값에 더해야** 한다. 프리즈한 트랜스폼이 이미 tweak 으로 들어가 있는 경우가
  흔해서(예: `ty=2` 프리즈 → 전 버텍스에 `(0,2,0)`), 덮어쓰면 그 값이 통째로 날아간다.
- 체인 헤드는 **연결을 타고 올라가 찾아야** 한다. 중간(Orig) 셰이프가 여러 개일 수 있어 이름으로 고르면 틀린다.
- 알려진 한계: blendShape **타겟 지오가 아직 라이브로 연결**돼 있고 weight 가 0 이 아니면 델타가
  매 평가마다 재계산돼 우리가 구운 값이 상쇄된다. 이 경우를 감지해 경고한다.
