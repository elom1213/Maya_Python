# Push 계획 — A00060_jointTool_V02 (신규 병합 툴, v01.00)

## 배경 / 목적

MEL `JointTool V05.03`(Curve / Divide / Aim 3탭)와 기존 Python `A00060_jointTool`(Hair)을
PySide(QTabWidget) 한 툴로 병합한 **신규 툴**을 `JUN_All/tools/A00060_jointTool_V02/` 에 완성했다.
원본 `A00060_jointTool` / MEL 파일은 미수정 보존. 이 작업을 원격에 push 한다.

실제 커밋/푸시는 **사용자 승인 후** 진행한다(이 문서는 계획).

## 대상 / 범위

전부 **신규(untracked)** 이고, 수정된 추적 파일은 없다. → **툴 + 사용법 문서만 푸시**.

**포함**
- `JUN_All/tools/A00060_jointTool_V02/` (??) — 신규 툴 전체 (`__pycache__` 제외, `.gitignore` 적용)
- `JUN_All/docs/A00060_jointTool_V02.md` (??) — 탭별 사용법 문서

**제외**
- `JUN_All/docs/plans/A00060_jointTool_V02_merge_plan.md` — 설계 문서(플랜 파일은 untracked 유지, 기존 컨벤션)
- `JUN_All/docs/plans/A00060_jointTool_V02_push_plan.md` (이 문서) — 커밋 제외
- `JUN_All/docs/plans/JUN_mgear_initial_push_plan.md` — 무관한 이전 작업 산출물
- `JUN_All/tools/A00060_jointTool_V02/__pycache__/` — `.gitignore` 대상

## 브랜치 / 원격

- 현재 브랜치: `dev`
- 푸시 대상: **`Dnable_repo` 원격의 `dev`** (`origin` 아님)
- `dev` 는 `Dnable_repo/dev` 와 동기 상태(ahead/behind 없음) → 바로 커밋/푸시 가능
- `JUN_All/dev/reload_path_list.py` 는 `RELOAD_PACKAGES = ["Framework", "tools"]` 로 `tools.*` 전체를
  커버 → **신규 툴 등록 수정 불필요**.

## 커밋 구성 (2개 — Conventional Commits)

### 커밋 1 — feat (신규 툴)
```bash
cd "C:/Users/USER/Desktop/JP/0030_maya_python_JUN/Maya_Python"

git add JUN_All/tools/A00060_jointTool_V02

git commit -m "feat(A00060_jointTool_V02): merge MEL JointTool V05.03 + A00060 into Qt tool (v01.00)

- new architecture (B) PySide tool: QTabWidget with Curve / Divide / Aim / Hair tabs
- port MEL JointTool V05.03 procs to maya.cmds managers (curve/obj/divide/aim)
- migrate A00060_jointTool hair-curve utilities into Hair tab (widget deps removed)
- reuse Framework.qt JUN_mod_tsl_qt_v01 for textScrollList + Select/Add/Del/Up/Down
- __dragDrop_A00060_V02.py: unique drop file + sys.modules.pop self-uncache
- original A00060_jointTool / MEL left untouched

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

### 커밋 2 — docs (사용법)
```bash
git add JUN_All/docs/A00060_jointTool_V02.md

git commit -m "docs(A00060_jointTool_V02): add usage guide for merged joint tool

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

## 푸시
```bash
git push Dnable_repo dev
```

## 푸시 전 확인
1. `git status -s` — 스테이징된 게 **툴 디렉터리 + 사용법 .md 뿐**인지 확인.
   plan 파일들과 `__pycache__` 가 staged 에 **없어야** 함.
2. `git diff --staged --stat` — 변경 규모 점검(신규 파일 14개 + 문서 1개 수준).
3. `git ls-files --error-unmatch JUN_All/tools/A00060_jointTool_V02/__pycache__ 2>/dev/null` 이
   아무것도 매칭 안 되는지(= `__pycache__` 미포함) 확인.
4. (가능하면) Maya 에서 `__dragDrop_A00060_V02.py` 드롭 설치 → 4탭 각 기능 1회 수동 검증 후 푸시.
   코드는 `py_compile` 수준만 보장, 실 Maya 미검증.
5. 푸시 후 `git log --oneline -3` 로 커밋 2개가 `Dnable_repo/dev` 에 올라갔는지 확인.

## 참고
- plan 파일은 untracked 로 남기는 관례를 따른다(이 문서 포함 커밋 제외).
- 1개 커밋으로 합치려면 feat 커밋에 docs `git add` 해서 함께 커밋 가능(컨벤션상 분리 권장).
