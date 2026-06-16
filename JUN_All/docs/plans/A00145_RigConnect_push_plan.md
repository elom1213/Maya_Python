# Push 계획 — A00145_RigConnect (신규 병합 툴, v01.00)

## 배경 / 목적

MEL `ConnectionTool V04.02`(Constrain / Connect / List Connected 3탭)와 `A00140_ConnectClosest`를
PySide 한 툴로 병합한 **신규 툴 `A00145_RigConnect`**(4탭)을 완성했다. 이 작업만 원격에 push 한다.

실제 커밋/푸시는 **사용자 승인 후** 진행한다(이 문서는 계획).

## 대상 / 범위

**A00145_RigConnect 관련 작업만** 푸시한다. 그 외 워킹트리 변경은 **건드리지 않는다.**

**포함 (이번 작업)**
- `JUN_All/tools/A00145_RigConnect/` (??) — 신규 툴 전체 (`__pycache__` 제외, `.gitignore` 적용)
- `JUN_All/docs/A00145_RigConnect.md` (??) — 사용법 문서

**제외 (이번 작업과 무관 — staging 하지 않음)**
- `JUN_All/tools/A00060_jointTool_V02/app/config/version.py` (M)
- `JUN_All/tools/A00060_jointTool_V02/app/core/aim_manager.py` (M)
- `JUN_All/tools/A00060_jointTool_V02/app/ui/main_window.py` (M)
- `JUN_All/docs/A00060_jointTool_V02.md` (M)
  → 위 4개는 A00060 관련 별개 변경. 이번 푸시에 섞지 않는다.
- `JUN_All/docs/plans/*_merge_plan.md`, `*_push_plan.md`, `JUN_mgear_initial_push_plan.md` (??)
  → 플랜 파일은 커밋하지 않는 관례(untracked 유지). 이 문서 포함.
- `JUN_All/tools/A00145_RigConnect/__pycache__/` — `.gitignore` 대상

## 브랜치 / 원격

- 현재 브랜치: `dev`
- 푸시 대상: **`Dnable_repo` 원격의 `dev`** (`origin` 아님)
- `dev` 는 `Dnable_repo/dev` 와 동기 상태 → 바로 커밋/푸시 가능
- `dev/reload_path_list.py` 는 `["Framework","tools"]` 로 `tools.*` 전체 커버 → **수정 불필요**

## 커밋 구성 (2개 — Conventional Commits)

### 커밋 1 — feat (신규 툴)
```bash
cd "C:/Users/USER/Desktop/JP/0030_maya_python_JUN/Maya_Python"

git add JUN_All/tools/A00145_RigConnect

git commit -m "feat(A00145_RigConnect): merge MEL ConnectionTool V04.02 + A00140 into Qt tool (v01.00)

- new architecture (B) PySide tool: QTabWidget with Constrain / Connect / List Connected / Connect Closest tabs
- port MEL ConnectionTool V04.02 procs to maya.cmds managers (constrain/connect/stream)
- connect_attrs: 3 broadcast patterns; connect_52_facial: 52 ARKit attrs constant
- list_stream: hyperShade up/down by node type (global flag replaced by upstream arg)
- copy A00140 maya_scene / closest_connector into Connect Closest tab (originals untouched)
- reuse Framework.qt JUN_mod_tsl_qt_v01 + CollapsibleBox; coral_dark theme
- __dragDrop_A00145.py: unique drop file + sys.modules.pop self-uncache
- fix MEL UI typos in labels (Maintain Offset, Destination)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

### 커밋 2 — docs (사용법)
```bash
git add JUN_All/docs/A00145_RigConnect.md

git commit -m "docs(A00145_RigConnect): add usage guide for merged connection tool

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

## 푸시
```bash
git push Dnable_repo dev
```

## 푸시 전 확인
1. `git status -s` — 스테이징된 게 **`A00145_RigConnect/` + `A00145_RigConnect.md` 뿐**인지 확인.
   A00060 의 M 파일 4개, plan 파일, `__pycache__` 가 staged 에 **없어야** 함.
2. `git diff --staged --stat` — 변경 규모 점검(신규 파일 16개 + 문서 1개 수준).
3. `git ls-files --error-unmatch JUN_All/tools/A00145_RigConnect/__pycache__ 2>/dev/null` 이
   아무것도 매칭 안 되는지(= `__pycache__` 미포함) 확인.
4. (가능하면) Maya 에서 `__dragDrop_A00145.py` 드롭 설치 → 4탭 각 기능 1회 수동 검증 후 푸시.
   코드는 `py_compile` 수준만 보장, 실 Maya 미검증.
5. 푸시 후 `git log --oneline -3` 로 커밋 2개가 `Dnable_repo/dev` 에 올라갔는지 확인.

## 참고
- A00060 의 M 변경은 **별도 작업**이므로 이번 푸시와 분리한다(필요 시 따로 커밋/푸시).
- plan 파일은 untracked 로 남기는 관례를 따른다(이 문서 포함 커밋 제외).
- 1개 커밋으로 합치려면 feat 커밋에 docs `git add` 해서 함께 커밋 가능(컨벤션상 분리 권장).
