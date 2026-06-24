# A00280_correctiveFromCache

MetaHuman **RBF(PoseWrangler) 의상 주름 코렉티브**를 후디니 **Alembic 캐시에서 일괄 추출**하는 PySide 툴.
각 포즈의 hold 프레임마다 Shape Editor 로 의상을 캐시에 수동 매치하던 **(타겟수 × 관절수)** 반복을 **버튼 한 번**으로 대체한다.

- **아키텍처**: (B) Standalone/Qt — PySide, Maya 내 실행 (`A00110_animTool` 클론)
- **버전**: `app/config/version.py`
- **설치**: `__dragDrop_A00280.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼 → `tools.A00280_correctiveFromCache.run(True)`
- **선행조건**: PoseWrangler(PoseDriverConnect / `epic_pose_wrangler`) 모듈이 Maya 에서 import 가능해야 함.

---

## 무엇을 하나

의상 메시는 관절에 스킨 바인드돼 있고, 후디니 클로스 시뮬 **abc 캐시**(의상과 **동일 토폴로지**)가 있다.
각 RBF 포즈에 대해:

1. 포즈의 프레임에서 캐시 메시 형상을 **월드 스냅샷**.
2. 리그를 그 포즈로(`go_to_pose`) → 의상 스킨이 un-corrected 포즈 형상.
3. PoseWrangler `edit_blendshape` 의 EDIT 메시에 캐시 형상을 복사 → `edit_blendshape(edit=False)` 가
   내부에서 **`cmds.invertShape()`** 로 bind(스킨 이전) 델타를 만들고 RBF 솔버 출력에 자동 연결.

→ 수동 매칭 없이 코렉티브 타겟이 생성·연결된다. 전체가 단일 undo.

## 입력

| 항목 | 설명 |
|------|------|
| **Solver Source** | `Scene solvers`(PoseWrangler 인식) 또는 `From JSON`(sample_04.json `solvers` 키). Load Solvers → 리스트에서 다중 선택 |
| **Garment Base Mesh** | 스킨된 의상 메시(여기에 front-of-chain blendShape 가 생성됨). `Pick Selected` |
| **Alembic Cache** | `Scene node`(이미 임포트한 캐시 메시) 또는 `.abc file`(AbcImport). `Pick / Browse` |
| **Start Frame** | 포즈→프레임 매핑 시작값. 테이블에서 프레임 직접 수정 가능 |
| **Frame Step** | 포즈 간 프레임 간격. `frame = start + poseIndex x step`(기본 1). abc 캐시가 포즈당 N프레임 간격(예: 60)으로 정착되도록 시뮬됐다면 step 을 그 값으로 → 0,60,120… 자동 채움 |

## 사용 순서

1. **Load Solvers** → 솔버 리스트에서 처리할 솔버 다중 선택.
2. **Refresh Poses** → per-pose 테이블 생성(`Solver | Pose | Frame | Process | Status`). `default` 는 자동 미체크.
3. Garment Base Mesh / Alembic / Start Frame 지정.
4. 옵션 확인 후 **Generate Correctives From Cache** → 체크된 포즈를 일괄 처리, 행별 Status 갱신.
5. (선택) 한쪽만 생성했다면 포즈 체크 후 **Mirror Selected Poses** 로 반대쪽 자동 생성.

## 옵션

- **Route**
  - `PoseWrangler (auto-wire)` (기본) — `edit_blendshape` 재사용, 솔버 출력까지 자동 연결.
  - `Direct invertShape (A00090 wires)` — `cmds.invertShape` 로 타겟만 만들고 포즈 이름으로 명명, 와이어는
    `A00090_ConnectionBuilder` 에 위임(`WRK_*__null__` 중간 노드 토폴로지 유지).
  - 참고: PoseWrangler route 는 v01.01 부터 `create_blendshape` 의 엄격한 skin 직결 체크를 우회하므로,
    skinCluster 가 디포머 체인 마지막이 아니어도(스킨돼 있으면) "Target mesh is not skinned" 없이 동작한다.
- **If target exists**: `Skip`(기본) / `Overwrite`(기존 타겟 삭제 후 재생성).
- **Skip if max delta <**: 캐시와 포즈 형상의 최대 버텍스 차가 임계값 미만이면 무주름으로 보고 스킵(0 = 끔).
- **Include 'default' pose**: 기본 OFF(default 는 무보정이라 스킵). ON 이면 default 행도 자동 체크되고
  코어가 스킵하지 않아 default 포즈 코렉티브까지 생성된다. 이때 타겟 이름은 A00090 `rules_v01` 약속을
  따라 `<prefix>_default`(예: `WRK_calf_l_UERBFSolver` → `calf_l_default`)로 만들어진다.
- **Mirror Selected Poses**: PoseWrangler `mirror_blendshape` 로 반대쪽 솔버에 복제(기본 수동 선택).

## 구조

```
A00280_correctiveFromCache/
├── __init__.py / launch.py / __dragDrop_A00280.py
└── app/
    ├── config/version.py
    ├── core/
    │   ├── pose_wrangler_bridge.py     # UERBFAPI(view=False) 래핑: 솔버/포즈/frame맵/go_to_pose/create·edit·mirror
    │   ├── alembic_cache.py            # abc 메시 프레임 평가 + 월드 포인트 스냅샷
    │   ├── mesh_transfer.py            # MFnMesh get/set points(월드) + 토폴로지 검사
    │   ├── corrective_batch_manager.py # 포즈별 추출(Route A/B) + undo/suspend + 복원
    │   ├── solver_source.py            # 씬 / sample_04 json 솔버 목록
    │   └── mirror_manager.py           # 선택 포즈 L/R 미러
    └── ui/main_window.py               # PySide UI (core 위임)
```

## 동작 규칙 · 주의

- **타겟 이름 규칙**: A00090 `rules_v01/WRK_*.json` 의 `mapping` 약속을 따른다. 솔버 이름에서 접두사를
  뽑아(`WRK_<prefix>_UERBFSolver` → `<prefix>`) default 는 `<prefix>_default`, 비-default 포즈는 이미
  접두사를 포함한 포즈 이름(`calf_l_back_50`)을 그대로 쓴다. 두 Route 모두 동일하게 적용.
- **토폴로지 동일 전제**: 캐시와 base 의 vertex/polygon 수가 다르면 검증에서 중단(행 Status 에 표기).
- **base 는 skin 필수**: skinCluster 없으면 invertShape/create_blendshape 불가 → 경고.
- **공간**: 캐시→EDIT 복사는 **월드 공간**(트랜스폼이 달라도 안전).
- **복원**: 배치 종료 시 처리한 모든 솔버를 `default` 로, 타임을 원래 프레임으로 되돌림.
- `Direct` Route 의 invertShape 결과는 세밀 undo 가 제한될 수 있음 → 정밀/되돌리기 중시하면 `PoseWrangler` Route 권장.

## 참고

- 설계 계획서: [A00280_correctiveFromCache_plan.md](A00280_correctiveFromCache_plan.md)
- 연계 툴: `A00090_ConnectionBuilder`(Direct Route 와이어), `A00100_jsonEditor_MH`(sample_04.json 솔버 데이터).
- PoseWrangler: `epic_pose_wrangler.v2`(api.py `edit_blendshape`/`invertShape`, `mirror_blendshape`; main.py `UERBFAPI`).
