# Push 계획 — A00110_animTool Smart bake (v01.07)

## 대상 / 범위

이번에 작업한 것만 푸시한다. **무관한 변경은 포함하지 않는다.**

**포함 (내 작업)**
- `JUN_All/tools/A00110_animTool/app/core/bake_manager.py` (M) — `smart` / `smart_tolerance` 추가
- `JUN_All/tools/A00110_animTool/app/ui/main_window.py` (M) — Smart bake 체크박스 + Tolerance + 연결
- `JUN_All/tools/A00110_animTool/app/config/version.py` (M) — `01.06` → `01.07`
- `JUN_All/docs/A00110_animTool_bake_vs_SmartLayer.md` (??) — 비교/이식 문서
- `JUN_All/docs/SmartLayer_bake_algorithm_analysis.md` (??) — SmartLayer bake 분석 문서

**제외 (이번 작업과 무관, 건드리지 않음)**
- `JUN_All/tools/A00080_KWI_creator_V02/.../A0003_Src_KWI_LD_v02.py` (M)
- `JUN_All/tools/A00080_KWI_creator_V02/.../A0101_tgtBones.py` (M)
- `JUN_All/docs/plans/dragDrop_rename_push_plan.md` (??) — 이전 작업 산출물
- 이 계획 파일(`A00110_smartbake_push_plan.md`) 자체 — 커밋 여부는 선택(아래 참고)

## 브랜치 / 원격

- 현재 브랜치: `dev`
- 푸시 대상: **`Dnable_repo` 원격의 `dev`** (upstream = `Dnable_repo/dev`, `origin` 아님)
- 현재 `dev`는 `Dnable_repo/dev`와 동기 상태(ahead/behind 없음) → 바로 커밋/푸시 가능

## 커밋 구성 (2개로 분리 — 기존 컨벤션 따름)

기존 로그가 Conventional Commits(`feat(scope): …`, `docs(scope): …`)이므로 코드와 문서를 분리한다.

### 커밋 1 — feat (툴 기능)
```bash
cd "C:/Users/USER/Desktop/JP/0030_maya_python_JUN/Maya_Python"

git add JUN_All/tools/A00110_animTool/app/core/bake_manager.py \
        JUN_All/tools/A00110_animTool/app/ui/main_window.py \
        JUN_All/tools/A00110_animTool/app/config/version.py

git commit -m "feat(A00110_animTool): add Smart bake option (native bakeResults -smart, v01.07)

- BakeManager.bake: smart / smart_tolerance params; sparseAnimCurveBake + smart=(1, tol)
- fall back to dense bake on Maya versions without the smart flag (<2020)
- Bake tab: 'Smart bake (reduce keys)' checkbox + Tolerance input, wired in on_bake

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

### 커밋 2 — docs (분석/비교 문서)
```bash
git add JUN_All/docs/A00110_animTool_bake_vs_SmartLayer.md \
        JUN_All/docs/SmartLayer_bake_algorithm_analysis.md

git commit -m "docs(A00110_animTool): compare bake with SmartLayer; document Smart bake

- analyze SmartLayer's compiled bake pipeline (speed-based adaptive sampling, space convert)
- compare with A00110 native dense bake; rationale for native smart bake (A) over custom (B)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

## 푸시
```bash
git push Dnable_repo dev
```

## 푸시 전 확인
1. `git status -s` 로 **스테이징된 게 위 5개 파일뿐**인지 확인(A00080·이전 plan 미포함).
2. `git diff --staged --stat` 로 변경 규모 점검.
3. (가능하면) Maya 2023에서 Smart bake 실제 동작 1회 검증 후 푸시 — 코드는 `py_compile`만 통과, 실 Maya 미검증.

## 참고 / 결정 필요
- **plan 파일 커밋 여부**: 기존 `docs/plans/dragDrop_rename_push_plan.md`가 untracked로 남아 있는
  걸 보면 plan 파일은 보통 커밋하지 않는 듯하다. 동일하게 이 파일도 커밋 제외를 기본으로 한다.
- 커밋을 **1개로 합치고 싶으면** feat 커밋에 docs 파일까지 `git add` 해서 한 번에 커밋해도 된다
  (단 컨벤션상 분리 권장).
- 실제 커밋/푸시는 **사용자 승인 후** 진행한다(현재는 계획만 작성).
