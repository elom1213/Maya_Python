# A00590_SwingTwistNative — 검토 + 계획서 (`SwingTwistEvaluatorNode` 를 마야 기본 노드로 대체)

> **작성** 2026-11-03 · **갱신** 2026-11-13 · 상태: **v1 구현 중 — Build(새 노드망 생성)만**, Convert · Container 는 §9 · §10 계획 · 대상 Maya 2023 ~ 2026 (실측은 2024)
> 요청: Epic MetaHuman for Maya 의 `SwingTwistEvaluatorNode` 의존성을 없애고 싶다 — 마야에 있는 노드만으로
> 기능을 **완벽하게** 재현할 수 있는지 검토하고, 가능하면 제작 계획서를 만든다.
> 원본: `~/Documents/maya/modules/MetaHumanForMaya/lib/SwingTwistEvaluatorPlugin/1.3.2/.../SwingTwistEvaluatorPlugin.mll`
> 참고 소스: UE 5.5 RigLogic `riglogic/joints/cpu/twistswing/TwistSwingJointsEvaluator.h`, `tdm/Computations.h`(slerp),
> MetaHuman `mh_pose_editor/1.3.3/model/swing_twist.py`(노드 생성 · 연결 방식)

---

## 0. 결론

**가능하다 — 마야에 동봉된 `quatNodes` 노드만으로 원본과 수치상 같은 결과를 낸다.** 2026-11-03 mayapy 2024 에서 원본 플러그인과
프로토타입 노드망을 나란히 놓고 같은 입력을 넣어 비교했다.

| 시험 | 샘플 | 최대 오차 (회전 행렬 원소) | 최대 오차 (오일러 값, 도) |
|------|------|---------------------------|---------------------------|
| `fromEnd = 0` | 1500 (±60° / ±180° 무작위, 블렌드 0 · 1 · 0~1 · -0.5~1.5) | **2.9e-15** | **3.3e-13** |
| `fromEnd = 1` | 1500 (같은 분포, endJoint 도 무작위) | **3.3e-15** | **2.1e-13** |
| 특이 입력 | 22 (Y/Z 180° = 쿼터니언 x=w=0, 360°, 1e-7°, 179.9999° 등) | **0** | **0** |

오일러 **값**까지 같다 — 즉 같은 회전일 뿐 아니라 **같은 오일러 가지**를 낸다(커브 · 조인트 채널 값이 그대로).

> `quatNodes` 는 Autodesk 가 마야 설치본에 넣어 배포하는 플러그인(`Maya2024/bin/plug-ins/quatNodes.mll`)이다.
> 외부 설치가 필요 없다(이 PC 2024 실측, 2023 · 2025 · 2026 은 1단계에서 확인). 씬 파일에 `requires "quatNodes"` 한 줄이 생기지만 "에픽 플러그인 의존" 은 사라진다.
> **코어 노드만**(플러그인 0개)으로 하려면 쿼터니언 곱 · slerp 를 `multiplyDivide`/`plusMinusAverage` 로 풀어야 하는데,
> slerp 의 `acos`/`sin` 이 코어 노드에 없다(2023 에 sin/cos 노드 없음 — [[maya-2023-compat]]). 그래서 **quatNodes 를 쓴다**.

---

## 1. 원본 노드 사양 (실측)

`SwingTwistEvaluatorPlugin` 1.3.2 가 등록하는 노드는 `SwingTwistEvaluatorNode` 하나.

| 어트리뷰트 | 타입 | 방향 | 비고 |
|-----------|------|------|------|
| `startJoint` | double3 | 입력 | 조인트 `.rotate` 를 연결 → 마야가 unitConversion(×57.2958) 삽입 → **도(degree)** 로 받는다 |
| `endJoint` | double3 | 입력 | `fromEnd` 일 때만 쓰인다 |
| `swingBlend` | double | 입력 | 기본 0 |
| `twistBlend[].values` | multi compound | 입력 | twist 출력 개수만큼 |
| `fromEnd` | bool | 입력 | 기본 False |
| `swing` | double3 | 출력 | → 스윙 조인트 `.rotate` (unitConversion ×0.01745) |
| `twists[]` | double3 multi | 출력 | → 트위스트 조인트들 `.rotate` |

- **트위스트 축은 X 고정**(축 어트리뷰트 없음). **rotateOrder 입력 없음** — 입력 · 출력 오일러를 항상 **XYZ** 로 해석한다.
- **jointOrient 무시** — `.rotate` 만 본다(MetaHuman 연결 방식 `swing_twist.py` 그대로).
- `affects` 관계가 비어 있다(`cmds.affects` → None). 그래도 getAttr / 재생에서 정상 평가된다.

## 2. 계산식 (RigLogic `TwistSwingJointsEvaluator` 와 같음 — 실측으로 확인)

`q = euler(startJoint, XYZ)` · Hamilton 곱 · `slerp` = 최단 경로(내적 < 0 이면 q2 부호 반전), 정규화 없음.

```
twist(q)   = normalize(q.x, 0, 0, q.w)        (길이 0 이면 identity)
invTwist   = inverse(twist(q))
swing      = q * invTwist
swingOut   = invTwist * slerp(inverse(swing), identity, swingBlend)
twistOut_i = slerp(base, identity, twistBlend_i)
             base = invTwist                    (fromEnd = 0)
             base = twist(euler(endJoint))      (fromEnd = 1, **역회전이 아님** — 원본 그대로)
출력 오일러 = quat → euler(XYZ)
```

- 블렌드는 출력을 "완전한 역회전(0)" → identity(1) 로 민다. 직관과 반대이므로 UI · 문서에 적는다.
  - twist: `0` → 시작 트위스트 **상쇄**(fromEnd 면 end 트위스트 복사), `1` → 회전 0.
  - swing: `0` → 시작 회전 **전체 상쇄**(= inverse(q)), `1` → **시작 트위스트만 상쇄**(= invTwist, 0 이 아니다).
    (2026-11-13 정정 — 처음 "1 = 영향 없음" 이라 적었는데 그건 twist 만 맞다. v1 시험에서 확인)
- 블렌드는 0~1 밖도 허용된다(외삽) — 프로토타입도 같은 값.

## 3. 마야 노드 대응 (프로토타입 그대로)

```
start.rotate ─▶ eulerToQuat ─┬─ outputQuatX/W ─▶ quatNormalize (twist) ─▶ quatInvert (invTwist) ─┐
                             │                                                                    │
                             └─ outputQuat ─▶ quatProd(in1=q, in2=invTwist) (swing)               │
                                               └▶ quatInvert (invSwing)                           │
                                                   └▶ quatSlerp(in1=invSwing, in2=I, T=swingBlend)│
                                                       └▶ quatProd(in1=invTwist, in2=slerp) ◀────┘
                                                           └▶ quatToEuler ─▶ swing.rotate
base(invTwist | twistEnd) ─▶ quatSlerp(in1=base, in2=I, T=twistBlend_i) ─▶ quatToEuler ─▶ twist_i.rotate
fromEnd: end.rotate ─▶ eulerToQuat ─▶ quatNormalize(X/W) = twistEnd
```

- 노드 수: **평가기 하나당 8 + 트위스트당 2**(fromEnd 면 +2). 스윙 출력이 없으면 스윙 가지 5개를 만들지 않는다.
- `quatProd` 의 in1·in2 순서는 위 그대로(마야 쪽 곱 순서 ↔ Hamilton 차이는 §2 식이 켤레 대칭이라 결과가 같다 — 실측 확인).
- 쿼터니언 x=w=0 (예: Y 180°) 에서 `quatNormalize` 결과가 원본의 identity 처리와 같다(특이 입력 시험 0 오차).

## 4. 만들 것

### 4-1. 공용 코어 `Framework/core/maya_swing_twist.py` (maya.cmds, UI 없음)

| 함수 | 역할 |
|------|------|
| `build(name, start_joint, end_joint, swing_joint, swing_blend, twist_joints, twist_blends, from_end)` | §3 노드망 생성. **MetaHuman `create_swing_twist_evaluator` 와 같은 인자** — 그 함수 자리에 바로 쓸 수 있게 |
| `read_plugin_node(node)` | 원본 노드에서 설정을 읽는다: start/end/swing/twist 조인트(`listConnections -skipConversionNodes`), 블렌드 값(**연결돼 있으면 소스 plug 도**), fromEnd |
| `convert(node)` | 읽기 → 노드망 생성 → 출력 연결을 새 망으로 옮김 → 원본 삭제. undo 한 덩어리([[undo-chunk-by-default]]) |
| `restore(holder)` | 반대 방향: 홀더의 메타데이터로 `SwingTwistEvaluatorNode` 를 다시 만든다(플러그인 있을 때만). DNA 내보내기용 — §6 |
| `verify(start_joint, ...)` | 무작위 포즈 N 개로 원본/변환 전후 출력 조인트 월드 행렬 비교 |

**홀더 노드**: 망 하나마다 `network` 노드 `<name>_SwingTwist` 를 만들고 사용자 어트리뷰트 `swingBlend`, `twistBlend[]`, `fromEnd`(정보),
`startJoint`/`endJoint`/`swingJoint`/`twistJoints[]`(message) 를 둔다. 블렌드는 홀더 → `quatSlerp.inputT` 로 연결 —
원본처럼 **한 노드에서 블렌드를 고칠 수 있고**, 리스토어 · 재검출의 근거가 된다. 노드망은 `container` 대신 홀더로 묶는다
(container 는 publish 규칙이 번거롭고 레퍼런스 편집에 불리).

### 4-2. 툴 `tools/A00590_SwingTwistNative` (PySide, arch B — [[prefer-pyside-for-new-tools]])

| 탭 | 내용 |
|----|------|
| **Convert** | 씬의 `SwingTwistEvaluatorNode` 목록(TSL, 노드 · start · 출력 개수 · fromEnd) → `Convert Selected` / `Convert All` → 진행 팝업 · 로그. 변환 뒤 `Verify` 자동(옵션), 마지막에 `Unload Plugin` 버튼(남은 노드 0 일 때만) |
| **Build** | 원본 없이 새로 만들기: Start / End / Swing 조인트 + Twist 조인트 리스트(TSL) + 블렌드 칸 → `Build` |
| **Restore** | 홀더 목록 → `Restore Plugin Node` (DNA 내보내기 전에) |

공용 위젯(TSL · log · progress · tabFit · menubar), 드롭 파일 `__dragDrop_A00590.py`, 아이콘, `docs/A00590_SwingTwistNative.md`.

## 5. 검증 계획

1. **골든 시험** `tests/test_swing_twist_golden.py` (mayapy) — 원본 플러그인 vs `build()` 무작위 3000 + 특이 22, 기준 행렬 1e-9 · 오일러 1e-9°. (§0 프로토타입을 시험으로 옮긴 것)
2. **변환 시험** — 원본으로 MetaHuman 식 셋업(start/end/swing/twist 3, fromEnd 둘 다, 블렌드 연결된 경우 포함) → `convert` →
   출력 조인트 월드 행렬 무작위 포즈 200 비교, `unloadPlugin` 뒤 씬 저장 · 다시 열기 → `requires` 에 SwingTwist 없음, 값 그대로.
3. **undo** — convert 한 번 undo 로 원본 복귀.
4. **restore 왕복** — convert → restore → 원본 노드 설정이 처음과 같음(연결 · 값).
5. **실제 MetaHuman 씬** — 바디 씬 하나에서 전부 변환, 애니메이션 재생 전후 조인트 월드 행렬 비교 + 재생 속도(fps) 측정. **씬 경로는 사용자에게 받는다**(원본 저장 금지, 결과는 scratchpad).
6. GUI 확인(Maya 2024 · 2023) — 툴 창 · 진행 팝업.

## 6. 위험 · 주의

| 항목 | 내용 · 대응 |
|------|------------|
| **DNA 내보내기** | MetaHuman Pose Editor 의 DNA export(`dna_serializer_2_5.py`)는 `cmds.ls(type="SwingTwistEvaluatorNode")` 로 셋업을 찾는다 → **변환한 씬에서 내보내면 swing/twist 데이터가 빠진다.** 대응: `Restore` 로 원본 노드를 되살린 뒤 내보내기(홀더 메타데이터). 문서에 굵게 |
| rotateOrder · jointOrient | 원본이 XYZ · `.rotate` 만 쓰므로 **그대로 재현**(고치지 않는다 — 고치면 "완벽 재현" 이 깨진다). 비 XYZ 조인트에 붙어 있으면 경고 로그만 |
| 성능 | 노드 수 증가(평가기당 ~10 → 바디 수십 개면 수백). 원본 C++ 한 노드보다 느릴 수 있다 — §5-5 에서 fps 측정, 큰 차이면 보고 |
| fromEnd 실시간 전환 | 원본은 어트리뷰트로 즉시 전환되지만, 노드망은 **빌드 때 구조가 정해진다**. fromEnd 를 애니메이션하는 경우는 없다고 보고 v1 은 구조로 처리(홀더의 `fromEnd` 는 정보용). 필요하면 v2 에서 두 base 를 `quatSlerp(T=fromEnd)` 로 전환 |
| 블렌드가 연결된 경우 | 원본 `swingBlend`/`twistBlend` 에 다른 노드가 연결돼 있으면 그 소스를 홀더로 옮겨 연결 |
| 레퍼런스 씬 | 레퍼런스 안의 원본 노드는 삭제할 수 없다 → v1 은 **레퍼런스 노드 건너뜀 + 로그**(원본 파일에서 변환하라고 안내) |
| quatNodes 로드 | 기본 자동 로드지만, 툴이 `loadPlugin quatNodes` 를 보장 |

## 7. 단계

| 단계 | 내용 | 산출물 |
|------|------|--------|
| 1 | 코어 `build` + 골든 시험 | `Framework/core/maya_swing_twist.py`, 시험 1 |
| 2 | `read_plugin_node` · `convert` · 홀더 · undo | 시험 2 · 3 |
| 3 | `restore` | 시험 4 |
| 4 | 툴 UI 3탭 + 드롭 · 아이콘 · 문서 | `tools/A00590_SwingTwistNative`, 오프스크린 UI 시험 |
| 5 | 실제 MetaHuman 씬 변환 · 성능 | 시험 5 결과를 이 문서 §8 에 |

## 8. 정할 것 (구현 전에 사용자 확인)

1. **툴 위치** — 새 툴 `A00590_SwingTwistNative`(권장) vs 기존 툴의 탭(예: A00090 ConnectionBuilder — MetaHuman 페이셜 연결 툴).
2. **실제 MetaHuman 테스트 씬** 경로.
3. **DNA 내보내기를 계속 쓰는지** — 쓴다면 `Restore` 가 필수, 안 쓰면 3단계를 뒤로 미룬다.
4. `quatNodes`(Autodesk 동봉) 사용 허용 여부 — 허용 안 하면 완벽 재현은 불가(§0).

**2026-11-13 사용자 답 · 범위 결정**

- 툴은 새 툴 **`A00590_SwingTwistNative`**. 번호 확인: `tools/` 에 A00580 다음이 A00600 이라 590 은 비어 있다(이 계획서가 잡아 둔 번호).
- 계획서대로 진행 → quatNodes 사용(허용으로 본다).
- **v1 = `SwingTwistEvaluatorNode` 를 대체하는 마야 노드망 생성(Build) 만.** 아래 두 기능은 "급하지 않음" — 계획만 적고 다음 단계로 미룬다.
  1. 기존 `SwingTwistEvaluatorNode` → 마야 노드망 **변환(Convert)** — §9
  2. 노드망을 **container 로 묶어 한 노드처럼** 다루기 — §10
- 실제 MetaHuman 씬 · DNA export 사용 여부는 아직 미정 → Convert 단계(§9) 에서 다시 묻는다.

**v1 범위 (§7 1단계 + 4단계 중 Build 탭)**

| 산출물 | 내용 |
|--------|------|
| `Framework/core/maya_swing_twist.py` | `build()` · 홀더 · `list_holders()` · `members()` · `delete_rig()` · `set_blends()` |
| `tests/test_swing_twist_golden.py` | 원본 플러그인 vs `build()` 골든 시험(§5-1) — 플러그인이 없는 PC 에선 수식 모델로 대조 |
| `tools/A00590_SwingTwistNative` | **Build** 탭(조인트 · 블렌드 · fromEnd → Build) + **Rigs** 탭(만든 홀더 목록 · Select · Delete · 블렌드 편집) |

홀더는 v1 부터 **멤버 노드 목록**(`nodes[]` message)을 갖는다 — §9 Restore 와 §10 Container 가 이 목록으로 망 전체를 찾는다.

---

## 9. (다음 단계) Convert — 기존 `SwingTwistEvaluatorNode` 를 노드망으로

§4-1 `read_plugin_node` · `convert` · `restore` 와 §4-2 Convert / Restore 탭을 그대로 구현한다. 순서와 세부:

1. **읽기** `read_plugin_node(node)` → `SwingTwistSpec`(v1 `build()` 인자와 같은 모양):
   - `startJoint`/`endJoint` 입력의 소스 조인트 = `listConnections(plug, s=True, d=False, skipConversionNodes=True)`.
   - `swing` 출력 · `twists[i]` 출력의 목적지 조인트(unitConversion 건너뜀). `twists` 는 **논리 인덱스 순서**로, 빈 인덱스는 `None` 으로 자리 유지.
   - 블렌드 = 값 + **입력 연결 소스 plug**(있으면). fromEnd 값(연결돼 있으면 경고 — v1 구조는 빌드 시 고정, §6).
   - start 가 조인트가 아니라 다른 노드 plug 면(예: 다른 평가기 출력) 그 plug 를 그대로 소스로 기억.
2. **생성** `build(spec)` — 이름은 원본 노드 이름 기준(`<name>_SwingTwistEvalNode` → `<name>`).
3. **옮기기** — 원본 출력 연결 끊기 → 새 망 출력을 같은 조인트 `.rotate` 에 연결 · 블렌드 소스 plug 는 홀더로 재연결.
4. **원본 삭제** + 홀더 `sourceNodeType = "SwingTwistEvaluatorNode"`, `sourceName` 기록. 전부 `undo_chunk` 한 덩어리.
5. **검증** `verify()` — 변환 전에 무작위 포즈 N 개의 출력 조인트 월드 행렬을 저장 → 변환 후 같은 포즈 재생 → 1e-9 비교. 실패면 undo 하고 로그.
6. **Restore** — 홀더 메타데이터로 원본 노드를 다시 만들고 노드망 삭제(플러그인이 로드돼 있을 때만). DNA export 용.
7. 레퍼런스 노드는 건너뜀 + 로그. 다 바꾸고 남은 원본이 0 이면 `Unload Plugin` 버튼 활성.

시험: §5-2 · 5-3 · 5-4. UI: Convert 탭(원본 목록 TSL + Convert Selected/All + Verify 옵션), Restore 는 Rigs 탭의 버튼으로.

## 10. (다음 단계) Container — 노드망을 한 노드처럼

노드망은 평가기 하나당 10~20 개라, 바디 전체를 바꾸면 Outliner/Node Editor 에 수백 개가 흩어진다.
마야 **`container`** 로 망 하나를 묶어 **원본 노드 하나를 다루던 감각**을 되살린다.

| 항목 | 설계 |
|------|------|
| 묶는 단위 | 평가기(홀더) 하나 = container 하나 `<name>_SwingTwist_CTN`. 멤버 = 홀더 `nodes[]` 전부 + 홀더 자신 |
| 만들기 | `cmds.container(name=..., addNode=members, includeNetwork=False, includeHierarchyBelow=False)` — 조인트는 **절대 넣지 않는다**(includeNetwork 를 켜면 연결된 조인트까지 빨려 들어간다) |
| 공개 어트리뷰트 | 홀더의 `swingBlend`, `twistBlend[i]` 를 `container -e -publishAndBind` 로 공개 → Channel Box · Attribute Editor 에서 container 하나만 고르고 블렌드 편집. 입력/출력도 원본 이름(`startJoint` · `endJoint` · `swing` · `twists[i]`)으로 공개해 Node Editor 에서 원본 노드와 같은 모양 |
| 숨기기 | `blackBox = True` — Outliner/Node Editor 에서 안이 보이지 않고 한 노드로 보인다. 툴에 `Black Box` 토글(디버그 때 펼치기) |
| 옵션 | Build · Convert 에 `Wrap in Container` 체크(기본 켬 예정 — 단계에서 사용자 확인). 기존 망에는 Rigs 탭 `Wrap` / `Unwrap` 버튼 |
| 지우기 | container 삭제 = 멤버까지 삭제(마야 기본). `delete_rig()` 는 container 가 있으면 그것 하나만 지운다 |
| 아이콘 | `container.iconName` 에 툴 아이콘 — Outliner 에서 구분 |

**확인할 함정(실측 후 확정)**

- container 에 넣은 노드의 **연결 · 평가 · 결과가 그대로**인지(골든 시험을 container 버전으로 한 번 더).
- `publishAndBind` 한 이름이 원본 어트리뷰트 이름과 겹칠 때 동작, multi(`twistBlend[i]`) 공개 방식.
- **레퍼런스로 불러온 container** 의 blackBox · 공개 어트리뷰트 편집이 레퍼런스 편집으로 남는지.
- undo 한 번으로 Wrap/Unwrap 이 되돌아가는지([[undo-chunk-by-default]]).
- Maya 2023 에서 같은 동작인지.
- 대안 `assets`(Asset Editor) · `dagContainer` 는 쓰지 않는다 — DAG 아닌 DG 노드망이라 `container` 로 충분.

---

### 부록 — 실측 스크립트

이 검토에 쓴 mayapy 스크립트(일회용)는 1단계에서 `tests/test_swing_twist_golden.py` 로 옮긴다.
- 어트리뷰트 조사: API 로 `MFnAttribute` 순회(§1)
- 수식 맞춤: 파이썬 Hamilton 곱 · tdm slerp 이식 vs 원본 2000 샘플 → 행렬 2e-8 · 오일러 1e-6°(파이썬 모델은 float epsilon 분기 차이)
- 프로토타입 노드망 vs 원본: §0 표
