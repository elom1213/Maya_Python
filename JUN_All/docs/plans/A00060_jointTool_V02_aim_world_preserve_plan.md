# A00060_jointTool_V02 — Aim 탭: 자식 월드 위치 보존 계획서

작성일: 2026-06-16 / 대상 툴: `JUN_All/tools/A00060_jointTool_V02`
선행: `A00060_jointTool_V02_aim_axis_plan.md` (Aim axis 드롭박스 + 컨스트레인트/cycle 제거)

---

## 0. Context (왜 또 바꾸는가)

현재 `make_joint_aim` 은 부모 joint 의 `jointOrient` 만 수정한다. 자식의 **로컬 translate** 는
그대로 두므로, "자식이 부모의 +X 뼈축 위에 있다"는 **표준 체인 가정에서만** 자식 월드 위치가 유지된다
(off-axis 체인이면 자식이 밀린다).

목표: 부모 재정렬 후에도 **자식 joint 의 월드 위치를 (off-axis 포함) 정확히 보존**한다.
레퍼런스로 불러온 조인트도 지원해야 하므로 **reparent·constraint 금지, `setAttr` 만 사용**한다.

### 진단 결론 — 가능
- 부모 재정렬 → 자식 월드 위치 이동. 자식의 **로컬 translate 를 역산해 다시 써넣으면** 월드 위치 복원.
- `jointOrient`(부모) + `translate`(자식) 둘 다 값 편집(`setAttr`)이라 **레퍼런스에서 허용**.
- reparent / aimConstraint 없음 → parent 편집 제한 / 평가 cycle 모두 회피.

---

## 1. 알고리즘 (parent → child)

각 `(Start, End)` 쌍의 체인 `chain = [root … leaf]` 에 대해:

1. **스냅샷(재정렬 전)**: 체인 모든 joint 의 원본 월드 위치 `W[0..m]` 와 pole 의 월드 위치를 먼저 읽는다.
   - 이유: 조상 재정렬로 손자가 미리 밀리므로, 단계마다 읽으면 "원본"을 못 잡는다. **반드시 선스냅샷.**
2. **root→leaf 순**으로 `k = 0 … m-1`:
   - 정렬 기저 계산: `X = normalize(W[k+1] - W[k])`(자식 방향), `aim_axis 축 → pole`, 나머지 = 외적.
     - `W[k]`(부모 위치)와 `W[k+1]`(자식 위치) 모두 **스냅샷 원본** 사용 → 원본 뼈 방향으로 정렬.
   - `_apply_world_orient(chain[k], x, y, z)` : 부모 `jointOrient` setAttr, `rotate/rotateAxis = 0`.
   - **자식 월드 위치 복원**: `cmds.xform(chain[k+1], ws=True, t=W[k+1])`
     → 새 부모 행렬 기준으로 자식 로컬 translate 역산·기록(`setAttr`).

각 joint 는 자기 **부모 단계**에서 원본 월드 위치로 복원되고, 그 뒤 자신/자손 재정렬로는 위치가 바뀌지
않는다(재정렬은 방향만 바꿈, 위치는 xform 으로 고정). root 는 체인 밖 부모를 두므로 처음부터 안 움직인다.
결과: **체인 전체 월드 위치 보존 + 각 X 가 원본 뼈를 향하고 aim_axis 가 pole 을 향함**. off-axis 무관.

> leaf(End) 는 정렬하지 않지만(자식 없음) 부모 단계에서 위치가 복원되며, 방향은 부모를 따라 바뀐다.
> list 저장 순서 무관: `_chain_between` 가 hierarchy 로 root→leaf 를 푼다(자식→부모 저장 OK).

---

## 2. 코드 변경 — `app/core/aim_manager.py`

`_chain_between` / `_aim_basis` / `_apply_world_orient` 는 그대로 두고 `make_joint_aim` 만 교체.

```python
def make_joint_aim(starts, ends, pole_targets, aim_axis=2):
    """각 (start,end) 체인을 자식 쪽으로 aim(원본 뼈 방향)하며 aim_axis 가 pole tgt 을 향하게.
    부모 jointOrient + 자식 translate setAttr 만 사용 -> 자식 월드 위치 보존, 레퍼런스 안전."""
    n = min(len(starts), len(ends))
    for i in range(n):
        chain = _chain_between(starts[i], ends[i])           # root -> leaf
        pole = (pole_targets[i] if i < len(pole_targets)
                else (pole_targets[-1] if pole_targets else None))

        # 1) 재정렬 전 원본 world 위치 스냅샷
        wpos = [cmds.xform(j, q=True, ws=True, translation=True) for j in chain]
        ppos = cmds.xform(pole, q=True, ws=True, translation=True) if pole else None

        # 2) parent -> child : 정렬 후 자식 월드 위치 복원
        for k in range(len(chain) - 1):                      # leaf 제외
            p_jnt, p_child = om.MVector(wpos[k]), om.MVector(wpos[k + 1])
            if (p_child - p_jnt).length() < _EPS:
                continue                                     # 두 joint 겹침 -> 방향 정의 불가
            p_pole = om.MVector(ppos) if ppos else None
            x, y, z = _aim_basis(p_jnt, p_child, p_pole, aim_axis)
            _apply_world_orient(chain[k], x, y, z)           # 부모 jointOrient (rotate=0)
            cmds.xform(chain[k + 1], worldSpace=True, translation=wpos[k + 1])  # 자식 위치 복원
```

- `_world_point` 헬퍼는 더 이상 쓰지 않으면 제거(또는 유지).
- undo 는 호출부 `main_window._run` 의 `undoInfo(open/close Chunk)` 로 이미 묶임.

UI(`main_window.py`)·버전: **변경 없음**. (Aim axis 드롭박스 그대로, 동작만 개선.)

---

## 3. 엣지 케이스 / 가정

- **잠금/연결**: 자식 `translate` 또는 부모 `jointOrient`/`rotate` 가 lock 되었거나 incoming 연결로
  구동 중이면 `setAttr`/`xform` 실패 → `_run` 이 `[ERR]` 로그. (포즈된 referenced 리그의 구동 채널 등.)
- **로컬 translate 변경**: 자식 월드 위치 유지를 위해 자식 **로컬 translate 값은 바뀐다**(의도된 결과).
  rest 스켈레톤의 로컬 수치가 달라짐에 유의.
- **체인 밖 branch 자식**: 정렬되는 chain joint 에 chain 외 다른 자식이 달려 있으면 그 자식은 부모를
  따라 회전(이번 범위 외). 필요 시 "각 단계에서 부모의 모든 immediate child 월드 위치 복원"으로 확장 가능
  (단, 깊은 branch 내부까지 보존하려면 descendant 전체 선스냅샷 필요).
- **leaf 방향**: 재정렬 안 함(자식 없음). 끝단 orient 을 0 으로 만들고 싶으면 후속 옵션.

---

## 4. 검증 (Maya)

1. **표준 체인**: X 가 자식 쪽인 3~4 joint + pole locator. Aim axis=Y → `Make Joint Aim`.
   - 각 joint Y 가 locator 향함, X 는 자식 향함, **모든 joint 월드 위치 그대로**, cycle 경고 없음.
2. **off-axis 체인**(자식 로컬 translate 에 Y/Z 성분 존재): 실행 후에도 **자식 월드 위치 불변**인지
   `xform -q -ws -t` 로 전/후 비교(기존 방식은 여기서 어긋났음).
3. **레퍼런스**: 조인트를 reference 로 불러와 동일 수행 → `[OK]` 로그, parent 편집 오류 없음,
   자식 월드 위치 유지.
4. Undo 1회로 전체 롤백 확인.
