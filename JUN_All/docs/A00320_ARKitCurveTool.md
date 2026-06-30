# A00320_ARKitCurveTool 사용법

> ⚠️ 이 항목은 **Maya 셸프 툴이 아니다.** Unreal Engine 5.5 의 *"Skeleton 우클릭 → Add ARKit Curves to
> Skeleton"* 기능을 **재현하기 위한 참조/이식 코드 모음**이다. 실제 적용은 사용자가 Unreal 프로젝트에
> 직접 복사·설치한다(이 저장소는 원본 코드를 보관·문서화하는 용도).

## 1. 개요

Unreal Content Browser 에서 **Skeleton 을 우클릭하면 나타나는 "Add ARKit Curves to Skeleton"** 기능을
분석하고, 같은 동작을 **직접 만들 수 있도록** 코드와 가이드를 정리한 모음이다.

- 동작 요지: 선택한 스켈레톤에 **Apple ARKit 표준 52개 블렌드셰이프 커브 메타데이터**를 일괄 등록한다.
  이게 있어야 LiveLink Face(iPhone) 등에서 들어오는 `eyeBlinkLeft`, `jawOpen` 같은 모프타겟 커브가 인식된다.
- 핵심 제약: UE 5.5 에서 `USkeleton::AddCurveMetaData()` 는 `UFUNCTION` 이 아니라 **Python/Blueprint 에
  직접 노출되지 않는다.** 그래서 두 가지 접근을 함께 제공한다.
  1. **하이브리드(B-2)** — 얇은 C++ 래퍼 1개를 노출시키고, 메뉴/반복/결과는 Python 으로 처리(빌드 1회 필요).
  2. **빌드-프리** — 커브 포함 애니 임포트 / `unreal.AnimationLibrary` 경로(컴파일 0, 단 버전별 실측 필요).

상세 설계·분석은 학습 노트 참고:
[Add_ARKit_Curves_to_Skeleton_분석](study/Add_ARKit_Curves_to_Skeleton_분석.md) ·
[Add_ARKit_Curves_B안_구현가이드](study/Add_ARKit_Curves_B안_구현가이드.md)

---

## 2. 폴더 구조

```
A00320_ARKitCurveTool/
├── README.md                    # 설치 순서 · 검증 체크리스트 · Maya↔UE 대응표
├── MANUSkeletonCurveLibrary.h   # C++ 래퍼 헤더 — AddCurveMetaData 를 BP/Python 에 노출
├── MANUSkeletonCurveLibrary.cpp # 래퍼 구현 (ARKit 52개 이름 자체 포함, 외부 모듈 의존 없음)
├── add_arkit_curves.py          # 선택 스켈레톤에 52개 커브 일괄 추가 (C++ 래퍼 호출)
├── init_unreal.py               # Skeleton 우클릭 메뉴 자동 등록 (ToolMenus, 에디터 시작 시 실행)
└── nobuild_arkit_curves.py      # 빌드-프리 경로 탐색/실행 (API discover + 임포트/AnimationLibrary)
```

| 파일 | 역할 | Unreal 내 권장 위치 |
|------|------|---------------------|
| `MANUSkeletonCurveLibrary.h/.cpp` | C++ 래퍼(핵심) | `<Project>/Source/<Module>/Utilities/` |
| `add_arkit_curves.py` | 실행 스크립트 | `<Project>/Content/Python/` |
| `init_unreal.py` | 우클릭 메뉴 등록 | `<Project>/Content/Python/` |
| `nobuild_arkit_curves.py` | 빌드 없는 우회로 PoC | `<Project>/Content/Python/` |

---

## 3. 적용 (설치)

### 3.1 하이브리드(B-2) — 권장
1. **Python 플러그인 활성화**: `Edit > Plugins > Python Editor Script Plugin` → 에디터 재시작.
2. **C++ 래퍼 이식 + 빌드**: `MANUSkeletonCurveLibrary.h/.cpp` 를 프로젝트 `Source/.../Utilities/` 에 복사 후 빌드.
   - 확인: Python 에서 `dir(unreal.MANUSkeletonCurveLibrary)` 에 `add_arkit_curves_to_skeleton` 노출.
3. **Python 이식**: `add_arkit_curves.py`, `init_unreal.py` 를 `Content/Python/` 에 복사 → 에디터 재시작.
4. **실행**: Content Browser 에서 Skeleton 우클릭 → **MANU Tools > Add ARKit Curves to Skeleton**.

### 3.2 빌드-프리 (컴파일 없이)
`nobuild_arkit_curves.py` 를 에디터 Python 창에서 실행:
- `discover_api()` — 현재 엔진이 노출하는 커브 관련 API 를 출력(실측).
- **경로 1(임포트)**: ARKit 52 커브가 든 FBX/애니를 대상 스켈레톤으로 임포트 → 엔진이 커브 자동 등록(가장 확실).
- **경로 2(AnimationLibrary)**: `unreal.AnimationLibrary.add_curve()` 로 AnimSequence 에 커브를 심음(순수 Python).

---

## 4. 동작 규칙

- **커브 목록**: ARKit 52개(Eyes 14 / Jaw 4 / Mouth 23 / Brow 5 / Cheek 3 / Nose 2 / Tongue 1), LiveLink Face 순서.
- **idempotent**: 이미 존재하는 커브는 건너뛴다(재실행해도 중복 추가 없음).
- **타입**: 추가되는 커브는 `bMorphtarget = true` 로 표시된다.
- **메뉴 노출 조건**: 선택 에셋에 클래스가 `Skeleton` 인 것이 있을 때만 항목이 보인다.
- **바닐라 호환**: 스톡 `unreal` API 만 사용 — 커스텀 엔진에 의존하지 않는다(바닐라 UE 5.5 에서 동작).

---

## 5. 문제 해결

- `unreal.MANUSkeletonCurveLibrary` 미인식 → C++ 빌드가 안 됐거나 Python 플러그인 미활성. 빌드 후 에디터 재시작.
- 우클릭 메뉴 안 보임 → `init_unreal.py` 가 `Content/Python/` 에 있는지, 에디터 재시작 했는지 확인.
- 빌드-프리에서 커브가 스켈레톤에 안 잡힘 → 경로 2 는 버전 의존적. `discover_api()` 로 확인 후 경로 1(임포트)로 전환.

> **요약**: Content Browser 익스텐더로 Skeleton 우클릭 메뉴를 추가하고, `USkeleton::AddCurveMetaData()` 로
> ARKit 52개 모프타겟 커브 메타데이터를 일괄 등록하는 에디터 기능. 핵심은 "얇은 C++ 래퍼 + 두꺼운 Python".
