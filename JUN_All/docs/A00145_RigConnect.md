# A00145_RigConnect — RigConnect (사용 안내)

MEL `ConnectionTool V04.02`(탭: Constrain / Connect / List Connected) · `Match Tool V05.04` 와 기존
`A00140_ConnectClosest`(최근접 1:1 constraint)를 하나로 합친 툴이다.
**UI 는 PySide(Qt)**, 로직은 `maya.cmds`(일부 `maya.api.OpenMaya`) 로 작성되었다.

- 버전: `v01.30` (`app/config/version.py`) — Match 탭에 **Cache**(노드를 만들지 않고 월드 T/R/S 만 기억) 추가 (§Cache)
  · v01.29 는 Match 탭이 **500개 이상**이면 리스트업하지 않고 개수만 요약 + `List All` 버튼, 대량 매칭 속도 개선 (§대량 선택)
  · v01.28 은 Constrain > Constraint 하위 탭의 `Maintain Offset` 기본값을 **ON** 으로 변경 (§Constraint)
  · v01.27 은 Target Replace 하위 탭이 **Target Edit** 으로 확장(타깃 **추가 / 삭제** 추가) (§Target Edit)
  · v01.27 은 Match 탭의 셰이프 해석을 공용 [`Framework.core.maya_shape`](Framework_maya_shape.md) 로 교체(동작 변화 없음, 다중 셰이프 메시 안전)
- 위치: `JUN_All/tools/A00145_RigConnect`
- 형태: 아키텍처 (B) — Maya 내 PySide 툴. **최상위 4탭**(Match / Constrain / Connect / Attribute),
  Constrain·Connect 는 다시 **중첩 탭**으로 나뉜다
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
  - 그 외 컴포넌트(CV/엣지/페이스) → 컴포넌트 **중심** 위치. v01.30 부터 엣지·페이스도 된다 —
    예전에는 `cmds.pointPosition` 을 썼는데 이 명령은 **점 컴포넌트만** 받아서 엣지/페이스 타겟이
    조용히 실패했다. 지금은 `xform -q -ws -t` 로 컴포넌트가 걸친 점들을 받아 평균을 낸다
    (점 컴포넌트면 결과가 `pointPosition` 과 동일).
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
- **Cache (remember without creating nodes)** — 타겟의 월드 T/R/S 를 **값으로만** 기억한다(아래).
- **Swap**: Targets ↔ Followers 목록 교환.
- (MEL 의 Blend Shape 버튼은 제거됨.)

#### Cache — 로케이터 없이 "원래 자리" 기억하기 (v01.30)

오브젝트를 잠깐 옮겼다가 되돌리려고 **로케이터를 수천 개 만들던** 흐름을 대신한다.
씬에 아무것도 만들지 않고 월드 위치/회전/스케일만 들고 있는다.

```
Targets 에 오브젝트/컴포넌트 리스트업
  → [Cache Targets]      Followers 에 '@cache <이름>' 항목이 채워진다 (노드 생성 없음)
  → [Swap]               Targets = 캐시,  Followers = 오브젝트
  → 마음대로 옮긴다
  → [Match]              원래 자리로 복구
```

`Locators` 버튼 자리에 그대로 대응하므로 손에 익은 순서(만들기 → Swap → Match)가 같다.

| | 로케이터 방식 | Cache |
|---|---|---|
| 씬에 남는 것 | 로케이터 N 개(뷰포트·아웃라이너·undo) | **없음** |
| 되돌린 뒤 정리 | 로케이터를 지워야 함 | 필요 없음 |
| 스케일 | 로케이터가 못 들고 있음 → 복구 불가 | **복구됨**(Scale 체크) |
| 메시 오브젝트 | centroid 규칙이라 **회전이 사라짐** | 그 오브젝트의 행렬 그대로 |
| 원본이 지워지면 | 로케이터는 남아 있음 | 캐시도 남아 있음 |
| 1000개 왕복(mayapy) | 0.161s | **0.065s** (기억 단계만 보면 5배) |

- **컴포넌트도 된다.** 메시 버텍스는 위치 + **노말**(라이브 버텍스 타겟과 같은 해석), 커브 CV ·
  엣지 · 페이스는 컴포넌트 중심 위치를 기억한다.
- **캐시 항목은 씬 오브젝트가 아니다.** 리스트에는 `@cache pCube1` 처럼 한 줄로 보이지만
  `@` 는 마야 이름에 쓸 수 없는 글자라 실제 노드와 겹치지 않고, 리스트 위젯도 이 항목을 씬에서
  찾으려 하지 않는다(마야 호출 0회). 클릭해도 씬 선택이 바뀌지 않는다.
- **Clear Cache** — 기억한 값을 전부 버리고, 두 리스트에 남은 `@cache` 항목도 함께 걷어낸다
  (가리킬 데이터가 없는 항목을 남기지 않기 위해).
- **수명**: 캐시는 **창이 들고 있는 세션 데이터**다. 창을 닫거나 툴을 reload 하면 사라지고
  씬 파일에도 저장되지 않는다. 반대로 **원본 오브젝트를 지워도 캐시는 살아 있다**(값만 들고 있으므로).

> [!tip] 정확히 되돌리려면 **Scale 도 체크**한다. 캐시는 스케일까지 들고 있는데 채널이 꺼져 있으면
> 옮길 때 바뀐 스케일이 그대로 남는다(로그가 알려 준다). T/R/S 를 모두 켠 복구는 임시 노드도 거치지
> 않고 `xform -ws -matrix` 한 번으로 끝나는 **가장 빠른 경로**이기도 하다.

> [!warning] **캐시가 오브젝트를 보는 방식은 라이브 타겟과 한 군데 다르다.** 라이브 매칭에서
> 메시 오브젝트 타겟은 "정점 평균(centroid) 위치"로 해석되지만, 캐시는 그 **오브젝트의 월드 행렬**을
> 기억한다. 캐시의 목적이 "이 오브젝트를 제자리로 되돌리는 것"이기 때문이다(centroid 는 *다른* 것을
> 메시 가운데로 보내는 규칙이지 그 메시의 정체가 아니다). 덕분에 메시를 로케이터로 되돌릴 때
> 회전이 사라지던 문제가 캐시에는 없다.

- 예외 상황은 멈추지 않고 로그에 남긴다: follower 자리에 캐시 항목이 있으면(움직일 대상이 없음)
  건너뛰고, `Parent` 옵션은 캐시 항목을 부모로 삼을 수 없어 그 짝만 건너뛰며, 캐시를 비운 뒤
  옛 항목으로 Match 하면 그 짝만 실패하고 나머지는 계속 매칭된다.

#### 대량 선택 — 500개 이상은 리스트업하지 않는다 (v01.29)

버텍스 수천 개를 Targets 에 담는 일이 잦은데, 예전에는 **항목 수만큼 리스트에 줄을 만들고 줄마다
UUID 를 조회**(`cmds.ls(name, uuid=True)`)해서 **Select 를 누르는 순간이 매칭 자체보다 오래 걸렸다**.

이제 `Targets` / `Followers` 는 항목이 **500개 이상**이면 리스트에 펼치지 않고 요약만 보여준다.

```
Targets                       Number: 4212
┌──────────────────────────────────────┐
│  4212 item(s) stored, not listed.    │   ← 리스트 대신 요약 라벨
│  First: body_mesh.vtx[0]             │
│  They are used exactly as if they    │
│  were listed.                        │
└──────────────────────────────────────┘
[        List All (4212)         ]   ← 필요하면 여기서 전부 펼친다
[Add][Del][Up][Down]
[              Sort              ]
```

- **담긴 항목은 그대로 쓰인다.** `Match` / `Create (Locators/Sphere/Cube)` / `Swap` / `Sort` 는
  요약 상태에서도 **리스트에 펼쳐져 있을 때와 완전히 동일**하게 동작한다(개수·순서 모두 유지).
  헤더의 `Number:` 도 실제 개수를 보여준다.
- **`List All (N)`** — 다 보고 싶을 때 누르면 그때 리스트를 채운다(항목마다 UUID 를 붙이는 느린
  경로를 **사용자가 명시적으로 고르는** 셈이다). 펼친 뒤에는 항목 클릭 → 씬 선택, `Del`/`Up`/`Down`
  같은 편집이 전부 예전처럼 동작한다. 다시 `Select` 로 목록을 채우면 개수에 따라 요약으로 돌아간다.
- 요약 상태에서 `Del`/`Up`/`Down` 을 누르면 고를 항목이 없으므로
  `Items are not listed - press 'List All' to edit them.` 안내만 남는다. `Sort` 는 요약 상태에서도
  보관 목록을 정렬한다.
- 요약 상태에서는 **UUID 를 붙이지 않는다** — 담은 뒤 오브젝트를 **리네임**하면 그 항목은 이름으로
  찾지 못한다(리네임 안전성이 필요하면 `List All` 로 펼쳐 둔다). 기준값은 `main_window.py` 의
  `MATCH_LIST_LIMIT = 500`.
- 기능 자체는 공용 TSL 위젯의 `list_limit` 옵션이다 → [공용 리스트 위젯 문서](Framework_MOD_tsl_qt.md)

##### 매칭 자체도 빨라졌다 (v01.29)

`match_manager` 가 **한 번의 호출 동안 공유하는 `_Ctx`** 를 쓴다. 항목마다 반복되던 마야 호출을
없앤 것이다.

| 항목마다 하던 일 | 이제 |
|------------------|------|
| 회전 매칭용 임시 transform 을 `createNode` → `delete` | **하나만 만들어 돌려 쓰고** 끝에 지운다 |
| `MFnMesh` 를 다시 만들며 셰이프 재탐색 | 메시 이름으로 **캐시** |
| `_classify` 의 shape 타입 조회 | 노드 이름으로 **캐시** |

버텍스 1000개 매칭 기준 **약 5.6배** 빨라졌다(mayapy 측정: 0.330s → 0.059s). 캐시는 호출 하나가
끝나면 함께 버려지므로 씬이 바뀌어도 낡은 값이 남지 않는다.

### Constrain
기능별 **하위 탭 5개**로 나뉜다(v01.22).

```
[ Match ][ Constrain ][ Connect ][ Attribute ]
          └─ [ Constraint ][ Skin Weight ][ Group Create ][ Transfer ][ Target Edit ]
```

| 하위 탭 | 내용 |
|---------|------|
| **Constraint** | 타겟 → 팔로워 constraint (+ Matrix Constraint, v01.07) |
| **Skin Weight** | Skin Weight to Constraint — 선택 버텍스의 스킨 웨이트로 구속 (+ Locators) |
| **Group Create** | 오프셋(zero-out) 노드 삽입 (v01.12, 옵션 확장 v01.13) |
| **Transfer** | Constraint Transfer — 기존 constraint 를 다른 오브젝트로 이관 (v01.14) |
| **Target Edit** | 타깃(드라이버) **교체**(v01.20) / **추가 · 삭제**(v01.26) |

탭 라벨은 창 폭(기본 560)에 맞춰 줄였고 **전체 이름은 탭 툴팁**에 있다. 폭이 모자라면 라벨이
말줄임(`ElideRight`)된다. **각 하위 탭은 따로 스크롤**되므로 창을 줄여도 위젯이 겹치지 않는다.

> **v01.22 이전**: 접이식 박스(`CollapsibleBox`)를 위에서 아래로 쌓고 탭 전체를 스크롤 영역에
> 담았다. 기능이 5개로 늘면서 원하는 것을 보려면 접었다 폈다 해야 해서 하위 탭으로 바꿨다.
> (Connect 탭의 Source/Destination 섹션은 여전히 접이식이다.)

#### Constraint
타겟(드라이버) → 팔로워로 constraint 를 건다.

- `Targets` / `Followers` 리스트에 오브젝트 추가(Select/Add/Del/Up/Down).
- Options: `Maintain Offset` 체크(**기본 ON**, v01.28) + constraint 종류 라디오
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

#### Skin Weight — Skin Weight to Constraint
선택한 버텍스의 **스킨 웨이트 비율**대로 영향 joint 들을 weight 로 follower 에 constraint 한다.
(예: 버텍스 웨이트가 `hip:0.2 / spine_01:0.5 / spine_02:0.3` 이면 세 joint 를 그 비율의
constraint weight 로 연결.)

- `Vertices` 리스트: 선택한 버텍스 컴포넌트(`mesh.vtx[i]`)를 담는다. `Followers` 리스트: 구속될 오브젝트.
- **constraint 타입 라디오(v01.16)**: `Parent`(기본) / `Scale` / `Point` / `Orient` 중 선택. 위
  `Constraint` 박스와 같은 라디오 패턴이며, 어떤 타입이든 영향 joint 들의 **가중치(weight) 배분 방식은
  동일**하다. `pointOnPoly` 는 mesh 를 타겟으로 삼아 joint 가중 방식에 쓸 수 없으므로 목록에서 빠진다.
- Options:
  - `Max Influence`(정수, 0 = 제한 없음): 웨이트 상위 N개 joint 만 남기고 합=1 로 정규화.
  - `Maintain Offset`.
  - `Per-vertex (vertex[i] -> follower[i], 1:1)`:
    - **해제(기본, average)**: 선택한 모든 버텍스의 joint 별 웨이트를 평균/정규화 → 모든 follower 에 동일 적용.
    - **체크(per-vertex)**: `vertices[i]` 웨이트 → `followers[i]` 에 1:1 적용(개수 일치 필요).
- `Skin Weight to Constraint` 클릭.
- 회전을 다루는 타입(`Parent` / `Orient`)은 **Interp Type 이 항상 `Shortest`(2)** 로 설정된다(v01.05).
  여러 joint 가 가중 평균될 때 기본 `Average` 가 일으키는 회전 튐(짐벌)을 피한다.
  (`Point` / `Scale` constraint 에는 `interpType` 어트리뷰트가 없으므로 건너뛴다.)
- **`Locators` 버튼(v01.06)**: `Followers` 를 직접 만들 필요 없이 **로케이터를 자동 생성**해 동일한 스킨
  웨이트 constraint 를 건다. 생성된 로케이터는 `RigConnect_skinLoc_grp#` 그룹으로 묶이고, `Followers`
  목록에 자동으로 채워지며 씬에서 선택된다.
    - **average(기본)**: 선택 버텍스 전체의 **centroid** 에 로케이터 1개를 만들어 평균 웨이트로 구속.
    - **per-vertex 체크**: 버텍스마다 로케이터 1개를 그 **버텍스 월드 위치**(`mesh_vtxN_loc`)에 만들어 1:1 구속.

#### Group Create (v01.12, 옵션 확장 v01.13)
리스트업된 각 오브젝트에 대해, **그 오브젝트와 위치·회전이 같은 오프셋 노드**를 계층에 삽입한다.
오프셋(zero-out) 노드를 만드는 리깅 상용 패턴이다. **부모 쪽(Parent)** 과 **자식 쪽(Child)** 을
따로/함께 만들 수 있다.

```
Parent (기본):  parent 와 obj 사이에 삽입 (obj 가 아래로 밀린다)
  before:  parent ─ obj
  after :  parent ─ obj_zro_01 ─ obj               (Count = 1)
           parent ─ obj_zro_02 ─ obj_zro_01 ─ obj  (Count = 2)

Child       :  obj 와 그 자식들 사이에 삽입 (자식들이 아래로 밀린다)
  before:  obj ─ child
  after :  obj ─ obj_zro_01 ─ child                (Count = 1)
           obj ─ obj_zro_01 ─ obj_zro_02 ─ child   (Count = 2)
  (자식이 없으면 오프셋 노드 체인이 obj 아래에 그냥 매달린다.)
```

- `Objects` 리스트에 대상 오브젝트 추가(Select/Add/Del/Up/Down).
- Options (v01.13):
  - **`Suffix`**(기본 `zro`) — 노드 이름 접미사. 노드명 = `<오브젝트>_<suffix>_01`.
  - **`Count`**(1~50) — **방향당** 만들 **중첩** 노드 수.
  - **`Padding`**(1~6, 기본 2) — 번호 자릿수(`2` → `01, 02`; `3` → `001, 002`).
  - **`Type`** — `Group`(기본, 빈 그룹=transform) 또는 `Match object type`(오브젝트와 **같은 타입**으로
    생성). shape 없는 타입(joint 등)은 같은 nodeType 으로 `createNode`(**joint → joint**), shape 있는
    타입(curve/mesh/locator 등)은 오브젝트를 **복제**해 하위 자식만 지우고 자신의 shape 만 남긴다
    (**curve → curve, mesh → mesh**; 스케일은 1 로 초기화). 순수 그룹은 빈 그룹.
  - **`Side`** — `Parent`(기본 on, 오브젝트 위) / `Child`(오브젝트 아래). 둘 다 켜면 양쪽 모두 삽입.
- `Create Groups` 클릭 → 생성된 노드들이 씬에서 선택된다.
- **노드 이름**: `<오브젝트>_<suffix>_01`(중첩이면 `_02`, `_03` …). Parent 쪽은 **`_01` 이 오브젝트의
  바로 위 부모**, Child 쪽은 **`_01` 이 오브젝트의 바로 아래 자식**이다(번호가 커질수록 바깥/깊은 쪽).
- 노드는 오브젝트의 **월드 위치·회전**을 가지며(**스케일은 1**, `matchTransform` position/rotation),
  오브젝트·자식의 **월드 트랜스폼과 기존 계층은 그대로 유지**된다(노드가 사이에만 삽입).
- **UUID 기반**: 씬에 같은 이름의 오브젝트가 여럿이거나 재부모(reparent)로 DAG 경로가 바뀌어도
  안전하도록, 대상 오브젝트·부모·자식·생성한 노드를 **UUID 로 잡아두고 매번 UUID → 현재 경로로
  해석**해 조작한다(중복 이름이면 경고를 남기고 첫 매치 사용).
- 존재하지 않거나(이름 못 찾음) 잠금/참조 등으로 재부모가 실패한 오브젝트는 건너뛰고 경고를 로그에 남긴다.

#### Transfer — Constraint Transfer (v01.14)
이미 걸려 있는 constraint 를 **다른 오브젝트에 걸리도록 옮긴다**. 원본 constraint 를 지우고, **세팅이
같은** constraint 를 오른쪽(대상) 오브젝트에 새로 만든다.

```
before:  [targets] ─(parentConstraint, MO)→ objA     (objA 가 driven)
after :  [targets] ─(parentConstraint, MO)→ objB     (원본 삭제, objB 로 이관)
```

- 왼쪽 `Constraints` 리스트: 옮길 **constraint 노드**(또는 constraint 가 걸린 **트랜스폼** — 그 오브젝트의
  자식 constraint 로 자동 확장). 오른쪽 `Apply To` 리스트: 새로 constraint 를 받을(**driven**) 오브젝트.
- `Transfer Constraint` 클릭 → 옮겨진(새로 만든) constraint 들이 씬에서 선택된다.
- **Maintain Offset 보장**: 새 constraint 는 항상 `maintainOffset=True` 로 만들어 **대상 오브젝트가 튀지
  않는다**. 원본 driven 오브젝트도 삭제 후 월드 트랜스폼을 복원 → **명령 전후 두 오브젝트 모두 위치·회전 불변**.
- **세팅 복제**: constraint **타입**, **타깃(드라이버) 목록**, **타깃별 weight**, aim 계열의 `aim/up/worldUp`
  설정, parent/orient 의 `interpType` 을 그대로 옮긴다. `maintainOffset` 을 지원하지 않는 타입
  (geometry/poleVector 등)은 자동으로 MO 없이 재시도한다.
- **매핑**: 오른쪽이 **1개면 모든 constraint 를 그 오브젝트로**, 개수가 **같으면 인덱스 1:1**, 그 외에는 적은
  쪽 개수만큼 1:1 하고 경고.
- **UUID 기반**: constraint 노드·타깃·driven·대상 오브젝트를 모두 UUID 로 잡아, **같은 이름의 오브젝트가
  여럿이어도** 안전하게 동작한다(중복 이름이면 경고 후 첫 매치 사용).
- 어떤 종류의 constraint 든 동작한다(parent/point/orient/scale/aim/poleVector/geometry/pointOnPoly/
  normal/tangent). 읽기/재생성이 불가한 항목은 건너뛰고 경고를 남긴다.

#### Target Edit (v01.20 교체 · v01.26 추가/삭제)
Constraint Transfer 가 **driven(구속당하는 쪽)** 을 옮긴다면, 이쪽은 **타깃(드라이버)** 을 다룬다.
이미 걸려 있는 constraint 의 타깃을 **교체 / 추가 / 삭제**한다.

```
Constraints        Targets                     ← List Targets 로 채움
[ con_01 ]         [ tgt_A_01   [1/3] ]
[ con_02 ]         [ tgt_A_02   [2/3] ]        ← 여기서 고른 것이 Replace/Remove 대상
[ con_03 ]         [ tgt_A_04   [1/3] ]

New Target (used by Replace / Add)             ← Replace 의 대체 / Add 로 붙일 오브젝트

[ Replace Target ]
[ Add Target ][ Remove Target ]
```

세 동작 모두 **`Constraints` 리스트에서 고른 항목만** 대상으로 한다(아무것도 고르지 않으면 리스트 전체).
`[INFO] using n picked constraint(s) of m` 로 어느 범위로 동작했는지 로그에 남는다.
`List Targets` 도 같은 범위를 따르므로, 편집 뒤 자동 갱신되는 목록은 항상 "지금 버튼이 건드릴 범위"를 보여 준다.

##### Replace — 타깃 교체
여러 constraint 가 공통으로 쓰는 타깃 하나를 씬의 다른 오브젝트로 **일괄 교체**한다.

```
before:  con_01 : [tgt_A_01, tgt_A_02]     con_02 : [tgt_A_02, tgt_A_03]     con_03 : [tgt_A_04]
replace: tgt_A_02  →  tgt_B_02
after :  con_01 : [tgt_A_01, tgt_B_02]     con_02 : [tgt_B_02, tgt_A_03]     con_03 : [tgt_A_04]  (방치)
```

- 왼쪽 `Constraints` 리스트: 대상 **constraint 노드**(또는 constraint 가 걸린 **트랜스폼** — 그 오브젝트의
  자식 constraint 로 자동 확장). Constraint Transfer 와 같은 규칙이다.
- **`List Targets`** → 오른쪽 `Targets` 목록에 위 constraint 들이 쓰고 있는 **모든 타깃의 합집합**이
  처음 나온 순서대로 채워진다. 각 항목 뒤의 **`[n/m]`** 은 *m개 중 n개의 constraint 가 이 타깃을 쓴다*는
  뜻이고, 항목에 마우스를 올리면 어떤 constraint 인지 목록이 뜬다.
  검색은 공용 [Filter](Framework_MOD_filter_qt.md), `Select` 는 고른 타깃을 씬에서 선택한다.
- 아래 `New Target` 리스트에 대신 들어갈 오브젝트를 넣고 **`Replace Target`**.
  **그 타깃을 쓰지 않는 constraint 는 손대지 않는다.**
- **매핑**: New Target 이 **1개면 고른 모든 타깃이 그것으로**, 개수가 **같으면 인덱스 1:1**, 그 외에는 적은
  쪽 개수만큼 1:1 하고 경고.

**재생성이 아니라 연결 교체** — constraint 를 지웠다 다시 만들면 노드 이름, weight 에 물려 있는 연결
(IK/FK 스위치 등), 커스텀 어트리뷰트가 날아간다. 그래서 constraint 노드는 그대로 두고 `target[i]` 로
들어오는 **입력 연결만** 새 오브젝트 쪽으로 갈아끼운다. **weight 값·weight 연결·노드 이름·다른 타깃은
그대로 보존된다.** `target[i]` 의 실제 멀티 인덱스는 들어오는 연결에서 역추적하므로 `targetList` 순서에
의존하지 않는다.

- **joint ↔ 일반 트랜스폼** 교체도 처리한다. joint → 트랜스폼이면 `targetJointOrient`/`targetInverseScale`/
  `targetScaleCompensate` 연결을 끊고 기본값으로, 반대면 새로 연결한다.
- **셰이프 기반 constraint**(geometry/normal/tangent/pointOnPoly)는 새 타깃의 **같은 타입 셰이프**로 연결을
  옮긴다. 새 타깃에 대응하는 입력이 없으면(예: 셰이프 없는 로케이터) **아무것도 건드리지 않고** 경고만 남긴다.
- 고른 타깃이 이미 그 constraint 의 타깃이거나 새 타깃과 같은 오브젝트면 건너뛴다(중복 타깃 방지).

##### Add — 타깃 추가 (v01.26)
`New Target` 리스트의 오브젝트를 씬에서 골라 담고 **`Add Target`** → 대상 constraint들에 **새 드라이버로
추가**된다. 대상 constraint × New Target **모든 조합**으로 붙는다.

```
before:  con_01 : [tgt_A_01]                 con_02 : [tgt_A_02]
add   : + tgt_B_01
after :  con_01 : [tgt_A_01, tgt_B_01]       con_02 : [tgt_A_02, tgt_B_01]
```

- **이미 그 타깃을 쓰는 constraint** 는 건너뛰고 경고한다(중복 슬롯이 생기지 않는다).
  constraint 자신의 **driven 오브젝트**를 타깃으로 넣으려는 경우도 막는다.
- `Added target weight` 스핀박스 값이 새 타깃의 constraint weight 가 된다(기본 `1.0`).
  weight 어트리뷰트(`<타깃>W<n>`)는 Maya 가 만들고, **기존 타깃과 그 weight 는 그대로**다.
- `Keep driven objects in place` 가 켜져 있으면 `maintainOffset` 으로 붙여 driven 이 움직이지 않는다.
- 어떤 타입이든 붙는다. `maintainOffset`/`weight` 를 받지 않는 타입(geometry/poleVector 등)은 그 플래그를
  떼고 다시 시도하며, 무엇이 빠졌는지 로그에 남는다.

##### Remove — 타깃 삭제 (v01.26)
`Targets` 목록에서 고르고 **`Remove Target`** → 대상 constraint들에서 그 타깃 슬롯을 **지운다**.
**그 타깃을 쓰지 않는 constraint 는 손대지 않는다.**

```
before:  con_01 : [tgt_A_01, tgt_A_02]       con_02 : [tgt_A_02, tgt_A_03]     con_03 : [tgt_A_04]
remove: tgt_A_02
after :  con_01 : [tgt_A_01]                 con_02 : [tgt_A_03]               con_03 : [tgt_A_04]  (방치)
```

- 여러 타깃을 한 번에 골라 지울 수 있다. 필터로 **가려진** 선택은 제외된다(Replace 와 동일).
- **마지막 타깃을 지우면 Maya 가 constraint 노드까지 지운다**(실측). 실수로 리그를 잃지 않도록 기본값은
  *건너뛰고 경고*이며, `Delete the constraint when its last target is removed` 를 켜야 실제로 지워진다.
  이때 driven 오브젝트는 **마지막 값을 그대로 유지**한 채 연결만 끊긴다.
- 연결을 손으로 끊지 않고 `cmds.<type>Constraint(tgt, driven, e=True, remove=True)` 를 쓴다 — 직접 끊으면
  weight 별칭과 빈 멀티 인덱스가 남아 지저분해지기 때문이다.

##### 옵션 (Replace / Add / Remove 공용)

| 옵션 | 기본 | 적용 | 동작 |
|------|------|------|------|
| `Keep driven objects in place` | ON | 공통 | 타깃이 바뀌어도 driven 이 **제자리에 남도록** constraint offset 을 다시 계산한다. |
| | OFF | 공통 | 원래 offset 을 유지 → driven 이 예전에 가졌던 **상대 관계 그대로** 바뀐 타깃을 따라간다(그만큼 튄다). |
| `Rename the weight attribute to the new target` | OFF | Replace | weight 어트리뷰트 이름을 `tgt_A_02W0` → `tgt_B_02W0` 로. Maya 가 자동 생성한 이름일 때만 손댄다. |
| `Delete the constraint when its last target is removed` | OFF | Remove | 마지막 타깃 삭제(= constraint 노드 삭제)를 허용. 꺼져 있으면 그 constraint 는 건너뛰고 경고. |
| `Added target weight` | 1.0 | Add | 새로 붙는 타깃의 constraint weight. |

- **Keep in place 정확도** — Maya 2024 에서 실측한 offset 규약대로 계산한다.
  - `parentConstraint` : **타깃별** offset(`targetOffsetTranslate/Rotate`). 위치는 전체 월드 행렬로,
    회전은 스케일을 뺀 순수 회전으로 각각 옮긴다(두 오프셋이 서로 다른 공간에 산다 — 타깃에 스케일이
    걸려 있어도 맞는다). 타깃이 여러 개이고 **weight 가 섞여 있어도 정확**하다(타깃별 기여도만 유지되므로).
  - `pointConstraint` 덧셈 / `scaleConstraint` 곱셈 / `orient`·`aim` 회전 합성(오일러 순서 = driven 의
    `rotateOrder`).
  - `geometry`/`normal`/`tangent`/`pointOnPoly`/`poleVector` 는 보정할 offset 이 없어 그대로 둔다(로그로 알림).
  - **Remove 의 `parentConstraint`** 는 옛 타깃 → 새 타깃 델타가 없으므로, 남은 타깃들의 offset 을 **현재
    포즈 기준으로 다시 굽는다**. 각 타깃이 *혼자서도* 삭제 전 월드 행렬을 만들도록 맞추면, weight 가 어떻게
    섞이든 블렌드 결과가 같은 행렬이 되어 정확하다(= maintainOffset 으로 다시 건 상태와 동일).
  - **Add** 는 Maya 의 `maintainOffset` 플래그가 같은 일을 해 준다(실측 확인 — parent 는 새 타깃 offset 만,
    point/scale/orient 는 공유 `.offset` 을 재계산해 driven 이 움직이지 않는다).
  - 보정 후 driven 의 월드 행렬을 **다시 읽어 검증**하고, 어긋나면 오차를 경고로 남긴다.
- **UUID 기반** — 같은 이름의 오브젝트가 여럿이어도 안전하다.

### Filter — 이름으로 어트리뷰트 찾기 (v01.19)

Connect 탭의 Source/Destination 두 패널과 Attribute 탭의 어트리뷰트 목록이 **같은 검색 UI** 를 쓴다.
공용 위젯 [`Framework_MOD_filter_qt`](Framework_MOD_filter_qt.md) 이며, A00290_BSTool 의 Filter 와
동작이 같다.

```
Attributes                              Number: 2 / 47
┌───────────────────────────────────┐
│ browInnerUp                        │   ← 일치하는 것만 남고
│ mouthInnerCorner                   │      나머지는 숨는다
└───────────────────────────────────┘
Filter [ inner              ] [Clear]   [Select All]
```

- **입력하는 즉시** 일치하는 항목만 남고 나머지는 **숨는다**(지우는 게 아니라 가리는 것 —
  필터를 비우면 그대로 돌아온다).
- **부분 일치**(`Inner` → `browInnerUp`), **대소문자 무시**.
- 공백으로 나눈 **여러 단어는 AND**(`brow up` → `browInnerUp`, `browOuterUpLeft` …).
- `Number` 라벨이 필터 중에는 **`보이는 수 / 전체 수`** 로 바뀐다.
- `List Attributes` 로 목록을 다시 채워도 **필터가 유지**된다.

> **필터가 걸린 동안에는 "보이는 것이 작업 대상"이다.** Qt 는 항목을 숨겨도 선택 상태를 유지하므로,
> 그대로 두면 **가려서 안 보이는 어트리뷰트까지 연결·복사된다.** 그래서 —
> - **`Select All`** 은 **지금 보이는 것만** 선택한다.
> - **`Connect Source to Destination`** / **Attribute 탭의 복사**는 **보이면서 선택된** 것만 처리하고,
>   가려진 선택이 있으면 `[INFO] ... hidden by the filter were skipped` 로 알린다.
>
> 여러 검색어를 오가며 고른 것을 **한 번에** 처리하려면 **필터를 비운 뒤** 실행하면 된다
> (선택 자체는 지워지지 않는다).

> **바뀐 점(v01.18 이전과 비교)**: 예전 `Search` 버튼은 ① 현재 목록에서 일치 항목을 **선택**하고,
> ② 일치가 없으면 검색어로 어트리뷰트를 **다시 질의**했다(MEL 시절 동작). ①은 `Filter` + `Select All`
> 로 대체됐고, ②는 부분 일치가 하나도 없을 때만 도는 경로라 실질적으로 쓰이지 않았다
> (`List Attributes` 가 전체 재조회를 담당한다).

### Connect
"연결" 작업을 묶은 상위 탭. **하위 탭 3개**로 나뉜다(v01.23).

```
[ Match ][ Constrain ][ Connect ][ Attribute ]
                       └─ [ Connect ][ List Connected ][ Connect Closest ]
```

| 하위 탭 | 내용 |
|---------|------|
| **Connect** | 어트리뷰트 **양방향** 연결(Source ↔ Destination) (+ Match from Source, 52 facial) |
| **List Connected** | 오브젝트의 up/down stream 노드를 타입별로 탐색 |
| **Connect Closest** | 각 driver 에 가장 가까운 오브젝트를 1:1 로 constraint (A00140 이식) |

Constrain 탭과 같은 방식이다(§Constrain 참고) — 짧은 라벨 + 툴팁, `ElideRight`, **하위 탭별 스크롤**.

> **v01.23 이전**: 이 셋은 최상위 탭이었다(최상위 6탭). 모두 "연결" 작업이라 최상위에 따로 있을
> 이유가 없어 하나로 묶었고, 최상위는 **Match / Constrain / Connect / Attribute 4탭**이 됐다.

#### Connect — 어트리뷰트 연결
어트리뷰트를 **양방향으로** 연결한다(v01.24부터 역방향 추가). 개수가 안 맞아도 멈추지 않고
**되는 만큼** 연결한다(v01.25).

- Source/Destination 각 섹션(이 둘은 **동시에** 봐야 해서 탭이 아니라 접이식이다):
  - `Objects` 리스트에 오브젝트 추가 → `List Attributes` 로 첫 오브젝트의 어트리뷰트를 우측 목록에 채움.
  - **`Filter`**(v01.19, 기존 `Search` 버튼 대체): 입력하는 즉시 **일치하는 것만 남고 나머지는 숨는다**.
    `Select All` 은 **보이는 것만** 선택한다. → 아래 **Filter** 절 참고.
  - 우측 어트리뷰트 목록에서 연결할 항목을 **선택(다중 가능)**.
- **blendShape 노드를 리스트업하면 `List Attributes` 가 타겟 이름을 나열한다(v01.17).**
  타겟은 `weight[i]` 멀티에 걸린 **별칭(alias)** 이라 일반 멀티 확장으로는 인덱스 0(첫 타겟) 하나만
  잡혔다. 이제 `aliasAttr` 에서 별칭을 직접 읽어 **weight 인덱스 순으로 전부** 목록 맨 앞에 놓는다.
  → 컨트롤러 어트리뷰트 → 블렌드셰이프 타겟 연결을 목록에서 바로 고를 수 있다.
##### 연결 방향 (v01.24)

두 방향 버튼이 나란히 있다. **어느 쪽이 드라이버인지 화살표가 그대로 알려 준다.**

| 버튼 | 방향 |
|------|------|
| **`Source  ->  Destination`** | Source 어트리뷰트가 Destination 어트리뷰트를 구동 (기존 동작) |
| **`Destination  ->  Source`** | 그 반대. Destination 어트리뷰트가 Source 어트리뷰트를 구동 |

- **두 버튼의 차이는 방향뿐이다.** 아래 브로드캐스트 패턴도 **그대로 뒤집혀** 적용된다
  (예: 역방향에서 Destination 오브젝트가 1개면 그것이 모든 Source 오브젝트로 브로드캐스트).
- 로그에 `... 6 connection(s) [패턴]  Destination -> Source` 처럼 **방향이 함께** 찍힌다.
- 리스트를 다시 채울 필요 없이 버튼만 바꿔 누르면 된다. 한쪽에서 `List Attributes` /
  `Match from Source` 로 짝을 맞춰 놓고 방향만 고르는 흐름이 된다.

**브로드캐스트 패턴** — 3가지:

1. 드라이버 obj **1개** → 한 드라이버를 **각 대상 obj** 의 attr 인덱스별로 (브로드캐스트)
2. 양쪽 attr 각각 1개 → obj 쌍 1:1
3. 그 외 → obj 쌍 × attr 인덱스 모두

##### 개수가 달라도 멈추지 않는다 (v01.25)

예전에는 어트리뷰트 수가 서로 다르면 **아무것도 연결하지 않고 에러**를 냈다. 이제는 그러지 않는다.

| 상황 | 동작 |
|------|------|
| 어트리뷰트 수가 다름 (예: 5 vs 3) | **적은 쪽 개수만큼**(앞에서부터 3쌍) 연결. 남는 2개는 **건드리지 않고 그대로** |
| 오브젝트 수가 다름 | 같은 규칙. 단 패턴 1(드라이버 1개)은 원래 **모든** 대상 obj 에 브로드캐스트한다 |
| 개별 연결이 실패 (잠김·타입 불일치·읽기 전용 등) | **거기서 멈추지 않고** 나머지를 계속 연결한 뒤, 실패한 것만 따로 보고 |

남은 항목과 실패는 로그로 **이름까지** 알려 준다 — 조용히 넘기면 "왜 일부만 연결됐지?" 가 되기 때문.

```
       2 connection(s) [1 obj -> #objs, attr set matched]  Source -> Destination
[INFO] 1 Source attribute(s) had no counterpart and were left untouched: s2
[WARN] could not connect A.s1 -> B.d1 : The attribute 'B.d1' is locked and cannot be connected.
```

여전히 에러가 나는 경우는 **입력이 아예 비었을 때뿐**이다(오브젝트 목록이 비었거나 어트리뷰트를
하나도 안 골랐을 때).

> `connect_attrs` 는 `(개수, 패턴, report)` 를 돌려주고 `report` 에 남은 항목
> (`unused_driver_attrs` / `unused_driven_attrs` / `unused_driver_objs` /
> `unused_driven_objs`)과 `failed` 목록이 담긴다. 키가 `src/dst` 가 아니라
> **driver/driven** 인 이유: 이 함수는 양방향으로 쓰여서 역방향에서는 "src" 가 Destination 을
> 가리켜 헷갈리기 때문.

- `Connect 52 Facial Target`: 52 ARKit 페이셜 어트리뷰트를 같은 이름끼리 obj 쌍 1:1 로 일괄 연결(없는
  attr 은 스킵). 이 버튼은 **Source → Destination 한 방향**이다.

##### Match from Source — 이름이 비슷한 어트리뷰트 찾기 (v01.21)

Destination 패널의 **`Match from Source`** 는 소스에서 고른 어트리뷰트 각각에 대해 **이름이 가장
비슷한** destination 어트리뷰트를 찾아, **소스 순서 그대로** 목록 맨 위로 올리고 선택한다.

```
Source (A)  : brow_up, brow_down
Destination : lod0_mesh_body_eye_L_up,  lod0_mesh_body_eye_L_down,
              lod0_mesh_body_brow_up,   lod0_mesh_body_brow_down
                              │ Match from Source
                              ▼
Destination : lod0_mesh_body_brow_up    ← 선택됨 (brow_up 에 대응)
              lod0_mesh_body_brow_down  ← 선택됨 (brow_down 에 대응)
              lod0_mesh_body_eye_L_up      (나머지는 원래 순서대로 뒤에)
              lod0_mesh_body_eye_L_down
```

`Connect Source to Destination` 이 `src[i] ↔ dst[i]` 를 **순서로** 짝짓기 때문에, 이 상태에서 곧바로
연결 버튼을 누르면 그대로 연결된다. 수백 개 페이셜 타겟을 손으로 하나씩 짝지어 고르던 작업이
버튼 한 번이 된다.

- 소스에서 **아무것도 선택 안 했으면** 지금 보이는 소스 어트리뷰트 **전체**를 쓴다.
- 후보는 destination 목록의 **전체 항목**이다. 매칭 후 destination 필터는 **자동으로 비운다**
  (선택이 필터에 가려지면 연결 대상에서 빠지기 때문).
- **`Unique`**(기본 ON): destination 어트리뷰트 하나가 두 번 쓰이지 않는다. 소스 순서대로 선점한다.
- **`Min`**(기본 0.40): 아래 *coverage* 하한. 못 넘으면 "못 찾음" 으로 보고, 가장 가까웠던 후보와
  그 점수를 로그에 남긴다. 1.00 이면 소스 이름의 변별 단어가 **전부** 들어 있는 후보만 통과한다.
- 로그에 `source -> target (점수)` 가 한 줄씩 남는다. 같은 점수의 후보가 더 있었으면 `ambiguous`
  가 붙는다(이름만으로는 못 가렸다는 뜻).

##### 어떻게 찾는가

문자열을 통째로 비교하지 않고 **토큰(단어) 단위**로 비교한다.

1. **토큰화** — 구분자(`_`, `-`, `.`)와 **camelCase 경계** 양쪽에서 자른다.
   `lod0_mesh_body_brow_up` → `[lod0, mesh, body, brow, up]`, `browInnerUp` → `[brow, inner, up]`.
   덕분에 **표기 스타일이 달라도**(`browUp` ↔ `brow_up`) 매칭된다.
2. **역색인(inverted index)** — destination 전체를 **한 번만** 훑어 `토큰 → 후보 목록` 을 만든다.
   질의마다 후보 전체를 훑지 않는 이유가 이것이다.
3. **IDF 가중치** `log(1 + m/df)` — `lod0` `mesh` `body` 처럼 **모든 후보에 나오는 토큰은 가중치가
   0 에 가깝고**, `brow` 처럼 드문 토큰이 점수를 지배한다.
   → **공통 접두어를 사람이 지정할 필요가 없다. 자동으로 무시된다.**
4. **coverage** = (후보가 설명하는 질의 토큰의 IDF) / (질의 토큰 IDF 총합), 0~1.
   이게 로그에 찍히는 점수이자 `Min` 의 기준이다.
5. **동점 가르기** — precision(후보 쪽도 질의로 설명되는가) · 토큰 연속 등장 · 접미 일치 ·
   부분 문자열 · 길이 근접을 **작은 가산점**으로 얹는다. 전부 coverage 보다 작아 순위를 뒤집지 못한다.
   (예: `translateX` 질의는 `rotatePivotTranslateX` 와 coverage 가 똑같이 1.0 이지만, 가산점 덕에
   정확히 `translateX` 를 고른다.)
6. **폴백** — 토큰이 하나도 안 겹칠 때만 `difflib` 문자 단위 비교로 구제한다(`browup` ↔ `browsup`).
   difflib 비율은 coverage 와 척도가 달라(무관한 이름도 0.45 가 흔하다) **0.5→0, 1.0→1 로 다시
   스케일**해서 같은 문턱값이 양쪽에서 같은 뜻을 갖게 한다.

##### 속도 — O 표기법

기호: **n** = 소스(질의) 어트리뷰트 수, **m** = destination(후보) 어트리뷰트 수,
**t** = 이름당 토큰 수(작은 상수, 보통 2~6), **L** = 이름 길이,
**g** = *질의와 토큰을 공유해 실제로 점수를 계산한 후보 수* (핵심 값, 보통 g ≪ m),
**k** = 질의당 보관하는 상위 후보 수(상수 8).

| 단계 | 복잡도 | 비고 |
|------|--------|------|
| 토큰화 + 역색인 구축 | **O(m · L)** | destination 목록당 **한 번만** |
| 질의 1개: 후보 수집 | **O(g)** | 포스팅 리스트 병합 |
| 질의 1개: 점수 계산 | **O(g · t)** | 후보마다 토큰 집합 교집합(해시 조회 t 회) |
| 질의 1개: 상위 k 선별 | **O(g · log k)** | `heapq.nlargest` |
| **전체** | **O(m · L + n · (g · t + g · log k))** | t, k 는 상수 → 실질 **O(m·L + n·g)** |

- **최악의 경우**: 모든 후보가 모든 질의와 드문 토큰을 공유하면 g → m 이라 **O(n · m · t)**.
  브루트포스와 차수는 같지만, 쌍마다 하는 일이 편집 거리(O(L²))가 아니라 **해시 조회 t 회**라
  상수가 훨씬 작다.
- **정확한 가지치기**: 포스팅 리스트를 **드문 토큰부터** 읽다가, *아직 안 읽은* 토큰들의 IDF 합이
  `Min × (질의 IDF 총합)` 에 못 미치면 멈춘다. 그 뒤 토큰만 공유하는 후보는 coverage 가 문턱을
  넘을 **수 없으므로** 버려도 정답을 놓치지 않는다(휴리스틱이 아니라 증명 가능한 가지치기).
  → `lod0` `mesh` `body` 같은 보일러플레이트 토큰의 **거대한 포스팅 리스트는 아예 읽지 않는다.**
  실측에서 g 가 341 → 121 로 줄고 전체 시간이 절반이 됐다.
- **브루트포스 비교**: 모든 (질의, 후보) 쌍의 편집 거리/`difflib` 는 **O(n · m · L²)**.
  n = m = 1000, L ≈ 25 면 약 6억 회 문자 연산 — 파이썬에서 분 단위다.

**실측** (mayapy, 1 코어. 이름 = `<part>_<dir>_<NNN>`, destination 은 `lod0_mesh_body_` 접두어):

| n = m | 색인 구축 | 전체 | 질의당 | 평균 g |
|-------|-----------|------|--------|--------|
| 1,000 | 0.005 s | **0.15 s** | 0.12 ms | 121 |
| 2,000 | 0.009 s | **0.46 s** | 0.23 ms | 243 |
| 5,000 | 0.023 s | **2.63 s** | 0.53 ms | 546 |

같은 1,000 × 1,000 을 브루트포스 `difflib` 로 하면 **약 22 초** — **≈ 145 배** 차이다.
(질의당 시간이 n 에 따라 조금씩 느는 것은 g 가 m 에 비례해 늘기 때문으로, 위 식과 일치한다.)

> 구현: `app/core/attr_match.py`. **maya import 가 없는 순수 파이썬 모듈**이라 DCC 없이
> 단독으로 테스트·벤치마크할 수 있다. `attr_match.complexity_notes()` 가 위 요약을 문자열로 돌려준다.

### Attribute (v01.17)
**소스 오브젝트의 어트리뷰트를 골라, 다른 오브젝트들에 같은 정의로 새로 만든다.**
이름은 그대로 쓰거나 **Prefix / Suffix** 를 붙일 수 있다.

```
SRC.stretch  (double, min 0 / max 1, default 0.5, keyable, 현재값 0.75)
    ──▶  TGT.L_stretch_ctrl   (Prefix "L_", Suffix "_ctrl" → 정의·값 그대로 복제)
```

- **Source**: `Source Object` 리스트(첫 항목을 소스로 사용) → `List Attributes` 로 어트리뷰트 목록을
  오른쪽에 채운다. 목록에서 복사할 항목을 **다중 선택**(`Select All` 버튼 제공).
  - **`User defined only`**(기본 ON): 사용자 정의(커스텀) 어트리뷰트만 나열. 끄면 `translateX` 같은
    기본 어트리뷰트까지 전부 나온다.
  - **`Filter`**(v01.19): 예전에는 검색어가 **조회 인자**여서 Enter/`List Attributes` 로 다시 질의해야
    했는데, 이제는 이미 채워진 목록을 **입력하는 즉시** 거른다. → 아래 **Filter** 절 참고.
  - 컴파운드 **자식**(`tintR`/`translateX` 등)은 목록에서 제외된다. 부모를 복사하면 자식도 같이
    만들어지고, 자식만 따로는 `addAttr` 로 만들 수도 없다.
  - **blendShape 노드를 소스로 넣으면 타겟 이름들이 나열된다.** 타겟은 `weight[i]` 의 별칭이라
    `listAttr(userDefined=True)` 로는 `attributeAliasList` 밖에 안 나온다 → `aliasAttr` 에서 직접
    읽는다. `User defined only` ON 이면 **타겟만**, OFF 면 타겟 + 노드의 모든 어트리뷰트.
    - 타겟을 복사하면 컨트롤러에 **타겟 이름 그대로의 float 어트리뷰트**가 생긴다(키어블, 값 복사).
      blendShape weight 의 정의를 그대로 가져오므로 **soft range 0~1 / hard range -10~10** 이다.
    - 이렇게 만든 어트리뷰트를 `Connect` 탭에서 blendShape 타겟에 이어주면 페이셜 드라이버가 된다.
- **Targets**: 어트리뷰트를 **새로 만들** 오브젝트들(여러 개).
- **New Attribute Name**: `Prefix` / `Suffix`. 둘 다 비우면 **소스와 같은 이름**. 아래 `Preview` 가
  선택한 첫 항목의 결과 이름을 실시간으로 보여준다.
- **`Copy current value`**(기본 ON): 소스의 **현재 값**도 새 어트리뷰트에 넣는다.
- `Copy Attributes to Targets` 클릭.

보존되는 정의: **타입**(double/float/long/short/bool/enum/string/message/doubleAngle/doubleLinear/
컴파운드 `double3`·`float3`/multi), **min·max·soft min·soft max**, **default**, **keyable**,
**channel box 표시**, **hidden**, **enum 이름 목록**, **usedAsColor**(컬러 어트리뷰트).

- 같은 이름이 **이미 있는 타겟은 건너뛰고** 로그에 `[WARN]` 을 남긴다(덮어쓰지 않는다).
- 이름을 바꾸지 않은 경우에만 원본 **short name** 을 유지한다. Prefix/Suffix 로 이름이 바뀌면
  short name 은 Maya 가 새로 만들게 둔다(그대로 쓰면 다른 어트리뷰트와 **충돌**).
- 컴파운드 자식 이름은 부모의 새 이름을 따라간다(`tint`→`L_tint_ctrl` 이면 자식은
  `L_tint_ctrlR/G/B`).
- 전체가 하나의 **undo chunk** 라 `Ctrl+Z` 한 번으로 되돌아간다.

#### List Connected
노드 그래프(up/down stream)를 타입별로 탐색한다.

- `Objects` 리스트에 오브젝트 추가.
- `List UpStream` / `List DownStream`: 연결된 노드의 **타입 목록**을 `Types` 에 표시.
- `Types` 에서 타입 선택 후 `Search`: 해당 타입의 **노드들**을 `Nodes` 에 표시.
- `Nodes` 목록에서 항목을 선택하면 씬에서도 선택된다.

#### Connect Closest
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
- **cluster handle 위치 처리(v01.15)**: 거리 계산에 쓰는 월드 좌표는 기본적으로 transform 의 월드
  translate 지만, **`clusterHandle` 은 translate 가 `(0,0,0)` 인 채로 실제 중심이 shape 의 `origin`**
  (아이콘이 그려지고 rotate pivot 이 놓이는 지점)에 있다. 그래서 클러스터는 `origin` 을 월드로 변환해
  쓴다(폴백: rotate pivot → translate). 이 처리가 없으면 클러스터 후보가 전부 월드 원점으로 잡혀
  `Get Closest` / `Connect` 가 거리와 무관하게 **리스트 순서대로** 짝지어진다.

---

## 3. 구조 (개발자용)

```
A00145_RigConnect/
├── launch.py                       # run(): MainWindow + coral_dark 테마
├── __dragDrop_A00145.py            # 셸프 설치 (RigConnect)
└── app/
    ├── config/version.py
    ├── core/                       # UI 비의존 maya.cmds 로직
    │   ├── match_manager.py        # Match (MEL Match Tool 포팅: 위치/회전 매칭·컨트롤 생성·버텍스 노말, 대량 매칭용 _Ctx 캐시, capture())
    │   ├── snapshot_manager.py     # Match > Cache (노드 없이 월드 T/R/S 만 기억하는 추상 스냅샷, maya 비의존)
    │   ├── constrain_manager.py    # Constrain  (MEL 포팅)
    │   ├── skin_constraint_manager.py # Skin Weight to Constraint (스킨 웨이트 → weighted Parent/Scale/Point/Orient constraint)
    │   ├── group_create_manager.py # Group Create (부모/자식 쪽 오프셋 노드 _<suffix>_NN 삽입, 그룹·오브젝트 타입, UUID 기반)
    │   ├── constraint_transfer_manager.py # Constraint Transfer (constraint 를 다른 오브젝트로 이관: 삭제+동일세팅 재생성, MO 유지, UUID 기반)
    │   ├── constraint_target_manager.py # Target Edit (타깃(드라이버) 교체 = target[i] 입력 연결만 rewire / 추가·삭제 = constraint 명령의 add·remove, offset 재계산, UUID 기반)
    │   ├── attr_match.py           # Match from Source (이름 유사 어트리뷰트 검색: 토큰 역색인 + IDF, maya 비의존 순수 파이썬)
    │   ├── connect_manager.py      # Connect    (MEL 포팅: attr 나열/검색/연결, 52 facial)
    │   ├── attribute_manager.py    # Attribute  (어트리뷰트 정의를 읽어 다른 오브젝트에 재생성, prefix/suffix)
    │   ├── blendshape_utils.py     # blendShape 타겟(weight 별칭) 조회 — Attribute / Connect 탭 공용
    │   ├── stream_manager.py       # List Connected (MEL 포팅: hyperShade up/down)
    │   ├── maya_scene.py           # Connect Closest (A00140 복사)
    │   └── closest_connector.py    # Connect Closest (A00140 복사)
    └── ui/
        ├── collapsible.py          # CollapsibleBox
        └── main_window.py          # QTabWidget 최상위 4탭(Constrain 5 / Connect 3 하위 탭) + 공유 로그 + Help>About
```

- 모든 textScrollList 는 `Framework.qt.JUN_mod_tsl_qt_v01` 위젯으로 대체.
  Match 탭의 두 리스트만 `list_limit=MATCH_LIST_LIMIT`(500) 으로 **요약 모드**를 켠다.
- `app/core`(로직) ↔ `app/ui`(화면) 분리. 위젯은 값만 읽어 매니저에 전달.
- UI 문자열은 영어, 한국어는 주석/독스트링만.
