# A00145_RigConnect — RigConnect (사용 안내)

MEL `ConnectionTool V04.02`(탭: Constrain / Connect / List Connected) · `Match Tool V05.04` 와 기존
`A00140_ConnectClosest`(최근접 1:1 constraint)를 하나로 합친 툴이다.
**UI 는 PySide(Qt)**, 로직은 `maya.cmds`(일부 `maya.api.OpenMaya`) 로 작성되었다.

- 버전: `v01.53` (`app/config/version.py`) — Match 에 **`Keep Children in Place`**(기본 OFF):
  팔로워만 움직이고 **그 아래 오브젝트는 있던 월드 자리에 그대로** 둔다. Mirror 탭의 같은 이름
  체크박스와 **같은 코어**(`app/core/keep_children.py`)를 쓴다 (§Match)
  · v01.52 는 Attribute 가 만든 어트리뷰트는 **반드시 채널 박스에
  보인다**: `Keyable` 을 꺼도 "키만 못 거는 보이는 채널" 이 된다. 레퍼런스로 들어온 어트리뷰트는
  마야가 표시 변경을 거부하므로 **만들 때** 해 둔다. `Edit` 에 이미 숨은 것을 되살리는
  **`Show in Channel Box`** 버튼 (§Attribute)
  · v01.51 은 Attribute > **Set Value** 하위 탭: 여러 오브젝트의 공통
  어트리뷰트에 값을 한 번에 — float / int 는 `Start` + `Step`(리스트 순서대로), enum 은 **항목 이름**을
  골라서 (옛 Number Tool 이식, §Attribute > Set Value)
  · v01.50 은 Attribute > **Create** 목록에도 같은 다중 선택 + 다중 체크
  · v01.49 는 Attribute > Edit 목록에서 **Shift / Ctrl 로 여러 행을 골라
  한 번에 체크**한다 (§Attribute > Edit)
  · v01.48 은 Attribute > Create 의 `Add` / `Edit` 로 **`enum`** · **`string`**
  어트리뷰트도 정의해 만든다 (§Attribute > Create)
  · v01.47 은 Constrain > Constraint 의 종류가 **체크박스**:
  `Parent` + `Scale`, `Point` · `Orient` · `Scale` 중 2~3개를 **한 번에** 건다. 같은 채널을 구동하는 종류는
  서로를 끈다 (§Constraint)
  · v01.46 은 Attribute > Edit 에 **`Maintain connections`**(기본 ON):
  `Up` / `Down` 으로 순서를 바꾸기 전 연결을 이름으로 적어 두고, 옮긴 뒤 어긋난 것만 되돌린다 (§Attribute)
  · v01.45 는 창 메뉴 바를 공용 위젯으로 — `Help > Copy Tool Name`
  · v01.44 는 Attribute 탭을 **`Edit` / `Create` 두 하위 탭**으로:
  예전 `Copy` 와 `Delete` 가 **한 목록**(`Edit`)을 함께 쓰고, 고르는 방법이 선택에서
  **체크박스**로 바뀌었다. 여기에 **`Order` `Up` / `Down`** 이 들어와 **채널 박스의 나열 순서**를
  바꾼다 — 마야엔 재정렬 명령이 없어 `deleteAttr` + `undo` 로 하므로 **`Ctrl+Z` 로는 되돌아가지
  않는다**(로그가 알린다). 필터에 가려진 체크를 쓸지 정하는
  **`Include attributes hidden by the filter`**(기본 OFF) 도 함께 (§Attribute)
  · v01.43 은 로그창을 **공용 위젯**(Expand / Clear / Copy)으로 교체 (§로그창)
  · v01.42 는 Mirror > Create 의 **노드 네트워크 미러 수정** 두 가지:
  (1) `multiplyDivide` · `vectorProduct` · `plusMinusAverage` 처럼 **셰이딩 노드를 상속하는**
  리깅 유틸리티가 네트워크에서 통째로 빠져 있었다 — 이제 노드 **분류**(`getClassification`)로
  셰이딩을 가려 이들도 복제·재연결한다.
  (2) `A00170_driverTool` 의 AttachCrv **Maintain offset** 처럼 `multMatrix` 에 **값으로 박힌
  오프셋**은 원본 쪽 프레임 기준이라 미러된 오브젝트를 제자리에서 끌어냈다 — 미러가 놓아 준
  월드 행렬로 돌아오도록 그 상수를 **다시 푼다** (§노드 네트워크)
  · v01.41 은 Mirror > Apply 에 **`Keep Children in Place`**(기본 ON):
  Target 을 옮겨도 **그 아래 자식들은 옮기기 전 월드 위치 / 회전 / 스케일을 지킨다.** 리스트 이름을
  `Left` / `Right` → **`Source` / `Target`** 으로(모드 `Apply (Source -> Target)`, 버튼 `Mirror to Target`) (§Apply)
  · v01.40 은 Mirror 탭에 **`Apply` 모드**:
  새로 만들지 않고, `Target` 리스트의 **이미 있는 오브젝트**를 같은 줄 `Source` 오브젝트의
  **미러 위치 / 회전**으로 옮긴다(`Translation` / `Rotation` 체크박스). Mirror Plane · Mirror Type 은
  Create 와 공유 (§Apply)
  · v01.39 는 Connect > `Pair` 에 **`Swap` 버튼**:
  `Driven` ↔ `Driver` 두 리스트를 통째로 맞바꿔 **constraint 방향만 뒤집는다**
  (자리 순서와 `(Null)` 은 그대로) (§Pair)
  · v01.38 은 **`Mirror` 탭 신규**: 리스트에 담은 오브젝트와
  **그 아래 자식 전부**를 반대쪽으로 미러한다. 이름은 공용 토큰 규칙으로 바꾸고
  **스킨 웨이트 · 컨스트레인트 · 클러스터**를 반대쪽에 다시 세운다.
  반사 평면(YZ/XY/XZ) · Behavior / Orientation / **Reflect**(컨트롤러 기본, 월드
  `scaleX -1` 과 같은 상태) · 컨스트레인트가 아닌 **임의의 노드망**도 다시 잇는다 ·
  `Disable token check`
  (토큰이 없어 멈추면 그 오브젝트 이름을 찍고 `mirror_noToken_set` 세트로 묶어 선택) (§Mirror)
  · v01.37 은 Connect > `Connect Closest` 하위 탭이
  **`Pair`** 로 바뀌면서 **`Match by Name`** 추가: Driver 와 **이름이 비슷한/같은** Driven 을
  찾아 driver 순서로 세우고, 짝이 없는 자리는 **`(Null)`** 로 채운다. 짝짓는 방법을 고르는
  **`Pairing`**(거리 / 리스트 자리) 도 함께 (§Pair)
  · v01.36 은 Constrain 탭에 **`Update` 하위 탭** 추가:
  Attribute Editor 의 constraint **Update 버튼**(= `parentConstraint -e -maintainOffset ...`)을
  **리스트에 담은 constraint 전부에 한 번에** 돌린다 (§Update)
  · v01.35 는 Match 탭의 **Followers 에 컴포넌트(메시 버텍스·CV 등)를
  담을 수 있다**: 타겟의 월드 위치로 그 점을 옮긴다 (§컴포넌트 팔로워)
  · v01.34 는 Connect > Connect 하위 탭에 **`Match Same Name`**(이름이
  **완전히 같은 것만** 매칭)과 **`Show Match Only`**(기본 ON) 추가: 짝이 없는 자리를 **`(Null)`** 로 채워
  destination 목록을 소스와 **1:1 로 세우고**, 연결할 때 그 짝만 건너뛴다 (§Match from Source)
  · v01.33 은 **Attribute 탭이 하위 탭 3개로** (`Copy` / `Create` / `Delete`):
  `Create` 는 **프로파일에 적어 둔 정의**로 어트리뷰트를 만들고, `Delete` 는 사용자 정의 어트리뷰트를 지운다 (§Attribute)
  · v01.32 는 Match 탭에 **`1 <- n`** 체크박스(기본 ON): Targets 가 **하나면** Followers 전부가 그 하나에 매칭 (§Match)
  · v01.30 은 Match 탭에 **Cache**(노드를 만들지 않고 월드 T/R/S 만 기억) 추가 (§Cache)
  · v01.29 는 Match 탭이 **500개 이상**이면 리스트업하지 않고 개수만 요약 + `List All` 버튼, 대량 매칭 속도 개선 (§대량 선택)
  · v01.28 은 Constrain > Constraint 하위 탭의 `Maintain Offset` 기본값을 **ON** 으로 변경 (§Constraint)
  · v01.27 은 Target Replace 하위 탭이 **Target Edit** 으로 확장(타깃 **추가 / 삭제** 추가) (§Target Edit)
  · v01.27 은 Match 탭의 셰이프 해석을 공용 [`Framework.core.maya_shape`](Framework_maya_shape.md) 로 교체(동작 변화 없음, 다중 셰이프 메시 안전)
- 위치: `JUN_All/tools/A00145_RigConnect`
- 형태: 아키텍처 (B) — Maya 내 PySide 툴. **최상위 5탭**(Match / Constrain / Connect /
  Attribute / Mirror), Constrain·Connect·Attribute 는 다시 **중첩 탭**으로 나뉜다
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
- **Match**: 기본은 `Targets[i] → Followers[i]` 인덱스 1:1 매칭(`n <- n`). **rotateOrder 가 달라도**
  안전(`cmds.matchTransform`, 임시 transform 경유). 개수가 다르면 적은 쪽만 매칭하고 경고.
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

##### 컴포넌트 팔로워 — 버텍스를 타겟 위치로 (v01.35)

`Followers` 에도 **컴포넌트**(메시 버텍스 `mesh.vtx[i]`, 커브 CV, 엣지, 페이스)를 담을 수 있다.
Targets 에 로케이터를, Followers 에 버텍스를 넣고 `Match` 하면 **그 점이 로케이터 자리로 간다.**

```
Targets : locator2            Followers : SIN_Body1.vtx[81]
                 [ Match ]
[OK] Match
       1 matched, 0 skipped [TR] (n <- n)
       [note] 1 component follower(s) matched by position only - rotation/scale
              do not apply to a vertex or CV
```

- **타겟은 종류를 안 가린다.** 로케이터·조인트(월드 rotatePivot), 다른 메시의 버텍스, CV/엣지/페이스
  (컴포넌트 중심), 메시 오브젝트(centroid), clusterHandle(피벗), 캐시 항목(`@cache`) 전부 쓸 수 있다.
- **위치만 옮긴다.** 점에는 회전도 스케일도 없다. `Rotation` / `Scale` 은 켜져 있어도 무시하고
  로그에 `[note]` 한 줄로 알린다. `Translation` 을 끄면 옮길 것이 없어 **skip** 된다.
- **`Parent Followers to Targets` 는 건너뛴다** — 버텍스는 부모를 가질 수 없다(이것도 `[note]`).
- 엣지·페이스처럼 **점이 여럿 걸린** 컴포넌트는 **중심**이 타겟 위치에 오도록 통째로 옮긴다.
  (절대 좌표를 그대로 주면 걸린 점이 전부 한 자리로 뭉개진다.)
- `1 <- n`, Swap, Cache 는 그대로 어울린다 — 예: 버텍스 여러 개를 로케이터 하나로 모으기.

> **v01.34 까지는 `0 matched, 1 skipped` 로 실패했다.** `cmds.matchTransform` 이 컴포넌트를
> 인자로 받지 못해서(`At least one source and one target object is needed to match transforms.
> Found 1.`) 팔로워를 늘 transform 으로 다뤘기 때문이다. 지금은 팔로워가 컴포넌트면 타겟에서
> 월드 위치 하나만 뽑아 `xform` 으로 그 점을 옮기는 **별도 경로**로 간다.

- **Match Options** (레거시 `DOOTOOL_PY_TOOL_Match.py` 이식, v01.10). 기본 체크 상태는 원본을 따름:
  - **Translation**(기본 ON) — follower 의 월드 위치를 타겟에 맞춘다. **컴포넌트 팔로워는 이것만**
    받는다(v01.35).
  - **Rotation**(기본 ON) — follower 의 월드 회전을 타겟에 맞춘다(vertex 타겟이면 노말 정렬).
    컴포넌트 팔로워에는 무시된다.
  - **Scale (world space)**(기본 OFF) — follower 의 **월드 스케일**을 타겟에 맞춘다. transform/joint
    타겟에만 의미가 있고 mesh/cluster/component/vertex 타겟에는 무시된다.
  - **Parent Followers to Targets**(기본 OFF) — 매칭 후 각 follower 를 타겟(컴포넌트면 소유
    오브젝트) 아래로 `parent` 한다. 이미 그 자식이면 스킵, 매칭된 월드 위치는 유지된다.
  - **Keep Children in Place**(v01.53~, **기본 OFF**) — 팔로워를 옮겨도 그 **아래 오브젝트는
    있던 월드 자리**에 남는다(아래 절).
  - **`1 <- n`**(v01.32~, **기본 ON**) — Targets 에 오브젝트가 **정확히 하나**일 때 Followers
    **전부**를 그 하나에 매칭한다. 컨트롤러 여러 개를 한 자리에 모으거나, 한 버텍스/캐시 위치로
    모두 보낼 때 쓴다.
    - **Targets 가 2개 이상이면 켜져 있어도 아무 일도 하지 않는다** — 평소대로 `Targets[i] →
      Followers[i]`(`n <- n`). 그래서 늘 켜 둬도 기존 작업 방식이 달라지지 않는다.
    - `1 <- n` 에서는 개수가 달라도 **정상**이라 개수 불일치 경고를 띄우지 않는다.
    - 타겟 종류별 규칙은 그대로다 — 메시 타겟이면 팔로워 전부가 centroid 로 **위치만**,
      버텍스 타겟이면 전부가 같은 노말 정렬 회전까지 받는다. `Parent Followers to Targets` 를
      켜면 **팔로워 전부가 그 하나의 타겟 아래로** 들어간다.
    - 로그에 `1 <- n` / `n <- n` 중 무엇으로 처리했는지 찍는다.
  - 원본의 **Rotate Order / Rotate Axis 는 제외**했다 — 이 툴은 월드 행렬 기반 매칭이라 두 옵션이
    의미가 없다. 채널을 하나도 안 켜면 경고만 남기고 아무 동작도 하지 않는다.
- **Create (at target positions)** — `Locators` / `Sphere` / `Cube`: 타겟 **수만큼** 컨트롤을 만들어
  **곧바로 타겟 위치/방향에 매칭**하고, 생성된 컨트롤을 **Followers 목록에 채운다**(씬에서도 선택).
- **Cache (remember without creating nodes)** — 타겟의 월드 T/R/S 를 **값으로만** 기억한다(아래).
- **Swap**: Targets ↔ Followers 목록 교환.
- (MEL 의 Blend Shape 버튼은 제거됨.)

##### Keep Children in Place — 팔로워만 옮기고 자식은 두기 (v01.53)

팔로워를 타겟으로 보내면 그 **아래 계층도 통째로 따라간다**. 컨트롤만 자리를 잡고 그 밑에 달린
것들은 **지금 자리에 그대로 있어야 할 때**가 있어서, 체크박스 하나로 고른다. **기본은 꺼짐** —
평소에는 자식이 부모를 따라가는 것이 맞다.

```
Targets : jnt_arm_L          Followers : ctrl_arm_L   (그 아래 ctrl_hand_L, geo_pad)
[x] Keep Children in Place
                 [ Match ]
[OK] Match
       1 matched, 0 skipped [TRK] (n <- n)
       [note] 2 child object(s) kept their world position / rotation
```

- **직계 자식만** 잡는다 — 자식을 월드에 붙잡아 두면 **손자들은 로컬이 그대로**라 저절로 제자리다.
- **읽기는 아무것도 옮기기 전에 전부** 한다. 앞 줄 팔로워가 움직이면 그 아래 자식도 밀리므로,
  옮기기 시작한 뒤에 읽으면 이미 늦은 값이다.
- **팔로워끼리 부모/자식이면 부모부터 맞춘다**(체크가 켜졌을 때만 순서를 정렬한다). 자식 쪽
  팔로워는 보존 대상에서 빠진다 — 제 차례에 **제 타겟**으로 가야 하니까. 순서를 안 맞추면
  자식을 먼저 맞춰 놓고 부모가 다시 끌고 간다.
- **잠기거나 연결된 채널**이 있는 자식은 잡을 수 없다 — 부모를 따라간 채로 두고 이유를 로그에
  적는다(`xform` 은 잠긴 채널을 에러 없이 건너뛰고 나머지만 써서 **반쪽 결과**를 만든다).
- 컨스트레인트 노드는 자식으로 세지 않는다(driven 밑에 붙어 있을 뿐 위치에 의미가 없다).
- 부모가 **좌우손계를 바꾸면**(음수 스케일 타겟에 `Scale` 을 켜고 매칭) 자식이 월드에 그대로
  있으려면 자기 로컬 스케일 부호가 바뀐다. 그때만 `scale` 채널까지 검사하고, 몇 개가 그렇게
  됐는지 로그에 적는다.
- 키가 걸린 자식 채널을 바꿨으면 **키는 안 찍는다** — 몇 개인지 알리므로 필요하면 직접 키를 건다
  (안 그러면 프레임을 옮기는 순간 커브 값으로 돌아간다).
- 로직은 **Mirror 탭의 같은 체크박스와 공용**이다(`app/core/keep_children.py`, v01.53 에서
  `mirror_manager` 에서 떼어 냈다). 두 탭의 동작이 갈라지지 않는다.

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
기능별 **하위 탭 6개**로 나뉜다(v01.22 에 5개, v01.36 에 `Update` 추가).

```
[ Match ][ Constrain ][ Connect ][ Attribute ]
          └─ [ Constraint ][ Skin Weight ][ Group Create ][ Transfer ][ Target Edit ][ Update ]
```

| 하위 탭 | 내용 |
|---------|------|
| **Constraint** | 타겟 → 팔로워 constraint (+ Matrix Constraint, v01.07) |
| **Skin Weight** | Skin Weight to Constraint — 선택 버텍스의 스킨 웨이트로 구속 (+ Locators) |
| **Group Create** | 오프셋(zero-out) 노드 삽입 (v01.12, 옵션 확장 v01.13) |
| **Transfer** | Constraint Transfer — 기존 constraint 를 다른 오브젝트로 이관 (v01.14) |
| **Target Edit** | 타깃(드라이버) **교체**(v01.20) / **추가 · 삭제**(v01.26) |
| **Update** | 기존 constraint 의 **maintain offset 을 지금 포즈로 다시 굽기** (v01.36) |

탭 라벨은 창 폭(기본 560)에 맞춰 줄였고 **전체 이름은 탭 툴팁**에 있다. 폭이 모자라면 라벨이
말줄임(`ElideRight`)된다. **각 하위 탭은 따로 스크롤**되므로 창을 줄여도 위젯이 겹치지 않는다.

> **v01.31**: 하위 탭이 없는 **Match 탭만 스크롤에 안 담겨 있었다.** 그래서 창이 모자라면 Qt 가
> 위젯을 짜부라뜨려 TSL 리스트 위로 `Add/Del/Up/Down` 버튼이 겹쳐 보였다(창 620px 에서 측정하면
> 리스트 아래와 버튼 위가 **−125px**, 즉 125px 파고들었다). 다른 탭들과 같은 `_scrolled()` 에
> 담아 고쳤고, 창 기본 높이도 860 → **900** 으로 올렸다. 이제 창을 500px 로 줄여도 간격이 유지된다.

> **v01.22 이전**: 접이식 박스(`CollapsibleBox`)를 위에서 아래로 쌓고 탭 전체를 스크롤 영역에
> 담았다. 기능이 5개로 늘면서 원하는 것을 보려면 접었다 폈다 해야 해서 하위 탭으로 바꿨다.
> (Connect 탭의 Source/Destination 섹션은 여전히 접이식이다.)

#### Constraint
타겟(드라이버) → 팔로워로 constraint 를 건다.

- `Targets` / `Followers` 리스트에 오브젝트 추가(Select/Add/Del/Up/Down).
- Options: `Maintain Offset` 체크(**기본 ON**, v01.28) + constraint 종류 **체크박스**(v01.47, 예전엔 라디오)
  (`Parent` / `Scale` / `Point` / `Orient` / `Point On Poly`, 기본은 `Parent` 하나).
- `Constrain` 클릭.
- **브로드캐스트**: target 이 1개면 모든 follower 에 동일 target 적용, 아니면 인덱스 1:1.

##### 여러 종류를 함께 걸기 (v01.47)

체크한 종류를 **모두** 건다. 조건은 하나 — **구동하는 채널이 겹치지 않아야 한다.**

| 종류 | 구동 채널 | 함께 걸 수 있는 것 |
|------|-----------|--------------------|
| `Parent` | translate + rotate | `Scale` |
| `Point` | translate | `Orient` · `Scale` |
| `Orient` | rotate | `Point` · `Scale` |
| `Scale` | scale | `Parent` 또는 `Point` · `Orient` |
| `Point On Poly` | translate + rotate (타깃이 버텍스) | **혼자** |

- 예: `Parent` + `Scale` → follower 마다 `parentConstraint` 와 `scaleConstraint` 둘.
  `Point` + `Orient` + `Scale` → 셋.
- **겹치는 것을 체크하면 먼저 체크돼 있던 쪽이 꺼진다** — `Parent` 가 켜진 채 `Point` 를 누르면 `Parent` 가 꺼지고
  `Scale` 은 그대로 남는다. 마야가 두 번째를 `Object is already connected.` 로 거절하기 때문이다(실측: Parent → Point,
  Parent → Orient). 체크박스에 마우스를 올리면 무엇과 겹치는지 나온다.
- `Point On Poly` 는 버텍스를 타깃으로 쓰므로 `Scale` 과도 섞을 수 없어 혼자 쓴다.
- 건 순서는 항상 `Parent` → `Scale` → `Point` → `Orient`. 로그에 종류별 개수가 남는다
  (`2 Parent constraint(s) created` / `2 Scale constraint(s) created`).
- **한 follower 에서 한 종류가 실패해도 나머지는 계속 건다**(이미 다른 constraint 가 걸린 채널 등) — 실패는
  `[WARN] <follower> <- <target> (<종류>): <이유>` 로 하나씩 남는다. 전체가 **Undo 한 번**이다.
- 아무것도 체크하지 않고 누르면 `[ERR] ... No constraint type is checked.` 만 남기고 아무것도 만들지 않는다.

> **주의 — 마야는 순서에 따라 에러 대신 `pairBlend` 를 끼운다.** 이미 `pointConstraint` 가 걸린 오브젝트에
> `parentConstraint` 를 걸면 에러가 나지 않고 두 constraint 사이에 **`pairBlend` 가 생겨 섞인다**(실측).
> 반대 순서(Parent 먼저)면 `already connected` 에러다. 이 탭은 한 번에 거는 종류끼리만 겹침을 막으므로,
> **이미 constraint 가 걸린 오브젝트**에 다시 걸 때는 채널 상태를 먼저 확인할 것.

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

#### Update — 오프셋을 지금 포즈로 다시 굽기 (v01.36)
Attribute Editor 에서 constraint 를 열면 **Update** 버튼이 있다. constraint 가 걸린 오브젝트를
다른 자리로 옮긴 뒤 이 버튼을 누르면 offset 이 **지금 위치/회전 기준으로 다시 계산**되어, 옮긴
자리 그대로 물린다. MEL 로는 이렇게 찍힌다.

```mel
parentConstraint -e -maintainOffset curve2  curve1_parentConstraint1;
```

AE 버튼은 **한 번에 constraint 하나씩**이다. 이 탭은 같은 일을 **리스트에 담은 constraint
전부**에 돌린다.

```
Constraints                        ← constraint 노드, 또는 constraint 가 걸린 오브젝트
[ curve1_parentConstraint1 ]         (오브젝트를 담으면 그 아래 constraint 로 자동 확장)
[ curve3 ]
[ jnt_L_arm ]

[ Update Offset ]
```

- **고른 항목만** 대상으로 한다(아무것도 고르지 않으면 리스트 전체). Target Edit 과 같은 규칙이고
  `[INFO] using n picked constraint(s) of m` 로 범위가 로그에 남는다.
- 지원 타입: **parent / point / orient / scale / aim / pointOnPoly**.
  `geometry` / `normal` / `tangent` / `poleVector` 는 애초에 `maintainOffset` 플래그가 없어
  (Maya 2024 실측: `Invalid flag 'mo'`) 건너뛰고 경고한다.
- 로그는 값이 실제로 바뀐 것(`updated`)과 그대로인 것(`no change`)을 구분한다. 아무도 움직이지
  않은 constraint 를 같이 담아도 무해한 no-op 이므로, "일단 다 담고 돌리기" 가 안전하다.

```
       curve1_parentConstraint1 (parentConstraint) : updated  <- curve2
       jnt_L_arm_parentConstraint1 (parentConstraint) : no change  <- ctl_L_arm
       1 of 2 constraint(s) re-baked
[OK] Update Offset
```

> **driven 을 어떻게 옮기나** — constraint 가 살아 있으면 driven 의 채널이 연결되어 있어 그냥은
> 움직일 수 없다. 보통은 `blendParent1`(키가 있는 오브젝트에 constraint 를 걸면 Maya 가 만드는
> pairBlend 어트리뷰트)을 **0 으로 두고 옮긴 뒤 Update → 다시 1 로** 되돌린다. 어떤 방법으로
> 옮겼든 이 기능은 **현재 월드 행렬**을 읽어 offset 을 굽는다.

##### 계산은 Maya 명령을 그대로 쓴다
offset 공식을 다시 구현하지 않고 `cmds.<type>Constraint(*targets, cn, e=True, mo=True)` 를
부른다 — AE 버튼과 결과가 어긋날 이유가 없어야 하기 때문이다. 대신 **명령에 넘길 타깃 목록**이
까다로워서, Maya 2024 에서 실측으로 확인했다.

- **타깃을 전부 넘겨야 한다.** 타깃 2개 중 하나만 넘기면 **넘긴 슬롯의 offset 만** 다시 구워지고
  나머지는 옛 값 그대로 남는다 → weight 가 섞이는 순간 driven 이 튄다.
- **타깃이 아닌 오브젝트를 넘기면 `-e` 인데도 타깃으로 추가된다.** 그래서 이름을 새로 만들지 않고
  지금 연결된 target 슬롯에서 그대로 읽어 넘긴다.
- `<type>Constraint -q -targetList` 는 **짧은 이름**이라 동명 노드가 있으면 어긋난다. Target Edit
  과 같은 `_target_entries()`(target 슬롯의 입력 연결을 역추적한 **롱네임**)를 쓴다.
- 타깃이 여럿이고 **weight 가 섞여 있어도 정확**하다 — driven 월드 행렬 오차 **4e-16**
  (parent / point / orient / scale / aim / pointOnPoly 전부 실측).
- 업데이트 뒤 driven 의 월드 행렬을 **다시 읽어 검증**하고, 어긋나면 경고를 남긴다.

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
                       └─ [ Connect ][ List Connected ][ Pair ]
```

| 하위 탭 | 내용 |
|---------|------|
| **Connect** | 어트리뷰트 **양방향** 연결(Source ↔ Destination) (+ Match from Source / Match Same Name, 52 facial) |
| **List Connected** | 오브젝트의 up/down stream 노드를 타입별로 탐색 |
| **Pair** | Driver ↔ Driven 을 **거리** 또는 **이름**으로 1:1 짝짓고 constraint (A00140 이식 + v01.37 이름 매칭) |

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
| 한쪽에 **`(Null)`** 자리가 있음 (v01.34) | 그 자리는 **양쪽에서 함께** 빠진다. 뒤의 짝은 밀리지 않는다 |

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

> 위는 **`Show Match Only` 를 끈** 모습이다. 기본값(ON)에서는 짝이 없는 자리를 `(Null)` 로 채워
> **소스와 1:1 로 세운 줄만** 남는다 — 바로 아래 절 참고.

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

##### 이름이 똑같은 것만 — `Match Same Name` (v01.34)

**`Match Same Name`** 은 이름이 **완전히 같은**(대소문자 구분) destination 어트리뷰트만 짝짓는다.
유사도도 추측도 없다 — `Min` 은 무시된다.

```
Source      : ab, abc, abcd
Destination : bcd, cd, abcd, ab
                    │ Match Same Name
                    ▼
Destination : ab        ← 선택됨 (ab 에 대응)
              (Null)    ← abc 에 짝이 없다
              abcd      ← 선택됨 (abcd 에 대응)
```

양쪽이 **이미 같은 이름 규칙을 쓰는데** 느슨한 매칭이 남의 어트리뷰트를 물어 오는 게 더 나쁜
상황에서 쓴다(같은 리그의 두 노드, 같은 이름으로 만든 blendShape 타겟 등).
`Match from Source` 와 **버튼만 다르고 나머지는 전부 같다** — `Unique`, `Show Match Only`, 로그 형식,
연결로 이어지는 흐름이 그대로다.

> 구현은 `attr_match.match_exact_names()`. 색인도 점수도 필요 없다 — `이름 → 인덱스` 사전 하나면
> 끝난다(O(n + m)). 반환 형태를 `match_attributes` 와 **똑같이** 맞춰 둬서 UI 가 두 매칭을 구분 없이
> 다룬다.

##### 짝이 없는 자리 — `Show Match Only` 와 `(Null)` (v01.34)

**`Show Match Only`**(기본 **ON**)를 켜면 destination 목록에 **소스와 1:1 로 맞춘 줄만** 남는다.
짝을 못 찾은 소스 자리는 **`(Null)`** 로 채우고, 그 줄까지 **전부 선택**한다.

| | `Show Match Only` **ON** (기본) | **OFF** (v01.33 까지의 동작) |
|---|---|---|
| 목록 | 소스와 자리를 맞춘 줄만 (`(Null)` 포함) | 매칭된 것이 맨 위, 나머지는 원래 순서로 뒤에 |
| 선택 | 전부 (`(Null)` 포함) | 매칭된 것만 |
| 짝이 어긋날 위험 | 없다 | 짝을 못 찾은 소스가 있으면 **그 뒤가 통째로 밀린다** |

**자리를 비우지 않는 것이 핵심이다.** 연결은 `src[i] ↔ dst[i]` 를 **순서로** 짝짓기 때문에,
짝 없는 소스 자리를 그냥 건너뛰고 목록을 만들면 그 뒤의 짝이 한 칸씩 밀려 **엉뚱한
어트리뷰트끼리 조용히 이어진다.** `(Null)` 은 그 자리를 잡아 두는 표식이다.

```
Source      : ab      abc      abcd            Source      : ab      abc     abcd
Destination : ab      (Null)   abcd            Destination : ab      abcd
                 └ 연결        └ 연결                            └ 연결   └ 연결 (?!)
              (Null 짝은 건너뜀)                (자리를 비우면 abc → abcd 로 밀린다)
```

- **연결할 때** `(Null)` 이 낀 자리는 **양쪽에서 함께** 빠진다(`attr_match.strip_null_pairs`).
  한쪽만 빼면 뒤가 밀리기 때문이다. 두 방향 버튼(`Source -> Destination` /
  `Destination -> Source`) 모두 같다.
- `(Null)` 줄은 **회색**으로 그려지고 툴팁이 붙는다. 실제 어트리뷰트가 아니라는 신호다.
  마야 어트리뷰트 이름에는 괄호를 못 쓰므로 실제 이름과 충돌하지 않는다.
- 다시 매칭할 때 **지난 `(Null)` 줄은 후보에서 빠진다.**
- ON 은 짝이 안 된 destination 어트리뷰트를 목록에서 **뺀다**(사라지는 게 아니라 안 보이는 것).
  몇 개가 빠졌는지 로그로 알려 주고, `List Attributes` 를 다시 누르면 전부 돌아온다.

```
[OK] Match Same Name : 2/3 matched (unique)
       ab  ->  ab   (1.00)
       abcd  ->  abcd   (1.00)
[WARN] no attribute named 'abc' in the destination list.
[INFO] Match Same Name : 1 unmatched source attribute(s) hold a '(Null)' row each so the
       pairing keeps its order - those pairs are skipped when connecting.
[INFO] Match Same Name : 2 destination attribute(s) are not shown (Show Match Only) -
       press 'List Attributes' to get the full list back.
[INFO] 1 '(Null)' pair(s) had no counterpart and were skipped
       2 connection(s) [1 obj -> #objs, attr set matched]  Source -> Destination
```

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

### Attribute (v01.44 부터 하위 탭, v01.51 부터 **3개**)

| 하위 탭 | 하는 일 | 원본이 필요한가 |
|---------|---------|-----------------|
| **Edit** (v01.44) | 씬에 **이미 있는** 어트리뷰트를 골라 **순서를 바꾸거나 · 복사하거나 · 지운다** | 필요 |
| **Create** (v01.33) | **프로파일에 적어 둔 정의**로 새로 만든다 | 불필요 |
| **Set Value** (v01.51) | 여러 오브젝트가 **공통으로 가진** 어트리뷰트의 **값**을 한 번에 넣는다 (숫자 + Step, enum 은 이름) | 필요 |

> [!note] v01.44 에서 `Copy` 와 `Delete` 를 `Edit` 하나로 합쳤다
> 두 탭은 화면이 이미 같았다 — **오브젝트를 담고 → `List Attributes` 로 나열하고 → 고른 것에
> 무언가를 한다.** 다른 것은 마지막 버튼 하나뿐인데, 목록은 두 벌을 따로 채워야 했다.
> 같은 어트리뷰트를 복사하고 나서 원본을 지우려면 **똑같은 나열을 옆 탭에서 한 번 더** 했다.
>
> 이번에 들어온 **순서 바꾸기(Up / Down)** 도 성격이 똑같다("고른 것에 무언가를 한다").
> 새 탭 `Move` 를 하나 더 만들면 같은 목록을 **세 번** 채우게 되므로, 목록을 한 벌로 모으고
> 그 아래에 동작들을 붙였다.
>
> `Create` 는 합치지 않았다. 씬에서 아무것도 읽지 않고 **저장해 둔 프로파일**로 만드는,
> 입력의 출처가 다른 작업이다. 같은 화면에 두면 "지금 목록이 씬인가 프로파일인가" 가 흐려진다.

#### ★ 만든 어트리뷰트는 반드시 채널 박스에 보인다 (v01.52)

**`Edit > Copy` 와 `Create` 로 만든 어트리뷰트는 예외 없이 채널 박스에 올라온다.**
예전에는 `Keyable` 을 끄면 **아무 데도 안 보이는** 어트리뷰트가 만들어졌다.

마야에서 유저 어트리뷰트가 채널 박스에 나오는 길은 **둘뿐**이다.

| 상태 | 채널 박스 | 키 |
|------|-----------|-----|
| `keyable = on` | 보인다 | 걸 수 있다 |
| `keyable = off` + `channelBox = on` | 보인다 (non-keyable displayed) | 못 건다 |
| 둘 다 아님 | **안 보인다** — Attribute Editor 에만 있다 | 못 건다 |

`addAttr` 은 `keyable` 을 주지 않으면 **세 번째 상태**로 만든다. 그래서 툴이 만든 직후에
표시 상태를 정리한다(`app/core/attr_display.py`). 이제 `Keyable` 은 **보이냐 마냐가 아니라
키를 걸 수 있냐**를 정한다 — 꺼도 **보이되 키만 못 거는** 채널이 된다.

> [!warning] 레퍼런스로 들어온 어트리뷰트는 **고칠 수 없다** (Maya 2024 실측)
> ```
> setAttr: The attribute 'RIG:ctl.plain' is from a referenced file,
>          thus the channelBox state cannot be changed.
> ```
> `keyable` 도 같은 문구로 거부된다. **레퍼런스 쪽에서는 손쓸 방법이 없다** — 그래서
> 어트리뷰트를 **만드는 그 순간에** 보이게 해 두는 것이 유일한 해법이다.
> 한 번 제대로 만들어 두면 그 상태는 파일에 저장되어(`setAttr -k on` / `-cb on`),
> **`.ma` · `.mb` 어느 쪽으로 저장해도 레퍼런스로 불러왔을 때 그대로 보인다**(실측).
> 레퍼런스된 노드에 **새로 더한** 어트리뷰트는 레퍼런스 에디트로 남아 씬을 다시 열어도 유지된다.

**이미 숨은 채로 만들어진 것** 은 `Edit` 탭의 `Display` 줄에 있는 **`Show in Channel Box`**
로 되살린다 — 체크한 어트리뷰트를 `Objects` 의 모든 오브젝트에서 채널 박스로 올린다.
keyable 이던 것은 keyable 그대로 두고, 숨어 있던 것만 non-keyable displayed 로 바꾼다.
레퍼런스에서 온 것은 위의 이유로 못 고치므로 **그 사유를 로그에 적는다**(리그 씬에서 고쳐 저장할 것).

그 밖에 실측으로 확인한 것:

- `addAttr -h true` 로 숨겨 만든 것도 `setAttr -k/-cb` 로 **되살아난다**
  (`attributeQuery -hidden` 은 계속 `True` 라고 답한다 — 표시 여부와는 별개다).
- **컴파운드는 부모만 켜도 자식이 안 나온다** → 자식까지 함께 켠다.
- 잠긴(locked) 어트리뷰트도 표시 상태는 바뀐다. **잠금은 그대로 둔다.**
- `string` 은 `keyable` 을 켜도 채널 박스에 안 나온다 → **항상 `channelBox`** 로 켠다.
- `message` 는 채널 박스에 값이 없다 → 건드리지 않고 사유만 남긴다.

#### Edit (v01.44)

```
┌ Objects and their attributes ──────────────────────────────────────┐
│ Objects                      Attributes             Number: 5      │
│ [ ctrl_L_arm   ]             ☑ stretch                             │
│ [ ctrl_R_arm   ]             ☐ twist                               │
│ [Select][Add][Del]           ☑ follow                              │
│ [ List Attributes ]          ☐ vis_ctrl   (회색 = 빌트인)          │
│                              ☐ lockedAttr (주황 = LOCKED)          │
│                              ☑ User defined only                   │
│                              [Filter ....][Check All][Clear Checks]│
│                              ☐ Include attributes hidden by filter │
│                              Order  [ Up ][ Down ]                 │
│                              ☑ Maintain connections                │
│                              Display [ Show in Channel Box ]       │
└────────────────────────────────────────────────────────────────────┘
┌ Copy to other objects ─────────────────────────────────────────────┐
│ Targets (new attributes here)  [ctrl_L_hand]                       │
│ Prefix [ L_ ]   Suffix [ _ctrl ]                                   │
│ Preview : stretch  ->  L_stretch_ctrl   (+1 more)                  │
│ ☑ Copy current value                                               │
│ ☑ Show in Channel Box                                              │
│ [        Copy Checked Attributes to Targets        ]               │
└────────────────────────────────────────────────────────────────────┘
[            Delete Checked Attributes            ]
```

**목록 — 씬에 있는 순서 그대로**
- `List Attributes`: `Objects` 리스트의 **모든 오브젝트**를 훑어 **합집합**을 보여준다. 좌우 컨트롤러에
  같은 이름을 나란히 만들어 두는 일이 흔해, 하나씩 다루는 것보다 "이 이름을 가진 것 전부" 가
  실제 작업에 맞는다. 몇 개가 가졌는지는 **항목 툴팁**에 나온다.
- **이름순으로 정렬하지 않는다.** 보이는 순서가 곧 **채널 박스에 나오는 순서**이고, `Up`/`Down` 이
  바꾸는 것이 바로 그 순서다. 정렬해 버리면 화면과 씬이 어긋난다. 첫 오브젝트의 순서를 기준으로
  삼고, 뒤 오브젝트에만 있는 것은 뒤에 이어 붙인다.
- **`User defined only`**(기본 ON): 사용자 정의(커스텀) 어트리뷰트만 나열. 끄면 `translate` 같은
  기본 어트리뷰트까지 나온다 — **복사는 되지만 순서는 못 바꾼다**(아래). 그런 행은 **회색**이다.
- **잠긴 어트리뷰트는 주황색**이고 툴팁에 `LOCKED` 가 붙는다.
- 컴파운드 **자식**(`translateX`/`tintR`)은 목록에서 빠진다. 부모를 다루면 자식도 함께 따라오고,
  자식만 따로는 `addAttr` 로 만들 수도 `deleteAttr` 로 지울 수도 없다.
- **blendShape 노드를 담으면 타겟 이름들이 나열된다.** 타겟은 `weight[i]` 의 별칭이라
  `listAttr(userDefined=True)` 로는 `attributeAliasList` 밖에 안 나온다 → `aliasAttr` 에서 직접 읽는다.
  `User defined only` ON 이면 **타겟만**, OFF 면 타겟 + 노드의 모든 어트리뷰트.

**고르는 방법 — 선택이 아니라 체크박스**
- 예전 `Copy`/`Delete` 는 **하이라이트 선택**으로 골랐다. 이제는 **체크박스**다. 필터를 바꿔도
  체크는 남으므로 `arm` 으로 걸러 두 개, `leg` 로 걸러 세 개를 **여러 번에 걸쳐 모을 수 있다.**
- **여러 행을 한 번에 체크 (v01.49)** — `Shift` / `Ctrl` 클릭으로 여러 행을 고른 뒤, 고른 행 중 **하나의
  체크박스를 누르면 고른 행 전부**가 같은 상태가 된다(`Space` 도 같다). 고른 것은 그대로 남아 몇 번이고
  켜고 끌 수 있다. 고르지 않은 행의 체크박스는 그 행 하나만 바꾼다. 필터에 가려진 행은 고른 범위 안에
  있어도 **바꾸지 않는다**. 동작은 Framework 공용 [`MOD_checkList_qt`](Framework_MOD_checkList_qt.md).
- `Check All` 은 **지금 보이는 행만** 켠다. `Clear Checks` 는 **가려진 것까지 전부** 끈다
  (안 보이는 곳에 체크가 남아 있는 것이 사고의 씨앗이라 끄는 쪽은 넓게 잡는다).
- **`Include attributes hidden by the filter`**(기본 **OFF**): 체크는 됐지만 필터에 가려진 것을
  작업 대상에 넣을지 정한다.
  - OFF — "보이는 것이 작업 대상". 가려진 체크는 **빠진다.**
  - ON — 가려진 체크도 **포함한다.** `arm` · `leg` 를 번갈아 걸러 모아 둔 것을 한 번에 옮길 때 쓴다.
  - **어느 쪽이든 로그가 몇 개가 가려졌는지 말한다.** 뺐으면 "고른 게 빠졌다", 넣었으면
    "안 보이는 것까지 건드렸다" 를 모르고 지나가면 안 되기 때문이다.
    ```
    [INFO] 3 checked attribute(s) hidden by the filter were skipped - tick
           'Include attributes hidden by the filter' to use them
    ```

**Order — 채널 박스의 나열 순서를 바꾼다 (v01.44)**

체크한 어트리뷰트를 `Up` / `Down` 으로 한 칸씩 옮긴다. **화면만이 아니라 씬의 실제 순서**가
바뀌고, `Objects` 리스트의 **모든 오브젝트에 같이** 적용된다(좌우 컨트롤러를 한 번에).

- 여러 개를 함께 옮기면 **덩어리가 서로를 밀지 않는다** — 바로 앞(뒤)이 이미 체크된 것이면
  그 자리는 건너뛴다. 맨 위(아래)에 닿은 것은 더 움직이지 않는다. 레이어 목록과 같은 규칙이다.
- 옮긴 뒤 목록을 **씬에서 다시 읽고**, 체크는 그대로 살린다. 그래서 `Up` 을 연달아 눌러
  원하는 자리까지 밀어 올릴 수 있다.

> [!caution] **`Ctrl+Z` 로 되돌아가지 않는다**
> 마야에는 어트리뷰트를 재정렬하는 명령이 **없다.** `addAttr` 에도 `attributeQuery` 에도 순서
> 플래그가 없다. 유일한 방법은 **`deleteAttr` → `undo`** 로, 지웠다 되돌리면 그 어트리뷰트가
> **목록 맨 뒤로** 간다. 원하는 순서대로 전부 한 바퀴 돌리면 결과가 정확히 그 순서가 된다.
> (실측: 200개 전체 재정렬이 **0.004초**. 값 · 커넥션 · 키는 undo 가 되돌려 주므로 그대로 살아남는다.)
>
> 문제는 **delete 와 undo 가 짝이라 undo 큐에 아무것도 남지 않는다**는 것이다. 그래서
> 순서를 바꾼 뒤 `Ctrl+Z` 를 누르면 되돌아가는 것은 **그 전에 하던 작업**이다(실측 확인).
> 실행할 때마다 로그가 이렇게 알린다:
> ```
> [INFO] Reorder cannot be undone with Ctrl+Z (it uses deleteAttr + undo internally).
> ```
> 되돌리려면 **반대 방향으로 같은 횟수만큼** 누르면 된다.

- **빌트인은 못 옮긴다.** `translate` 같은 기본 어트리뷰트는 `deleteAttr` 대상이 아니다. 체크되어
  있으면 그 이름을 짚어 `[WARN] ctrlA : translate cannot be moved (not user defined)` 로 알리고
  **나머지만** 옮긴다(조용히 넘어가면 "왜 아무 일도 안 일어나지" 가 된다).
- **undo 가 꺼져 있으면 아예 시작하지 않는다.** 지우고 되돌릴 수 없으면 어트리뷰트를 **그대로
  잃기** 때문이다(`[ERR] Undo is disabled ...`).
- **`deleteAttr` 이 실패했을 때는 `undo` 를 부르지 않는다.** 실패한 자리에서 undo 를 부르면
  **남의 작업**이 되돌아간다(실측: 사용자가 만든 노드가 사라졌다). 잠긴 어트리뷰트는 잠금을
  잠시 풀고 옮긴 뒤 **다시 잠근다.**

**`Maintain connections` — 순서를 바꿔도 연결은 이름 그대로 (v01.46, 기본 ON)**

`Up` / `Down` 줄 아래 체크박스. 켜 두면 **어느 어트리뷰트가 어느 어트리뷰트에 물려 있는지**가
순서와 상관없이 그대로다. `obj_02` 의 `attr_02_a` / `attr_02_b` 자리를 바꿔도:

```
attr_01_b ─▶ attr_02_b        ← obj_02 의 새 순서 (b, a, c)
attr_01_a ─▶ attr_02_a
attr_01_c ─▶ attr_02_c        obj_01 의 순서는 그대로다
```

- **옮기기 전에** 그 오브젝트의 연결(들어오는 것 · 나가는 것 · 키 커브 · multi 원소)을 **플러그 이름으로
  적어 두고**, **옮긴 뒤** 다시 읽어 **어긋난 것만** 되돌린다. 어긋난 것이 없으면 씬을 **전혀 건드리지
  않는다**(재연결 0회). 로그:
  ```
         Maintain connections : all 6 connection(s) kept.
  [OK] Maintain connections : fixed 2 connection(s) (6 checked).      ← 되돌린 게 있을 때
  ```
  되돌린 연결은 한 줄씩(`obj_02 : reconnected obj_01.attr_01_a -> obj_02.attr_02_a`) 남는다.
- `unitConversion` 은 **건너뛴 실제 양 끝**으로 비교한다 — undo 가 변환 노드를 다른 이름으로 되살려도
  멀쩡한 연결을 끊지 않는다. 다시 이을 때 필요하면 마야가 변환 노드를 새로 만든다.
- 잠긴 받는 쪽은 잠깐 풀었다가 다시 잠근다. 소스가 사라져 되돌릴 수 없는 연결은 `[WARN]` 으로 짚는다.
- `Objects` 에 서로 연결된 오브젝트를 **함께** 넣어도 된다 — **전부 먼저 적고 → 전부 옮기고 → 전부
  확인**한다(한쪽을 옮긴 뒤 다른 쪽을 적으면 이미 어긋난 상태를 "원래" 로 삼게 된다).
- 끄면 연결을 확인하지 않는다(v01.45 까지의 동작).

> [!note] 이 증상은 사용자 씬에서 보고됐고 **mayapy · 마야 GUI(2024, 병렬 평가)에서는 재현되지 않았다**
> (이름 · API 연결 · 실제 값 흐름 모두 유지, 17가지 변형). 그래서 원인을 고치는 대신 **결과를 확인하고
> 어긋나면 되돌리는** 방식으로 만들었다. 검증은 옮긴 직후 연결을 일부러 엇갈리게 만들어 했다.

**Copy — 다른 오브젝트에 같은 정의로 만들기**

```
SRC.stretch  (double, min 0 / max 1, default 0.5, keyable, 현재값 0.75)
    ──▶  TGT.L_stretch_ctrl   (Prefix "L_", Suffix "_ctrl" → 정의·값 그대로 복제)
```

- **정의는 `Objects` 의 첫 오브젝트에서 읽는다.** 합집합 목록이라 첫 오브젝트에 없는 것이
  체크될 수 있는데, 그때는 읽을 곳이 없으므로 **그 이름만 빼고** 이유를 로그에 남긴다.
- **Targets**: 어트리뷰트를 **새로 만들** 오브젝트들(여러 개).
- **Prefix / Suffix**: 둘 다 비우면 **원본과 같은 이름**. `Preview` 가 체크한 첫 항목의 결과
  이름을 실시간으로 보여준다.
- **`Copy current value`**(기본 ON): 원본의 **현재 값**도 새 어트리뷰트에 넣는다.
- **`Show in Channel Box`**(기본 ON, v01.52): 원본이 **숨어 있던** 어트리뷰트라도 사본은
  채널 박스에 보이게 만든다(keyable 이던 것은 keyable 그대로). 끄면 예전처럼 **원본의 표시
  상태를 그대로** 따라간다. 켜 두는 편이 낫다 — 레퍼런스로 불러온 뒤에는 마야가 표시 변경을
  거부해서 숨은 채로 굳는다(위 [채널 박스](#-만든-어트리뷰트는-반드시-채널-박스에-보인다-v0152)).
- 보존되는 정의: **타입**(double/float/long/short/bool/enum/string/message/doubleAngle/doubleLinear/
  컴파운드 `double3`·`float3`/multi), **min·max·soft min·soft max**, **default**, **keyable**,
  **channel box 표시**, **hidden**, **enum 이름 목록**, **usedAsColor**.
- 같은 이름이 **이미 있는 타겟은 건너뛰고** `[WARN]` 을 남긴다(덮어쓰지 않는다).
- 이름을 바꾸지 않은 경우에만 원본 **short name** 을 유지한다. Prefix/Suffix 로 이름이 바뀌면
  short name 은 마야가 새로 만들게 둔다(그대로 쓰면 다른 어트리뷰트와 **충돌**).
- 컴파운드 자식 이름은 부모의 새 이름을 따라간다(`tint`→`L_tint_ctrl` 이면 자식은 `L_tint_ctrlR/G/B`).
- blendShape 타겟을 복사하면 컨트롤러에 **타겟 이름 그대로의 float 어트리뷰트**가 생긴다
  (blendShape weight 의 정의를 그대로 가져오므로 **soft range 0~1 / hard range -10~10**).
  이걸 `Connect` 탭에서 타겟에 이어 주면 페이셜 드라이버가 된다.
- 전체가 하나의 **undo chunk** 라 `Ctrl+Z` 한 번으로 되돌아간다.

**Delete — 담은 오브젝트들에서 지우기**

- 확인 창을 한 번 거친 뒤, `Objects` 의 **모든 오브젝트**에서 체크된 어트리뷰트를 지운다.
  그 어트리뷰트가 **없는 오브젝트는 조용히 넘어간다**(합집합 목록에서 고른 것이라 "원래 없음" 은
  알릴 일이 아니다). 지운 뒤 목록을 자동으로 다시 읽는다.
- **무엇을 지울 수 있나** — 마야에서 지울 수 있는 것은 **사용자 정의 어트리뷰트의 최상위 항목**
  뿐이다. 실측(Maya 2024):

  | 대상 | `deleteAttr` 결과 |
  |------|-------------------|
  | `translateX` 같은 기본 어트리뷰트 | ❌ `Cannot delete child 'translateX' of compound attribute 'translate'.` |
  | 컴파운드 **자식**(`vecX`) | ❌ 같은 에러 — 자식만 따로는 못 지운다 |
  | 컴파운드 **부모**(`vec`) | ✅ 지워지고 **자식도 함께** 사라진다 |
  | **잠긴** 어트리뷰트 | ❌ `'node.attr' is locked and may not be removed.` |
  | **연결/키가 걸린** 어트리뷰트 | ✅ 지워진다 |

- **잠금은 몰래 풀지 않는다** — 잠금은 "건드리지 말라" 는 의사표시다.
  `[WARN] node.attr : locked - unlock it first` 로 사유가 남으므로 풀고 다시 누르면 된다.
  (순서 바꾸기만은 예외다. 자리를 옮길 뿐 잠금 상태를 그대로 되돌려 놓기 때문이다.)
- 전체가 하나의 **undo chunk** 라 `Ctrl+Z` 한 번으로 되돌아간다.

#### Create (v01.33)
> v01.50: 어트리뷰트 목록도 Shift / Ctrl 로 여러 행을 골라 체크박스 한 번(또는 `Space`)으로 함께 켜고 끈다 (Framework 공용 동작 [`MOD_checkList_qt`](Framework_MOD_checkList_qt.md)).

**씬에 원본이 없어도** 어트리뷰트를 만든다. 정의를 **프로파일**에 적어 두고, 컨트롤러를
고른 뒤 `Create` 한 번이면 끝이다. 리그마다 늘 같은 어트리뷰트를 손으로 `addAttr` 하던
일을 없애는 것이 목적이다.

```
왼쪽 : Objects              오른쪽 : ┌ Profile ────────────────┐
       (새로 만들 대상)                │ [ UpperArm         ▼ ] │
       [Select][Add][Del]              │ [New] [Rename] [Delete]│
       [Sort]                          └────────────────────────┘
                                       ☑ World      float [0,1] default 0
                                       ☑ Root       float [0,1] default 0
                                       ☐ Shoulder   float [0,1] default 0
                                       [Filter ...]
                                       ☑ Check All (visible)   Checked: 2
                                       [Add] [Edit] [Remove]
                 [ Create Checked Attributes ]
```

> **폭에 대해**: 이 탭은 좌우로 나뉘어 있어 한쪽이 넓어지면 곧바로 오른쪽이 잘린다.
> 그래서 두 가지를 줄였다 — 왼쪽 TSL 에서 **`Up`/`Down`/`Order` 를 뺐고**(여기서는 순서가
> 아무 뜻도 없다. 체크한 어트리뷰트를 리스트의 **모든** 오브젝트에 똑같이 만든다),
> 프로파일 그룹의 버튼을 **콤보 아래 줄로** 내렸다.
> 실측 최소 폭 **675 → 441px** 로, 창 최소 폭(480)과 기본 폭(560) 안에 들어온다
> (예전 `Copy` 604 · `Delete` 503 보다도 좁다 — 둘은 v01.44 에서 `Edit` 으로 합쳐졌다).

**프로파일**
- 콤보에서 고른다. `New` / `Rename` / `Delete` 로 관리한다
  (구성은 [A00340_SelectionTool](A00340_SelectionTool.md) 의 프로파일 UI 와 같다).
- 프로파일 하나 = **JSON 파일 하나**. `<툴>/data/attr_profiles/<이름>.json` 에 저장되고
  마지막으로 쓰던 프로파일은 `attr_profiles_active.json` 에 기억된다.
  **git 에는 올라가지 않는다**(사용자 데이터).
- 프로파일이 하나도 없으면 `Default` 를 자동으로 만든다. **마지막 하나는 지울 수 없다.**

**어트리뷰트 정의**
- `Add` / `Edit`(행 더블클릭도 가능) 로 작은 편집 창이 뜬다.

  | 항목 | 내용 |
  |------|------|
  | `Name` | 어트리뷰트 롱네임. 영문자/밑줄로 시작, 영숫자/밑줄만 |
  | `Type` | `float`(double) · `int`(long) · `bool` · `enum` · `string` (v01.48) |
  | `Min` / `Max` | **체크박스로 켜고 끈다** — 끄면 "제한 없음" (float / int 만) |
  | `Items` | enum 항목. `left, mid, right` 처럼 `,` 또는 `:` 로 가른다 (enum 만) |
  | `Default` | 기본값 — bool 은 On/Off 체크박스, enum 은 **항목 이름 콤보**, string 은 글자 칸 |
  | `Keyable` | **켜면 키를 걸 수 있는 채널, 끄면 키만 못 거는 채널** — 어느 쪽이든 채널 박스에는 보인다 (v01.52). string 에서는 **`Channel Box`** 로 바뀌고 켜진 채 잠긴다 |

- **`Min`/`Max` 를 체크박스로 둔 이유**: 마야에서 "범위 없음" 과 "범위가 0" 은 다른데,
  스핀박스만 두면 그 둘을 구분해 넣을 방법이 없다.
- **enum / string (v01.48)**
  - enum 은 `Items` 를 적으면 `Default` 콤보가 그 항목으로 채워진다. 기본값은 **항목 번호**로 저장된다
    (마야 `defaultValue` 가 번호다). 항목이 하나도 없으면 저장하지 않는다.
    범위를 벗어난 번호를 주면 마야는 **조용히 0** 으로 만들기 때문에 저장할 때 항목 수 안으로 자른다.
  - string 은 `addAttr -dataType string` 으로 만들고 **기본값은 만든 뒤 `setAttr -type string`** 으로 넣는다
    — `addAttr` 이 문자열 `defaultValue` 를 못 받는다(실측: `Expected float, got str`). 비워 두면 값을 넣지 않는다.
  - string 은 키를 걸 수 없고 `addAttr -keyable` 을 켜도 채널 박스에 안 나온다(실측). 그래서
    **`setAttr -channelBox`** 로 올린다. v01.52 부터는 **늘 올리므로** 고를 것이 없어
    체크는 **`Channel Box` 로 켜진 채 잠긴다**(그 사실을 보여 주는 표시다).
  - 리스트 표시: `side   enum   [left | mid | right]   default mid`, `note   string   default "hello"`.
- `Remove` 는 **프로파일에서만** 지운다(씬의 어트리뷰트는 건드리지 않는다).
- `min > max` 로 적으면 **서로 바꿔** 저장한다(거꾸로 넣는 일이 흔하다).

**⚠️ 범위 밖 기본값은 마야가 조용히 버린다**
`addAttr` 에 범위 밖 `defaultValue` 를 주면 **에러가 아니라 경고만 내고 기본값을 무시한다**
(실측: `Specified default value '5' is out of the range ...; defaultValue ignored`).
그래서 이 툴은 저장할 때 **기본값을 범위 안으로 자른다**. 편집 창에서도 벗어나 있으면
`Default is outside the range - it will be clamped into it.` 라고 미리 알려 준다.
(같은 상황에서 `setAttr` 은 **에러를 던진다** — 두 명령의 반응이 다르다.)

**체크박스와 생성**
- 각 행 왼쪽 체크박스가 **만들 대상**을 정한다. 선택(하이라이트)은 `Edit`/`Remove` 대상이라
  서로 다른 뜻이다. UI 방식은 [A00290_BSTool](A00290_BSTool.md) 의 `Mix Targets` 탭을 따랐다.
- **`Check All (visible)`** — 지금 **보이는 행**만 켜고 끈다(필터를 걸면 그 안에서만).
  보이는 행이 전부 켜져 있으면 끄고, 아니면 전부 켠다.
- 프로파일을 새로 고르면 **전부 체크된 상태**로 시작한다. 프로파일은 사용자가 직접 골라 담은
  묶음이라 "이 프로파일을 만든다" 가 기본 의도이기 때문이다.
- 필터에 **가려진 체크는 그대로 만든다.** 체크는 명시적인 의사표시라 필터에 가렸다고 없던 일로
  하면 오히려 놀랍다 — 대신 몇 개가 가려져 있었는지 로그로 알린다.
  (`Edit` 탭은 반대로 **기본이 "보이는 것이 작업 대상"** 이고, 켜야 가려진 체크까지 포함한다
  — 거기서는 씬의 어트리뷰트를 **옮기고 지우기** 때문에 안 보이는 것을 건드리는 쪽이 더 위험하다.
  여기 `Create` 는 없던 것을 만들 뿐이라 되돌리기도 쉽다.)
- `Create Checked Attributes`: 왼쪽 리스트의 **모든 오브젝트**에 만든다.
  **이미 있으면 건너뛴다** — 타입이나 범위가 달라도 손대지 않는다. 기존 어트리뷰트를 고치면
  거기 걸린 연결·키가 깨지기 때문이다. 건너뛴 것은 `[WARN]` 으로 남는다.

#### Set Value (v01.51)

옛 **Number Tool**(`_archive/legacy_tools/01_Modules/JUN_PY_numberTool_V01_01.py`)의 이식이다.
원래 의도 그대로 — **여러 오브젝트를 담고 → 그 오브젝트들이 공통으로 가진 어트리뷰트를 나열하고
→ 고른 어트리뷰트를 한 번에 바꾼다.** 원본은 모든 값을 실수 칸 하나로 `setAttr` 해서 enum 도
정수로만 넣을 수 있었다. 여기서는 **고른 어트리뷰트의 종류에 따라 입력칸이 바뀐다.**

```
┌ Objects and the attributes they share ─────────────────────────────┐
│ Objects (order = step order)  Common Attributes      Number: 12    │
│ [ ctrl_01 ]                   visibility                           │
│ [ ctrl_02 ]                   translateX                           │
│ [ ctrl_03 ]                   mode        <- 선택                  │
│ [Select][Add][Del][Up][Down]  ☑ Channel Box Only                   │
│ [ List Common Attributes ]    [Filter ....]                        │
└────────────────────────────────────────────────────────────────────┘
┌ Value ─────────────────────────────────────────────────────────────┐
│ Attribute : mode   (enum)                                          │
│ Item [ Low  (5)        v]   Step [ 1 ]      <- enum / bool         │
│ Start [ 0.0 ]  Step [ 0.25 ]                <- float / int         │
│ Repeat every [ Off ] objects   ☑ Clamp to range          [ Get ]   │
│ Object          Current  New   Note                                │
│ ctrl_01.mode    Off      Low                                       │
│ ctrl_02.mode    Off      High                                      │
│ ctrl_03.mode    Off      Max                                       │
│ [                     Set Values                     ]             │
└────────────────────────────────────────────────────────────────────┘
```

**목록 — 공통으로 가진 것만**
- `List Common Attributes`: `Objects` 의 **모든 오브젝트가 가진** 어트리뷰트(교집합)만 보여 준다.
  `Edit` 탭은 합집합이지만, 여기서는 한 번에 모두에게 넣는 것이 목적이라 하나라도 없으면 뺀다.
  순서는 첫 오브젝트의 채널 순서.
- 값 하나로 넣을 수 있는 종류만 나온다 — **float · int · bool · enum**. 문자열 · 행렬 · compound
  부모(`translate` 등, 자식 `translateX` 는 나온다)는 빠진다.
- **`Channel Box Only`**(기본 ON): 채널박스에 보이는 것만(`Connect` 탭과 같은 판정 — keyable +
  channelBox, hidden 제외). 끄면 노드의 모든 숫자 / enum 어트리뷰트.
- blendShape 노드면 타겟 이름(별칭)이 맨 앞에 나온다.
- 여러 어트리뷰트를 `Shift` / `Ctrl` 로 골라 같은 값을 한 번에 넣을 수 있다. 입력칸은 **첫 번째로
  고른 어트리뷰트의 종류**를 따르고, 종류가 다른 것은 건너뛰고 알린다.

**값 — 종류마다 다른 입력칸**

| 종류 | 입력 | Step 의 뜻 |
|------|------|------------|
| float | `Start` 실수 (소수 4자리) | 오브젝트마다 더할 값 |
| int (long/short/byte) | `Start` 정수 (소수점 없음) | 오브젝트마다 더할 정수 |
| enum | `Item` 콤보 — **항목 이름**(값) 에서 고른다 | 몇 항목씩 건너뛸지. 끝에서 처음으로 돈다 |
| bool | `Item` 콤보 — `Off` / `On` | 1 이면 Off, On 번갈아 |

- **Step 은 `Objects` 리스트 순서대로** 쌓인다: i 번째 오브젝트 = `Start + i × Step`.
  그래서 이 탭의 오브젝트 리스트는 `Up` / `Down` 이 켜져 있다. Step 0 = 모두 같은 값.
- **`Repeat every N objects`**(기본 Off): N 개마다 시작값으로 돌아간다.
  `Start 0, Step 1, Repeat 3` → `0, 1, 2, 0, 1, 2 …`.
- **enum 은 이름으로 넣는다.** `Off:Low=5:High:Max` 처럼 값이 건너뛰는 enum 도 콤보에 `Low (5)` 로
  보이고, 고른 항목의 **이름**을 오브젝트마다 다시 찾아 그 오브젝트의 값으로 넣는다 — 오브젝트마다
  항목 값이 달라도 같은 이름이면 맞게 들어간다. 그 이름이 없는 오브젝트는 건너뛴다.
- **`Clamp to range`**(기본 ON, float / int): 어트리뷰트의 min / max 밖이면 잘라서 넣는다(미리보기
  Note 에 `clamped to range`). 끄면 마야가 거부해 그 오브젝트는 실패로 남는다 — 마야는 범위를
  **자르지 않고 에러를 낸다**.
- `Get`: 첫 오브젝트의 현재 값을 `Start`(enum 이면 `Item`)로 읽어 온다.

**미리보기와 적용**
- 입력을 바꿀 때마다 아래 표에 **오브젝트마다 현재 값 → 새 값**이 나온다. 건너뛸 것은 회색이고
  `Note` 에 이유가 있다 — `locked` · `driven by a connection` · `no enum item 'X'` · 종류 불일치.
- `Set Values`: 미리보기대로 넣는다. **undo 한 번**으로 되돌린다.
- **키가 걸린 어트리뷰트**(animCurve · 애니메이션 레이어)는 현재 프레임에 **키를 찍고** `setAttr`
  한다. `setAttr` 만 하면 다음 프레임에 커브 값으로 돌아가 버린다. 로그에 `n keyed` 로 센다.
- 키가 아닌 다른 노드가 구동하는 어트리뷰트는 건너뛴다(`setAttr` 이 실패한다).

> 원본 Number Tool 도 같은 기능으로 `JUN_PY_numberTool_V01_02.py`(maya.cmds 단일 파일)를 새로
> 두었다. V01_01 은 그대로 남아 있다. 현행은 이 탭이다.

#### List Connected
노드 그래프(up/down stream)를 타입별로 탐색한다.

- `Objects` 리스트에 오브젝트 추가.
- `List UpStream` / `List DownStream`: 연결된 노드의 **타입 목록**을 `Types` 에 표시.
- `Types` 에서 타입 선택 후 `Search`: 해당 타입의 **노드들**을 `Nodes` 에 표시.
- `Nodes` 목록에서 항목을 선택하면 씬에서도 선택된다.

#### Pair — Driver ↔ Driven 짝짓기 (v01.37 이름 매칭, 예전 이름 `Connect Closest`)
두 리스트를 **1:1 로 짝짓고** 그 짝을 constraint 로 연결한다. 짝을 세우는 방법이 둘이다 —
**거리**(`Get Closest`, A00140 이식)와 **이름**(`Match by Name`, v01.37).

```
Driven                       Driver
[ rig:jnt_L_arm  ]           [ ctrl_L_arm  ]   [ Get Closest ][ Match by Name ]
[ rig:jnt_L_hand ]           [ ctrl_L_hand ]
[ (Null)         ]           [ ctrl_R_foot ]   <- 짝을 못 찾은 자리
[ Add ][ Del ][ Up ][ Down ] [ Add ][ Del ][ Up ][ Down ]
[         Sort            ]  [         Sort            ]
[--------------------- Swap ---------------------------]  <- 두 리스트를 통째로 맞바꾼다

Match by Name : [ ] Same Name Only  [x] Unique  [x] Ignore Namespace   Min [0.40]
Pairing       : ( ) Closest distance   (o) List order
```

- `Driven` / `Driver` 리스트 구성.
- **`Swap`(v01.39)**: 두 리스트의 `Sort` **아래에 상자 전체 폭**으로 놓인 버튼. 두 리스트를
  통째로 맞바꾼다 — 지금 `Driven` 인 것이 `Driver` 가 되고 그 반대도 된다.
  리스트 하나에 딸린 버튼이 아니라 **둘 다에 걸리는** 동작이라 폭을 전체로 둔다. Match 탭의 `Swap` 과 같은 동작이고, 담을 때 방향을 거꾸로 골랐거나 **같은 짝을 반대로
  한 번 더 걸어 보고 싶을 때** 리스트를 다시 담지 않게 해 준다.
  - 짝은 **자리**로 서 있으므로 `(Null)` 을 포함한 **행 순서가 그대로 보존**된다 —
    `Match by Name` 으로 세운 짝을 `List order` 로 그대로 이어서 방향만 반대로 걸 수 있다.
  - `Pairing` 설정은 건드리지 않는다.
- constraint 종류 체크박스(`Parent` / `Point` / `Orient` / `Scale`, 다중) + `Maintain Offset`.
- `Connect`: 짝을 지어 constraint 를 건다. **무엇을 짝으로 볼지는 `Pairing` 이 정한다**(아래).
- **`Get Closest`(v01.08, Driver 리스트 버튼 행)**: 각 driver 에 가장 가까운 오브젝트를 찾아
  `Driven` 을 **driver 순서대로** 채운다. "어떤 오브젝트가 각 driver 와 가장 가까운지" 발견용.
  - **후보 풀**: `Driven` 에 항목이 있으면 그걸 풀로, 비어 있으면 **현재 씬 선택**을 풀로 사용.
  - driver 자신은 풀에서 자동 제외(거리 0 회피). 매칭은 **greedy 1:1**(쓰인 후보는 제거)로
    `Connect` 와 동일한 로직 → 채워진 `Driven` 은 곧 `Connect` 가 연결할 페어의 **미리보기**.
  - 찾은 오브젝트는 로그(`driver -> closest (dist)`)에 남고 **뷰포트에서도 선택**돼 눈으로 확인 가능.
##### Match by Name — 이름으로 짝 세우기 (v01.37)
`Get Closest` 의 **이름 버전**이다. 거리 대신 이름으로 짝을 찾아 `Driven` 을 **driver 순서대로**
세운다. 버튼은 `Get Closest` 옆(Driver 리스트 버튼 행)에 있고 **후보 풀 규칙도 같다** —
`Driven` 에 항목이 있으면 그걸, 비어 있으면 현재 씬 선택을 후보로 쓰고, driver 자신은 뺀다
(자기 이름과 가장 비슷한 것은 언제나 자기 자신이다).

점수 계산은 Connect 탭의 **어트리뷰트 매칭과 같은 엔진**이다(토큰 역색인 + IDF,
§Match from Source). 그래서 `ctrl_L_arm` ↔ `jnt_L_arm` 이 이어지고, 양쪽에 다 붙은 접두어는
IDF 가 알아서 0 으로 만든다.

| 옵션 | 기본 | 뜻 |
|------|------|-----|
| `Same Name Only` | OFF | 이름이 **완전히 같은 것만** 짝짓는다(대소문자 구분, `Min` 무시). |
| `Unique` | ON | Driven 하나가 두 번 쓰이지 않는다. |
| `Ignore Namespace` | ON | `rig:jnt_L_arm` 을 `jnt_L_arm` 으로 본다(한쪽이 레퍼런스일 때). |
| `Min` | 0.40 | driver 이름이 얼마나 설명되어야 짝으로 인정하는가(0~1). |

- **경로는 비교 전에 떼고, 연결은 전체 경로로 한다.** `|grp|rig:jnt_L_arm` 을 통째로
  토큰화하면 `grp` · `rig` 가 토큰으로 섞여, 한쪽 리스트에만 경로가 붙어 있으면 **같은
  오브젝트인데 문턱을 못 넘는다.** 그래서 비교는 말단 이름으로 하되, **돌려주는 것은 언제나
  원래 이름**이다 — 말단 이름만 돌려주면 동명 노드가 있는 씬에서 엉뚱한 노드를 잡는다.
- **짝을 못 찾은 자리는 `(Null)`** 이 지킨다. 연결은 `driver[i] ↔ driven[i]` 를 **순서로**
  짝짓기 때문에, 그냥 비우면 뒤가 통째로 한 칸 밀려 **엉뚱한 오브젝트끼리 조용히 연결된다.**
  Connect 는 그 자리를 **짝째** 건너뛴다.
- 로그는 점수와, 못 찾은 자리의 **최선 후보**를 함께 적는다(`Min` 만 낮추면 되는지 보려고).
  1등과 점수가 같은 후보가 또 있었으면 `[ambiguous]` 를 붙인다.
- 찾은 오브젝트는 **뷰포트에서도 선택**된다(`Get Closest` 와 같은 확인 방식).

##### Pairing — Connect 가 무엇을 짝으로 보는가 (v01.37)
예전에는 `Connect` 가 **언제나 거리로 다시 계산**했다. 그러면 `Match by Name` 으로 세운 짝이나
`Up`/`Down` 으로 맞춰 둔 순서가 **연결 순간 조용히 뒤집힌다.** 그래서 짝짓는 방법을 눈에
보이게 꺼냈다.

| 값 | 뜻 |
|-----|-----|
| `Closest distance` (기본) | 리스트 순서를 무시하고 각 driver 의 최근접 driven 을 다시 찾는다(기존 동작). |
| `List order` | 리스트에 보이는 자리 그대로 짝짓는다. `(Null)` 자리는 짝째 건너뛴다. |

`Match by Name` 을 누르면 **자동으로 `List order` 로 바뀐다** — 애써 세운 짝을 거리로 다시
짝지으면 뜻이 없기 때문이다. 로그 첫 줄이 어느 방법으로 연결했는지 밝힌다
(`--- Connect (list order) ---`).

> **`List order` 는 거르기 전에 짝을 만든다.** 씬에 없는 항목을 먼저 빼 버리면 그 자리가
> 사라져 뒤의 짝이 한 칸씩 밀린다. 없는 항목은 **그 줄만** 경고하고 넘어간다.

- **cluster handle 위치 처리(v01.15)**: 거리 계산에 쓰는 월드 좌표는 기본적으로 transform 의 월드
  translate 지만, **`clusterHandle` 은 translate 가 `(0,0,0)` 인 채로 실제 중심이 shape 의 `origin`**
  (아이콘이 그려지고 rotate pivot 이 놓이는 지점)에 있다. 그래서 클러스터는 `origin` 을 월드로 변환해
  쓴다(폴백: rotate pivot → translate). 이 처리가 없으면 클러스터 후보가 전부 월드 원점으로 잡혀
  `Get Closest` / `Connect` 가 거리와 무관하게 **리스트 순서대로** 짝지어진다.

---

### Mirror — 리그를 통째로 반대쪽으로 (v01.38)

리스트에 담은 오브젝트와 **그 아래 자식 전부**를 복제해 반대쪽 리그를 만든다.
이름은 좌/우 토큰으로 바꾸고, 계층 안에서 유지되어야 할 관계를 다시 세운다.

```
┌ Objects (TSL) ──────────────────────────────┐
│  grp_l_all                                  │
│  mesh_l_02                                  │
│  [Select][Add][Del][Up][Down] ...           │
└─────────────────────────────────────────────┘
┌ Mirror Plane ───────────────────────────────┐
│  (•) YZ    ( ) XY    ( ) XZ                 │
└─────────────────────────────────────────────┘
┌ Mirror Type ─────────────────────────────────────────┐
│  Joints          :  (•) Behavior ( ) Orient.         │
│  Curves / Others :  ( ) Behavior ( ) Orient. (•) Refl│
└──────────────────────────────────────────────────────┘
┌ Options ─────────────────────────────────────────────┐
│  [ ] Disable token check                             │
│  [v] Skin Weights [v] Constraints                    │
│  [v] Clusters     [v] Node Networks                  │
└──────────────────────────────────────────────────────┘
[             Mirror             ]
```

다시 세우는 관계는 셋이다.

| 관계 | 무엇을 하는가 |
|------|---------------|
| **스킨 웨이트** | 미러된 메시에 `skinCluster` 를 다시 만든다. 인플루언스는 **반대쪽 조인트**로 갈아끼우고 웨이트 값은 그대로. `maxInfluences` · `skinningMethod` · `normalizeWeights` 도 원본을 따른다 |
| **컨스트레인트** | 미러된 오브젝트를 구동하던 컨스트레인트를 **반대쪽 드라이버 → 반대쪽 드리븐**으로 다시 건다. 타깃 가중치 · skip 채널 · `interpType` 유지 |
| **클러스터** | 미러된 지오메트리를 물던 `cluster` 를 반대쪽 핸들 + 같은 웨이트로 다시 만든다 |
| **노드 네트워크** | 컨스트레인트가 아닌 **임의의 유틸리티 노드망**(`pointOnCurveInfo` → `fourByFourMatrix` → `multMatrix` → `decomposeMatrix` → …)을 복제하고 반대쪽으로 다시 잇는다 |

체크박스로 각각 끌 수 있다(기본 전부 ON).

#### ★ 스코프 — 리스트에 없으면 복사하지 않는다

미러 대상은 **리스트에 올라온 오브젝트와 그 자손뿐**이다. 스코프 밖 노드는 복제하지 않고
*그대로 참조*한다.

예를 들어

```
grp_l_all
├── jnt_l_01
│   └── jnt_l_01_parentConstraint
├── jnt_l_01_zro > jnt_l_01_con > jnt_l_01_ctl > jnt_l_01_tgt
└── mesh_l_01

mesh_l_02          ← 계층 밖. jnt_l_01 에 바인드되어 있다
```

- `grp_l_all` 과 `mesh_l_02` 를 **둘 다** 담으면 → `grp_r_all`, `mesh_r_02` 가 생긴다.
- `grp_l_all` **만** 담으면 → `mesh_l_02` 는 `jnt_l_01` 에 바인드되어 있어도
  **복사되지 않는다.** `mesh_r_01` 만 생기고, 원래 `mesh_l_02` 는 그대로 남는다.
- `jnt_l_01_tgt` 가 `jnt_l_01` 을 parentConstraint 로 구동하고 있었다면,
  미러 뒤에는 `jnt_r_01_tgt` 가 `jnt_r_01` 을 똑같이 구동한다.

**스코프 밖이 드라이버/인플루언스면 그 노드를 그대로 쓴다** — 센터 조인트가
좌우 메시를 함께 물고 있으면 미러된 스킨도 같은 센터 조인트를 인플루언스로 갖는다.
컨스트레인트도 마찬가지로, 센터 컨트롤이 드라이버면 미러 후에도 같은 센터 컨트롤이
드라이버다.

#### 이름 — 공용 토큰 규칙

이름은 [`Framework/rules/mirror_tokens.json`](Framework_mirror_tokens.md) 의 좌/우 토큰으로
바꾼다. **`A00110_animTool_V02` 의 Mirror Key 와 같은 파일**이라 한쪽에서 토큰을 추가하면
양쪽에 적용된다.

- **토큰이 없는 이름**(`grp_center_all` 처럼)은 **경고를 띄우고 미러하지 않는다.**
  하나라도 걸리면 아무것도 만들지 않고 멈춘다 — 반쪽만 만들어진 리그가 제일 고치기 어렵다.
  이때 **걸린 오브젝트 이름을 전부 로그에 찍고, 그 오브젝트들을 세트
  `mirror_noToken_set` 하나로 묶은 뒤 선택**한다. 이름만 찍어 두면 씬에서 다시 찾아야 하니,
  바로 고를 수 있게 해 둔 것이다.
  - 세트 이름은 **고정**이고, 다시 돌리면 **비워서 재사용**한다.
    같은 이름으로 세트를 또 만들면 `mirror_noToken_set1`, `...2` 로 쌓여서
    정작 어느 것이 방금 것인지 알 수 없어진다.
  - 씬에 남는 변화는 이 세트 하나뿐이다(미러는 아무것도 만들지 않았다).
    `Ctrl+Z` 한 번이면 세트도 사라진다.
- **`Disable token check`** 를 켜면 경고는 그대로 띄우되 진행한다. 토큰이 없는 노드는
  이름 뒤에 **`_mir`** 를 붙여 만든다(이 경우 세트는 만들지 않는다).
- 셰이프 이름도 따라간다. 다만 마야가 **트랜스폼을 리네임하면 `<transform>Shape*` 를
  알아서 따라 바꾸므로**, 이미 맞는 이름을 다시 미러해 되돌리지 않도록 마야가 손대지 않은
  셰이프만 바꾼다.

#### ★ Behavior 와 Orientation

조인트와 "커브 / 나머지"(컨트롤러 · 그룹 · 메시)를 따로 고른다.
**조인트 기본은 Behavior, 컨트롤러 기본은 Reflect** 다.
`Reflect` 는 컨트롤러 쪽에만 있다 — 조인트에 음수 스케일을 남길 일은 없다.

| | 무엇이 되는가 |
|---|---|
| **Behavior** | 로컬 축이 뒤집혀서 **같은 회전값이 좌우 대칭 동작**을 만든다. Maya `mirrorJoint` 의 Mirror function **Behavior** 와 행렬 단위로 같다 |
| **Orientation** | 로컬 축이 원본과 **같은 방향**을 계속 가리킨다(위치만 반사) |
| **Reflect** (컨트롤러 기본) | **진짜 거울상**. 그룹에 넣고 월드 `scaleX` 를 -1 한 것과 **같은 상태**다 |

수학은 간단하다. 평면의 **법선 축**(YZ → X, XZ → Y, XY → Z)만 알면,

- **Orientation** : 축 3개 그대로, 위치만 법선 성분을 뒤집는다.
- **Behavior** : 위치는 같고, **각 축에서 법선 성분만 남기고 나머지 둘을 뒤집는다.**
  (= 반사한 뒤 세 축을 모두 뒤집기. 세 축을 다 뒤집어야 행렬식이 양수로 돌아와
  오른손 좌표계가 유지된다.)
- **Reflect** : 그냥 `M·S`. 행렬식이 음수라 **한 축의 스케일이 -1** 로 남는다.

##### Reflect — 로컬 축이 거울상 방향을 가리킨다

컨트롤러의 로컬 X, Y, Z 가 각각 월드 **-X, +Y, -Z** 를 향한다고 하자. YZ 평면으로
Reflect 미러하면 미러본의 로컬 축은 **+X, +Y, -Z** 가 된다 — 그래서 미러한 컨트롤러를
**로컬 +X / +Y / +Z 로 옮기면 월드 +X / +Y / -Z 로** 간다(평면을 가로지르는 X 만 뒤집힌다).
mayapy 로 실측 확인한 값이다.

> [!tip] Reflect 로 계층 전체를 미러하면 **후손의 로컬 트랜스폼은 원본 그대로**다
> `local = (M_자식·S)·(M_부모·S)⁻¹ = M_자식·M_부모⁻¹` 이므로 뒤집힘은 **맨 위 노드 하나**만
> 갖는다. "복제해서 그룹에 넣고 scaleX -1, 그걸 루트에 프리즈" 와 정확히 같은 결과다.

메시는 Reflect 를 골라도 **Orientation 으로 놓고 지오메트리를 반사**한다. 메시에 Reflect 를
그대로 쓰면 월드 행렬이 왼손계가 되어 노멀이 뒤집힌 채 렌더되고 그 위에 스킨을 얹게 된다.
(부모가 Reflect 라면 그걸 상쇄하느라 메시의 **로컬** 스케일 한 축이 음수가 되지만,
정작 중요한 **월드**는 오른손계로 남는다.) 로그로 몇 개가 그렇게 놓였는지 알린다.

> [!warning] Behavior 는 **회전**을 미러하지, 이동을 미러하지 않는다
> 양쪽 컨트롤을 똑같이 `rotateZ +40` 하면 좌우 대칭으로 움직인다. 그런데 똑같이
> `translateY +2` 하면 **반대 방향으로** 간다 — 로컬 Y 축이 뒤집혀 있기 때문이다.
> 이동으로 구동하는 오브젝트(대표적으로 **클러스터 핸들**)가 있으면
> `Curves / Others` 를 **Orientation** 으로 두는 편이 낫다.
> mirrorJoint 의 Behavior 도 똑같은 성질을 갖는다.

조인트는 회전을 `rotate` 가 아니라 **`jointOrient`** 에 넣고 `rotate` 는 0 으로 둔다
(`xform -ws -m` 는 회전을 `rotate` 에 넣으므로, 그 뒤에 로컬 행렬을 다시 읽어 옮긴다).

#### ★ 노드 네트워크 — 컨스트레인트가 아닌 연결

리그의 연결이 늘 컨스트레인트인 것은 아니다. 예를 들어

```
crv_l_01 ─▶ pointOnCurveInfo ─▶ fourByFourMatrix ─┐
                                                   ├▶ multMatrix ─▶ decomposeMatrix ─▶ jnt_l_01.translate
                        jnt_l_01.parentInverseMatrix ─┘
```

처럼 **한 종류로 특정할 수 없는 유틸리티 노드**들을 거쳐 이어져 있다.
`Node Networks` 체크박스(기본 ON)를 켜면 이런 연결도 반대쪽에 그대로 선다.

- **찾는 법**: 스코프 안 오브젝트의 **구동 플러그**(t/r/s · `jointOrient` ·
  `offsetParentMatrix` · 사용자 정의 어트리뷰트 …)에서 **거슬러 올라가며** DG 노드를 모은다.
  **DAG 노드를 만나면 멈춘다** — DAG 노드는 미러 대상이면 리스트에 있어야 하고,
  아니면 스코프 밖 드라이버라 그대로 공유하면 된다.
  지오메트리 입력(`inMesh`, `create`)은 일부러 보지 않는다. 그쪽은 디포머/히스토리라
  따로 다루고, 거슬러 올라가면 씬 절반이 딸려온다.
- **다시 세우는 법**: 모은 노드를 복제하고 **모든 연결의 양쪽 끝을 갈아끼워** 다시 잇는다.
  | 끝 | 어떻게 |
  |---|---|
  | 네트워크 노드 | 그 복제본 |
  | 스코프 안 오브젝트 (셰이프 포함) | 미러본 |
  | 그 밖(센터 컨트롤 등) | **원본 그대로 공유** |
  - 다만 **나가는 연결의 도착지가 스코프 밖이면 잇지 않는다.** 이으면 그 노드를
    양쪽에서 구동해 버린다. 그런 연결은 로그에 남긴다.
  - 네트워크가 셰이프에 붙는 일이 흔해서(`crv.worldSpace[0] → pointOnCurveInfo.inputCurve`)
    트랜스폼뿐 아니라 **셰이프 짝도** 지도에 넣는다.

일부러 데려가지 않는 것들이 있다.

| 빼는 것 | 왜 |
|---|---|
| 컨스트레인트 · 디포머(skinCluster / cluster / blendShape) | 위에서 규칙대로 **따로** 다시 만든다 |
| `animCurve*` · `animBlendNode*` · `pairBlend` | 애니메이션은 미러 대상이 아니다(키 미러는 `A00110_animTool` 의 Mirror Key). 컨스트레인트 + 키가 만드는 블렌드는 컨스트레인트 재생성과 겹친다 |
| `expression` | 식 안에 **원본 이름이 문자열로 박혀 있어**, 복제하면 미러본이 원본을 또 구동한다 |
| 머티리얼 · 텍스처 · 폴리 히스토리 | 복제본에는 히스토리가 없다 |

> [!caution] 셰이딩은 **타입 상속이 아니라 분류**로 가른다 (v01.42 에 고쳤다)
> `multiplyDivide` · `vectorProduct` · `plusMinusAverage` 는 마야에서 **셰이딩 노드를
> 상속한다** — `nodeType(inherited=True)` 가 `['shadingDependNode', 'multiplyDivide']` 다.
> 그래서 `shadingDependNode` 로 셰이딩을 거르던 v01.41 까지는 **리깅에서 제일 흔한
> 유틸리티 노드들이 네트워크에서 통째로 빠졌다.** 미러된 쪽은 노드망이 반만 서고 나머지는
> 원본 노드를 계속 바라봐서, 겉보기엔 "미러가 안 된" 상태가 된다.
> 지금은 `getClassification` 의 **기능 분류**로 판정한다 — `multiplyDivide` 는
> `math/operation`, `file` 은 `texture/2d`, `lambert` 는 `shader/surface` 라 둘이 깔끔히
> 갈린다(앞의 `drawdb/shader/...` 는 하이퍼셰이드 그리기 분류라 **버린다**).

> [!warning] 박혀 있는 값은 그대로 복사된다 — 오프셋만 다시 푼다
> 연결로 들어오는 값은 미러 쪽에서 다시 계산되지만, 노드에 **박혀 있는** 값은 그대로
> 복사된다. 그중 **`offsetParentMatrix` 를 구동하는 `multMatrix` 의 오프셋**은 v01.42 부터
> 자동으로 다시 풀고(아래), 나머지 상수(스케일 · 각도 등)는 반사 평면을 가로지르는 성분이
> 있으면 손으로 고쳐야 한다. 실행할 때마다 로그로 알린다.

#### ★ maintain offset — 박힌 오프셋을 미러 쪽 기준으로 다시 푼다 (v01.42)

`A00170_driverTool` 의 **AttachCrv > Maintain offset** 처럼, 오브젝트를 **옮기지 않고** 커브에
붙이는 리그는 `offsetParentMatrix` 를 이렇게 구동한다.

```
multMatrix.matrixIn[0] = <상수>                # 빌드 시점의 오프셋 (OPM0 · frame0⁻¹)
multMatrix.matrixIn[1] ◀ fourByFourMatrix      # 커브 위의 라이브 프레임
multMatrix.matrixIn[2] ◀ parent.worldInverseMatrix
multMatrix.matrixSum   ▶ obj.offsetParentMatrix
```

`matrixIn[0]` 은 연결이 아니라 **값**이라 복제하면 그대로 따라오는데, 그 값은 **원본 쪽
프레임 `frame0` 기준**이다. 미러된 커브의 프레임 `frame'` 과 곱해지는 순간 오브젝트는
미러 위치가 아니라 원본 쪽으로 끌려간다 (YZ 미러 실측: `x = -4` 로 가야 할 조인트가
`x = -10.1` 로 갔다 — 커브는 미러됐는데 붙어 있던 조인트만 "미러가 안 된" 것처럼 보인다).

**오프셋의 미러는 "같은 상수" 가 아니라 "미러된 프레임 기준으로 같은 관계"다.** 그래서
네트워크를 다시 세운 뒤, 미러가 놓아 준 월드 행렬 `T` 로 돌아오도록 그 상수를 다시 푼다.

```
W = L · OPM · P                                  (마야: 로컬 · offsetParentMatrix · 부모 월드)
OPM_need    = OPM_now · P · W_now⁻¹ · T · P⁻¹
matrixIn[k] = (앞쪽 곱)⁻¹ · OPM_need · (뒤쪽 곱)⁻¹   (matrixSum = matrixIn[0]·[1]·…)
```

로컬 `L` 을 직접 읽지 않고 **현재 상태에서 역산**하므로 피벗 · `jointOrient` · `rotateAxis` 가
섞여 있어도 그대로 성립한다. 연결되지 않은 `matrixIn` 이 하나도 없으면 풀 자유도가 없으니
로그로 알리고 넘어간다.

> [!note] Maintain offset 을 **끄고** 붙인 조인트는 회전을 네트워크가 정한다
> 그쪽은 `decomposeMatrix` 가 `translate` / `rotate` 를 직접 구동하므로 미러가 놓은 자리를
> 네트워크가 덮어쓴다(위치는 미러된 커브 위라 대칭이다). 이때 미러가 회전을
> **`jointOrient` 로 옮겨 두면** 네트워크의 `rotate` 와 겹쳐 조인트가 엉뚱한 곳을 본다 —
> 그래서 `jointOrient` 는 **원본 값 그대로** 두고(= 커브 프레임에 대한 같은 로컬 오프셋),
> 그 사실을 로그에 남긴다.

> [!tip] 월드 값을 로컬 채널에 바로 꽂은 네트워크는 원래부터 계층에 취약하다
> `decomposeMatrix` 결과를 driven 의 `translate` 에 바로 꽂으면서 **driven 의
> `parentInverseMatrix` 를 거치지 않은** 네트워크는, 부모가 원점이 아니게 되는 순간
> 결과가 달라진다. 미러하면 부모(그룹)가 반드시 원점이 아니게 되므로 여기서 드러난다.
> 미러의 문제가 아니라 원본 리그의 성질이다 — `parentInverseMatrix` 를 물린 리그는
> 그대로 대칭이 된다(실측 확인).

#### ★ 메시는 트랜스폼만으로 뒤집히지 않는다

Behavior 도 Orientation 도 **강체 회전**이라, 메시는 회전만 하고 거울상이 되지 않는다
(왼쪽 신발이 오른쪽에서도 왼쪽 신발이다). 그래서 메시는 트랜스폼을 규칙대로 놓은 뒤
오브젝트 공간에서 보정 행렬 `C = (M·S)·M_new⁻¹` 로 정점을 한 번 더 반사하고 노멀을
뒤집는다. 결과의 월드 형상은 원본의 **정확한 거울상**이다.

정점 순서는 그대로라, 스킨 웨이트도 클러스터 웨이트도 인덱스 그대로 옮겨진다.

#### ★ 스킨된 메시의 복제본은 트랜스폼이 **잠긴 채로** 나온다

마야는 `skinCluster` 가 붙은 메시의 트랜스폼 t/r/s 를 잠근다. 그 메시를 복제하면
**히스토리를 지워도 잠금이 남는다.** 그런데 `cmds.xform` 은 잠긴 채널에 대해
**에러도 없이 조용히 아무것도 하지 않는다** — 메시만 제자리에 남고, 게다가 위의 지오메트리
보정이 그걸 가려서 월드 형상은 맞아 보인다(트랜스폼만 엉뚱한 자리에 있다).

그래서 놓기 직전에만 잠금을 풀고 되돌리며, **적용 뒤 월드 행렬을 되읽어 확인**한다.
확인에 실패하면 그 노드를 로그에 남긴다(잠김 또는 연결된 채널).

#### 로그 예

```
--- Mirror (YZ plane, joints behavior, others behavior) ---
       4 token pair(s) loaded.
       10 object(s) mirrored across the YZ plane.
       2 skinCluster(s) rebuilt.
       1 cluster(s) rebuilt.
       1 constraint(s) rebuilt.
       4 utility node(s) rebuilt.
[OK] Mirror
```

토큰이 없어 멈춘 경우 — 이름은 한 줄에 4개씩 묶어 찍는다(하나씩 한 줄이면 수백 줄이 쏟아지고,
한 줄에 다 넣으면 잘려 읽을 수 없다):

```
--- Mirror (YZ plane, joints behavior, others behavior) ---
[WARN] 5 object(s) have no mirror token:
[WARN]   spine_01, spine_02, chest_ctl, neck_ctl
[WARN]   head_ctl
[WARN] Collected in the set 'mirror_noToken_set'.
       members of 'mirror_noToken_set' are selected.
[ERR] Mirror : 5 object(s) have no mirror token - nothing was mirrored
      (see the set 'mirror_noToken_set'). Check 'Disable token check' to mirror them anyway.
```

만든 오브젝트는 실행 뒤 씬에서 선택된다. 전체가 **undo 한 번**으로 되돌아간다.

#### Apply — 이미 있는 반대쪽을 미러 위치 / 회전으로 (v01.40)

반대쪽 오브젝트가 **이미 있을 때**(따로 만든 리그, 한쪽 포즈만 고친 경우) 새로 복제하지 않고
**있는 오브젝트를 옮긴다.** 탭 맨 위 `Mode` 에서 `Apply (Source -> Target)` 를 고르면 리스트가 둘로
바뀌고, `Options` 박스 대신 `Apply` 박스가 나온다. Mirror Plane · Mirror Type 은 Create 와 **공유**한다.

```
┌ Mode ─────────────────────────────────────────────────┐
│  ( ) Create (Objects)   (•) Apply (Source -> Target)  │
└───────────────────────────────────────────────────────┘
┌ Source (TSL) ───────────┐ ┌ Target (TSL) ───────────┐
│  arm_l_ctl              │ │  arm_r_ctl              │
│  hand_l_ctl             │ │  hand_r_ctl             │
└─────────────────────────┘ └─────────────────────────┘
┌ Mirror Plane ─ (그대로) ┐   ┌ Mirror Type ─ (그대로) ┐
┌ Apply ────────────────────────────────────────────────┐
│  [v] Translation   [v] Rotation   [v] Keep Children in Place │
└───────────────────────────────────────────────────────┘
[                  Mirror to Target                   ]
```

> [!note] 리스트 이름이 `Left` / `Right` 가 아닌 이유 (v01.41)
> 원본은 읽기만 하는 **Source**, 옮겨지는 쪽은 **Target** 이다. 아래 스왑처럼 오른쪽 오브젝트가
> Source 에 들어가는 일이 정상 사용법이라, 좌우 이름은 틀린 설명이 됐다.

- **짝은 같은 줄끼리다** — `Target[i]` 가 `Source[i]` 의 미러 위치 / 회전을 받는다. Source 의 자식은
  미러되지 않으므로 옮길 오브젝트를 전부 담는다. 개수가 다르면 적은 쪽만큼만 하고 경고한다.
- **`Keep Children in Place`**(기본 ON, v01.41): Target 을 옮겨도 **그 아래 자식들(과 손자 전부)은
  옮기기 전 월드 위치 / 회전 / 스케일에 그대로** 남는다. 끄면 예전처럼 자식이 부모를 따라간다(로컬 값 그대로).
  v01.53 부터 구현은 **`app/core/keep_children.py` 공용**이고 `Match` 탭의 같은 이름 체크박스와 나눠 쓴다
  (Match 는 기본 OFF — 두 탭의 **기본값만** 다르고 동작은 같다).
  - 방법: 아무것도 옮기기 전에 각 Target 의 **직계 자식** 월드 행렬을 읽어 두고, 그 Target 을 놓은
    직후 되돌린다. 손자는 로컬이 그대로라 저절로 제자리다. 피벗 · `jointOrient` · `rotateAxis` 가 있어도
    월드 행렬로 되돌리므로 상관없다(조인트 자식은 `rotate` 가 바뀐다).
  - **자식이 그 자신도 Target 이면 붙잡지 않는다** — 제 차례에 자기 미러 위치로 간다. 그 아래 자식은
    다시 지켜진다. 컨스트레인트 노드(driven 밑에 붙는 노드)는 건너뛴다.
  - **잠겼거나 연결된 자식은 붙잡을 수 없어 부모를 따라간 채로 남고** 로그에 이유가 찍힌다
    (Target 과 같은 판정). 단 **컨스트레인트가 구동하는 자식은 보통 이미 제자리**라(월드를 드라이버가
    잡고 있다) 경고 없이 넘어간다.
  - Reflect 로 **부모의 좌우손계가 바뀌면** 자식이 월드에서 그대로 있으려면 자기 로컬 손계가 바뀌어야 해
    **한 축 스케일이 음수**가 된다 — 그래서 이때는 scale 채널도 검사하고, 그런 자식 수를 로그로 알린다.
- **결과는 "Create 모드가 그 자리에 만들었을 트랜스폼" 과 같다.** 같은 미러 행렬, 같은
  조인트 / 컨트롤러 줄, 메시는 Reflect 대신 Orientation(Create 와 동일). 포즈를 준 왼쪽 리그에
  Apply 한 결과는 그 리그를 **새로 Create 한 결과와 행렬 단위로 같다**(mayapy 확인).
- **이동 / 회전만 바꾼다.** 스케일 **크기**는 Target 오브젝트의 것을 유지한다.
  조인트는 `jointOrient` 를 그대로 두고 **`rotate`** 가 바뀐다(포즈를 고치는 것이지 리그를 다시
  짜는 게 아니다).
- `Reflect` 는 진짜 거울상이라, 반사된 적 없는 오브젝트에 회전을 적용하면 **한 축 스케일이 음수**가
  된다(Create 결과와 같은 상태). 그런 오브젝트 수를 로그로 알린다.

> [!tip] 좌우 포즈 스왑
> **Source 의 트랜스폼을 아무것도 옮기기 전에 전부 읽어 둔다.** 그래서 `Source = [arm_l, arm_r]`,
> `Target = [arm_r, arm_l]` 로 담으면 양쪽이 **한 번에 맞바뀐다.** 한쪽을 먼저 옮기고 나머지를
> 읽는 방식이면 두 번째가 이미 옮겨진 값을 미러해 버린다.

쓰는 순서는 **부모 -> 자식**이다(자식을 먼저 담아도 된다). 자식을 먼저 놓으면 부모를 놓을 때
자식이 밀린다.

> [!warning] 잠긴 / 연결된 채널이 있으면 그 오브젝트는 **통째로 건너뛴다**
> `cmds.xform` 은 잠긴 채널을 **에러 없이 건너뛰고 나머지만 바꾼다** — `rotateX` 가 잠겼으면
> 이동만 되고 회전은 그대로인 반쪽 결과가 조용히 남는다(실측). 그래서 쓰기 전에 바꿀 채널
> (`Translation` 이면 translate, `Rotation` 이면 rotate, 좌우손계가 바뀌면 scale)을 검사해,
> **잠겼거나 컨스트레인트 · 애님 레이어 등이 구동하면** 건너뛰고 이유를 로그에 남긴다.
> **키만 걸린 채널**은 옮긴다 — 다만 키를 찍지는 않으므로 프레임을 바꾸면 커브 값으로 돌아간다(로그로 알린다).

한 줄이 없는 이름이거나 컴포넌트여도 **그 줄만** 빠지고 뒤의 짝은 밀리지 않는다.
옮긴 오브젝트는 실행 뒤 선택되고, 전체가 undo 한 번이다.

```
--- Mirror Source -> Target (YZ plane, joints behavior, others reflect, translation on, rotation on, keep children on) ---
[WARN] 'hand_r_ctl' skipped - rotateX is locked.
[WARN] Child 'arm_r_fk_grp' could not be kept in place and followed its parent - translateX is locked.
       1 object(s) moved to the mirror of their Source partner across the YZ plane (translation + rotation).
       3 child object(s) kept their world position / rotation.
[OK] Mirror Source -> Target
```


---

## 3. 구조 (개발자용)

```
A00145_RigConnect/
├── launch.py                       # run(): MainWindow + coral_dark 테마
├── __dragDrop_A00145.py            # 셸프 설치 (RigConnect)
└── app/
    ├── config/version.py
    ├── core/                       # UI 비의존 maya.cmds 로직
    │   ├── match_manager.py        # Match (MEL Match Tool 포팅: 위치/회전 매칭·컨트롤 생성·버텍스 노말, 대량 매칭용 _Ctx 캐시, capture(), resolve_pairs())
    │   ├── keep_children.py        # Match · Mirror 공용 (부모를 옮겨도 직계 자식을 월드 자리에 붙잡아 둔다: 사전 읽기 -> 되돌리기, 잠긴/연결된 채널은 건너뛰고 보고)
    │   ├── snapshot_manager.py     # Match > Cache (노드 없이 월드 T/R/S 만 기억하는 추상 스냅샷, maya 비의존)
    │   ├── constrain_manager.py    # Constrain  (MEL 포팅)
    │   ├── skin_constraint_manager.py # Skin Weight to Constraint (스킨 웨이트 → weighted Parent/Scale/Point/Orient constraint)
    │   ├── group_create_manager.py # Group Create (부모/자식 쪽 오프셋 노드 _<suffix>_NN 삽입, 그룹·오브젝트 타입, UUID 기반)
    │   ├── constraint_transfer_manager.py # Constraint Transfer (constraint 를 다른 오브젝트로 이관: 삭제+동일세팅 재생성, MO 유지, UUID 기반)
    │   ├── constraint_update_manager.py # Update (AE 의 Update 버튼 = <type>Constraint -e -mo 를 리스트 전체에, 타깃은 연결에서 역추적)
    │   ├── constraint_target_manager.py # Target Edit (타깃(드라이버) 교체 = target[i] 입력 연결만 rewire / 추가·삭제 = constraint 명령의 add·remove, offset 재계산, UUID 기반)
    │   ├── attr_match.py           # Match from Source (이름 유사 어트리뷰트 검색: 토큰 역색인 + IDF, maya 비의존 순수 파이썬)
    │   ├── connect_manager.py      # Connect    (MEL 포팅: attr 나열/검색/연결, 52 facial)
    │   ├── attribute_manager.py    # Attribute > Edit   (정의를 읽어 다른 오브젝트에 재생성 prefix/suffix + 여러 오브젝트 합집합 나열 list_attributes_multi)
    │   ├── attr_order_manager.py   # Attribute > Edit   (Up/Down = 채널 박스 나열 순서 변경. 마야엔 재정렬 명령이 없어 deleteAttr+undo 로 맨 뒤로 보내는 방식)
    │   ├── attr_profile_prefs.py   # Attribute > Create (프로파일 JSON 저장 + 스펙 정규화, maya 비의존)
    │   ├── attr_create_manager.py  # Attribute > Create (프로파일 스펙 -> addAttr, 이미 있으면 건너뜀)
    │   ├── attr_delete_manager.py  # Attribute > Edit   (지울 수 있는 어트리뷰트 나열 + deleteAttr, 잠김 보고)
    │   ├── attr_display.py         # Attribute 공용     (만든 어트리뷰트를 채널 박스에 올린다. 레퍼런스는 못 고치므로 만들 때 해 둔다)
    │   ├── attr_value_manager.py   # Attribute > Set Value (공통 어트리뷰트 교집합 · Start/Step/Repeat 값 계산 · enum 은 이름으로 · 키 걸린 plug 는 키+setAttr)
    │   ├── blendshape_utils.py     # blendShape 타겟(weight 별칭) 조회 — Attribute / Connect 탭 공용
    │   ├── stream_manager.py       # List Connected (MEL 포팅: hyperShade up/down)
    │   ├── maya_scene.py           # Pair (A00140 복사)
    │   ├── closest_connector.py    # Pair (A00140 복사 + 짝짓기 모드: 거리 / 리스트 자리)
    │   └── object_match.py         # Pair > Match by Name (이름으로 오브젝트 짝짓기 — attr_match 엔진 재사용, 비교는 말단 이름·반환은 전체 경로)
    │   └── mirror_manager.py       # Mirror (계층 복제 -> 미러 행렬 -> 스킨/컨스트레인트/클러스터 재구성, 토큰은 Framework 공용 규칙, MissingTokenError 가 이름 목록 + 세트를 실어 나른다 · mirror_onto = Apply(Source -> Target), 있는 오브젝트에 미러 위치/회전만, keep_children 이면 자식 월드 보존 · 네트워크 재구성 뒤 multMatrix 에 박힌 maintain offset 을 다시 푼다)
    ├── data/                        # 사용자 데이터 (git 제외)
    │   ├── attr_profiles/<이름>.json   # Attribute > Create 프로파일
    │   └── attr_profiles_active.json   # 마지막으로 쓰던 프로파일
    └── ui/
        ├── collapsible.py          # CollapsibleBox
        ├── attr_spec_dialog.py     # Attribute > Create 의 어트리뷰트 정의 편집 창
        └── main_window.py          # QTabWidget 최상위 5탭(Constrain 6 / Connect 3 / Attribute 3 하위 탭) + 공유 로그 + Help>About
```

- 모든 textScrollList 는 `Framework.qt.JUN_mod_tsl_qt_v01` 위젯으로 대체.
  Match 탭의 두 리스트만 `list_limit=MATCH_LIST_LIMIT`(500) 으로 **요약 모드**를 켠다.
- 좌/우 토큰 규칙은 공용 [`Framework.core.mirror_tokens`](Framework_mirror_tokens.md)
  (`Framework/rules/mirror_tokens.json`) — `A00110_animTool_V02` 의 Mirror Key 와 **같은 파일**.
- `app/core`(로직) ↔ `app/ui`(화면) 분리. 위젯은 값만 읽어 매니저에 전달.
- UI 문자열은 영어, 한국어는 주석/독스트링만.

---

## 로그창 (v01.43)

로그창은 **공용 위젯 `JUN_mod_log_qt_v01`** 이다. 오른쪽 위에 작은 버튼 셋이 붙어 있다.

| 버튼 | 동작 |
|------|------|
| `Expand` | 로그를 **별도 창으로 옮겨** 크게 본다. 확장 중에 들어온 로그도 같은 곳에 쌓이고, 창을 닫으면 제자리로 돌아온다 |
| `Clear` | 로그를 비운다 |
| `Copy` | 로그 **전문**을 클립보드로 |

자세한 것은 [`Framework_MOD_log_qt.md`](Framework_MOD_log_qt.md).
