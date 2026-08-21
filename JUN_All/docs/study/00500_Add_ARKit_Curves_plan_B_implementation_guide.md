# B안(Python / Editor Utility) 으로 "Add ARKit Curves to Skeleton" 구현하기

> 선행 문서: `Add_ARKit_Curves_to_Skeleton_분석.md`
> 작성일: 2026-06-30
> 목적: C++ 풀 모듈(A안) 없이 스크립트 기반으로 동일 기능을 만드는 **구체적 작업 절차**

---

## 0. 결론 먼저 — B안의 현실적 형태

UE 5.5에서 `USkeleton::AddCurveMetaData()` 는 **Python/Blueprint에 기본 노출되어 있지 않다.**
따라서 "순수 Python만으로" 커브를 스켈레톤에 추가하는 것은 표준 경로로는 불가능에 가깝다.

→ **B안의 가장 현실적인 형태 = "하이브리드"**:

```
[ 얇은 C++ 래퍼 1개 ]  +  [ 두꺼운 Python / Editor Utility ]
  AddCurveMetaData를         메뉴 노출, 선택 처리, 반복,
  BlueprintCallable로 노출    결과 표시 등 나머지 전부
```

이 문서는 두 트랙을 모두 다룬다:
- **B-1 (순수 스크립트)**: Editor Utility Blueprint(AssetActionUtility) — 우클릭 메뉴까지는 코드 없이. 단, 커브 추가 단계에서 한계.
- **B-2 (하이브리드, 권장)**: 얇은 C++ `BlueprintFunctionLibrary` 래퍼 1개 + EUB/Python 호출.

---

## 1. 사전 준비 (공통)

### 1-1. Python Editor Scripting 플러그인 활성화
현재 `MANU.uproject`에 Python 관련 플러그인이 **비활성** 상태다. 먼저 켜야 한다.

- 에디터: `Edit > Plugins` → 검색 `Python` → **"Python Editor Script Plugin"** 체크 → 재시작
- 또는 `.uproject`의 `Plugins` 배열에 추가:
  ```json
  { "Name": "PythonScriptPlugin", "Enabled": true }
  ```
- (선택) `Editor Scripting Utilities` 플러그인도 함께 활성화 권장

> ⚠️ `.uproject` 는 JSON이라 Edit/Write 도구로 수정해도 안전하지만,
> 팀 공유 파일이므로 변경 시 커밋 규칙(한국어 태그) 준수.

### 1-2. Python 스크립트 폴더 생성
- `MANUProject/Content/Python/` 폴더 생성 (없으면 만든다)
- 이 경로의 `init_unreal.py` 는 에디터 시작 시 자동 실행됨 (메뉴 등록에 활용 가능)

### 1-3. 커브 이름 데이터 — 이미 존재함 (재사용)
프로젝트에 **`FARKitBlendShapeHelper::GetARKitBlendShapeNames()`** (52개 이름)가 이미 있다.
B-2 하이브리드라면 이걸 그대로 재사용하면 되고, 순수 Python이면 Python 리스트로 복제한다.

```
Plugins/MANUAnimation/Source/MANUAnimation/Private/ARKitBlendShapeHelper.cpp
```

---

## 2. 트랙 B-2 (하이브리드, 권장) — 단계별 작업

### Step 1 — 얇은 C++ 래퍼 함수 작성

기존 `MANULookDevBlueprintLibrary` (`Source/MANU/LookDev/`) 와 동일한 패턴으로
`UBlueprintFunctionLibrary` 하나에 함수 1~2개만 추가한다.

**헤더 (`MANUSkeletonCurveLibrary.h`)** — 예시
```cpp
#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MANUSkeletonCurveLibrary.generated.h"

class USkeleton;

UCLASS()
class MANU_API UMANUSkeletonCurveLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    /** 스켈레톤에 ARKit 52개 모프타겟 커브를 추가. 추가된 개수 반환. */
    UFUNCTION(BlueprintCallable, CallInEditor, Category = "MANU|Skeleton")
    static int32 AddARKitCurvesToSkeleton(USkeleton* Skeleton);

    /** 임의 커브 이름 1개 추가(모프타겟). 성공 여부 반환. */
    UFUNCTION(BlueprintCallable, CallInEditor, Category = "MANU|Skeleton")
    static bool AddMorphTargetCurve(USkeleton* Skeleton, FName CurveName);
};
```

**구현 (`MANUSkeletonCurveLibrary.cpp`)** — 핵심만
```cpp
#include "MANUSkeletonCurveLibrary.h"
#include "Animation/Skeleton.h"
#include "ARKitBlendShapeHelper.h"   // 기존 52개 이름 재사용

bool UMANUSkeletonCurveLibrary::AddMorphTargetCurve(USkeleton* Skeleton, FName CurveName)
{
    if (!Skeleton) return false;
    if (Skeleton->GetCurveMetaData(CurveName)) return false; // 중복 skip
    Skeleton->Modify();
    if (Skeleton->AddCurveMetaData(CurveName))
    {
        if (FCurveMetaData* Meta = Skeleton->GetCurveMetaData(CurveName))
            Meta->Type.bMorphtarget = true;
        return true;
    }
    return false;
}

int32 UMANUSkeletonCurveLibrary::AddARKitCurvesToSkeleton(USkeleton* Skeleton)
{
    if (!Skeleton) return 0;
    int32 Added = 0;
    for (const FName& Name : FARKitBlendShapeHelper::GetARKitBlendShapeNames())
        if (AddMorphTargetCurve(Skeleton, Name)) ++Added;
    if (Added > 0) Skeleton->MarkPackageDirty();
    return Added;
}
```

> **의존성**: 이 라이브러리가 `MANU` 모듈(런타임)에 들어간다면, `MANU.Build.cs` 에
> `MANUAnimation` 의존성을 추가해야 `ARKitBlendShapeHelper` 를 쓸 수 있다.
> (또는 52개 이름을 라이브러리 안에 직접 정의해 의존성 회피)

> **주의**: `Skeleton.h`, `AddCurveMetaData` 는 런타임 헤더에 있지만,
> `Modify()`/`MarkPackageDirty()` 같은 에디터 트랜잭션은 `WITH_EDITOR` 가드를 권장.

이후 C++ 빌드 1회 필요. (래퍼만 추가하는 것이므로 빌드는 가볍다)

---

### Step 2 — 노출 방식 선택 (둘 중 하나)

#### 방식 ① Editor Utility Blueprint (AssetActionUtility) — 우클릭 메뉴
1. Content Browser → 우클릭 → `Editor Utilities > Editor Utility Blueprint`
2. 부모 클래스 = **`AssetActionUtility`**
3. Class Settings → `Get Supported Classes`(또는 `Supported Classes`)에 **`Skeleton`** 지정
   → Skeleton 우클릭 시에만 메뉴 노출
4. 새 함수 추가 (예: `Add ARKit Curves`):
   - `Get Selected Assets In Content Browser` 노드로 선택 에셋 획득 (또는 함수 입력)
   - 각 에셋을 `Cast to Skeleton`
   - Step 1에서 만든 **`Add ARKit Curves To Skeleton`** 노드 호출
   - 결과 개수 `Print String` 또는 `Show Message Dialog`
5. 저장 후 → Content Browser에서 Skeleton 우클릭 → `Scripted Asset Actions` 하위에 항목 표시

#### 방식 ② Python 스크립트 호출
`Content/Python/add_arkit_curves.py`
```python
import unreal

def run():
    assets = unreal.EditorUtilityLibrary.get_selected_assets()
    total = 0
    skipped = 0
    for asset in assets:
        if isinstance(asset, unreal.Skeleton):
            # Step 1에서 노출한 C++ static 함수 호출
            added = unreal.MANUSkeletonCurveLibrary.add_arkit_curves_to_skeleton(asset)
            total += added
            unreal.log(f"[ARKit] {asset.get_name()}: {added}개 추가")
        else:
            skipped += 1
    unreal.log(f"[ARKit] 완료 — 총 {total}개 커브 추가, {skipped}개 에셋 스킵")

run()
```
- 실행: 에디터 `Output Log` 하단 Python 입력창 또는
  `Tools > Execute Python Script`, 또는 EUB 버튼에서 호출

> Python에서 우클릭 메뉴까지 등록하려면 `init_unreal.py` 에서
> `unreal.ToolMenus.get()` 으로 `ContentBrowser.AssetContextMenu.Skeleton` 메뉴에
> 엔트리를 추가하는 방식도 가능(고급).

---

## 3. 트랙 B-1 (순수 스크립트, 빌드 없음) — 가능 범위와 한계

C++ 빌드를 전혀 안 하고 싶다면:

- **메뉴 노출**: AssetActionUtility 로 가능 ✅
- **선택 에셋 순회 / Skeleton 판별**: BP/Python 으로 가능 ✅
- **커브 메타데이터 실제 추가**: ❌ 표준 노출 API 없음 (UE 5.5)
  - 우회: 커브가 들어있는 AnimSequence를 임포트/리타게팅하면 스켈레톤에 커브가 생기지만,
    "빈 메타데이터만 미리 등록"하는 깔끔한 순수 스크립트 경로는 사실상 없음.

> 결론: **B-1 단독으로는 핵심 기능(커브 추가)이 막힌다.**
> 그래서 B-2(얇은 C++ 래퍼 1개)가 사실상 최소 비용의 정답.

---

## 4. 검증 체크리스트

- [ ] Python 플러그인 활성 후 에디터 재시작됨
- [ ] `unreal.MANUSkeletonCurveLibrary` 가 Python에서 인식됨 (`dir(unreal.MANUSkeletonCurveLibrary)`)
- [ ] 테스트 Skeleton 우클릭 → 메뉴 노출 확인
- [ ] 실행 후 해당 Skeleton 더블클릭 → **Anim Curve(커브) 패널에 52개 표시**
- [ ] 2번 실행 시 중복 추가 없이 "0개 추가"로 나오는지 (idempotent 확인)
- [ ] Skeleton 저장(`Ctrl+S`) 가능 상태(dirty)로 표시되는지

---

## 5. 작업 순서 요약 (최단 경로)

```
1. .uproject 에 PythonScriptPlugin 활성화 + 에디터 재시작
2. UMANUSkeletonCurveLibrary (C++ 래퍼) 작성 → 빌드          [얇은 C++ 1개]
3. AssetActionUtility EUB 생성 (Supported Class = Skeleton)
     └─ 노드에서 AddARKitCurvesToSkeleton 호출 + 결과 다이얼로그
4. Skeleton 우클릭 → Scripted Asset Actions → 실행 → 검증
```

소요 난이도: **C++ 파일 2개(.h/.cpp) 추가 + EUB 1개**. A안 대비 메뉴 등록/모듈 작업이 빠진다.

---

## 6. A안 대비 장단점 재확인

| | B-2 (하이브리드) | A (C++ 풀모듈) |
|--|------------------|----------------|
| C++ 코드량 | 함수 2개 | 모듈 + 익스텐더 + 매니저 |
| 우클릭 위치 | Scripted Asset Actions 하위 | 원하는 섹션 자유 |
| 빌드 | 1회 (가벼움) | 1회 |
| 메뉴 로직 수정 | EUB/Python에서 즉시(빌드 X) | C++ 재빌드 필요 |
| 학습 가치 | 스크립트+노출 메커니즘 체득 | UE 에디터 확장 정석 |

**Maya Python 워크플로우에 익숙하다면 B-2가 학습/유지보수 균형이 가장 좋다.**
