# A00060_jointTool_V02 — Aim 탭: IK+pole 식 트위스트(위치 완전 보존) 계획서

작성일: 2026-06-16 / 대상 툴: `JUN_All/tools/A00060_jointTool_V02`
선행: `..._aim_twist_only_plan.md`(트위스트만), `..._aim_world_preserve_plan.md`(자식 위치 보존)

> **개정(2026-06-16, 분할 입력 대응)**: start/end 가 체인을 여러 쌍으로 쪼개 줄 때
> (예: `start=[j01,j02]`, `end=[j02,j03]`) **쌍마다 위치를 스냅샷하면** 1번째 쌍이 j01 을 정렬하며
> j03 을 먼저 흔들어 놓고, 2번째 쌍이 그 이동된 위치를 원본으로 착각해 j03 위치가 보존되지 않았다.
> → `make_joint_aim` 을 **(작업 수집 → 전역 1회 스냅샷 → 깊이(조상) 순 적용)** 로 재구성.
> 모든 대상 joint 의 원본 위치를 정렬 전에 한 번에 잡고, joint 을 항상 "원본" 자식 위치로 조준하므로
> 분할 입력도 단일 체인 입력과 동일한 결과(전 위치 보존)가 된다. 입력 리스트 순서와 무관.

---

## 0. Context (무엇이 틀렸나)

가정: `joint_01 → joint_02 → joint_03` (왼쪽이 부모). 모든 joint 의 X 가 자식을 향함.
기대: 기능 수행 후 **세 joint 의 월드 위치는 모두 불변**, pole tgt 위치에 따라 **트위스트만** 적용.

현재 동작: 수행 후 `joint_02`, `joint_03` 의 월드 위치가 바뀐다(틀림).

사용자가 원하는 레퍼런스 동작 = **IK + pole vector**:
`(joint_02,joint_03)` IK + `(joint_01,joint_02)` IK + 두 IK 에 poleVectorConstraint → 타겟을
움직이면 **위치는 고정**된 채 pole 방향으로 joint 가 트위스트 → IK 삭제 시 그 회전이 유지.
즉 **회전(rotation)만 바뀌고 위치는 핀으로 고정**되는 것.

### 진단 (근본 원인 2가지)
1. **translate 를 건드림**: 현재 코드는 부모 재정렬 후 자식 위치를 `cmds.xform(ws,t=...)` 로 복원하며
   **자식 local translate 를 바꾼다**. IK 는 translate 를 절대 안 바꾼다(회전만). 이 translate 수정이
   체인을 따라 누적되며 위치 드리프트를 만든다.
2. **X 소스 = 현재 월드 X 축(순수 트위스트)**: 굽은 체인에서 자식이 X축 둘레로 공전해 위치가 틀어진다.

### 핵심 원리 (위치가 저절로 보존되는 이유)
부모의 X 를 **자식의 원본 위치로 정확히 조준**하면, 자식은 *고정된 local 거리(=뼈 길이)*만큼
새 X 방향에 놓이므로 **원래 월드 위치에 그대로 떨어진다** — translate 수정 불필요.
보조축(트위스트)은 X 둘레 회전이라 X 위에 있는 자식을 움직이지 않는다(트위스트는 위치 무관).
root→leaf 로 처리하면 각 자식이 부모 단계에서 원위치로 자동 복원되어, **세 joint 위치 모두 불변**.
이것이 IK(위치 핀 + 회전만 굽기)와 동일한 결과다.

조준된 체인(사용자 케이스: X 가 이미 자식을 향함)에서는 **자식 방향 = 현재 X** 이므로
X 방향(swing)도 그대로 유지되고, 결과적으로 **트위스트만** 바뀐다.

---

## 1. 알고리즘 (회전만, 위치 보존)

각 `(Start,End)` 쌍의 체인 `[root … leaf]`:

1. **선스냅샷**: 체인 모든 joint 의 월드 위치 `W[]`, pole 월드 위치 `P` 를 읽는다. (위치 비교/조준용)
2. **root→leaf** 로 `k = 0 … m-1`:
   - `x = normalize(W[k+1] - W[k])`  ← **자식 방향**(원본 위치). 조준된 체인이면 = 현재 X(swing 보존).
   - `up = P - W[k]` → X 에 수직 평면으로 투영되어 aim_axis 가 pole 을 향하는 **트위스트** 결정.
   - 직교기저 `(x, y, z)` 구성(`_aim_basis`), `_apply_world_orient(chain[k], x, y, z)` 로
     **부모 jointOrient 만** 세팅(rotate/rotateAxis=0). **translate 는 절대 건드리지 않는다.**
   - 자식은 고정 local 거리만큼 새 X 위에 놓여 `W[k+1]` 에 자동 복원 → 위치 보존.
3. leaf 는 정렬 안 함(자식 없음). 위치는 부모 단계에서 보존됨.

→ `xform` 위치 복원 제거. translate 미변경. 세 joint 월드 위치 모두 불변, 트위스트만 적용.

---

## 2. 코드 변경 — `app/core/aim_manager.py`

`make_joint_aim` 만 수정. `_chain_between` / `_aim_basis(x, p_jnt, p_pole, aim_axis)` /
`_apply_world_orient` 는 그대로. `_world_x_axis` 헬퍼와 `wxax` 스냅샷, 그리고 `cmds.xform` 위치
복원 라인을 **제거**한다.

```python
def make_joint_aim(starts, ends, pole_targets, aim_axis=2):
    """각 (start,end) 체인 joint 의 X 를 자식으로 조준(=조준된 체인이면 X 불변)하고, aim_axis 가
    pole tgt 을 향하도록 X 둘레 트위스트만 jointOrient 에 기록한다. 회전만 바꾸므로(translate 미변경)
    세 joint 의 월드 위치가 모두 보존된다(IK+pole 식)."""
    n = min(len(starts), len(ends))
    for i in range(n):
        chain = _chain_between(starts[i], ends[i])           # root -> leaf
        pole = (pole_targets[i] if i < len(pole_targets)
                else (pole_targets[-1] if pole_targets else None))

        wpos = [om.MVector(cmds.xform(j, q=True, ws=True, translation=True)) for j in chain]
        ppos = om.MVector(cmds.xform(pole, q=True, ws=True, translation=True)) if pole else None

        for k in range(len(chain) - 1):                      # leaf 제외
            x = wpos[k + 1] - wpos[k]                         # 자식 방향(원본 위치 조준)
            if x.length() < _EPS:
                continue                                     # 두 joint 겹침 -> 방향 정의 불가
            xb, yb, zb = _aim_basis(x, wpos[k], ppos, aim_axis)
            _apply_world_orient(chain[k], xb, yb, zb)        # jointOrient 만 (translate 미변경)
```

- 제거 대상: `_world_x_axis()` 정의, `wxax = [...]` 스냅샷, `cmds.xform(chain[k+1], ws, t=...)` 복원.
- UI / 버전 변경 없음.

---

## 3. 엣지 케이스 / 가정

- **위치 보존 전제 = 스케일 없음**: 체인에 비균등/비1 스케일이 있으면 회전만으로 거리가 안 맞아
  위치가 어긋날 수 있다(joint 는 보통 scale=1).
- **굽은 체인 OK**: 자식이 X 위에 놓이도록 X 를 자식으로 조준하므로, 굽은 체인도 위치 보존.
- **조준 안 된 입력**: X 가 자식을 정확히 안 향하던 joint 는 자식으로 재조준되어 그만큼 swing 이 바뀐다
  (조준된 체인이면 변화 없음 — 사용자 케이스).
- **aim_axis == X**: 트위스트 축과 충돌 → 임의 up 폴백(보통 Y/Z 사용).
- **pole ∥ bone**: 트위스트 미정 → 폴백(결과 튐, 입력 주의).
- **leaf 방향**: 재정렬 안 함. 끝단 트위스트가 필요하면 후속 옵션.

---

## 4. 검증 (Maya)

1. `joint_01→joint_02→joint_03`(X 가 자식 향함) + pole locator.
   실행 **전/후 세 joint 의 월드 위치**를 `xform -q -ws -t` 로 비교 → **모두 동일**(핵심 회귀 항목).
2. 각 joint 의 월드 X 축(`getAttr .worldMatrix[0]` row0) 전후 비교 → **dot ≈ 1**(swing 보존).
3. 선택 aim_axis(Y/Z)의 월드 방향이 pole 쪽으로 회전(트위스트)했는지 확인.
4. pole locator 위치를 바꿔가며 재실행 → 위치 불변, 트위스트만 변함.
5. cycle 경고 없음, 레퍼런스 조인트 동작, Undo 1회 롤백.
