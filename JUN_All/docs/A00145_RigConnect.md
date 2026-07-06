# A00145_RigConnect — RigConnect (사용 안내)

MEL `ConnectionTool V04.02`(탭: Constrain / Connect / List Connected) · `Match Tool V05.04` 와 기존
`A00140_ConnectClosest`(최근접 1:1 constraint)를 하나로 합친 툴이다.
**UI 는 PySide(Qt)**, 로직은 `maya.cmds`(일부 `maya.api.OpenMaya`) 로 작성되었다.

- 버전: `v01.12` (`app/config/version.py`)
- 위치: `JUN_All/tools/A00145_RigConnect`
- 형태: 아키텍처 (B) — Maya 내 PySide 툴(`QTabWidget` 5탭)
- 원본 `A00140_ConnectClosest` / MEL 파일은 그대로 보존(미수정)

---

## 1. 설치 / 실행

### 드래그&드롭 설치
`__dragDrop_A00145.py` 를 Maya 뷰포트로 드래그&드롭 → 현재 셸프에 **`RigConnect`** 버튼 설치.
이후 셸프 버튼 클릭으로 실행된다.

### 코드로 실행
```python
import tools.A00145_RigConnect as A00145_RigConnect
A00145_RigConnect.run(True)   # True = DEV_MODE 면 reload 후 실행
```

---

## 2. 탭 구성

### Match
(MEL `Match Tool V05.04` 이식·리팩토링) follower 를 target 의 **위치/회전에 맞춘다**. 첫 번째 탭.

- `Targets` / `Followers` 리스트(Select/Add/Del/Up/Down). 버텍스를 선택하면 `cmds.ls(fl=True)` 로
  **각 버텍스가 개별 항목**(`mesh.vtx[i]`)으로 들어간다(`mesh.vtx[0:13]` 처럼 하나로 묶이지 않음).
- **Match**: `Targets[i] → Followers[i]` 인덱스 1:1 매칭. **rotateOrder 가 달라도** 안전
  (`cmds.matchTransform`, 임시 transform 경유). 개수가 다르면 적은 쪽만 매칭하고 경고.
  target 종류별 동작:
  - transform/joint/curve → 위치+회전(+옵션 스케일) 매칭.
  - mesh(오브젝트 전체) → 월드 정점 평균(centroid)으로 위치만.
  - clusterHandle → 월드 rotatePivot 으로 위치만.
  - **vertex(`.vtx[i]`) → 정점 월드 위치로 이동 + follower 의 `+Y` 축을 정점 노말에 정렬**
    (`maya.api.OpenMaya` 의 `MFnMesh.getVertexNormal`).
- **Match Options** (레거시 `DOOTOOL_PY_TOOL_Match.py` 이식, v01.10). 기본 체크 상태는 원본을 따름:
  - **Translation**(기본 ON) — follower 의 월드 위치를 타겟에 맞춘다.
  - **Rotation**(기본 ON) — follower 의 월드 회전을 타겟에 맞춘다(vertex 타겟이면 노말 정렬).
  - **Scale (world space)**(기본 OFF) — follower 의 **월드 스케일**을 타겟에 맞춘다. transform/joint
    타겟에만 의미가 있고 mesh/cluster/component/vertex 타겟에는 무시된다.
  - **Parent Followers to Targets**(기본 OFF) — 매칭 후 각 follower 를 타겟(컴포넌트면 소유
    오브젝트) 아래로 `parent` 한다. 이미 그 자식이면 스킵, 매칭된 월드 위치는 유지된다.
  - 원본의 **Rotate Order / Rotate Axis 는 제외**했다 — 이 툴은 월드 행렬 기반 매칭이라 두 옵션이
    의미가 없다. 채널을 하나도 안 켜면 경고만 남기고 아무 동작도 하지 않는다.
- **Create (at target positions)** — `Locators` / `Sphere` / `Cube`: 타겟 **수만큼** 컨트롤을 만들어
  **곧바로 타겟 위치/방향에 매칭**하고, 생성된 컨트롤을 **Followers 목록에 채운다**(씬에서도 선택).
- **Swap**: Targets ↔ Followers 목록 교환.
- (MEL 의 Blend Shape 버튼은 제거됨.)

### Constrain
접이식 섹션 3개로 구성된다(`CollapsibleBox`). **`Constraint`(기본 펼침)** / **`Skin Weight to
Constraint`(기본 접힘)** / **`Group Create`(기본 접힘, v01.12)**.

#### Constraint
타겟(드라이버) → 팔로워로 constraint 를 건다.

- `Targets` / `Followers` 리스트에 오브젝트 추가(Select/Add/Del/Up/Down).
- Options: `Maintain Offset` 체크 + constraint 종류 라디오
  (`Parent` / `Scale` / `Point` / `Orient` / `Point On Poly`).
- `Constrain` 클릭.
- **브로드캐스트**: target 이 1개면 모든 follower 에 동일 target 적용, 아니면 인덱스 1:1.

##### Matrix Constraint (v01.07)
`Matrix Constraint` 체크 시 일반 `*Constraint` 노드 대신 **`multMatrix` + `decomposeMatrix`
노드 네트워크**로 구속한다(레거시 `JUN_PY_MatrixCon_01_01.py` 이식). 컨스트레인트 노드가 쌓이지
않아 가볍고 부모공간/오프셋을 명시적으로 제어한다.

- 체크하면 **`Translate` / `Rotate` / `Scale` 채널 체크박스**(기본 전부 on)가 활성화되고,
  일반 constraint 종류 라디오는 비활성된다. 연결할 채널을 자유 조합한다.
- `Maintain Offset` 체크박스는 일반 모드와 **공유**한다.
  - on: 현재 오프셋을 유지하며 추종(offset = `follower.worldMatrix * target.worldInverseMatrix`).
  - off: follower 가 target 에 스냅.
- 부모 공간은 `follower.parentInverseMatrix[0]` 로 처리한다(부모가 없으면 자동 단위행렬).
- **jointOrient 보정**: follower 가 joint 면 `jointOrient` 역행렬로 rotate 출력만 보정해 회전이
  어긋나지 않는다(translate/scale 은 보정 전 행렬에서 가져옴).
- 구운 offset 행렬 그룹은 `JUN_matAll_grp` 아래로 정리된다.
- 브로드캐스트 규칙은 일반 모드와 동일(target 1개 → 다수 follower).
- 원본 대비 수정: scale 채널이 translate 플래그로 잘못 게이팅되던 버그, `Maintain Offset` 이 무시되던
  버그를 고쳤다.

#### Skin Weight to Constraint
선택한 버텍스의 **스킨 웨이트 비율**대로 영향 joint 들을 weight 로 follower 에
`parentConstraint` 한다. (예: 버텍스 웨이트가 `hip:0.2 / spine_01:0.5 / spine_02:0.3` 이면
세 joint 를 그 비율의 constraint weight 로 연결.)

- `Vertices` 리스트: 선택한 버텍스 컴포넌트(`mesh.vtx[i]`)를 담는다. `Followers` 리스트: 구속될 오브젝트.
- Options:
  - `Max Influence`(정수, 0 = 제한 없음): 웨이트 상위 N개 joint 만 남기고 합=1 로 정규화.
  - `Maintain Offset`.
  - `Per-vertex (vertex[i] -> follower[i], 1:1)`:
    - **해제(기본, average)**: 선택한 모든 버텍스의 joint 별 웨이트를 평균/정규화 → 모든 follower 에 동일 적용.
    - **체크(per-vertex)**: `vertices[i]` 웨이트 → `followers[i]` 에 1:1 적용(개수 일치 필요).
- `Skin Weight to Constraint` 클릭.
- 생성되는 `parentConstraint` 의 **Interp Type 은 항상 `Shortest`(2)** 로 설정된다(v01.05). 여러 joint 가
  가중 평균될 때 기본 `Average` 가 일으키는 회전 튐(짐벌)을 피한다.
- **`Locators` 버튼(v01.06)**: `Followers` 를 직접 만들 필요 없이 **로케이터를 자동 생성**해 동일한 스킨
  웨이트 constraint 를 건다. 생성된 로케이터는 `RigConnect_skinLoc_grp#` 그룹으로 묶이고, `Followers`
  목록에 자동으로 채워지며 씬에서 선택된다.
    - **average(기본)**: 선택 버텍스 전체의 **centroid** 에 로케이터 1개를 만들어 평균 웨이트로 구속.
    - **per-vertex 체크**: 버텍스마다 로케이터 1개를 그 **버텍스 월드 위치**(`mesh_vtxN_loc`)에 만들어 1:1 구속.

#### Group Create (v01.12)
리스트업된 각 오브젝트에 대해, **그 오브젝트와 위치·회전이 같은 빈 그룹**을 **오브젝트의 부모와
오브젝트 사이 계층**에 삽입한다. 오프셋(zero) 그룹을 만드는 리깅 상용 패턴이다.

```
before:  parent ─ obj
after :  parent ─ obj_con_01 ─ obj              (Count = 1)
         parent ─ obj_con_02 ─ obj_con_01 ─ obj (Count = 2)
```

- `Objects` 리스트에 대상 오브젝트 추가(Select/Add/Del/Up/Down).
- Options: `Count`(1~50) — 오브젝트당 만들 **중첩** 그룹 수.
- `Create Groups` 클릭 → 생성된 그룹들이 씬에서 선택된다.
- **그룹 이름**: `<오브젝트>_con_01`(중첩이면 `_con_02`, `_con_03` …). **`_con_01` 이 오브젝트의
  바로 위 부모**, 번호가 커질수록 더 바깥(위쪽) 그룹이다.
- 그룹은 오브젝트의 **월드 위치·회전**을 가지며(**스케일은 1**, `matchTransform` position/rotation),
  오브젝트의 **월드 트랜스폼과 기존 부모 계층은 그대로 유지**된다(그룹이 부모와 오브젝트 사이에만 삽입).
- **UUID 기반**: 씬에 같은 이름의 오브젝트가 여럿이거나 재부모(reparent)로 DAG 경로가 바뀌어도
  안전하도록, 대상 오브젝트·부모·생성한 그룹을 **UUID 로 잡아두고 매번 UUID → 현재 경로로 해석**해
  조작한다(중복 이름이면 경고를 남기고 첫 매치 사용).
- 존재하지 않거나(이름 못 찾음) 잠금/참조 등으로 재부모가 실패한 오브젝트는 건너뛰고 경고를 로그에 남긴다.

### Connect
어트리뷰트를 source → destination 으로 연결한다.

- Source/Destination 각 섹션:
  - `Objects` 리스트에 오브젝트 추가 → `List Attributes` 로 첫 오브젝트의 어트리뷰트를 우측 목록에 채움.
  - `search` 입력 + `Search`: 현재 목록에서 일치 항목을 **선택**하고, 없으면 검색어로 어트리뷰트를 다시 질의.
  - 우측 어트리뷰트 목록에서 연결할 항목을 **선택(다중 가능)**.
- `Connect Source to Destination`: 선택된 src/dst 어트리뷰트 수에 따라 3가지 패턴으로 연결.
  1. src obj 1개 & src/dst attr 수 동일 → 한 src 를 각 dst obj 의 attr 별로
  2. src/dst attr 각각 1개 → obj 쌍 1:1
  3. src/dst attr 수 동일 → obj 쌍 × attr 모두
- `Connect 52 Facial Target`: 52 ARKit 페이셜 어트리뷰트를 같은 이름끼리 obj 쌍 1:1 로 일괄 연결(없는 attr 은 스킵).

### List Connected
노드 그래프(up/down stream)를 타입별로 탐색한다.

- `Objects` 리스트에 오브젝트 추가.
- `List UpStream` / `List DownStream`: 연결된 노드의 **타입 목록**을 `Types` 에 표시.
- `Types` 에서 타입 선택 후 `Search`: 해당 타입의 **노드들**을 `Nodes` 에 표시.
- `Nodes` 목록에서 항목을 선택하면 씬에서도 선택된다.

### Connect Closest
각 driver 에 대해 가장 가까운 driven 을 1:1 매칭해 constraint 로 연결한다(A00140 이식).

- `Driven` / `Driver` 리스트 구성.
- constraint 종류 체크박스(`Parent` / `Point` / `Orient` / `Scale`, 다중) + `Maintain Offset`.
- `Connect`: 월드 좌표 유클리드 거리 기준 최근접 매칭. 각 driven 은 한 번만 사용.
- **`Get Closest`(v01.08, Driver 리스트 버튼 행)**: 각 driver 에 가장 가까운 오브젝트를 찾아
  `Driven` 을 **driver 순서대로** 채운다. "어떤 오브젝트가 각 driver 와 가장 가까운지" 발견용.
  - **후보 풀**: `Driven` 에 항목이 있으면 그걸 풀로, 비어 있으면 **현재 씬 선택**을 풀로 사용.
  - driver 자신은 풀에서 자동 제외(거리 0 회피). 매칭은 **greedy 1:1**(쓰인 후보는 제거)로
    `Connect` 와 동일한 로직 → 채워진 `Driven` 은 곧 `Connect` 가 연결할 페어의 **미리보기**.
  - 찾은 오브젝트는 로그(`driver -> closest (dist)`)에 남고 **뷰포트에서도 선택**돼 눈으로 확인 가능.

---

## 3. 구조 (개발자용)

```
A00145_RigConnect/
├── launch.py                       # run(): MainWindow + coral_dark 테마
├── __dragDrop_A00145.py            # 셸프 설치 (RigConnect)
└── app/
    ├── config/version.py
    ├── core/                       # UI 비의존 maya.cmds 로직
    │   ├── match_manager.py        # Match (MEL Match Tool 포팅: 위치/회전 매칭·컨트롤 생성·버텍스 노말)
    │   ├── constrain_manager.py    # Constrain  (MEL 포팅)
    │   ├── skin_constraint_manager.py # Skin Weight to Constraint (스킨 웨이트 → weighted parentConstraint)
    │   ├── group_create_manager.py # Group Create (부모↔오브젝트 사이 오프셋 그룹 _con_NN 삽입, UUID 기반)
    │   ├── connect_manager.py      # Connect    (MEL 포팅: attr 나열/검색/연결, 52 facial)
    │   ├── stream_manager.py       # List Connected (MEL 포팅: hyperShade up/down)
    │   ├── maya_scene.py           # Connect Closest (A00140 복사)
    │   └── closest_connector.py    # Connect Closest (A00140 복사)
    └── ui/
        ├── collapsible.py          # CollapsibleBox
        └── main_window.py          # QTabWidget 4탭 + 공유 로그 + Help>About
```

- 모든 textScrollList 는 `Framework.qt.JUN_mod_tsl_qt_v01` 위젯으로 대체.
- `app/core`(로직) ↔ `app/ui`(화면) 분리. 위젯은 값만 읽어 매니저에 전달.
- UI 문자열은 영어, 한국어는 주석/독스트링만.
