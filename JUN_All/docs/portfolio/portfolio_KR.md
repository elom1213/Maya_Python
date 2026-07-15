---
title: 포트폴리오 작업 내역 (2026-05-06 ~ 2026-07-15)
aliases: [Portfolio KR, 포트폴리오 국문]
tags: [portfolio, technical-artist, pipeline, unreal, metahuman]
updated: 2026-07-15
---

# Technical Artist / Pipeline TD 작업 내역 — 국문

> **작성자**: 박지훈 (Ji Hun Park / Junny)
> **기간**: 2026-05-06 ~ 2026-07-15 (약 10주)
> **범위**: Autodesk Maya 툴 개발 · 언리얼 엔진 연동 자동화 · MetaHuman 페이셜 · 파이프라인 인프라
> **규모**: 커밋 299건 · 사내 툴 40여 종 · 전 툴 공용 프레임워크 1식
> **스택**: Python 3, `maya.cmds` / OpenMaya, PySide2·PySide6(Qt), PyInstaller, Unreal Engine (Control Rig / KawaiiPhysics / RBF), Houdini Alembic 캐시 연동

---

## 0. 한 줄 / 세 줄 소개 (이력서 상단용)

**한 줄**
> Maya·언리얼·MetaHuman을 잇는 리깅/페이셜 파이프라인 툴을 직접 설계·개발하는 Technical Artist. 10주간 40여 종의 사내 툴과 이를 지탱하는 공용 프레임워크를 구축했습니다.

**세 줄**
> - 아티스트의 반복 작업을 **툴로 제거**하는 데 집중합니다. 수백 회의 수동 반복(포즈별 코렉티브 매칭, 본 단위 물리 노드 세팅 등)을 버튼 한 번으로 대체했습니다.
> - **Maya ↔ Unreal 브릿지**를 텍스트 노드 생성 방식으로 자동화했습니다. Maya의 리그 데이터(조인트/컨스트레인트/오브젝트 배열)를 언리얼 Control Rig·KawaiiPhysics 그래프에 **Ctrl+V로 그대로 붙여넣는** 변환기를 만들었습니다.
> - 툴을 낱개가 아니라 **파이프라인으로** 만듭니다. 공용 위젯·테마·경로관리·언두·드래그&드롭 설치·릴리스 빌더를 프레임워크로 묶어, 신규 툴을 반나절 단위로 찍어낼 수 있는 구조를 갖췄습니다.

---

## 1. MetaHuman · 페이셜 / 코렉티브 (실사·MetaHuman 파이프라인)

### 1-1. PoseWrangler(언리얼 Pose Driver) 기반 아바타 관절별 의상 주름 코렉티브 자동 생성
`A00280_correctiveFromCache`

- **문제**: 어깨·팔꿈치·무릎 등 관절별로 의상 주름 코렉티브 셰이프를 만들 때, 각 RBF 포즈마다 Houdini 클로스 시뮬 캐시를 보고 Shape Editor로 손으로 형상을 맞추는 작업을 **(포즈 수 × 관절 수)** 만큼 반복해야 했습니다.
- **한 일**: Houdini에서 뽑은 **Alembic 클로스 캐시**를 읽어, 각 RBF 포즈 프레임의 캐시 형상을 스냅샷 → 리그를 해당 포즈로 이동 → PoseWrangler의 `invertShape` 경로로 **바인드(스킨 이전) 델타**를 산출해 코렉티브 타겟을 만들고 **RBF 솔버 출력에 자동 연결**하는 툴을 개발했습니다.
- **결과**: 포즈별 수동 매칭 작업이 **버튼 한 번의 일괄 처리**로 대체됐습니다. 좌우 미러 생성, 임계값 이하 무주름 포즈 스킵, 기존 타겟 Skip/Overwrite 정책, 프레임 스텝 매핑 등 실사용 옵션을 갖췄고 전체 작업이 단일 Undo로 묶입니다.
- **키워드**: MetaHuman, PoseWrangler / RBF Pose Driver, Corrective Blendshape, `invertShape`, Alembic, Houdini Cloth

### 1-2. MetaHuman 페이셜 RBF 연결 자동화
`A00090_ConnectionBuilder`

- MetaHuman 페이셜 리그의 **RBF 솔버 → 드라이버 노드 → 블렌드셰이프** 어트리뷰트 연결을 **규칙(JSON) 기반으로 자동 결선**하는 툴입니다.
- 소스/타겟 리스트업 방식으로 **1→n, n→n 배치 연결**을 지원하고, 중간 노드(`WRK_intermediate`) 경유 결선과 연결 상태 검증(validate)/해제(disconnect)를 제공합니다.
- 수백 개 어트리뷰트를 손으로 잇던 작업을 규칙 파일로 관리해 **재현 가능·검증 가능**하게 만들었습니다.

### 1-3. MetaHuman 페이셜 데이터 유틸
`A00100_jsonEditor_MH`, `A00200_CSV_tool`, `A00320_ARKitCurveTool`

- **jsonEditor_MH** — MetaHuman 페이셜 정의 JSON의 정렬·편집 도구. RBF 솔버 세팅(보간 방식, 정규화 방식)을 데이터로 관리.
- **CSV_tool** — ARKit 페이셜 캡처 CSV를 Maya로 임포트해 커브로 굽는 도구.
- **ARKitCurveTool** — 언리얼의 `Add ARKit Curves to Skeleton` 동작을 분석해 **Maya 측에서 동일 결과를 재현**하는 코드/가이드로 정리.

### 1-4. 페이셜 컨트롤 구성 — blendShape 타겟 → 컨트롤러 어트리뷰트
`A00145_RigConnect` (Attribute 탭)

- blendShape의 타겟은 일반 어트리뷰트가 아니라 **`weight[]` 멀티에 걸린 별칭(alias)** 이라, 보통의 어트리뷰트 나열로는 첫 타겟 하나만 잡힙니다. `aliasAttr`에서 직접 읽어, **blendShape를 선택하면 Attribute·Connect 탭 양쪽에서 모든 타겟이 이름으로 나열**되게 했습니다.
- 고른 타겟을 **컨트롤러에 이름 있는 키어블 float 어트리뷰트로 복사**(접두/접미사 옵션, 타입·범위·기본값 보존)하고, Connect 탭으로 **컨트롤러 → blendShape 타겟**을 결선합니다.
- "이 수십 개 표정 셰이프를 리그 컨트롤로 노출" 하는 작업을, 어트리뷰트와 연결을 하나씩 손으로 추가하는 대신 골라서 복사하는 단계로 바꿨습니다 — 페이셜 컨트롤 리그 구성의 일상적 반복 작업입니다.

---

## 2. 언리얼 엔진 노드 생성 툴 (Maya → UE 브릿지)

> 공통 아이디어: 언리얼 그래프의 노드는 **텍스트로 복사/붙여넣기가 가능**합니다.
> Maya 씬의 리그 정보를 읽어 **언리얼 노드 텍스트를 생성 → 클립보드 복사 → UE 그래프에 Ctrl+V** 하면
> 수십~수백 개의 노드가 정확한 값과 위치로 한 번에 만들어집니다. 이 원리로 3종의 변환기를 만들었습니다.

### 2-1. Maya 조인트 → 언리얼 KawaiiPhysics 변환기
`A00080_KWI_creator` (V01 → V02 standalone → **V03 in-Maya**)

- Maya에서 선택한 **타겟 루트 본 목록**을 읽어, 본 개수만큼 **KawaiiPhysics AnimGraph 노드**(base / 세팅 / LOD 분기)를 템플릿 치환으로 생성하고, 노드 위치까지 자동 배치해 그래프에 붙여넣습니다.
- **Constraints 탭**: KawaiiPhysics **Bone Constraints Data Asset** 내용을 생성. 씬에 존재하는 본 쌍만 필터링하고 인덱스 제로 패딩을 맞춰 그대로 데이터 애셋에 반영됩니다.
- **진화 과정**: 텍스트 생성 로직(core)은 유지한 채 UI만 standalone Qt 앱 → Maya 내부 PySide 툴로 재구성. 본 목록을 파일이 아니라 **Maya 씬 선택에서 바로** 받도록 개선했습니다. (core/ui 분리 설계의 실효 사례)
- **결과**: 헤어·의상·액세서리의 흔들림 물리를 본 단위로 손수 세팅하던 작업을 **본 리스트만 넘기면 끝나는 작업**으로 만들었습니다.

### 2-2. Maya 컨스트레인트 → 언리얼 Control Rig 컨스트레인트 변환기
`A00260_ConstraintConverter`

- Maya 씬에 걸린 **컨스트레인트 세팅(타입/타겟/웨이트)** 을 읽어 언리얼 **Control Rig의 Parent / Position / Rotation Constraint 노드 텍스트**로 변환합니다.
- 축별 필터(Translate/Rotate 축 On/Off), 노드 접힘(collapsed) 출력, 4개마다 줄바꿈하는 **자동 가로 배치**, 노드 간 **ExecutePin 연결(RigVMLink)** 까지 생성해 붙여넣는 즉시 실행 가능한 그래프가 나옵니다.
- **결과**: Maya에서 검증한 리그 구속 관계를 언리얼에서 다시 손으로 짤 필요가 없어졌습니다.

### 2-3. Maya 오브젝트 → 언리얼 Control Rig Item Array 변환기
`A00350_ArrayCreator`

- 리스트에 담은 Maya 오브젝트를 그 순서대로 언리얼 Control Rig의 **Item Array 노드(`TArray<FRigElementKey>`)** 텍스트로 생성 → 클립보드 복사.
- Element Type(Bone/Control/Null/Curve/Socket 등) 지정, 순서 조정(Up/Down/Reverse)을 지원합니다. 체인을 끝→루트로 선택했을 때 한 번에 뒤집는 **Reverse**는 공용 위젯 레벨의 옵션으로 만들어 다른 툴에도 재사용됩니다.

---

## 3. 리깅 자동화 (캐릭터 리그 · 스키닝 · 셰이프)

| 툴 | 내용 |
|----|------|
| `A00145_RigConnect` | **리깅 연결 작업 통합 툴**. 레거시 MEL 툴(ConnectionTool·Match Tool) 2종을 Qt로 흡수 통합. 매칭(T/R/S/Parent 옵션), 매트릭스 컨스트레인트, 최근접 오브젝트 연결, **스킨 웨이트 → 컨스트레인트 변환**(Parent/Scale/Point/Orient), 오프셋(제로아웃) 그룹 일괄 생성, **기존 컨스트레인트를 다른 오브젝트로 이관**하는 Constraint Transfer, 그리고 선택한 어트리뷰트를 접두/접미사를 붙여 다른 오브젝트에 복제하는 **Attribute 탭**(타입·범위·기본값·키어블 보존, blendShape 타겟 포함 — 1-4 참고) 등 |
| `A00270_skinMigrate` | **토폴로지가 다른 메시 간 스킨 웨이트 전이 + 본 재매핑**을 원클릭으로. 레거시 2버튼 UI도 Classic 탭으로 보존 |
| `A00060_jointTool_V02` | 레거시 MEL JointTool을 Qt로 통합. 커브 기반/분할 조인트 생성(월드 절대좌표 기준), 트위스트 전용 Aim 리디자인, 미사용 조인트 선택기 |
| `A00120_FKIK`, `A00190_FKIK_General_Tool` | FK/IK 스위칭 및 베이크. 네이티브 `bakeResults` 도입으로 프레임 루프 대비 성능 개선, **구간 밖 키·애님 레이어 포즈를 훼손하지 않는** 컨스트레인트리스 베이크로 수정 |
| `A00130_ControlRig` | 컨트롤 리그 생성 |
| `A00180_abSymMesh` | 레거시 abSymMesh를 **OpenMaya 기반으로 재구현**(속도 개선). 대칭 스냅 / 미러 디폼 / 선택 버텍스 한정 옵션 |
| `A00290_BSTool` | blendShape 편집 툴. **Maya 기본 Shape Editor를 대체**하는 탭(전체 타겟 목록 + 타겟별 Edit 토글 + 라이브 웨이트 동기화), Base Shape 편집, 프레임 단위 셰이프 복사 |
| `A00170_driverTool`, `A00150_remapVal`, `A00160_sphericalEye` | 드리븐 키·리맵 밸류(마스터 노드에서 자식 리맵 일괄 구동, 사인 웨이브/슬러프 램프 모드), 커브 최근접 어태치·균일 분배, 구형 눈 리그(동공 확장·중심 수렴) |

---

## 4. 애니메이션 툴

`A00110_animTool`

- 키 복사/붙여넣기(축 반전 포함), **L/R 컨트롤러 키 미러**, 포즈 키(6축), Offset & Hold, 베이크(Smart bake 포함), **Follow(타겟 매치 베이크)**, Graph Editor 자동 프레이밍(선택 시 현재 프레임 ±마진으로 확대) 등 애니메이터 반복 작업을 한 창에 통합.
- 레거시 MEL/SmartLayer의 베이크 알고리즘을 분석·문서화하고 **네이티브 API 기반으로 이식**해 결과 동등성과 속도를 함께 확보했습니다.

---

## 5. 모델링 / 에셋 QC · 익스포트

- **`A00300_meshDoctor`** — 메시 **읽기 전용 진단 + 안전 원클릭 수정** 툴. non-manifold, lamina, zero-area(형상 품질 기반 판정), N-gon 등을 검사하고 **여러 메시를 배치 진단해 색상 코드 요약 테이블**로 보여줍니다. 진단 결과는 JSON/TXT 로그로 남습니다.
- **`A00040_file_exporter_V02`** — 익스포트 자동화. 타입 필터(그룹 하위까지 적용), 레퍼런스 메시 처리, 씬 최상위로 빼기/계층 유지 선택.
- **`A00050_uvTool`**, **`A00030_quickTool`**, **`A00330_NamingTool`**(레거시 네이밍 툴 이식 + Quick Rename), **`A00310_SearchTool`**(타입·이름 기반 선택), **`A00360_SortTool`**(월드 X/Y/Z·이름·타입 기준 정렬 및 아웃라이너 재정렬).

---

## 6. 파이프라인 인프라 · 공용 프레임워크 (툴을 찍어내는 툴)

낱개 스크립트가 아니라 **툴을 지탱하는 공통 기반**을 함께 설계했습니다.

- **공용 Framework**
  - 재사용 위젯(리스트/버튼/콤보 등)과 **14종 컬러 테마(qss)** 통일 — 21개 Qt 툴의 UI를 카테고리별로 정리.
  - **UUID 기반 오브젝트 리스트** — 이름 중복·리네임·리페어런트에도 리스트↔씬 선택이 흔들리지 않도록 전 툴 공용 위젯을 개선(18개 툴에 동시 적용).
  - 공용 `undo_chunk` — 반복 씬 변경을 **Ctrl+Z 한 번**으로 되돌리도록 규약화.
  - `PathManager`(읽기/쓰기 경로 분리), Maya 메인 윈도우 부모 설정, 모듈 리로더.
- **배포/설치 체계**
  - **드래그&드롭 셸프 설치** — `.py` 파일을 Maya 뷰포트에 끌어놓으면 아이콘 셸프 버튼이 설치되는 방식. 툴별 고유 파일명 규칙으로 `sys.modules` 캐시 충돌 문제를 해결.
  - **PyInstaller 기반 `.exe` 빌드**, 릴리스 빌더(툴 + 프레임워크 + 문서 자동 패키징), 작업표시줄 아이콘 처리.
- **스탠드얼론 파이프라인 유틸**
  - `A00210_FileManager` — 파일/버전 매니저. 파일 간 **참조 관계를 노드 그래프(Lineage)로 시각화**, Remote(Git) ↔ Local(NAS) 소스 모드, 폴더 구조 캡처/재생성, 썸네일·로그 기록. (`A00211_RefLineage`로 Maya 씬의 레퍼런스 관계를 그대로 내보내기)
  - `A00220_BackupTool` — 지정 파일 **주기적/저장 시점 자동 백업**(크래시 대비).
  - `A00240_PathTool` · `A00370_ToolLauncher` · `A00230_StartupTool` — 자주 쓰는 경로/툴을 버튼·프로파일로 즉시 실행, Windows 부팅 시 자동 실행. **PC가 바뀌어도 경로가 자동 재매핑**되도록 처리.
- **문서화** — 툴마다 사용 가이드 문서 + CHANGELOG + 버전 파일을 유지하고, 일일 작업 로그(WORKLOG)를 운영했습니다.

---

## 7. 이 작업에서 강조하고 싶은 점

1. **DCC를 넘나드는 문제 해결** — Maya, Unreal, Houdini(캐시)를 하나의 흐름으로 잇는 툴을 만들었습니다. 특히 언리얼 노드를 텍스트로 생성하는 접근은, 엔진 플러그인 없이도 대량의 그래프 세팅을 자동화할 수 있는 실용적인 해법이었습니다.
2. **레거시 자산의 현대화** — 사내에 흩어져 있던 MEL/단일 파일 스크립트들을 분석해 Qt 툴로 통합·이식하면서, 기존 동작의 동등성을 검증하고 문서로 남겼습니다.
3. **아티스트 우선 설계** — 툴의 성패는 UI에서 갈린다고 봅니다. 항상 위(Pin) 토글, 접이식 섹션, 정렬/검색, 색상 커스터마이즈, 되돌리기 안전성 등 실제 손이 가는 부분을 반복적으로 다듬었습니다.
4. **재사용 가능한 구조** — 로직(core)과 UI를 분리해두었기에, KWI Creator를 standalone에서 Maya 내부 툴로 옮길 때 생성 로직을 그대로 재사용할 수 있었습니다.

---

## 8. 문서 · 저장소

- 툴별 상세 가이드: `JUN_All/docs/`
- 작업 로그: `JUN_All/docs/WORKLOG.md`
- 저장소 구조와 아키텍처 개요: 루트 `README.md`
