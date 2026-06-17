# Push 계획 — A00060_jointTool_V02 Aim 탭 개선 (v01.01)

## 배경 / 목적

`A00060_jointTool_V02` 의 **Aim 탭**을 재설계했다. 구 `ikHandle + poleVectorConstraint`(라이브
노드, 축 선택 불가, cycle 경고) 방식을 버리고:

- **Aim axis 드롭박스(X/Y/Z)** 추가 — pole tgt 을 향할 보조축 선택.
- **IK+pole 식 트위스트** — 각 joint 의 X(자식 방향)는 보존하고 X 둘레 트위스트만 바꿔 보조축이
  pole 을 향하게 함. 회전(jointOrient)만 수정하므로 **모든 joint 의 월드 위치가 보존**된다.
- `aimConstraint`/reparent/translate 변경 없음 → **평가 cycle 없음, 레퍼런스 조인트에서도 동작**.
- start/end 가 체인을 여러 쌍으로 쪼개 줘도 정확(전역 스냅샷 + 조상 우선 적용).

이 JointTool 작업만 원격에 push 한다. 실제 커밋/푸시는 **사용자 승인 후** 진행(이 문서는 계획).

## 대상 / 범위

작업트리에 무관한 다른 변경이 섞여 있으므로 **A00060 파일만 선택 스테이징**한다.

**포함 (추적 파일 4개, 수정)**
- `JUN_All/tools/A00060_jointTool_V02/app/core/aim_manager.py` — Aim 로직 재작성(핵심)
- `JUN_All/tools/A00060_jointTool_V02/app/ui/main_window.py` — Aim axis 드롭박스 + 핸들러
- `JUN_All/tools/A00060_jointTool_V02/app/config/version.py` — `01.00` → `01.01`
- `JUN_All/docs/A00060_jointTool_V02.md` — Aim 탭(3.3) 사용법 갱신

**제외 (이번 push 와 무관 — 스테이징 금지)**
- 문서 수정: `JUN_All/docs/A00170_driverTool.md`, `A00190_FKIK_General_Tool.md`,
  `README.md`, `SmartLayer_bake_algorithm_analysis.md`
- `JUN_All/docs/.obsidian/` (Obsidian 설정), `JUN_All/docs/plans/A00145_*`,
  `JUN_mgear_initial_push_plan.md`, `worklog_doc_plan.md`
- **A00060 plan 파일 전부**: `..._aim_axis_plan.md`, `..._aim_world_preserve_plan.md`,
  `..._aim_twist_only_plan.md`, `..._aim_ik_twist_plan.md`, `..._merge_plan.md`,
  `..._push_plan.md`, `..._aim_push_plan.md`(이 문서)
  → **plan 파일은 untracked 로 남기는 기존 컨벤션** 유지.
- `__pycache__/` — `.gitignore` 대상.

## 브랜치 / 원격

- 현재 브랜치: `dev`
- 푸시 대상: **`Dnable_repo` 원격의 `dev`** (`origin` 아님)
- `dev` 는 `Dnable_repo/dev` 와 동기(ahead/behind = 0/0) → 바로 커밋/푸시 가능.

## 커밋 구성 (2개 — Conventional Commits)

### 커밋 1 — feat (Aim 탭 재설계 + 버전)
```bash
cd "C:/Users/USER/Desktop/JP/0030_maya_python_JUN/Maya_Python"

git add JUN_All/tools/A00060_jointTool_V02/app/core/aim_manager.py \
        JUN_All/tools/A00060_jointTool_V02/app/ui/main_window.py \
        JUN_All/tools/A00060_jointTool_V02/app/config/version.py

git commit -m "feat(A00060_jointTool_V02): redesign Aim tab as twist-only IK-style aim (v01.01)

- add Aim axis dropdown (X/Y/Z) to pick the axis that faces the pole target
- replace ikHandle + poleVectorConstraint with a constraint-free solve
  (no live nodes, no evaluation cycle)
- twist-only: keep each joint's X (toward child), roll around X so the chosen
  axis faces the pole; world positions of all joints are preserved (rotation
  only -> jointOrient, no translate / reparent changes) -> reference-safe
- robust to split start/end input (global snapshot + ancestor-first apply)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

### 커밋 2 — docs (사용법)
```bash
git add JUN_All/docs/A00060_jointTool_V02.md

git commit -m "docs(A00060_jointTool_V02): update Aim tab usage for twist-only aim

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

> 한 커밋으로 합치려면 커밋 1 에 `JUN_All/docs/A00060_jointTool_V02.md` 를 함께 `git add` 하면 된다.

## 푸시
```bash
git push Dnable_repo dev
```

## 푸시 전 확인
1. `git status -s` — 스테이징된 게 **A00060 파일 4개뿐**인지 확인.
   A00170/A00190/README/SmartLayer/.obsidian/A00145/mgear/worklog/plan 파일이 staged 에 **없어야** 함.
2. `git diff --staged --stat` — `aim_manager.py`(다수) + `main_window.py` + `version.py`
   (+ 합칠 경우 사용법 .md)만 잡히는지 점검.
3. `git ls-files --error-unmatch JUN_All/docs/plans/A00060_jointTool_V02_aim_ik_twist_plan.md` 가
   **실패**(= plan 파일 미추적)하는지 확인.
4. (가능하면) Maya 에서 `__dragDrop_A00060_V02.py` 드롭/`run(True)` → Aim 탭으로
   `joint_01→joint_02→joint_03` + pole 실행: 세 joint 월드 위치 불변(`xform -q -ws -t`),
   보조축이 pole 향함, cycle 경고 없음 확인. 코드는 `py_compile` 수준만 보장, 실 Maya 미검증.
5. 푸시 후 `git log --oneline -3` 으로 커밋 2개가 `Dnable_repo/dev` 에 올라갔는지 확인.

## 참고
- 다른 무관한 변경(A00170/A00190/README/SmartLayer/.obsidian 등)은 **이번 push 에서 건드리지 않고**
  작업트리에 그대로 둔다(별도 작업으로 분리).
- plan 파일은 untracked 관례 유지(이 문서 포함 커밋 제외).
