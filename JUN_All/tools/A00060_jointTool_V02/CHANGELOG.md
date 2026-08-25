# Changelog — A00060_jointTool_V02

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
