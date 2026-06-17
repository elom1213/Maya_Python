# A00060_jointTool_V02 — Aim 탭 개선 계획서

작성일: 2026-06-16 / 대상 툴: `JUN_All/tools/A00060_jointTool_V02`

> **개정(2026-06-16)**: 초안의 `aimConstraint` 방식은 부모 joint 가 자기 **자식을 타깃**으로 aim 하면
> `joint.rotate → child.worldMatrix → constraint → joint.rotate` 평가 **cycle** 을 일으킨다
> (`# Warning: Cycle on ...`). 라이브 유지(bake off) 모드는 이 토폴로지에서 본질적으로 불가능.
> → **컨스트레인트를 제거**하고 현재 world 위치로 직교 기저를 계산해 **jointOrient 에 직접 기록**하는
> 방식으로 교체. cycle/잔여 노드 없음. UI 의 `Bake & delete constraint` 체크박스는 삭제(2장 갱신).
>
> **개정2(2026-06-16)**: 자식 unparent/reparent 로 위치를 보존하던 부분도 제거. 레퍼런스로 불러온
> 조인트는 부모 변경 편집이 제한되어 `cmds.parent` 가 실패/오염되기 때문. **`setAttr`(jointOrient/rotate)
> 만 사용**하고, root→leaf 순으로 매 단계 world 위치를 live 로 다시 읽어 처리한다(표준 체인 = 자식이
> 부모 +X 뼈축 위에 놓인 경우 위치 자동 유지). → 레퍼런스 조인트에서도 동작.

---

## 0. Context (왜 바꾸는가)

현재 Aim 탭은 MEL `JUN_cmd_make_jntAim` 를 그대로 포팅한 것으로, 각 `(Start, End)` 쌍마다
`ikHandle` + `poleVectorConstraint` 를 생성한다(`app/core/aim_manager.py`). 문제점:

- IK 핸들 / poleVector 컨스트레인트가 **씬에 라이브 노드로 남는다** → 회전값이 직접 수정되지 않고
  IK 로 구동되며, 사용자가 수동으로 정리해야 함.
- pole tgt 을 향하는 **축을 고를 수 없다**(joint orient 에 의존).

목표: "Start~End 조인트의 **회전값을 일괄 수정**하되, **선택한 한 축이 pole tgt 을 향하도록**" 하는
단순한 동작으로 바꾼다. UI 에 **`Aim axis` 드롭박스(X/Y/Z)** 를 추가하고, 기본적으로 결과를
조인트 회전값으로 굳혀(bake) 보조 노드를 남기지 않는다.

### 사용자가 확정한 사항
1. **동작**: *체인 유지 + 보조축 pole*. 조인트는 **뼈(자식) 방향으로 1차 정렬을 유지**하고,
   드롭박스에서 고른 축은 **pole tgt 을 향하는 보조(up) 축**이 된다(현재 IK+poleVector 의도와 동일,
   체인 모양 보존).
2. **구현/정리**: 기본은 *임시 컨스트레인트 → 회전값 bake → 삭제*(노드 0개). 단, **체크박스로
   라이브 유지(노드 남김) 모드로 전환** 가능. **체크박스는 기본 체크됨(= bake/삭제)**.
3. **UI**: 기존 **Start / End / pole tgt 3리스트 유지** + `Aim axis` 드롭박스 + 체크박스 추가.

---

## 1. 동작 정의 (geometry)

각 `(Start, End)` 쌍에 대해 `Start → … → End` 부모 체인을 구한 뒤, **leaf(End) 를 제외한 각
조인트**를 자기 자식으로 aim 한다. 이를 `aimConstraint` 로 구현:

- `aimVector = (1,0,0)` — **primary = +X (down-bone)**. 툴 전반의 X-down 관례
  (`obj_joint_manager.set_joint_orient` / `joints_to_objs` 와 동일)와 일치.
- `upVector = 선택한 Aim axis` (X/Y/Z) — pole tgt 을 향할 보조축.
- `worldUpType = "object"`, `worldUpObject = pole tgt` → 보조축이 pole tgt 쪽으로 정렬.
  (pole tgt 없으면 `worldUpType="vector"` 로 폴백.)

결과: 뼈는 자식 쪽으로(체인 유지), 고른 축은 pole tgt 을 향함.

> 가정: primary down-bone 축 = **+X**. 미러된(-X) 체인이면 후속 옵션화 가능(이번 범위 외).
> Aim axis 로 X 를 고르면 primary 와 겹쳐 degenerate → Maya 가 임의 직교축을 잡음. 기본값은 **Y**.

---

## 2. 코드 변경 (구현 완료)

### 2-1. `app/core/aim_manager.py` — 전면 재작성
IK 대신 aimConstraint 기반으로 교체. `_chain_between(start, end)` 헬퍼로 부모 체인을 root→leaf
순으로 구하고, `make_joint_aim(starts, ends, pole_targets, aim_axis=2, bake=True)` 에서 각 조인트를
자식 쪽으로 aim(primary +X), 선택한 `aim_axis` 를 up 으로 두어 pole tgt 을 향하게 한다.

- **bake=True**(기본): 모든 컨스트레인트 적용 상태에서 local `rotate` 를 `getAttr` 로 일괄 캡처 →
  컨스트레인트 삭제 → 캡처값 `setAttr`. jointOrient 오프셋은 컨스트레인트가 보정한 local rotate 에
  반영되어 월드 방향이 동일하게 재현된다. 키프레임/노드 없음.
- **bake=False**: aimConstraint 를 라이브로 남긴다.
- leaf(End) 조인트는 자식이 없어 회전하지 않음(기존 IK 동작과 동일).
- undo 는 호출부(`main_window._run`)의 `undoInfo(openChunk/closeChunk)` 로 감싸짐.

### 2-2. `app/ui/main_window.py` — `_build_aim_tab`
`Make Joint Aim` 버튼 직전에 옵션 행 추가(기존 3리스트/Select·Add 버튼 유지):
`Aim axis` 콤보(`_axis_combo(["X","Y","Z"], "Y")`) + `Bake & delete constraint` 체크박스(기본 체크).

### 2-3. `app/ui/main_window.py` — `on_make_aim`
콤보 index+1(1-base axis)과 체크박스 상태(bake)를 `aim_mgr.make_joint_aim(...)` 에 전달.

### 2-4. 버전 / 문서
- `app/config/version.py` → `VERSION = "01.01"`, `LAST_UPDATE = "2026-06-16"`.
- `main_window.py` 헤더 주석에 v01.01 변경 이력 추가.
- 사용 가이드 `JUN_All/docs/A00060_jointTool_V02.md` 의 Aim 탭(3.3) 설명 갱신.

---

## 3. 검증 (Maya)

1. 조인트 체인(예: 3~4개) 생성, X 가 자식 쪽을 향하도록 orient. 별도 locator 를 pole tgt 로 배치.
2. 툴 실행 → Aim 탭 → 체인 선택 후 **Select Start End**(또는 Add) → pole tgt 리스트에 locator 등록.
3. **Aim axis = Y**, **Bake 체크 ON** → **Make Joint Aim**.
   - 기대: 각 조인트의 **Y 축이 locator 쪽**으로, **X 축은 자식 쪽(체인 유지)**. 씬에 IK/컨스트레인트
     노드가 **남지 않음**. 조인트 `rotate` 값이 직접 변경됨. `[OK] Make Joint Aim` 로그.
4. **Bake 체크 OFF** 로 재실행 → aimConstraint 가 **라이브로 남아** 있고 pole tgt 을 움직이면 보조축이
   따라 도는지 확인.
5. **Aim axis = Z** 로 바꿔 보조축이 Z 로 전환되는지 확인. Undo 1회로 전체 롤백되는지 확인.

---

## 4. 확인 / 가정 사항
- **primary down-bone = +X** 고정(툴 관례). 미러(-X) 체인 지원은 이번 범위 외(필요 시 옵션화).
- **leaf(End) 조인트는 재정렬 안 함**(자식 없음) — 기존 IK 동작과 동일.
- bake 모드는 **단일 정지 포즈**(키프레임 생성 안 함). 애니메이션 구간 bake 는 범위 외.
