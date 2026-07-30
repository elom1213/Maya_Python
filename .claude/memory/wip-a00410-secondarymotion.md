---
name: wip-a00410-secondarymotion
description: "A00410_SecondaryMotion — FK 체인 관성(2차 모션)을 키로 굽는 신규 툴, 설계 근거와 마야 변환 규칙"
metadata: 
  node_type: memory
  type: project
  originSessionId: 023af178-09b0-4514-8e85-069cf18e3ef9
  modified: 2026-07-29T09:04:00.209Z
---

`A00410_SecondaryMotion` (2026-07-30, v01.02, 헤드리스 검증 + 푸시 완료, **마야 실기 UI 테스트 대기**)
— FK 컨트롤러/조인트 체인에 언리얼 KawaiiPhysics 식 **관성(찰랑임)** 을 얹어 **키로 굽는** in-Maya PySide 툴.

**Why:** 마야 nucleus 계열은 성능 이전에 **작업 흐름**이 안 맞는다 — 시작 프레임부터 순차 재생해야
결과가 나와서 스크럽 불가, 파라미터를 바꿀 때마다 처음부터 재생, 결국 별도 베이크 단계가 필요하다.
Jiggle 은 메시 포인트 전용(조인트에 못 씀), spring 컨스트레인트는 길이/각도 제어가 없다.

**How to apply:**
- **설계를 결정한 실측**(mayapy, 20본×300f): 솔버 6ms + 벌크 키 7ms + 샘플링 13ms = **전 구간 30ms**.
  그래서 파라미터 변경마다 **구간 전체를 다시 풀어 프리뷰 override 레이어에 통째로 다시 굽는다**
  (scriptJob 으로 매 프레임 시뮬 X). 재생은 커브 재생이라 런타임 시뮬 없이 실시간.
- 키 기록은 **반드시 `MFnAnimCurve.addKeys` 벌크** — `cmds.setKeyframe` 대비 **74배**(0.529s vs 0.007s).
- 씬 샘플링(`getAttr -time`)만 비싸다(0.4s) → **한 번만 하고 캐시**, 이후는 캐시로 솔브만.
- **마야 변환 규칙(검증 완료, 틀리면 조인트 모드가 통째로 어긋남)**
  - joint `local = R * JO` → `R = L * JO⁻¹` (**jointOrient 를 벗겨야 함**), R 은 노드 rotateOrder
  - transform `local = RA * R` → `R = RA⁻¹ * L`
  - 공통 `world = local * parentWorld`
  - override 애님 레이어에 **절대값**을 넣으면 weight 가 base↔layer **선형 블렌드**(additive 의
    쿼터니언 합성 규칙을 추측할 필요 없음). 레이어 커브 이름은 규칙에 의존하지 말고 **추가 전/후 차집합**으로.
- **v01.01 버그(같은 실수 반복 금지)**: 회전 재구성에서 각 노드의 부모를 **앞 체인 노드로 가정하면 안 된다**.
  FK 리그는 `ctl_01 > ctl_01_offset > ctl_02` 처럼 오프셋 그룹이 껴서 **그룹 회전이 컨트롤러에 구워지고**
  첫 프레임부터 포즈가 깨진다. 노드별 **실제 DAG 부모**를 샘플링해 `parent_orig[i] * q_swing[i-1]` 사용.
- **팁 회전**: 마지막 노드는 자식이 없어 방향이 없다 → KWI 의 **dummy bone** 처럼 마지막 뼈를 한 번 더
  연장한 가상 점을 붙인다(`Rotate last node` 기본 켬). 가상 점이 falloff 분모에 포함된다.
- **v01.02 모드**: `Mode: Bone Chain / Bone Root`(A00390 과 같은 어휘, core 상수 `MODE_CHAIN`/`MODE_ROOT`,
  `MODE_LIST` 는 별칭). Bone Root = TSL 항목마다 그 자손으로 체인을 만들어 **여러 체인 동시 처리**.
  **함정: Root+Controller 에서 계층 탐색이 transform 을 전부 담으면 오프셋 그룹이 체인 노드가 된다**
  (그룹에 키가 찍히고 falloff 분모가 부풀음) → **셰이프 있는 노드(컨트롤)만 담고 그룹은 통과**시킬 것.
  셰이프 없는 계층은 필터를 끄고 재시도하는 폴백 필요.
- **v01.02 출력 확장 지점**: `app/core/outputs.py` 레지스트리 —
  `OutputSpec(id, label, family, apply_fn, needs_solve)` + `register()`.
  `FAMILY_CURVE`(키 굽기) / `FAMILY_NODE`(예약). `needs_solve=False` 면 프레임별 솔브를 건너뛴다.
  **UI Output 라디오는 레지스트리에서 자동 생성**되므로 spec 만 등록하면 나타난다.
  A00390 식 라이브 노드 출력의 난점: 이 솔버는 **이전 프레임 속도가 필요한 상태 누적형**이라
  싸인처럼 t 만으로 값이 정해지지 않는다 → 적분 표현식/커스텀 노드가 필요하다.
- **아이콘**: `icon/*.svg` → `dev/build_icons.py`. 32px 에서는 **요소 2개·굵은 선**이어야 읽힌다
  (점선은 스페클, 얇은 선+작은 점은 뭉개짐, 세로선은 핀처럼 보임). 이 스크립트는 **41개 SVG 를 전부
  다시 렌더**하므로 무관한 PNG 바이트 변경을 되돌려야 한다.
- **검증 관용구**: "기록한 회전으로 계산된 실제 씬 위치 == 솔버 위치" **왕복 검증**이 가장 강력했다
  (조인트 9.7e-13 / 컨트롤러 5.4e-12). 반드시 **비자명 jointOrient·rotateAxis·rotateOrder 혼합**으로
  테스트할 것 — JO 가 0 인 씬으로 테스트하면 통과해도 아무것도 검증하지 못한다.
- 문서: `JUN_All/docs/A00410_SecondaryMotion.md`, 계획서 `docs/plans/A00410_ChainPhysics_plan.md`.
- 미해결: 빠른 구동 + Substeps=3 에서 왕복 오차 4.7e-05(~3ppm), 원인 미특정. 콜라이더/키 감축 없음(v01.03~04 예정).

관련: [[mayapy-headless-verify]], [[tsl-selection-order]], [[undo-chunk-by-default]], [[maya-2023-compat]]
