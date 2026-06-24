# Changelog — A00280_correctiveFromCache

## v01.01 (2026-06-24)
- **Fix(PoseWrangler route): "Target mesh is not skinned" 오탐 제거.** PoseWrangler `create_blendshape`
  의 skin 체크는 skinCluster 가 **노출 셰이프에 직접 연결**돼 있어야만 통과 — skinCluster 가 디포머
  체인의 마지막이 아닌 의상 메시에서 스킨돼 있어도 에러가 났다. 체크 없는 `create_blendshape_safe`
  (동일 절차: go default → isolate → duplicate → `add_existing_blendshape`)로 대체. invertShape 는
  히스토리로 skin 을 찾으므로 결과는 동일.
- **Feat: `default` 포즈 코렉티브 생성 옵션.** Options 에 `Include 'default' pose` 체크박스 추가.
  ON 이면 default 행도 자동 체크되고 코어가 default 를 스킵하지 않는다(기존엔 항상 스킵).
- **Fix: 타겟 이름이 A00090 `rules_v01` 약속을 따른다.** default 타겟이 `default` 로 생성되던 문제 수정 →
  솔버 이름에서 접두사를 뽑아 `<prefix>_default`(예: `WRK_calf_l_UERBFSolver` → `calf_l_default`,
  `lowerarm_r_default`)로 명명. 비-default 포즈는 이미 접두사를 포함하므로 그대로 사용. 양 Route 공통
  (Direct=invertShape 결과 rename, PoseWrangler=시드 메시 이름 → blendShape 타겟 별칭).
- **Feat: Frame Step 입력 추가.** 포즈→프레임 매핑이 `start + index x step` 가 되도록 "Frame Step"
  필드 추가(기본 1). abc 캐시가 포즈당 N프레임 간격(예: 60)으로 정착되도록 시뮬된 경우, step 을 그
  간격으로 두면 0,60,120… 으로 자동 채워져 미정착 프레임 샘플링을 피한다. 행별 수동 편집도 유지.

## v01.00 (2026-06-24)
- 최초 버전.
- MetaHuman RBF(PoseWrangler) 의상 주름 코렉티브를 후디니 **Alembic 캐시에서 배치 추출**하는
  in-Maya PySide 툴 (`A00110_animTool` 클론, coral_dark 테마).
- 각 포즈의 프레임에서 캐시 형상을 가져와 `cmds.invertShape()` 로 bind(스킨 이전) 델타를 만들고
  RBF 솔버 출력에 연결 → Shape Editor 수동 매칭(타겟수×관절수)을 버튼 한 번으로 대체.
- **엔진**: PoseWrangler `edit_blendshape`(invertShape 내장) 재사용. 토폴로지 동일(캐시==의상) 전제로
  월드 공간 포인트 복사. `UERBFAPI(view=False)` 헤드리스 래핑.
- **Route 2종**: `PoseWrangler`(솔버 자동 와이어, 기본) / `Direct invertShape`(타겟 이름만, 와이어는 A00090 위임).
- 입력: 솔버 소스(씬/JSON), Garment Base Mesh, Alembic(노드/.abc), Start Frame, per-pose 테이블(체크/프레임 편집).
- 옵션: If target exists(Skip/Overwrite), Skip if max delta < eps, L/R Mirror(선택 포즈).
- 전체 단일 undo 청크 + suspend_refresh, 종료 시 솔버 default/타임 복원.
- 아이콘: 파란 주름 캐시 → RBF 허브 모티프.
