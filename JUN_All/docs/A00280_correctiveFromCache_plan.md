# A00280_correctiveFromCache — 작업 계획서 (RESUME CACHE)

> **이 문서는 재작업(resume) 캐시다.** 컴퓨터가 갑자기 종료돼도 재부팅 후 이 문서만 읽으면
> 처음부터 다시 설계할 필요 없이 구현을 바로 이어갈 수 있도록 모든 결정·근거·알고리즘을 담았다.
> 작성: 2026-06-24 / 상태: **✅ v01.00 구현 완료** (가이드: [A00280_correctiveFromCache.md](A00280_correctiveFromCache.md))
> 정적 검증(py_compile) 통과. 마야 실기 테스트는 sample_04.json 솔버 + 후디니 abc 로 필요.

---

## 0. Context — 왜 이걸 만드나

MetaHuman **RBF 솔버(PoseWrangler)** 로 아바타 관절부 **의상 주름(cloth wrinkle) 코렉티브 블렌드셰이프**를
만드는 작업의 **수동 병목**을 없앤다.

**현재 수동 워크플로우**:
1. 후디니가 원본 의상에 클로스 시뮬 → **Alembic(.abc) 캐시** 생성.
2. PoseWrangler **"Bake Poses To Timeline"** 로 각 드라이버 관절을 포즈별 각도로 애니메이션/키 베이크.
   (포즈 index N → frame `start+N`, 양옆 `N-1/N+1` 에 hold 키)
3. `A00110_animTool` **"Hold Selected Range"** 로 각 포즈를 구간 hold.
4. **← 병목**: 마야 Shape Editor 에서 각 포즈의 hold 프레임마다 의상 버텍스를 abc 캐시에 **수동 매치**해
   코렉티브 타겟을 만든다. = **(포즈수 × 관절수)** 만큼 수동 반복 (≈ 8 솔버 × 4 비-default 포즈 ≈ **32회**).

**목표**: 4번의 수동 Shape Editor 매칭을 **캐시에서 코렉티브를 배치 추출**하는 버튼 한 번으로 대체.

---

## 1. 핵심 발견 (이미 검증됨 — 재조사 불필요)

- **PoseWrangler 가 이미 코렉티브 추출 API 내장** (`...\PoseDriverConnect\python\epic_pose_wrangler\v2\model\api.py`):
  - `create_blendshape(pose, mesh)` (api.py:1142) — default 포즈로 가서 base 메시 복제 → front-of-chain 타겟 생성 + 솔버 출력에 와이어. (base 가 skin 안 돼 있으면 에러: api.py:1165)
  - `edit_blendshape(pose, edit=True)` (api.py:1261) — 해당 포즈에서 `<name>_EDIT` 복제(=현재 포즈로 deform 된 메시).
  - `edit_blendshape(pose, edit=False)` (api.py:1307) — **핵심**: `cmds.invertShape(orig, EDIT)` 로 포즈된 셰이프를
    **bind(스킨 이전) 델타**로 변환 → front-of-chain 타겟으로 재연결 → 솔버 출력 재와이어.
  - `add_existing_blendshape(pose, bs_mesh, base)` (api.py:1184) — front-of-chain(`frontOfChain=True`, api.py:1226)
    blendShape 생성/추가 + `isolate_blendshape(isolate=False)`(api.py:1259) 로 `solver.outputs[idx] → blendShape.weight` 직접 연결.
  - `mirror_blendshape(pose, mirror_mapping)` (api.py:1446) — 반대쪽 솔버에 미러 타겟 자동 생성. `mirror_mapping = UERBFAPI().mirror_mapping` (main.py:130).
  - `go_to_pose(pose)` (api.py:659), `poses()` (api.py:691, OrderedDict, bake 와 동일 순서), `pose_index` (api.py:570).
- **High-level 헤드리스 래퍼** (`...\v2\main.py`): `UERBFAPI(view=False)` — `create_blendshape`(357), `edit_blendshape`(401),
  `go_to_pose`(474), `get_rbf_solver_by_name`(246), `rbf_solvers`(138), `mirror_mapping`(130), `delete_blendshape`(385).
  **`view=False` 로 생성** (PoseWrangler 자체 Qt 창이 우리 PySide 창과 충돌 방지).
- **Bake 순서** (`...\v2\extensions\bake_poses.py:38`): `frame(pose) = start_frame + list(solver.poses().keys()).index(pose)`.
  → 타임라인 베이크 여부와 무관하게 **재유도 가능**.
- **사용자 기존 툴**:
  - `A00090_ConnectionBuilder` — `solver.outputs[idx] → driver(WRK_*__null__) → blendShape` 와이어. **빈 타겟만** 생성.
    규칙 `app/rules_v01/WRK_*.json` (`mapping` = 타겟 이름 배열). `connection_manager.py:29-53`.
  - `A00100_jsonEditor_MH` 의 `sample_04.json` — 8 WRK 솔버 × 5 포즈(default+4), 포즈명에 관절+방향+각도(예: `calf_l_back_50`).
    **frame 정보는 없음**, 포즈별 driver 4x4 매트릭스는 있음.

## 2. 사용자 결정 (확정)

| 항목 | 결정 | 영향 |
|------|------|------|
| **캐시 vs 의상 토폴로지** | **동일**(같은 메시로 시뮬) | invertShape 에 캐시 프레임을 **그대로** 넣어 코렉티브 직접 추출 가능 (wrap 불필요) |
| **L/R 미러** | **부분적** | mirror 는 **옵션**(기본 수동 선택), 항상 켜지 않음. `mirror_blendshape` 사용 |
| **산출물 형태** | **새 JUN 툴 `A00280`** | A00110 클론, arch B PySide, PoseWrangler API + invertShape + alembic 래핑 |

---

## 3. 핵심 알고리즘 — 포즈 1개당 코렉티브 생성 (공간 정렬이 관건)

**공간 문제**: front-of-chain 블렌드셰이프 타겟은 **bind(스킨 이전) 공간** 델타여야 한다(blendShape 가 skinCluster
upstream). 그런데 abc 캐시는 **포즈된 월드 주름 형상**(스킨+시뮬). 그대로 타겟에 넣으면 스킨이 이중 적용됨.
→ `cmds.invertShape(base, target)` 가 포즈된 target 을 "스킨 재적용 시 그 포즈를 재현하는 bind 델타"로 변환.
   **전제**: invertShape 실행 순간 base 의 deformer 가 그 포즈로 평가돼 있어야 함. PoseWrangler 의 edit 흐름이 이를 보장.

**Route A (권장 — PoseWrangler 재사용, 솔버 자동 와이어)**, 솔버 S·포즈 P(비-default)·base 의상 G·캐시 C_P:
1. `F = start_frame + list(S.poses().keys()).index(P)` (frame 매핑, §4).
2. `cmds.currentTime(F)` → `cmds.dgdirty(allPlugs=True)` / `refresh(force=True)` (abc 평가 커밋).
3. `S.go_to_pose(P)` (리그를 포즈 P 로 — G 의 skin 이 un-corrected 포즈 형상으로 평가). **베이크 키에 의존하지 않음.**
4. abc 캐시를 **정적 스냅샷** `C_P` 로 (OpenMaya `MFnMesh.getPoints`, viewport 비의존). 토폴로지 동일 가정.
5. `bs = ue_api.create_blendshape(P, mesh_name=G, edit=False, solver=S)` (없을 때만) → `edit_blendshape(P, edit=True)` 로
   `<name>_EDIT`(포즈 P 상태 복제) 생성 → **EDIT 메시 포인트에 `C_P` 포인트를 그대로 복사**(`MFnMesh.setPoints`, object space,
   토폴로지 동일이라 1:1) → `edit_blendshape(P, edit=False)` → 내부 `invertShape` 가 bind 델타 생성 + 솔버 출력 재와이어. **끝.**
6. 복원: `S.go_to_pose('default')`, `C_P` 삭제, 다음 포즈.

**Route B (대안 — 직접 invertShape)**: G 복제 → `C_P` 포인트 복사 → (S 가 P, time=F 인 상태에서) `inv = cmds.invertShape(G, dup)` →
`S.add_existing_blendshape(P, inv, G)`. (PoseWrangler edit 흐름의 churn 이 문제일 때만)

**왜 옳은가**: invertShape 가 `skin(bind+delta) == C_P` 인 delta 를 계산. 두 Route 모두 (a) 솔버가 P, (b) target=캐시 포즈 형상,
(c) abc 가 F 에서 평가 — 를 보장. `add_existing_blendshape` 가 `frontOfChain=True` 로 deform order 자동 충족.

**Gotcha**: EDIT/delta 메시는 invertShape 순간 base 와 **동일 포즈**여야 함(포인트만 이동, 트랜스폼/freeze 금지). abc 는 스냅샷 전에
F 에서 평가. 포인트 복사는 **object space** 일관. `create_blendshape` 는 G 가 skin 돼 있어야 함(사전 검증).

## 4. 포즈→프레임 매핑 & Alembic 평가

- **frame 매핑(우선)**: `poses()` 순서로 재유도 `start_frame + index`. (대안: driver 관절 키 읽기 `cmds.keyframe(j,q,timeChange)`;
  또는 per-pose 수동 입력 컬럼.) 알고리즘이 `go_to_pose` 로 직접 포즈하므로 frame 은 **abc 평가용으로만** 필요(타임라인 베이크 비의존).
- **Alembic**: `cmds.AbcImport(file, mode='import')` 로 실제 polyMesh(+`AlembicNode.time`) 임포트(gpuCache 아님 — 버텍스 읽기 불가).
  툴은 **이미 임포트된 abc mesh transform**(권장) 또는 **.abc 파일 경로**(첫 사용 시 임시 namespace 로 AbcImport) 둘 다 허용.
  스냅샷: `currentTime(F)` → `dgdirty` → `MFnMesh(abc).getPoints(kObject)` (headless, batch-safe).

## 5. 툴 구조 — A00280 (A00110 클론, arch B)

A00110 스켈레톤 클론. 재사용: `launch.py`, `__dragDrop_<num>.py`, `app/config/version.py`, `JUN_mod_tsl_qt`,
`JUN_mod_collapsible_qt`, `ThemeManager`(coral_dark 리깅), `maya_main_window`, `Framework/core/maya_refresh.suspend_refresh`,
`Framework/core/maya_undo.undo_chunk`.

```
JUN_All/tools/A00280_correctiveFromCache/
├── __init__.py                       # from .launch import run
├── launch.py                         # A00110 클론; reload_for_tool("tools.A00280_correctiveFromCache"); ThemeManager coral_dark
├── __dragDrop_A00280.py              # A00110 클론; TOOL_LABEL="CacheCorrective"; A00280 run(True); sys.modules.pop
└── app/
    ├── config/version.py             # VERSION="01.00"
    ├── core/
    │   ├── pose_wrangler_bridge.py   # UERBFAPI(view=False) 래핑: 솔버/포즈 목록, frame 맵, go_to_pose, create/edit/add/mirror
    │   ├── alembic_cache.py          # abc 해석(노드/파일), frame 평가, 토폴로지 검사, 포인트 스냅샷(MFnMesh)
    │   ├── mesh_transfer.py          # set_points(target,source) MFnMesh getPoints/setPoints(object space) + 토폴로지 동일 assert
    │   ├── corrective_batch_manager.py # generate_one(...) + generate_batch(...); undo_chunk + suspend_refresh; status 콜백
    │   ├── solver_source.py          # 씬 솔버 OR sample_04 json(이름→get_rbf_solver_by_name)
    │   └── mirror_manager.py         # mirror_blendshape(pose, mirror_mapping) 선택 포즈
    └── ui/main_window.py             # QWidget; 솔버소스/메시/프레임/포즈테이블/옵션/배치버튼/로그 (core 위임, UI문자열 영어)
```

**UI(단일 탭, collapsible)**:
- **Solver Source**: 라디오 Scene/JSON + `JUN_mod_tsl_qt` 솔버 다중선택.
- **Meshes**: Garment Base Mesh(+Pick Selected), Alembic(Scene node / .abc file +browse).
- **Frames**: Start Frame(기본=bake 값), 라디오 Derive from pose order / Read from keys / Manual.
- **Per-pose 테이블**(QTableWidget): `Solver | Pose | Frame(편집) | Process(체크) | Status`. default 자동 해제/스킵. "Refresh Poses".
- **Options**: Route(A/B), If target exists(Skip/Overwrite), "Wire to solver output"(기본 on), Mirror 그룹(기본 off+수동 L→R 선택).
- **Batch 버튼**: "Generate Correctives From Cache" → `generate_batch`, 행별 Status 갱신 + 공유 로그(te_log).
- A00110 의 "Force Refresh" 버튼 + copyright 재사용.

## 6. A00090 ConnectionBuilder 와의 상호작용

PoseWrangler 가 자동 와이어 → 이 코렉티브엔 A00090 **불필요**(둘 다 `solver.outputs[idx]→blendShape.weight` 직결).
단 **차이**: A00090 는 중간 `WRK_*__null__` 를 끼움(`solver→__null__→blendShape`). PoseWrangler 는 직결.
→ **"Wire to solver output" 체크박스**: ON(기본)=PoseWrangler 자동 와이어. OFF=타겟 생성+invert+이름만(`rule.mapping` 일치) 짓고
와이어는 A00090 `ConnectionManager.connect(rule)` 에 위임(`__null__` 토폴로지 유지).

## 7. 엣지 케이스 / 검증

- **토폴로지 불일치 가드**: `MFnMesh(abc).numVertices==numVertices(G)` & numPolygons 동일 assert. 불일치 시 해당 포즈 Status 표기 후 continue.
- **abc 프레임 없음**: 범위 밖이면 "no cache at frame F" 스킵.
- **default/무주름 스킵**: default 항상 스킵. 옵션 "skip if delta < eps"(스냅샷 후 `max|C_P - posed G| < tol`).
- **정규화**: front-of-chain weight 0~1(RBF 구동). `normalizeGroup` 켜지 말 것. 기존 blendShape 있으면 `add_existing_blendshape` 가 append.
- **undo**: `generate_batch` 전체를 `undo_chunk`(`undoName='A00280 Generate Correctives'`) + `suspend_refresh` 로 감쌈. `finally` 에서 currentTime/`go_to_pose('default')` 복원.
- **이미 존재(Skip/Overwrite)**: `S.get_blendshape_data_for_pose(P)`(api.py:1625) 비어있지 않으면 존재. Overwrite=`delete_blendshape` 후 진행 또는 edit 재진입.
- **invertShape 가용성(2023/2024)**: 기본 동봉. 배치 시작 시 `pluginInfo('invertShape',q,loaded)`/`loadPlugin('invertShape')` 가드.
- **헤드리스**: `UERBFAPI(view=False)` 1회 생성. json 이름→`get_rbf_solver_by_name` 로 live RBFNode 해석.

## 8. 효과 (수동 작업 절감)

- Before: 비-default 포즈 × 솔버 = **~32 회 수동 Shape Editor 매칭**(각각 다수 버텍스 조정).
- After(미러 없음): 설정 1회 + 버튼 1회 → 수동 매칭 **0**. 남는 결정은 처리 포즈 선택/플래그된 행 해결뿐.
- After(미러 ON, L/R 대칭): **왼쪽만**(~4 솔버×4 포즈=16) 생성 후 오른쪽 미러 자동 → 생성량 **절반(~16)**.

---

## 9. 재개(RESUME) 절차 — 재부팅 후 이걸 그대로 따른다

1. 이 문서 + 메모리 `metahuman-cloth-corrective-A00280` 를 읽는다(이미 컨텍스트로 로드됨).
2. **✅ 완료**. `JUN_All/tools/A00280_correctiveFromCache/` 가 §5 구조대로 생성돼 있고 전 파일 `py_compile` 통과.
   (클론 원본: `A00110_animTool` 의 `launch.py`/`__init__.py`/`__dragDrop_A00110.py`/`app/*`.)
3. core 부터 구현: `pose_wrangler_bridge` → `alembic_cache` → `mesh_transfer` → `corrective_batch_manager` → `solver_source`/`mirror_manager` → `ui/main_window`.
4. §3 Route A 알고리즘이 본체. §7 가드 필수.
5. `py_compile` 로 문법 검증(마야 직접 실행 불가). 실기 테스트: sample_04.json 솔버 + 후디니 abc 로 1 포즈 → 전체.
6. 문서: 가이드 `docs/A00280_correctiveFromCache.md` + CHANGELOG + README 목록 + WORKLOG. 푸시 시 Dnable_repo/dev.

### 참조 파일(재사용, 절대경로)
- `C:\Users\USER\Documents\maya\2024\modules\PoseDriverConnect\python\epic_pose_wrangler\v2\model\api.py`
  (create_blendshape:1142, add_existing_blendshape:1184, edit_blendshape+invertShape:1261/1307, mirror_blendshape:1446, poses:691)
- `...\epic_pose_wrangler\v2\main.py` (UERBFAPI: create:357, edit:401, go_to_pose:474, get_rbf_solver_by_name:246, mirror_mapping:130)
- `...\epic_pose_wrangler\v2\extensions\bake_poses.py:38` (frame 순서)
- `JUN_All\tools\A00110_animTool\app\ui\main_window.py` (UI/로그/undo 스켈레톤), `...\app\core\bake_manager.py` (undo_chunk+suspend_refresh 매니저 패턴)
- `JUN_All\tools\A00090_ConnectionBuilder\app\core\connection_manager.py` (A00090 위임 모드용), `...\app\rules_v01\WRK_*.json`
- `JUN_All\tools\A00100_jsonEditor_MH\app\core\0010_src\sample_04.json` (8 WRK 솔버 데이터)
