# Push 계획 — docs 경로 미푸시 파일 정리

## 배경 / 목적

`JUN_All/docs/` 에 커밋/푸시 안 된 파일이 섞여 있다. 분류해서 **(a) 버릴 것 / (b) gitignore 할 것 /
(c) 푸시할 것 / (d) 로컬 보관**으로 정리하고, 가치 있는 문서만 `Dnable_repo/dev` 에 올린다.
실제 작업은 **사용자 승인 후** 진행(이 문서는 계획).

## 현황 분류

| 파일 | 분류 | 조치 |
|------|------|------|
| `docs/A00170_driverTool.md` | (a) EOL only | **discard** |
| `docs/A00190_FKIK_General_Tool.md` | (a) EOL only | **discard** |
| `docs/README.md` | (a) EOL only | **discard** |
| `docs/SmartLayer_bake_algorithm_analysis.md` | (a) EOL only | **discard** |
| `docs/.obsidian/` (app/appearance/core-plugins/workspace.json) | (b) 개인 설정 | **gitignore** |
| `docs/plans/A00145_RigConnect_merge_plan.md` | (c) 설계 문서 | **푸시** |
| `docs/plans/worklog_doc_plan.md` | (c) 설계 문서 | **푸시** |
| `docs/plans/A00060_jointTool_V02_aim_axis_plan.md` | (d) 중간 반복본 | 로컬 보관 |
| `docs/plans/A00060_jointTool_V02_aim_world_preserve_plan.md` | (d) 중간 반복본 | 로컬 보관 |
| `docs/plans/A00060_jointTool_V02_aim_twist_only_plan.md` | (d) 중간 반복본 | 로컬 보관 |
| `docs/plans/A00060_jointTool_V02_push_plan.md` | (d) 운영 체크리스트 | 로컬 보관 |
| `docs/plans/A00060_jointTool_V02_aim_push_plan.md` | (d) 운영 체크리스트 | 로컬 보관 |
| `docs/plans/A00145_RigConnect_push_plan.md` | (d) 운영 체크리스트 | 로컬 보관 |
| `docs/plans/JUN_mgear_initial_push_plan.md` | (d) 타 repo(JUN_mgear) 관련 | 로컬 보관 |
| `docs/plans/docs_cleanup_push_plan.md` (이 문서) | (d) 운영 체크리스트 | 로컬 보관 |

### 분류 근거
- **(a) EOL only**: 이 4개는 `git diff` 가 **빈 결과**(내용 변경 0, CRLF/LF 정규화 차이뿐). 커밋하면
  의미 없는 줄바꿈 churn 만 남으므로 **되돌린다**.
- **(b) .obsidian**: `workspace.json` 등은 열린 패널/포커스 같은 **개인 UI 상태**라 매번 바뀐다 →
  공유 부적합. `.gitignore` 에 추가해 추적 제외.
- **(c) 푸시**: repo 가 이미 설계 plan 문서를 추적하는 관행(`A00060_*_merge_plan`,
  `qt_wrapper_migration_plan` 등)과 일관. A00145 병합 설계 + WORKLOG 설계는 이미 머지/푸시된
  기능의 근거 문서이므로 함께 올린다.
- **(d) 로컬 보관**: A00060 중간 반복본(정본 `aim_ik_twist_plan` 으로 대체됨)·운영 push 체크리스트·
  타 repo(JUN_mgear) 문서는 push 가치가 낮아 untracked 로 둔다. (push 체크리스트도 올리고 싶으면
  repo 에 전례는 있음 — 선택.)

## 작업 절차

### 1) EOL-only 가짜 변경 되돌리기
```bash
cd "C:/Users/USER/Desktop/JP/0030_maya_python_JUN/Maya_Python"
git restore JUN_All/docs/A00170_driverTool.md \
            JUN_All/docs/A00190_FKIK_General_Tool.md \
            JUN_All/docs/README.md \
            JUN_All/docs/SmartLayer_bake_algorithm_analysis.md
```
> (선택) 재발 방지: `.gitattributes` 에 `*.md text eol=lf` 추가해 정규화 고정 — 범위가 넓어 별도 작업 권장.

### 2) .obsidian gitignore
`.gitignore` 에 추가:
```
# Obsidian vault 개인 설정
JUN_All/docs/.obsidian/
```
(전체 폴더 무시. 공유 설정 일부를 남기려면 `JUN_All/docs/.obsidian/workspace.json` 만 무시해도 됨.)

### 3) 푸시할 설계 문서 + .gitignore 커밋 (2개)
```bash
# 커밋 A — gitignore
git add .gitignore
git commit -m "chore(gitignore): ignore Obsidian vault settings under docs/.obsidian

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"

# 커밋 B — 설계 문서
git add JUN_All/docs/plans/A00145_RigConnect_merge_plan.md \
        JUN_All/docs/plans/worklog_doc_plan.md
git commit -m "docs(plans): add A00145_RigConnect merge + WORKLOG design docs

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

### 4) 푸시
```bash
git push Dnable_repo dev
```

## 푸시 전 확인
1. `git status -s JUN_All/docs/` — EOL 4개가 **사라지고**(restore 됨), `.obsidian/` 가 untracked
   목록에서 **빠졌는지**(gitignore 적용) 확인.
2. `git diff --staged --stat` — staged 가 `.gitignore` + 설계 문서 2개뿐인지.
3. staged 에 (d) 로컬 보관 plan 들이 **없는지** 확인.
4. 푸시 후 `git log --oneline -3`, `git rev-list --left-right --count Dnable_repo/dev...dev` = `0 0`.

## 참고
- `dev` 는 `Dnable_repo/dev` 와 동기 상태에서 시작.
- 메모리의 "plan 파일 untracked 관례" 표기는 실제 repo 관행(설계 plan 추적)과 달라 정정이 필요
  ([[docs-go-in-jun-all-docs]] 참고).
