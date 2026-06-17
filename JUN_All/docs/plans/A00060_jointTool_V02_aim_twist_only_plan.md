# A00060_jointTool_V02 — Aim 탭: 트위스트만 수정(swing 보존) 계획서

작성일: 2026-06-16 / 대상 툴: `JUN_All/tools/A00060_jointTool_V02`
선행: `..._aim_axis_plan.md`(Aim axis·cycle 제거), `..._aim_world_preserve_plan.md`(자식 월드 위치 보존)

---

## 0. Context (왜 바꾸는가)

현재 `make_joint_aim` 은 조인트마다 X 축을 `normalize(child - jnt)` 로 **새로 계산**한다. 조인트의
원래 X 가 자식을 정확히 향하지 않았다면 X 방향(= **swing**)까지 바뀐다.

목표: 부모가 자식을 향하는 **X 벡터(swing)는 그대로 유지**하고, 월드 쿼터니언 관점에서 **X 축 둘레의
트위스트(roll)만** 조정해 선택한 `aim_axis` 가 pole tgt 을 향하게 한다.

### 원리 (swing-twist)
- 임의 회전은 `R = swing · twist`(twist = X축 둘레 회전)로 분해된다.
- **월드 X 축이 동일한 두 회전은 오직 트위스트만 다르다** (X 를 고정하면 swing 고정).
- ⇒ 목표 기저의 X 를 `child-jnt` 가 아니라 **조인트의 현재 월드 X 축**으로 두고 보조축만 pole 로
  맞추면, swing 보존 + 트위스트만 변경. 별도 쿼터니언 분해 불필요(기저 구성만 변경).

> "X 가 자식을 향한다"는 것은 정렬된 체인의 전제. 본 방식은 **현재 X 를 그대로 보존**하므로,
> 자식을 향하든 아니든 입력 X 방향을 건드리지 않는다(가장 보수적).

---

## 1. 알고리즘 변경점

`..._aim_world_preserve_plan.md` 의 흐름(선스냅샷 → root→leaf 정렬 → 자식 월드 위치 복원)은 유지.
**기저 계산의 X 만** "child 방향" → "현재 월드 X 축"으로 바꾼다.

조인트 `j` 의 현재 월드 X 축 = worldMatrix 의 첫 행(row0, 정규화):
```
wm = cmds.getAttr(j + ".worldMatrix[0]")     # row-major flat 16
x_cur = om.MVector(wm[0], wm[1], wm[2]).normal()
```

- 스냅샷 시점: **재정렬 전**에 각 체인 joint 의 (원본) 월드 X 축과 월드 위치를 함께 스냅샷.
  (조상 트위스트로 자손 프레임이 바뀌기 전의 "원본 X" 를 보존하려는 의도. `_apply_world_orient` 가
  절대 월드 기저를 세팅하므로, 부모가 바뀌어도 목표 X = 원본 X 가 정확히 재현된다.)
- 보조축 up = `pole_pos - j_pos`(스냅샷) → X 에 수직인 평면으로 투영되어 트위스트 결정.
- `aim_axis == X` 는 X 와 충돌(트위스트로 X 를 pole 에 맞출 수 없음) → 기존 폴백 유지(임의 up) 또는 무시.
- pole 방향이 X 와 평행하면 트위스트 미정 → 폴백(현재 보조축 유지에 가깝게). `_aim_basis` 의 평행 폴백 재사용.

결과: 각 joint 의 **X(swing) 불변**, **트위스트만** 보조축이 pole 을 향하도록 변경, **자식 월드 위치 보존**.

---

## 2. 코드 변경 — `app/core/aim_manager.py`

### 2-1. `_aim_basis` 시그니처 변경 (X 를 인자로 받음)
`x` 를 내부에서 `child-jnt` 로 계산하지 않고 **인자로 전달**받게 한다.

```python
def _aim_basis(x, p_jnt, p_pole, aim_axis):
    """주어진 X(고정, swing 보존) 기준으로 aim_axis 축이 pole 을 향하는 직교기저 (x,y,z) 반환."""
    x = x.normal()
    up = (p_pole - p_jnt) if p_pole is not None else None
    if up is None or up.length() < _EPS or abs(up.normal() * x) > 0.9999:
        up = om.MVector(0, 1, 0)
        if abs(up * x) > 0.9999:
            up = om.MVector(0, 0, 1)
    if aim_axis == 3:                 # Z 가 pole 을 향함
        y = (up ^ x).normal(); z = (x ^ y).normal()
    else:                             # 2(Y, 기본) / 1(X 충돌 폴백)
        z = (x ^ up).normal(); y = (z ^ x).normal()
    return x, y, z
```

### 2-2. `make_joint_aim` — X 를 현재 월드 X 축으로
```python
def _world_x_axis(jnt):
    wm = cmds.getAttr(jnt + ".worldMatrix[0]")
    return om.MVector(wm[0], wm[1], wm[2]).normal()

def make_joint_aim(starts, ends, pole_targets, aim_axis=2):
    n = min(len(starts), len(ends))
    for i in range(n):
        chain = _chain_between(starts[i], ends[i])
        pole = (pole_targets[i] if i < len(pole_targets)
                else (pole_targets[-1] if pole_targets else None))
        # 선스냅샷: 원본 월드 위치 + 원본 월드 X 축
        wpos = [cmds.xform(j, q=True, ws=True, translation=True) for j in chain]
        wxax = [_world_x_axis(j) for j in chain]
        ppos = cmds.xform(pole, q=True, ws=True, translation=True) if pole else None
        for k in range(len(chain) - 1):
            x_cur = wxax[k]                              # ← 현재 X 보존(swing 유지)
            p_jnt = om.MVector(wpos[k])
            p_pole = om.MVector(ppos) if ppos else None
            x, y, z = _aim_basis(x_cur, p_jnt, p_pole, aim_axis)
            _apply_world_orient(chain[k], x, y, z)       # 절대 월드 기저 → 트위스트만 반영
            cmds.xform(chain[k + 1], worldSpace=True, translation=wpos[k + 1])  # 자식 위치 복원
```

- `_apply_world_orient` / `_chain_between` 은 변경 없음.
- 더 이상 X 를 child 로 계산하지 않으므로 `(p_child - p_jnt)` 겹침 가드는 제거(또는 X 길이 가드로 대체:
  worldMatrix row0 길이가 0 인 경우는 없으므로 사실상 불필요).
- UI / 버전 변경 없음.

---

## 3. 엣지 케이스 / 가정

- **X 가 자식을 안 향하는 입력**: 그래도 현재 X 를 그대로 보존(요청대로 swing 미변경). X 가 자식을 향하길
  원하면 "월드 위치 보존" 버전(선행 계획)을 쓰면 됨 — 두 동작은 목적이 다름.
- **aim_axis == X**: X 둘레 트위스트로 X 자신을 pole 에 맞출 수 없음 → 임의 up 폴백(보조축 정의용).
- **pole ∥ X**: 트위스트 미정 → 폴백 up. 보조축이 사실상 임의가 되므로 결과가 튈 수 있음(입력 주의).
- **자식 월드 위치 보존**: 트위스트만 줘도 off-axis 자식은 X 둘레로 공전하므로 `xform` 복원 유지.
  on-axis 자식은 애초에 트위스트로 안 움직임.
- 잠금/연결된 jointOrient·translate 는 `setAttr` 실패 → `_run` 이 `[ERR]` 로그.

---

## 4. 검증 (Maya)

1. 정렬된 체인 + pole. 실행 **전후 각 joint 의 월드 X 축**을 `getAttr worldMatrix[0]` row0 로 비교
   → **dot ≈ 1**(X 불변, swing 보존) 확인.
2. 선택한 `aim_axis`(Y/Z)의 월드 방향이 pole 쪽으로 회전(트위스트)했는지 확인.
3. 자식 월드 위치 `xform -q -ws -t` 전후 동일 확인. cycle 경고 없음. 레퍼런스 조인트 동작 확인.
4. 일부러 X 가 자식을 안 향하게 틀어둔 joint → 실행 후에도 **X 방향 그대로**, 보조축만 pole 로.
5. Undo 1회 롤백.
