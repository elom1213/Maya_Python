# Changelog — A00275_skinTool_V01

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
