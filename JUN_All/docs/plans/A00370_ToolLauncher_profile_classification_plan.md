# A00370_ToolLauncher — 프로파일 분류 · 미등록 툴 등록 계획서

> **작성** 2026-10-22 · 상태: **착수 전 (사용자 확인 대기 — §6)** · 대상 `A00370_ToolLauncher` v01.09
> 배경: `data/profiles/*.json` 5개는 사용자가 지금까지 툴을 **기능별로 분류해 온 흔적**이다. 이 분류를 이어받아,
> 자주 쓰는 툴 가운데 **아직 버튼이 없는 툴**을 프로파일에 등록한다.
> 관련: [`A00370_ToolLauncher.md`](../A00370_ToolLauncher.md) §7 프로파일 · §8-1 기본 프로파일 · v01.07 (기본 프로파일 정리)

---

## 0. 요청

| # | 요청 | 이 계획의 절 |
|---|------|-------------|
| R1 | 기존 프로파일 분류(ANIM · Mesh · RIG · UE · Default)를 **참고 기준**으로 삼는다 | §1 현황 · §2 분류 축 |
| R2 | 자주 쓰는 툴 중 **미등록 툴**을 찾아 등록한다 | §3 후보 · §4 제외 |
| R3 | 분류 작업의 **계획서**를 먼저 쓴다 (이 문서) | §5 절차 · §6 확인 질문 |

---

## 1. 현황 (2026-10-22, `data/profiles/*.json` 실측)

| 프로파일 | 카테고리 | 버튼 (저장 경로는 `tools/<폴더>` 상대) |
|----------|----------|----------------------------------------|
| `ANIM` | Main | `A00110_animTool_V02` · `A00120_FKIK` |
| `Mesh` | Main | `A00380_MeshTool` · `A00050_uvTool_V02` · `A00180_abSymMesh` · `A00290_BSTool_V02` |
| `RIG` | Main | `A00060_jointTool_V03` · `A00145_RigConnect` · `A00170_driverTool` · `A00275_skinTool_V01` |
| `UE` | Main | `A00080_KWI_creator_V03` · `A00260_ConstraintConverter` · `A00350_ArrayCreator` |
| `Default` | — | (비어 있음) |

- 등록된 툴 **13개**. 카테고리는 전부 `Main` 하나(카테고리 축은 아직 안 쓴다). 버튼 색은 전부 없음.
- `tools/` 폴더 69개 중 템플릿 · 구버전 · 런처 자신을 빼면 현행 **54종**(저장소 README 기준), 그중 등록은 13 → 미등록 **40여 종**.
- 런처가 버튼을 받아 주는 조건(`tool_launcher.validate`): 폴더가 있고 **`__init__.py` 가 있어야** 한다
  (`tools.<폴더>` 를 import 해 `run(True)` 호출). → **standalone 툴(`__init__.py` 없음)은 지금 구조로는 등록 불가** (§4-B).
- 경로 저장은 `to_portable` 로 `tools/...` 상대. `dev/A005xx_*` 는 `tools` 앵커가 없어 절대경로로 남는다 → PC 간 깨짐 (§4-C).

---

## 2. 분류 축 — 기존 프로파일을 어떻게 읽었나

프로파일 이름이 곧 **작업 상황**이다. 기존 네 개는 저장소 README 의 도메인 분류와 거의 겹친다.

| 프로파일 | 뜻(읽은 대로) | README 도메인 |
|----------|---------------|---------------|
| `RIG` | 리깅 세팅 중 켜 두는 툴 | 리깅 |
| `ANIM` | 애니메이션 작업 중 | 애니메이션 |
| `Mesh` | 모델링 · 블렌드셰이프 · 메시 정리 | 모델링 / 블렌드셰이프 |
| `UE` | 마야 → 언리얼 텍스트 생성 | Unreal 연동 |
| `Default` | 처음 실행 시 자동 생성되는 빈 세트 | — |

미등록 40여 종을 이 네 축에만 넣으면 **페이셜**(A00540 · A00550 · A00280 …)과 **씬 유틸**(네이밍 · 선택 · 정렬 · 세트 · 머티리얼 · 파일 입출력 …)이 갈 곳이 없다.

| ID | 결정 | 권장 | 이유 |
|----|------|------|------|
| D1 | 프로파일 신설 | **`FACIAL` · `UTIL` 2개 신설**, 기존 네 개는 이름 · 순서 그대로 | 페이셜 · 씬 유틸이 갈 곳이 없다 |
| D2 | 카테고리 분할 | **프로파일당 2~3개**로 가볍게(예: RIG = `Joint & Control` / `Connect & Driver` / `Skin`) | `Main` 하나면 버튼 10개를 넘을 때 찾기 어렵다. v01.08 Filter 가 카테고리 이름으로도 검색하므로 **카테고리 이름이 곧 검색어**가 되게 짓는다 |
| D3 | 중복 등록 | 한 툴을 **두 프로파일에 중복 등록 허용**(예: `A00410_SecondaryMotion` 은 RIG 와 ANIM 둘 다) | 프로파일은 "상황" 이라 겹치는 게 자연스럽다 |

---

## 3. 등록 후보 (미등록 · in-Maya · `__init__.py` 있음)

"자주 쓴다" 는 사용자만 안다. 아래 **활동량**은 2026-06 이후 그 폴더를 건드린 커밋 수(개발 활동의 대리 지표)이며
**사용 빈도가 아니다** — 표의 `제안` 열은 제안이고 §6 Q1 에서 사용자가 고른다.

### 3-A. RIG (제안 카테고리: `Joint & Control` · `Connect & Driver` · `Skin`)

| 툴 | 한 줄 | 활동량 | 제안 | 비고 |
|----|-------|-------:|:----:|------|
| `A00130_ControlRig_V02` | 템플릿 조인트 → 컨트롤 리그 굽기 (Match · Orient & Place · Pair & Constrain · IK) | 126 | **등록** | V01 은 구버전 |
| `A00400_CurveTool` | 커브 생성 · 편집 · 표시 (Joints · Controls · Wrap · Shape Edit) | 110 | **등록** | Mesh 에도 중복 등록 후보 (D3) |
| `A00460_ControllerTool` | 조인트 체인 → `zro > con > ctl > tgt` FK 컨트롤러 계층 | 33 | **등록** | |
| `A00410_SecondaryMotion` | FK 체인 관성(찰랑임), Virtual Child | 60 | **등록** | ANIM 에도 중복 (D3) |
| `A00010_humanIKTool_V02` | HumanIK 캐릭터라이즈 · Mirror | 44 | 등록 | RIG 또는 ANIM — Q2 |
| `A00430_DemBone` | Dem Bones 스킨 분해 | 32 | 등록 | 외부 실행 파일 의존 · **아이콘 없음**(후보 25종 중 유일 — 등록 전 `A00520_icon_builder` 로 만든다) |
| `A00270_skinMigrate` | 토폴로지 다른 메시로 스킨 전이 | 30 | 보류 | `A00275_skinTool` Transfer 탭과 겹침 — 겹치면 제외 |
| `A00190_FKIK_General_Tool` | 범용 FK/IK 스위칭 | 29 | 보류 | ANIM 의 `A00120_FKIK` 와 역할 확인 |
| `A00150_remapVal` · `A00160_sphericalEye` · `A00140_ConnectClosest` | 단일 기능 | 50 · 36 · 30 | **제외** | 각각 `A00170_driverTool`(Remap · Spherical Eye) · `A00145_RigConnect`(Connect Closest) 에 통합됨 |

### 3-B. ANIM (제안 카테고리: `Keys` · `Motion`)

| 툴 | 한 줄 | 활동량 | 제안 | 비고 |
|----|-------|-------:|:----:|------|
| `A00390_WindTool_V03` | 본 체인 바람 일렁임 (Envelope · Chain Wave) | 21 (V01 41 · V02 46) | **등록** | V03 만. V01 · V02 는 구버전 |
| `A00410_SecondaryMotion` | (3-A 와 중복) | 60 | **등록** | |
| `A00010_humanIKTool_V02` | (3-A 와 중복) | 44 | Q2 | |
| `A00190_FKIK_General_Tool` | (3-A 참고) | 29 | 보류 | |

### 3-C. Mesh (제안 카테고리: `Edit` · `Shape` · `UV`)

| 툴 | 한 줄 | 활동량 | 제안 | 비고 |
|----|-------|-------:|:----:|------|
| `A00420_Wrapper` | 커브 쌍 가이드로 다른 토폴로지 메시 래핑 | 36 | **등록** | |
| `A00400_CurveTool` | (3-A 와 중복) | 110 | 등록 | D3 |
| `A00440_SetTool` | 컴포넌트 세트 집합 연산 · Find | 36 | 등록 | UTIL 로 보내도 됨 — Q2 |
| `A00300_meshDoctor` | 메시 진단 | 38 | **제외** | `A00380_MeshTool` MeshDoctor 탭으로 이식됨(v01.07 때 같은 이유로 삭제) |

### 3-D. FACIAL (신설 제안, 카테고리: `Shape` · `Lip Sync`)

| 툴 | 한 줄 | 활동량 | 제안 | 비고 |
|----|-------|-------:|:----:|------|
| `A00550_PoseMapper` | 음소 어트리뷰트 → 블렌드셰이프 포즈 (Solo preview · Capture · JaLi) | 53 | **등록** | |
| `A00540_JaliLipSync` | VisemeNet txt → JALI 리그 키 | 28 | **등록** | |
| `A00280_correctiveFromCache` | RBF 의상 주름 코렉티브 | 28 | 등록 | |
| `A00290_BSTool_V02` · `A00180_abSymMesh` | 블렌드셰이프 편집 · 대칭 | — | 중복 등록 | 지금 Mesh 에 있음 — FACIAL 에도 (D3) |
| `A00090_ConnectionBuilder` · `A00100_jsonEditor_MH` | MetaHuman RBF 연결 · json | 96 · 12 | **등록 불가** | standalone(`__init__.py` 없음) — §4-B |

### 3-E. UTIL (신설 제안, 카테고리: `Select & Name` · `Scene` · `File`)

| 툴 | 한 줄 | 활동량 | 제안 | 비고 |
|----|-------|-------:|:----:|------|
| `A00330_NamingTool` | 토큰 규칙 리네임 · Set Rename · Insert | 112 | **등록** | |
| `A00480_FileTool` | Export / Import / Path | 90 | **등록** | `A00040_file_exporter_V02` 를 통합 → V02 는 제외 |
| `A00340_SelectionTool` | 선택 세트 버튼 · 프로파일 | 56 | **등록** | |
| `A00470_MaterialTool` | 머티리얼 이름 규칙 진단 · Copy · Rename | 43 | **등록** | |
| `A00030_quickTool_V02` | 퀵 유틸 모음 | 37 | 등록 | File · Import 는 A00480 으로 갔음 — 남은 기능 확인 |
| `A00310_SearchTool` | 타입 · 토큰 · 규칙으로 선택 | 28 | 등록 | |
| `A00211_RefLineage` | 씬 레퍼런스 그래프 → FileManager 로 내보내기 | 22 | 등록 | |
| `A00250_SceneMemo` | 오브젝트별 메모 | 21 | 등록 | |
| `A00450_manipulatorTool` | 매니퓰레이터 축 굵기 | 20 | 등록 | |
| `A00360_SortTool` | 정렬 · 아웃라이너 재정렬 | 19 | 등록 | |
| `A00200_CSV_tool` | CSV 입출력 | 9 | 보류 | 안내 문서 없음 — 현행인지 확인 |

### 3-F. UE

| 툴 | 한 줄 | 활동량 | 제안 | 비고 |
|----|-------|-------:|:----:|------|
| `A00320_ARKitCurveTool` | ARKit 커브 참조 코드 | 9 | **제외** | `__init__.py` 없음 · 참조 코드(README 표기) |

UE 프로파일은 현행 3개가 전부 등록돼 있어 **추가 없음**.

---

## 4. 제외 (등록하지 않는 것과 이유)

### 4-A. 구버전 · 템플릿 · 자기 자신
`A00000_base` · `A00004_base_QT` · `A00008_base_QT_maya`(템플릿) / `A00010_humanIKTool` · `A00030_quickTool` · `A00040_file_exporter`(·`_V02`, A00480 에 통합) · `A00050_uvTool` · `A00060_jointTool`(·`_V02`) · `A00070_KWI_creator` · `A00080_KWI_creator_V02` · `A00110_animTool` · `A00130_ControlRig` · `A00290_BSTool` · `A00390_WindTool`(·`_V02`) · `A00300_meshDoctor`(구버전 · 이식) / `A00020_move_skineWeightTool`(레거시) / `A00370_ToolLauncher`(자신).

### 4-B. standalone 툴 — 지금 구조로는 등록 불가
`A00210_FileManager` · `A00220_BackupTool` · `A00240_PathTool` · `A00230_StartupTool` · `A00490_KeyboardTool` · `A00090_ConnectionBuilder` · `A00100_jsonEditor_MH` · `A00320_ARKitCurveTool`.
`__init__.py` 가 없어 `validate` 가 거절하고, 있어도 마야 안에서 `run()` 으로 띄우는 구조가 아니다(별도 파이썬 프로세스).

- 선택지 ① **이 계획에서는 제외**하고 standalone 은 `A00230_StartupTool`(로그인 시 자동 실행) · `A00240_PathTool`(폴더 버튼) 이 맡는다. **권장**.
- 선택지 ② 런처에 **"standalone 실행" 모드**(버튼이 `launch.py` 를 `subprocess` 로 띄움)를 추가한다 — 기능 작업이라 **별도 계획서** 로 분리.

→ Q4.

### 4-C. dev 툴
`dev/A00500_reloader` · `A00510_release_builder` · `A00520_icon_builder` · `A00530_dependency_check` 는 `__init__.py` 가 있어 **등록은 되지만** 경로에 `tools` 앵커가 없어 `to_portable` 이 **절대경로로 저장** → 다른 PC 에서 깨지고 프로파일 json 이 PC 마다 달라진다(v01.04 가 막은 바로 그 문제). 셸프 버튼으로 두는 것이 맞다. **제외**.

---

## 5. 절차 (코드 변경 없음 — `data/profiles/*.json` 만)

| 단계 | 내용 | 산출물 |
|------|------|--------|
| S1 | §6 질문에 사용자가 답한다 → §3 표의 `제안` 열을 **확정** 으로 바꾼다 | 이 문서에 §0-A 확정 표 추가 |
| S2 | json 편집. 기존 프로파일은 **카테고리를 나누고(D2) 버튼을 추가**, `FACIAL` · `UTIL` 신설(D1). 경로는 `tools/<폴더>` 상대, 버튼 이름은 기존 관례(`jointTool_V03` 처럼 접두 번호 없이 폴더명 꼬리) | `ANIM.json` `Mesh.json` `RIG.json` `UE.json` `FACIAL.json` `UTIL.json` |
| S3 | 헤드리스 검증: 모든 버튼에 `tool_launcher.validate(resolve(path))` OK · `find_icon` 있음(2026-10-22 선검사: 후보 25종 전부 validate OK, 아이콘은 `A00430_DemBone` 만 없음) · 한 프로파일 안에 같은 경로 중복 없음 · json 이 `prefs.load_profile` 로 읽힘 | 검증 스크립트 결과(scratchpad) |
| S4 | 마야 GUI 에서 프로파일 전환 · 각 버튼 1회 실행(툴이 뜨는지) · v01.08 Filter 로 카테고리 이름 검색 확인 | 사용자 확인 |
| S5 | 문서: `A00370_ToolLauncher.md` §8-1 기본 프로파일 표 갱신 · `CHANGELOG` v01.10(데이터 변경, v01.07 과 같은 종류) · `version.py` 주석 · `WORKLOG` · 메모리 | 커밋 (푸시는 요청 시) |

- 버튼 색(§1 전부 없음)은 이번 범위 밖 — 원하면 Q5.
- `Default` 는 빈 채로 둔다(처음 실행 시 자동 생성되는 세트. 비어 있어야 "내 것" 과 섞이지 않는다).
- `data/active.json`(마지막 프로파일) 은 gitignore 대상이라 건드리지 않는다.

---

## 6. 확인 질문 (답하면 S1 → S2 진행)

| # | 질문 | 권장 |
|---|------|------|
| Q1 | §3 표에서 **실제로 자주 쓰는 툴**만 고른다. `등록` 으로 표시한 것 중 빼거나, `보류` · `제외` 중 넣을 것이 있나? (활동량은 개발량이라 사용 빈도와 다를 수 있다) | 표의 **굵은 등록** 전부 + 나머지는 사용자 선택 |
| Q2 | 자리가 애매한 툴: `A00010_humanIKTool_V02`(RIG / ANIM), `A00440_SetTool`(Mesh / UTIL), `A00400_CurveTool`(RIG / Mesh) — 한 곳만, 또는 둘 다(D3)? | **둘 다** (D3) |
| Q3 | 프로파일 `FACIAL` · `UTIL` 신설(D1) 과 카테고리 2~3개 분할(D2) 에 동의하나? 이름을 바꾸고 싶으면(예: `UTIL` → `SCENE`) 지정 | 동의, 이름 그대로 |
| Q4 | standalone 툴(§4-B): 이번엔 제외(①) 인가, 런처에 standalone 실행 모드를 넣는 별도 계획(②)을 열까? | **①** — ②는 필요해지면 별도 |
| Q5 | 버튼 색을 프로파일(또는 카테고리)별로 입힐까? 예: RIG 파랑 · ANIM 주황 · Mesh 초록 · FACIAL 분홍 · UTIL 회색 · UE 보라 | 선택 — 입히면 카테고리 단위 한 색 |

---

## 7. 체크리스트 (S2 ~ S5)

- [ ] `FACIAL.json` · `UTIL.json` 생성, 기존 4개 카테고리 분할 + 버튼 추가
- [ ] 모든 경로 `tools/<폴더>` 상대 · `validate` OK · 아이콘 있음 · 중복 없음 (헤드리스)
- [ ] 마야 GUI: 프로파일 6개 전환 · 버튼 실행 · Filter 검색
- [ ] `docs/A00370_ToolLauncher.md` §8-1 표 · `CHANGELOG` v01.10 · `version.py` 주석 · `WORKLOG` · 메모리
- [ ] 커밋 (푸시는 그 턴 요청 시)
