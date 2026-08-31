# Changelog — A00060_jointTool_V03

`A00060_jointTool_V02` 를 복제해 갈라낸 **탭 재분류판**이다.
아래 `v01.xx` 항목은 갈라 나오기 전 V02 의 이력이다.

## v03.03 (2026-08-31)
**[Feature] `Chain > Pole Target` — 굽은 곳 바깥에 늘 붙어 있는 폴 벡터 타깃.**

세 오브젝트 `[끝, 가운데, 끝]` 에 대해

```
A  = (p1 + p3) / 2          v = p2 - A          A' = A + n*v
```

**A' 에 늘 붙어 있는 오브젝트**를 만든다. 체인을 움직이면 따라오고, `poleDistance`
어트리뷰트로 거리를 실시간으로 바꾼다. `Create IK` 가 폴 타깃을 **받기만** 했는데,
이제 그걸 **만드는 단계**가 바로 앞에 생겼다.

**★ 수식을 전개하니 `pointConstraint` 하나였다**

```
A' = (1-n)A + n*p2 = ((1-n)/2)*p1 + n*p2 + ((1-n)/2)*p3
```

**세 점의 가중 평균이고 가중치 합이 언제나 1**이다. 벡터 노드망을 짤 필요가 없다.
직접 짜 보면 `translate` 가 **로컬**이라 체인에서 깨지고, 월드로 하려면
`decomposeMatrix` 셋 + `multMatrix` 까지 노드가 8개쯤 든다. **컨스트레인트가 월드 공간과
타깃의 부모 공간을 공짜로 처리한다** — 노드는 **3개**로 끝난다.

**★ 가중치는 `setAttr` 이 아니라 연결로 넣는다** (실측)

`n > 1` 이면 양 끝 가중치가 음수인데 가중치 어트리뷰트는 `min = 0` 이다:

```
setAttr(w0, -0.25)  ->  RuntimeError: Cannot set ... below its minimum
연결로 -0.25        ->  통과. 결과가 수식과 정확히 일치
```

**모르면 `n>1` 에서 통째로 막힌다.** 어차피 연결해야 하므로 `n` 을 살아 있는
어트리뷰트로 두는 것은 공짜다.

**버튼** — `Check`(씬 불변) · `Create` · `Update Selected`(거리만) ·
`Bake Selected`(노드를 지우고 그 자리에 굳힌다).

**세 점이 일직선이면** `v = 0` 이라 n 이 얼마든 A 에 머문다 — T 포즈에서 흔하다.
**막지 않고 경고**한다(굽히면 살아난다).

로직은 `app/core/pole_target_manager.py` 에 있어 **UI 없이 import 해서** 쓸 수 있다 —
`A00130_ControlRig_V02` 가 그렇게 쓴다.

**검증**(mayapy headless, **54항목**): n 전 범위(음수 가중치 포함) · 체인을 움직이면
따라오는가 · **회전·이동한 부모 아래에서도** · **조인트가 아닌 로케이터 3개** ·
종류 3가지 · **노드가 정확히 3개** · 일직선 경고 · 이름 충돌 · `Update` 가 다시 만들지
않는가 · `Bake` 가 위치를 지키는가 · **undo 한 스텝** · 네임스페이스 ·
`solve_position` 이 씬 없이 도는가.

## v03.02 (2026-08-27)
**[Fix] 레퍼런스에서 온 ikHandle 은 `IK Edit` 이 폴 벡터를 갱신하지 않고 있었다.**

케이지 파일을 **레퍼런스로 불러와** 그 안의 조인트를 고치는 것이 `A00130_ControlRig_V02` 의
작업 방식이라, 그 경로가 실제로 되는지 확인하다 찾았다.

**증상** — 레퍼런스된 핸들에서 `EDIT IK CHAIN` 으로 조인트를 옮기고 확정하면
**조인트가 제자리에 남지 않는다.** 실측 편차 **위치 2.036 / 회전 45.77도**
(로컬 씬에서는 0.000000 이다). `Load Selection` 이 아무 경고도 내지 않아 **조용히 틀린다.**

**원인** — `ikHandle -q -solver` 는 솔버의 **노드 이름**을 준다. 그런데 파일을 레퍼런스하면
**솔버 노드까지 함께 레퍼런스되어** `CAGE:ikRPsolver` 로 온다(실측).

```python
cmds.ikHandle(h, q=True, solver=True)   # 'CAGE:ikRPsolver'
'CAGE:ikRPsolver' in ("ikRPsolver", "ikSpringSolver")   # False (!)
```

`_apply_pole_vector()` 가 맨 앞에서 `if solver not in RP_LIKE_SOLVERS: return True` 로
빠져나가면서 **폴 벡터 갱신이 통째로 건너뛰어졌다.** 핸들만 이펙터로 스냅되고 폴 벡터는
옛 평면을 계속 가리키니, 정확히 v01.05 개발 때 측정했던 **"핸들 스냅만 하면 편차 1.615"**
그 실패 모드로 되돌아간 것이다. `inspect()` 도 같은 비교를 쓰므로 `blockers` 가 비어 있었고,
**폴 벡터 컨스트레인트를 찾지도 못했다**(`pv_constraint: None`).

**수정** — `handle_solver()` 가 이름이 아니라 **노드 타입**(`cmds.nodeType`)을 돌려준다.
네임스페이스에도, **솔버 노드를 리네임한 씬**에도 흔들리지 않는다(둘 다 검증에 포함).
바꾼 곳은 이 함수 하나이고, 비교하는 쪽 3곳(`inspect` · `_apply_pole_vector` · `describe`)은
그대로 둔다.

**레퍼런스 워크플로에서 그 밖에 확인한 것** (전부 문제없음 — 실측)

| | 결과 |
|---|---|
| 레퍼런스 조인트/핸들/컨스트레인트에 `setAttr` | ✅ 된다. **reference edit 으로 저장되어 씬을 다시 열어도 남는다** |
| 레퍼런스 핸들에 `addAttr` / `deleteAttr` (편집 상태 저장) | ✅ 된다. 확정 후 지워지므로 **케이지 파일에는 흔적이 남지 않는다** |
| `preferredAngle` 쓰기 | ✅ 된다 |
| `rename` | ❌ `Cannot rename a read only node` — 다만 **이 모듈은 rename 을 쓰지 않는다** |
| `ikBlend` 가 FK/IK 스위치에 물린 케이지 | 예상대로 **씬 전역 폴백**(`ikSystem -solve 0`)을 탄다 |

**검증**(mayapy headless, **39항목 신규** + 기존 79 · 130항목 회귀 통과):
솔버 이름이 네임스페이스로 오는 것 · 솔버 노드 리네임 · 레퍼런스 씬에서 `inspect` 가 폴 벡터를
찾는가 · **편집 후 조인트가 제자리에 남고 편차가 0 인가** · 로컬 씬 회귀 · 레퍼런스 노드의
`addAttr`/`deleteAttr` · 편집 상태를 껐다 켜도 되찾는가 · **저장 후 다시 열어도 남는가** ·
**케이지 원본 파일이 안 더럽혀지는가** · SC 솔버 분류.

## v03.01 (2026-08-26)
**[Feature] `Chain > Create IK` 하위 탭 신규 — 시작/끝 조인트 쌍마다 ikHandle 생성.**

폴 벡터 타깃이 주어진 체인에만 폴 벡터 컨스트레인트를 건다. **타깃이 없으면 IK 핸들만
만들고 컨스트레인트는 만들지 않는다.**

MEL `JointTool V05.03` 의 `JUN_cmd_make_jntAim` 이 원래 하던 일이다. V02 로 포팅하면서
`Aim` 탭이 **IK 를 쓰지 않고 jointOrient 만 고치는** 방식으로 다시 설계됐고, 그 과정에서
ikHandle 을 만드는 경로가 사라져 있었다. UI 레이아웃은 원본 Aim 탭(Start / End / pole tgt
3분할)을 그대로 따랐다.

**MEL 원본에서 고친 것**

| # | 원본 | V03 |
|---|---|---|
| 1 | 폴 리스트가 짧으면 빈 문자열을 넘겨 **에러** | 폴이 없으면 **컨스트레인트를 안 만든다** |
| 2 | 개수가 안 맞으면 `min()` 으로 조용히 자름 | 몇 쌍만 쓰는지 로그로 알린다 |
| 3 | 솔버 고정 | `ikRPsolver` / `ikSCsolver` / `ikSpringSolver` 선택 |
| 4 | 이름 `ikHandle1` / `effector1` | 시작 조인트에서 이름 생성(이펙터는 옵션) |
| 5 | 검증 없음 | 조인트인가 · 끝이 시작의 자손인가 · 이미 핸들이 있는가 |
| 6 | 한 쌍이 실패하면 멈춤 | 그 쌍만 건너뛰고 계속 |
| 7 | undo 가 흩어짐 | 전체가 undo 한 스텝 |

**더한 것**: `Add with Pole` — 정확히 3개(시작 · 끝 · 폴)를 골라 세 리스트에 한 줄씩
동시에 넣는다. 세 리스트를 따로 채우다 순서가 어긋나면 엉뚱한 체인에 폴이 걸린다.

**Maya 2024 실측으로 알게 된 것**

- **`ikSCsolver` 핸들에도 `poleVector` 어트리뷰트가 있다**(`attributeQuery` → `True`).
  그런데 컨스트레인트를 걸면 `Handle must be valid and use rotate plane solver` 다.
  → **어트리뷰트가 아니라 솔버 이름으로 갈라야 한다.**
- **`ikSpringSolver` 는 플러그인 로드만으로는 안 된다** — 솔버 *노드*가 없어
  `The ikSolver does not exist.` 로 죽는다. MEL 프로시저 `ikSpringSolver;` 로 노드를 만든다.
- **같은 체인에 두 번째 핸들을 마야는 조용히 만들어 준다** → 툴이 경고한다(막지는 않는다).
- 일직선 체인에 폴 벡터를 걸어도 **에러는 안 난다**(평면만 임의가 된다) → 경고만.
- `ikHandle -e -sticky "off"` 는 경고를 낸다 → 켤 때만 건드린다.

**그 밖에**

- `IKE_SUB_INDEX` 를 **`CHAIN_PAGES` 에서 찾도록** 바꿨다. `Create IK` 가 `IK Edit` 앞에
  들어가면서 실제로 1 → 2 로 밀렸고, v03.00 처럼 숫자를 박아 뒀다면 **에러 없이**
  IK Edit 의 씬 재조회가 죽었을 자리다.
- 창 높이 720 → **760** (`Create IK` 페이지가 511px 로 가장 길다).

**검증** (mayapy headless, **79항목 전부 통과** + v03.00 회귀 130항목 통과)

- 폴 있음/없음, 빈 문자열 폴, 개수 불일치, 남는 폴 타깃, 빈 입력
- 솔버 3종 각각의 생성 결과와 폴 벡터 처리
- 잘못된 입력(자손 아님 · 조인트 아님 · start==end)이 **그 쌍만** 건너뛰는지
- 이미 핸들이 있는 체인 경고, 일직선 체인 경고
- suffix · 이펙터 리네임 · sticky · 이름 충돌
- **undo 한 번에 전부 사라지는지**
- UI 경로: 버튼 클릭 → 핸들 2개 · 폴 벡터 컨스트레인트 1개, 새 핸들 선택,
  `Add with Pole` 이 3개가 아니면 거부, **다른 탭 리스트를 건드리지 않는지**

---

## v03.00 (2026-08-25)
**[Refactor] 탭 재분류 — 상위 탭 = 카테고리 / 하위 탭 = 기능 의 2단 구조로.**

기능은 **하나도 빼거나 더하지 않았다.** 평평하던 상위 탭 5개(그 안에 접이식 6섹션)를
카테고리 5 → 기능 11 로 다시 나눠 담았다.
계획서: `JUN_All/docs/plans/A00060_jointTool_V02_tab_reorg_plan.md`

**`Hair` 라는 상위 탭 이름이 사라진다.** 헤어 리깅에 쓰던 기능은
`Curve > Edit Curve`(Separate / Remove / Rebuild)와 `Chain > Reverse` 에 있다.

**왜 갈랐나** — V02 의 `Curve` 탭은 이름과 내용이 맞지 않았다. 안에 들어 있던 네 섹션 중
커브를 쓰는 것은 둘뿐이고, `Clusters` 는 조인트를 만들지도 않으며, 나머지 둘(orient/rotate 교환,
Set Orient)은 커브와 아무 상관이 없었다. `Hair` 탭도 커브 편집 · 체인 편집 · 선택이 섞여 있었다.
가장 분명한 증거는 **리스트 하나(`Selections`)를 다섯 기능이 나눠 쓰면서 커브 · 오브젝트 ·
조인트가 번갈아 담기던 것**이다.

**이동 매핑 (기존 15기능 — 전부 자리 있음)**

| V02 위치 | V03 위치 |
|---|---|
| Curve > joint to Crv > `Joints to Crv` | **Create > From Curve** |
| Curve > joint to Crv > `Clusters` | **Curve > Clusters** |
| Curve > joint to obj > `Match to Obj` / `Match to Sel` | **Create > From Object** |
| Curve > joint orient and rotate (2버튼) | **Orient > Orient / Rotate** |
| Curve > Set Orient | **Orient > Set Orient** (접힘 해제) |
| Divide | **Create > Divide** |
| Aim | **Orient > Aim** |
| Hair > Sub Tool : Curve (Separate / Remove / Rebuild) | **Curve > Edit Curve** |
| Hair > Tool : Edit > `Reverse joint chain` | **Chain > Reverse** |
| Hair > Tool : Edit > `Select Unused Joints` | **Select > Unused Joints** |
| IK Edit | **Chain > IK Edit** |

**새 카테고리** — 기준은 "무엇이 바뀌는가"(입력이 아니라 결과물).

| 상위 탭 | 뜻 | 하위 탭 |
|---|---|---|
| `Create` | 씬에 조인트가 생긴다 | From Curve · From Object · Divide |
| `Orient` | 있는 조인트의 방향만 바뀐다 | Aim · Set Orient · Orient / Rotate |
| `Chain` | 있는 체인의 구조·연결을 고친다 | Reverse · IK Edit |
| `Curve` | 커브·디포머를 다룬다(조인트 준비) | Edit Curve · Clusters |
| `Select` | 씬을 바꾸지 않는다 | Unused Joints |

**함께 바뀐 것**

- **공용 리스트를 쪼갰다.** `tsl_curve`(5기능 공용) · `tsl_hair`(5기능 공용)가 사라지고
  하위 탭마다 자기 리스트를 갖는다. 제목이 곧 담아야 할 타입이다 —
  `Curves` / `Objects` / `Joints` / `Root Joints`.
- **접이식(`CollapsibleBox`) 제거.** 전부 하위 탭이 되어 `app/ui/collapsible.py` 를 삭제했다.
  다시 필요하면 공용 `Framework.qt.JUN_mod_collapsible_qt` 를 쓴다.
- **`Chain > IK Edit` 이 탭을 열 때마다 씬을 다시 읽는다.** 편집 상태는 UI 가 아니라 ikHandle
  노드에 있는데, V02 는 창을 만들 때 한 번만 읽어서 다른 창에서 편집을 시작/종료하면 버튼 색과
  씬이 어긋났다. 상위/하위 두 `currentChanged` 를 같은 슬롯에 물리되 **상위 탭 인덱스로 비교하지
  않는다**(중첩하면 인덱스의 뜻이 조용히 변한다) — 상위는 위젯 동일성, 하위는 `IKE_SUB_INDEX`.
- **버전 번호를 폴더명에 맞췄다.** V02 는 폴더가 `_V02` 인데 버전이 `01.05` 로 남아 있던
  저장소 유일한 예외였다. V03 은 `03.00` 부터 센다
  (`A00010_humanIKTool_V02`=02.01, `A00110_animTool_V02`=02.12 와 같은 규칙).
- 창 크기 `540 × 820` → **`560 × 720`**. 상위 탭이 5개라 폭이 조금 더 필요하고, 접이식이
  하위 탭으로 갈라지면서 페이지가 짧아졌다(실측: 상위 탭 바 291px, 가장 넓은 하위 탭 바
  `Create` 241px, 가장 긴 페이지 `Create` 423px).
- 셸프 라벨 `JointTool2` → **`JointTool3`**, 드롭 파일 `__dragDrop_A00060_V03.py`,
  `WINDOW_OBJECT_NAME` 도 갈라 **V02 와 동시에 띄워도 서로를 닫지 않는다.**

**`app/core/*` 는 한 줄도 고치지 않았다.** 바뀐 것은 `app/ui/main_window.py` 뿐이다.

**검증** (mayapy headless, 128항목 전부 통과)

- **스냅샷 diff** — V02 와 V03 의 `MainWindow` 를 같은 프로세스에서 띄워 위젯 속성 이름 집합을
  비교. 사라진 것은 `tsl_curve` · `tsl_hair` **둘뿐**(= 어떤 핸들러도 참조를 잃지 않았다).
- 탭 트리(상위 5 / 하위 11)와 라벨 · 툴팁 · 스크롤 래핑 전수 확인.
- **씬 동작 회귀** — 15기능을 실제 씬에서 각각 실행해 `[OK]` 로그 확인.
- **조용히 틀릴 수 있는 두 지점**(계획서 8장) — `Match to Sel` 이 `From Object` 탭 리스트의
  `Order` 를 읽는지, `Unused Joints` 가 자기 탭 리스트를 하이라이트하는지.
- **IK 세션 인수** — 코어로 편집을 켠 씬에서 툴을 새로 열면 상태를 되찾는지, 다른 카테고리로
  갔다가 `Chain > IK Edit` 으로 돌아오면 다시 읽는지.

---

## v01.05 (2026-08-25)
**[Feature] `IK Edit` 탭 신규 — 설치된 ikHandle 을 그대로 둔 채 본 체인을 고친다.**

IK 도 폴 벡터 컨스트레인트도 지우지 않고 체인만 수정한 뒤, 리그를 편집 결과에 맞춘다.
`A00275_skinTool_V01` 의 `Edit Mesh` 와 같은 **토글 버튼**(`EDIT IK CHAIN` → 다시 눌러 확정).

**마야에는 이 기능이 없다.** 마야 2024 컨스트레인트의 `Update Offset` 버튼은
`parentConstraint -e -maintainOffset` 이지만(`AEparentConstraintTemplate.mel`),
`AEikHandleTemplate.mel` 에는 대응 버튼이 없고 `ikHandle` 명령에도 플래그가 없다.

**왜 그냥은 안 되는가 (Maya 2024 실측)**

| | 결과 |
|---|---|
| IK 가 켜진 채 중간 조인트를 `(2, 5, 1)` 로 이동 | 솔버가 **`(0.00068, 5.2, 1.72)` 로 되돌린다** |
| IK 를 끄고 고친 뒤 **핸들만** 이펙터로 스냅 | 최대 편차 **1.615** — 체인이 옛 평면으로 비틀린다 |
| 핸들 스냅 **+ 폴 벡터 재계산** | 최대 편차 **0.00000000** (위치·회전 모두) |

**어떻게 고치는가**

편집된 체인에서 원하는 폴 벡터를 역산한다. `poleVectorConstraint` 의 식은 실측으로
`pv = (target_world − ikRoot_world) × handle.parentInverseMatrix(3x3) + offset` 이고,
`offset` 이 출력(핸들 부모) 공간에서 그대로 더해지므로 역산이 선형이다.

```
new_offset = desired_pv − (current_pv − current_offset)
```

**컨스트레인트도 타깃도 건드리지 않고 offset 만** 갱신한다 — 마야의 `Update Offset` 과 같은 발상.
`desired_pv` 는 루트→중간 벡터에서 체인 축 성분을 뺀 **수직 성분**(축과 평행해질 수 없어 안정적).

`twist` 가 0 이 아니면 솔버가 평면 위에 그 각을 더 얹으므로(보정 없이 편차 1.06) 원하는 벡터를
축 기준 **−twist** 만큼 미리 돌려 상쇄한다. **twist 값 자체는 애니메이션 채널이라 안 건드린다.**
(`ikRPsolver` 는 `roll` 을 쓰지 않는다 — 실측.)

**UI**

| | |
|---|---|
| `Load Selection` | 핸들 자체 / 체인 안의 아무 조인트 / 핸들을 구동하는 컨트롤러 — 무엇을 골라도 된다 |
| `EDIT IK CHAIN` | 토글. ON 이면 IK 가 내려가 체인이 자유롭다. 다시 누르면 확정 |
| `Cancel Edit` | 조인트 · 핸들 · 폴 벡터 오프셋 · 타깃 위치 · `ikBlend` 를 시작 시점으로 |
| `Update Now` | 편집 세션 없이 지금 상태로 한 번 맞춘다 (마야 `Update` 버튼에 가장 가까운 것) |
| `Pole vector` | **Constraint offset**(기본) / Move the pole vector target |
| `Snap` | **IK handle**(기본) / Handle's parent |
| `Set preferred angles` | 기본 ON |

확정할 때마다 **편집한 포즈와 얼마나 다른지 실측치**를 로그에 남긴다.

**상태는 씬에 있다** — 편집 중이라는 사실과 되돌릴 스냅샷은 UI 가 아니라 ikHandle 의
어트리뷰트(`JUN_ikEdit` / `JUN_ikEditData`)에 있다. 툴을 껐다 켜도, 씬을 저장했다 열어도
이어서 확정·취소할 수 있고, 툴을 열면 진행 중인 편집을 알아서 되찾는다.

**막히는 경우를 조용히 넘기지 않는다**

- `ikBlend` 가 FK/IK 스위치에 연결돼 있으면 `setAttr` 이 거부된다(실측 `RuntimeError`).
  그럴 때만 마야의 `Enable IK Solvers` 토글(`ikSystem -e -solve 0`)로 물러서고, **씬 전체의 IK 가
  꺼진다는 사실을 로그로 알린다.** 그 플래그는 세션 상태라 마야를 다시 켜면 살아나는데,
  툴을 열 때 진행 중인 편집을 찾으면 다시 꺼 준다.
- 핸들이 `pointConstraint` 로 구동되면 그 컨스트레인트의 `offset` 을 갱신한다.
- `ikSplineSolver` 는 커브가 체인을 구동하므로 **거부하고 이유를 알린다**(조용히 망가뜨리지 않는다).
- 체인이 일직선이면 팔꿈치 방향을 읽을 수 없으므로 폴 벡터를 손대지 않고 경고한다.
- `ikSCsolver` 는 폴 벡터가 없어 핸들 스냅만으로 편차 0.

**[Internal] 실측으로 잡은 두 함정**

- **`getAttr(plug, settable=True)` 는 컨스트레인트가 구동하는 트랜스폼에도 `True` 를 돌려준다.**
  그 말을 믿으면 "핸들을 옮겼다" 고 보고해 놓고 실제로는 컨스트레인트가 도로 끌어가,
  편차 1.0 이 조용히 남는다. 잠금과 `connectionInfo(isDestination=True)` 를 직접 본다.
- **`ikHandle.snapEnable`(기본 ON) 은 IK 가 꺼진 동안 핸들을 이펙터에 자동으로 붙인다.**
  그래서 구속된 핸들의 델타를 핸들 트랜스폼에서 내면 0 이 나온다 — 컨스트레인트의 출력
  플러그 `constraintTranslate` 를 직접 봐야 한다.

**검증** — mayapy(Maya 2024) 헤드리스 **core 87항목 + UI 스모크 56항목**.
편차 0 은 정적으로만이 아니라 **핸들을 끌었다 되돌린 뒤 · 씬을 저장했다 다시 연 뒤**까지 확인했다.
3·4 조인트 체인, 변환된 그룹 아래의 핸들, `twist` +35/−50/0, 폴 벡터 컨스트레인트 없는 경우,
`ikSCsolver`, `ikSplineSolver` 거부, `ikBlend` 가 연결된 리그, `snapEnable` ON/OFF,
pointConstraint 로 구동되는 핸들, 두 핸들 동시 편집, `Cancel` 복원, 일직선 체인 경고.

---

## v01.04 (2026-07-30)
**[Feature]** Curve 탭 `joint to obj` 에 **`Match to Sel`** 버튼 추가 — 리스트를 거치지 않고
지금 씬에서 선택한 오브젝트/버텍스로 바로 실행. `Order` 가 켜져 있으면 버텍스를 고른 순서대로 처리.

## v01.03
**[Fix]** Curve / Divide 조인트 생성을 **월드 절대 좌표**로 바로잡았다. 원본 MEL 의
object-space / 이중 가산 좌표 처리는 계층 아래 오브젝트에서 오차를 냈다.

## v01.01
**[Change]** Aim 탭 개선 — `Aim axis` 드롭박스(X/Y/Z)로 pole tgt 을 향할 보조축 선택.
`aimConstraint`(부모→자식 cycle) 대신 벡터 연산으로 `jointOrient` 를 직접 계산.

## v01.00
MEL `JointTool V05.03` 의 3탭(Curve / Divide / Aim)을 PySide 로 포팅하고,
`A00060_jointTool` 의 헤어 기능을 `Hair` 탭으로 추가(총 4탭).
