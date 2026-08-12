# JUN_All 툴 사용법 문서 아카이브

이 폴더는 `JUN_All/tools/` 안의 각 툴에 대한 **사용법 · 폴더 구조 안내 문서**를 모아두는 곳이다.
새 툴을 만들거나 기존 툴을 업데이트하면 여기에 한글 안내 문서를 추가/갱신한다.

> **하위 폴더 `plans/`** — 사용법이 아니라 **기능 개발 계획 · 설계 결정 기록**(개발 문서)을 모은다.
> 파일명은 `<툴 폴더명>_<기능>.md` 규칙(예: `A00150_remapVal_sine_wave_mode.md`).
>
> **하위 폴더 `study/`** — 특정 툴 안내가 아닌 **작업 방법론 · 기법 학습 노트**(공부용 문서)를 모은다.
> 예: `study/skinWeight_transfer_workflow.md`. 목록은 [study/README.md](study/README.md) 참고.

> 정리하면 — `docs/*.md`=툴 안내, `docs/plans/`=개발 계획, `docs/study/`=학습 노트.

---

## 문서 목록

| 툴 | 도메인 | 문서 |
|----|--------|------|
| `A00030_quickTool` | 잡동사니 / 퀵 유틸 | [A00030_quickTool](A00030_quickTool.md) |
| `A00060_jointTool_V02` | 리깅 / 조인트 생성 (Curve·Divide·Aim·Hair) | [A00060_jointTool_V02](A00060_jointTool_V02.md) |
| `A00080_KWI_creator_V03` | 언리얼 / KawaiiPhysics | [A00080_KWI_creator_V03](A00080_KWI_creator_V03.md) |
| `A00110_animTool` | 애니메이션 | [A00110_animTool](A00110_animTool.md) |
| `A00140_ConnectClosest` | 리깅 / 페이셜 | [A00140_ConnectClosest](A00140_ConnectClosest.md) |
| `A00145_RigConnect` | 리깅 / 연결·매칭·컨스트레인트 통합 | [A00145_RigConnect](A00145_RigConnect.md) |
| `A00150_remapVal` | 리깅 | [A00150_remapVal](A00150_remapVal.md) |
| `A00160_sphericalEye` | 리깅 / 페이셜 | [A00160_sphericalEye](A00160_sphericalEye.md) |
| `A00180_abSymMesh` | 모델링 / 블렌드셰이프 | [A00180_abSymMesh](A00180_abSymMesh.md) |
| `A00210_FileManager` | 파이프라인 / 파일·버전 기록 (standalone) | [A00210_FileManager](A00210_FileManager.md) |
| `A00260_ConstraintConverter` | 리깅 / 언리얼 | [A00260_ConstraintConverter](A00260_ConstraintConverter.md) |
| `A00270_skinMigrate` | 리깅 / 스킨 | [A00270_skinMigrate](A00270_skinMigrate.md) |
| `A00280_correctiveFromCache` | 페이셜·리깅 / RBF 코렉티브 | [A00280_correctiveFromCache](A00280_correctiveFromCache.md) |
| `A00290_BSTool` | 블렌드셰이프 / 페이셜 | [A00290_BSTool](A00290_BSTool.md) |
| `A00320_ARKitCurveTool` | 언리얼 / ARKit·스켈레톤 커브 (참조 코드) | [A00320_ARKitCurveTool](A00320_ARKitCurveTool.md) |
| `A00330_NamingTool` | 네이밍 / 리네임 | [A00330_NamingTool](A00330_NamingTool.md) |
| `A00340_SelectionTool` | 선택 / 리깅·애니 (오브젝트 재선택 버튼) | [A00340_SelectionTool](A00340_SelectionTool.md) |
| `A00410_SecondaryMotion` | 애니메이션 / 2차 모션 (FK 체인 관성·찰랑임) | [A00410_SecondaryMotion](A00410_SecondaryMotion.md) |
| `A00420_Wrapper` | 모델링·페이셜 / 커브 가이드 래핑 (다른 토폴로지 메시 맞추기) | [A00420_Wrapper](A00420_Wrapper.md) |

### 공용 위젯 · 헬퍼 (Framework)

특정 툴이 아니라 **여러 툴이 함께 쓰는 위젯/헬퍼**의 동작·옵션 문서. 툴 문서는 "재사용 위젯 …" 이라고만 적고
자세한 동작은 아래를 참조한다.

| 모듈 | 내용 | 문서 |
|------|------|------|
| `Framework/qt/MOD_tsl_qt_v01.py` | 공용 리스트(TSL) 위젯 — Select/Add/Del/Up/Down/Sort, **Order(선택 순서 유지)**, UUID 보관 | [Framework_MOD_tsl_qt](Framework_MOD_tsl_qt.md) |
| `Framework/qt/MOD_filter_qt_v01.py` | 공용 **검색/필터** 위젯 — 입력 즉시 일치 항목만 표시, "보이는 것이 작업 대상" 헬퍼 | [Framework_MOD_filter_qt](Framework_MOD_filter_qt.md) |
| `Framework/core/maya_shape.py` | **트랜스폼 → 셰이프 확정** 헬퍼 — `extendToShape()` 가 엉뚱한 셰이프를 집는 함정을 막는다(`kInvalidParameter` 원인) | [Framework_maya_shape](Framework_maya_shape.md) |

---

## 새 문서 추가 규칙

1. **파일명은 툴 폴더명과 동일**하게 만든다. 예: `tools/A00150_Foo` → `docs/A00150_Foo.md`.
2. 문서 본문은 **한글**로 작성한다. (UI/코드 식별자·로그 예시는 영어 그대로 인용)
3. 아래 **문서 템플릿** 섹션 순서를 따른다.
4. 문서를 추가하면 위 **문서 목록** 표에 한 줄 등록한다.

---

## 문서 템플릿

각 툴 문서는 다음 순서를 표준으로 한다.

1. **개요** — 무엇을 하는 툴인지 한두 문단.
2. **폴더 구조** — 실제 파일 트리와 각 모듈의 역할(특히 core/ui 분리).
3. **설치** — 셸프 버튼 설치 방법(드래그&드롭 등).
4. **실행** — 셸프 버튼 또는 `run()` 호출 방법.
5. **UI 구성** — 화면 요소(버튼/리스트/체크박스/로그)의 의미.
6. **사용 순서** — 실제 작업 단계(①②③…).
7. **동작 규칙** — 내부 매칭/검증 규칙, 주의할 동작.
8. **로그 · 문제 해결** — 로그 메시지 예시와 자주 겪는 문제.
