# A00145_RigConnect — RigConnect (사용 안내)

MEL `ConnectionTool V04.02`(탭: Constrain / Connect / List Connected) · `Match Tool V05.04` 와 기존
`A00140_ConnectClosest`(최근접 1:1 constraint)를 하나로 합친 툴이다.
**UI 는 PySide(Qt)**, 로직은 `maya.cmds`(일부 `maya.api.OpenMaya`) 로 작성되었다.

- 버전: `v01.35` (`app/config/version.py`) — Match 탭의 **Followers 에 컴포넌트(메시 버텍스·CV 등)를
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
- 형태: 아키텍처 (B) — Maya 내 PySide 툴. **최상위 4탭**(Match / Constrain / Connect / Attribute),
  Constrain·Connect·Attribute 는 다시 **중첩 탭**으로 나뉜다
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
| **Connect** | 어트리뷰트 **양방향** 연결(Source ↔ Destination) (+ Match from Source / Match Same Name, 52 facial) |
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

### Attribute (v01.33 부터 **하위 탭 3개**)

어트리뷰트를 다루는 세 가지 작업을 중첩 탭으로 나눴다. 셋 다 "어트리뷰트" 지만 **입력이
서로 달라**(원본 오브젝트 / 저장해 둔 정의 / 지울 대상) 한 화면에 쌓으면 읽기 어렵다.

| 하위 탭 | 하는 일 | 원본이 필요한가 |
|---------|---------|-----------------|
| **Copy** (v01.17~) | 씬에 있는 **소스 오브젝트의 어트리뷰트를 복제** | 필요 |
| **Create** (v01.33) | **프로파일에 적어 둔 정의**로 새로 만든다 | 불필요 |
| **Delete** (v01.33) | 사용자 정의 어트리뷰트를 **지운다** | — |

#### Copy (v01.17)
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

#### Create (v01.33)
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
> (`Copy` 604 · `Delete` 503 보다도 좁다).

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
  | `Type` | `float`(double) · `int`(long) · `bool` |
  | `Min` / `Max` | **체크박스로 켜고 끈다** — 끄면 "제한 없음" |
  | `Default` | 기본값 (bool 은 On/Off 체크박스) |
  | `Keyable` | 끄면 채널 박스에 안 보이게 만든다 |

- **`Min`/`Max` 를 체크박스로 둔 이유**: 마야에서 "범위 없음" 과 "범위가 0" 은 다른데,
  스핀박스만 두면 그 둘을 구분해 넣을 방법이 없다.
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
  (`Delete` 탭의 **선택**은 반대로 "보이는 것이 작업 대상" 규칙을 따른다. 체크는 남고 선택은
  스쳐 가는 상태라 규칙이 다르다.)
- `Create Checked Attributes`: 왼쪽 리스트의 **모든 오브젝트**에 만든다.
  **이미 있으면 건너뛴다** — 타입이나 범위가 달라도 손대지 않는다. 기존 어트리뷰트를 고치면
  거기 걸린 연결·키가 깨지기 때문이다. 건너뛴 것은 `[WARN]` 으로 남는다.

#### Delete (v01.33)
오브젝트들이 가진 **지울 수 있는** 어트리뷰트를 골라 지운다. 구성은 `Connect` 하위 탭과 같다
(왼쪽 오브젝트 리스트 + 오른쪽 어트리뷰트 목록 + 검색 + 다중 선택).

- `List Attributes`: 왼쪽 리스트의 **모든 오브젝트**를 훑어 **합집합**을 보여준다. 좌우 컨트롤러에
  같은 이름을 나란히 만들어 두는 일이 흔해, 하나씩 지우는 것보다 "이 이름을 가진 것 전부"를
  지우는 쪽이 실제 작업에 맞는다. 몇 개가 가졌는지는 **항목 툴팁**에 나온다.
- **무엇이 목록에 오르나** — 마야에서 지울 수 있는 것은 **사용자 정의 어트리뷰트의 최상위 항목**
  뿐이다. 실측(Maya 2024):

  | 대상 | `deleteAttr` 결과 |
  |------|-------------------|
  | `translateX` 같은 기본 어트리뷰트 | ❌ `Cannot delete child 'translateX' of compound attribute 'translate'.` |
  | 컴파운드 **자식**(`vecX`) | ❌ 같은 에러 — 자식만 따로는 못 지운다 |
  | 컴파운드 **부모**(`vec`) | ✅ 지워지고 **자식도 함께** 사라진다 |
  | **잠긴** 어트리뷰트 | ❌ `'node.attr' is locked and may not be removed.` |
  | **연결/키가 걸린** 어트리뷰트 | ✅ 지워진다 |

  그래서 목록에는 기본 어트리뷰트와 컴파운드 자식이 **아예 오르지 않는다**.
- **잠긴 어트리뷰트는 주황색**으로 표시되고 툴팁에 `LOCKED` 라고 나온다. 목록에는 올리되
  **이 툴이 몰래 잠금을 풀지는 않는다** — 잠금은 "건드리지 말라" 는 의사표시다. 눌러 보면
  `[WARN] node.attr : locked - unlock it first` 로 사유가 남으므로 풀고 다시 누르면 된다.
- `Filter` 로 걸러 `Select All` 로 보이는 것만 전체 선택할 수 있다. **가려진 선택은 제외**되고
  몇 개였는지 로그에 남는다("보이는 것이 작업 대상" 규칙).
- `Delete Selected Attributes`: 확인 창을 한 번 거친 뒤 지운다. 그 어트리뷰트가 **없는
  오브젝트는 조용히 넘어간다**(합집합 목록에서 고른 것이라 "원래 없음" 은 알릴 일이 아니다).
  지운 뒤 목록을 자동으로 다시 읽는다.
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
    │   ├── match_manager.py        # Match (MEL Match Tool 포팅: 위치/회전 매칭·컨트롤 생성·버텍스 노말, 대량 매칭용 _Ctx 캐시, capture(), resolve_pairs())
    │   ├── snapshot_manager.py     # Match > Cache (노드 없이 월드 T/R/S 만 기억하는 추상 스냅샷, maya 비의존)
    │   ├── constrain_manager.py    # Constrain  (MEL 포팅)
    │   ├── skin_constraint_manager.py # Skin Weight to Constraint (스킨 웨이트 → weighted Parent/Scale/Point/Orient constraint)
    │   ├── group_create_manager.py # Group Create (부모/자식 쪽 오프셋 노드 _<suffix>_NN 삽입, 그룹·오브젝트 타입, UUID 기반)
    │   ├── constraint_transfer_manager.py # Constraint Transfer (constraint 를 다른 오브젝트로 이관: 삭제+동일세팅 재생성, MO 유지, UUID 기반)
    │   ├── constraint_target_manager.py # Target Edit (타깃(드라이버) 교체 = target[i] 입력 연결만 rewire / 추가·삭제 = constraint 명령의 add·remove, offset 재계산, UUID 기반)
    │   ├── attr_match.py           # Match from Source (이름 유사 어트리뷰트 검색: 토큰 역색인 + IDF, maya 비의존 순수 파이썬)
    │   ├── connect_manager.py      # Connect    (MEL 포팅: attr 나열/검색/연결, 52 facial)
    │   ├── attribute_manager.py    # Attribute > Copy   (어트리뷰트 정의를 읽어 다른 오브젝트에 재생성, prefix/suffix)
    │   ├── attr_profile_prefs.py   # Attribute > Create (프로파일 JSON 저장 + 스펙 정규화, maya 비의존)
    │   ├── attr_create_manager.py  # Attribute > Create (프로파일 스펙 -> addAttr, 이미 있으면 건너뜀)
    │   ├── attr_delete_manager.py  # Attribute > Delete (지울 수 있는 어트리뷰트 나열 + deleteAttr, 잠김 보고)
    │   ├── blendshape_utils.py     # blendShape 타겟(weight 별칭) 조회 — Attribute / Connect 탭 공용
    │   ├── stream_manager.py       # List Connected (MEL 포팅: hyperShade up/down)
    │   ├── maya_scene.py           # Connect Closest (A00140 복사)
    │   └── closest_connector.py    # Connect Closest (A00140 복사)
    ├── data/                        # 사용자 데이터 (git 제외)
    │   ├── attr_profiles/<이름>.json   # Attribute > Create 프로파일
    │   └── attr_profiles_active.json   # 마지막으로 쓰던 프로파일
    └── ui/
        ├── collapsible.py          # CollapsibleBox
        ├── attr_spec_dialog.py     # Attribute > Create 의 어트리뷰트 정의 편집 창
        └── main_window.py          # QTabWidget 최상위 4탭(Constrain 5 / Connect 3 / Attribute 3 하위 탭) + 공유 로그 + Help>About
```

- 모든 textScrollList 는 `Framework.qt.JUN_mod_tsl_qt_v01` 위젯으로 대체.
  Match 탭의 두 리스트만 `list_limit=MATCH_LIST_LIMIT`(500) 으로 **요약 모드**를 켠다.
- `app/core`(로직) ↔ `app/ui`(화면) 분리. 위젯은 값만 읽어 매니저에 전달.
- UI 문자열은 영어, 한국어는 주석/독스트링만.
