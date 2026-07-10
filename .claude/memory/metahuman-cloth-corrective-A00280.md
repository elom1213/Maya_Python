---
name: metahuman-cloth-corrective-a00280
description: Planned tool A00280 to batch-extract MetaHuman RBF cloth-wrinkle correctives from a Houdini Alembic cache (resume cache for crash recovery)
metadata: 
  node_type: memory
  type: project
  originSessionId: a22e8469-3b48-4ab0-bc7c-d911e925d529
---

신규 툴 **A00280_correctiveFromCache** **v01.00 구현 완료** (2026-06-24, py_compile 통과; 마야 실기 테스트는 미완).
`JUN_All/tools/A00280_correctiveFromCache/` 에 존재. core: pose_wrangler_bridge/alembic_cache/mesh_transfer/corrective_batch_manager/solver_source/mirror_manager + ui/main_window.

**목표**: MetaHuman RBF(PoseWrangler) 의상 주름 코렉티브 블렌드셰이프를 만들 때, 각 포즈 hold 프레임에서
후디니 Alembic 캐시에 의상을 마야 Shape Editor 로 수동 매치하던 (포즈수×관절수 ≈ 32회) 병목을 제거. 캐시에서 코렉티브를 **배치 추출**.

**핵심 기술(검증됨)**: PoseWrangler(`...\maya\2024\modules\PoseDriverConnect\python\epic_pose_wrangler\v2`)가
이미 코렉티브 API 내장 — `edit_blendshape(pose, edit=False)`(api.py:1307)가 내부에서 `cmds.invertShape()`로
포즈된 메시를 bind(스킨 이전) 델타로 변환+솔버 자동 와이어. 토폴로지가 캐시==의상(동일)이라, 각 포즈 frame의 캐시
포인트를 EDIT 메시에 그대로 복사 후 invertShape → 수동 매칭 불필요. frame=`start+poses().index(pose)`. `UERBFAPI(view=False)` 헤드리스.

**사용자 결정**: ① 캐시/의상 토폴로지 동일 ② L/R 미러는 옵션(기본 수동) ③ 새 JUN 툴 A00280(A00110 클론, arch B PySide).

**전체 상세(알고리즘 Route A, 툴 구조, 엣지케이스, 재개 절차)는** repo 계획서에 있음:
`JUN_All/docs/A00280_correctiveFromCache_plan.md` — 재부팅 후 이 문서를 먼저 읽고 §9 RESUME 절차대로 진행.

관련: [[prefer-pyside-for-new-tools]] (A00110 클론), [[docs-go-in-jun-all-docs]], [[push-target-dnable-dev]], [[push-includes-tool-guide-docs]].
사용자 기존 툴 연계: A00090_ConnectionBuilder(와이어 위임 모드), A00100_jsonEditor_MH(sample_04.json 8 WRK 솔버).
