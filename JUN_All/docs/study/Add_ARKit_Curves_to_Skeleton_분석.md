# "Add ARKit Curves to Skeleton" 기능 분석 및 구현 가이드

> 분석 대상: MANUProject (UE 5.5) Content Browser 우클릭 메뉴
> 작성일: 2026-06-30
> 목적: 기존 구현 구조 이해 + 직접 만드는 방법 제안

---

## 1. 기능 개요

Content Browser에서 **Skeleton 에셋을 우클릭** → `MANU Tools` → **`Add ARKit Curves to Skeleton`** 을 선택하면,
선택한 스켈레톤에 **Apple ARKit 표준 52개 블렌드셰이프(blendshape) 커브 메타데이터**가 한 번에 등록된다.

이 커브들이 스켈레톤에 등록되어 있어야 LiveLink Face(iPhone) 데이터나 애니메이션에서 들어오는
`eyeBlinkLeft`, `jawOpen` 같은 이름의 모프타겟 커브가 정상적으로 인식·구동된다.

핵심 동작:
- 선택된 에셋 중 클래스가 `Skeleton`인 것만 처리 (나머지는 실패 카운트)
- 52개 커브 이름을 순회하며 스켈레톤에 `CurveMetaData`로 추가
- 이미 존재하는 커브는 건너뜀(skip)
- 커브 타입은 `bMorphtarget = true`로 설정
- 변경된 스켈레톤을 dirty 표시 → 사용자가 저장 가능
- 결과(성공/실패 개수)를 메시지 다이얼로그로 표시

---

## 2. 아키텍처 — 어디에 무엇이 있나

이 기능은 **2개 플러그인, 3개 모듈**에 걸쳐 분업되어 있다.

```
[ MANUEditor 플러그인 / MANUEditor 모듈 (Editor) ]
   └─ MANUEditor.cpp
        ├─ 메뉴 등록 (Content Browser 컨텍스트 메뉴 확장)
        └─ "Add ARKit Curves to Skeleton" 항목 클릭 → ARKitCurveManager 호출

[ MANUAnimation 플러그인 / MANUAnimationEd 모듈 (Editor) ]
   └─ ARKitCurveManager.h / .cpp
        └─ 실제 스켈레톤에 커브를 추가하는 로직

[ MANUAnimation 플러그인 / MANUAnimation 모듈 (Runtime) ]
   └─ ARKitBlendShapeHelper.h / .cpp
        └─ ARKit 52개 블렌드셰이프 "이름" 데이터의 단일 출처(Single Source of Truth)
```

| 역할 | 파일 | 모듈 |
|------|------|------|
| 메뉴 UI 등록 + 클릭 핸들러 | `Plugins/MANUEditor/Source/MANUEditor/Private/MANUEditor.cpp` | MANUEditor (Editor) |
| 커브 추가 비즈니스 로직 | `Plugins/MANUAnimation/Source/MANUAnimationEd/Private/ARKitCurveManager.cpp` | MANUAnimationEd (Editor) |
| 52개 커브 이름 데이터 | `Plugins/MANUAnimation/Source/MANUAnimation/Private/ARKitBlendShapeHelper.cpp` | MANUAnimation (Runtime) |

> **왜 이렇게 나눴나?** 커브 이름 목록(`ARKitBlendShapeHelper`)을 Runtime 모듈에 두면,
> 에디터 툴뿐 아니라 런타임 LiveLink 처리(`ARKitFacialPreProcessor`)에서도 같은 목록을 재사용할 수 있다.
> 즉 "이름 정의 중복 방지"가 목적. 메뉴(UI)와 로직(Manager)을 분리한 것은 단일 책임 원칙(SRP).

---

## 3. 실행 흐름 (Call Flow)

```
사용자 우클릭
  │
  ▼
FMANUEditorModule::StartupModule()                       [모듈 로드 시 1회 등록]
  └─ ContentBrowserModule.GetAllAssetViewContextMenuExtenders()
       .Add( OnExtendContentBrowserAssetSelectionMenu )
  │
  ▼
OnExtendContentBrowserAssetSelectionMenu(SelectedAssets) [우클릭마다 호출]
  └─ Extender->AddMenuExtension("GetAssetActions", After, ... AddContentBrowserAssetActions)
  │
  ▼
AddContentBrowserAssetActions(MenuBuilder, SelectedAssets)
  └─ "MANU Tools" 서브메뉴 생성
       └─ 선택 에셋 중 Skeleton 존재 여부 검사 (bHasSkeleton)
            └─ true면 "Add ARKit Curves to Skeleton" 메뉴 엔트리 추가
                 └─ 클릭 시 FUIAction 람다 실행
                      │
                      ▼
ARKitCurveManager->AddARKitCurvesToSkeletons(SelectedAssets)   [MANUAnimationEd]
  └─ for each AssetData:
       ├─ 클래스가 "Skeleton"인지 확인
       ├─ Cast<USkeleton>(AssetData.GetAsset())
       └─ AddARKitCurvesToSkeleton(Skeleton)
            └─ FARKitBlendShapeHelper::GetARKitBlendShapeNames() 로 52개 이름 획득
                 └─ for each CurveName:
                      └─ AddCurveToSkeleton(Skeleton, CurveName)
                           ├─ GetCurveMetaData() → 이미 있으면 skip
                           ├─ Skeleton->Modify()
                           ├─ Skeleton->AddCurveMetaData(CurveName)
                           └─ AddedCurve->Type.bMorphtarget = true
            └─ AddedCount > 0 이면 Skeleton->MarkPackageDirty()
  └─ FMessageDialog 로 성공/실패 결과 표시
```

---

## 4. 핵심 코드 해설

### 4-1. 메뉴 등록 — `MANUEditor.cpp` `StartupModule()`

UE 에디터의 Content Browser는 "익스텐더(Extender) 델리게이트"를 등록하면,
우클릭 메뉴를 만들 때마다 그 델리게이트를 호출해 메뉴를 추가할 기회를 준다.

```cpp
// 모듈 시작 시 1회: Content Browser에 "에셋 선택 컨텍스트 메뉴 익스텐더"를 등록
FContentBrowserModule& ContentBrowserModule =
    FModuleManager::LoadModuleChecked<FContentBrowserModule>("ContentBrowser");

TArray<FContentBrowserMenuExtender_SelectedAssets>& AssetExtenders =
    ContentBrowserModule.GetAllAssetViewContextMenuExtenders();
AssetExtenders.Add(FContentBrowserMenuExtender_SelectedAssets::CreateRaw(
    this, &FMANUEditorModule::OnExtendContentBrowserAssetSelectionMenu));
```

### 4-2. 익스텐더 → 메뉴 빌더 연결

```cpp
TSharedRef<FExtender> FMANUEditorModule::OnExtendContentBrowserAssetSelectionMenu(
    const TArray<FAssetData>& SelectedAssets)
{
    TSharedRef<FExtender> Extender = MakeShared<FExtender>();
    Extender->AddMenuExtension(
        "GetAssetActions",          // 기존 "Asset Actions" 섹션 다음에 끼워넣기
        EExtensionHook::After,
        nullptr,
        FMenuExtensionDelegate::CreateRaw(
            this, &FMANUEditorModule::AddContentBrowserAssetActions, SelectedAssets));
    return Extender;
}
```

### 4-3. 실제 메뉴 항목 생성 (조건부 표시)

```cpp
// "MANU Tools" 서브메뉴 안에서 ...
// Skeleton 에셋이 하나라도 선택됐는지 확인
bool bHasSkeleton = false;
for (const FAssetData& Asset : SelectedAssets)
{
    if (Asset.AssetClassPath.GetAssetName().ToString() == TEXT("Skeleton"))
    {
        bHasSkeleton = true;
        break;
    }
}

// Skeleton일 때만 메뉴 노출 (UX: 관련 없는 에셋엔 안 보이게)
if (bHasSkeleton)
{
    SubMenuBuilder.AddMenuEntry(
        FText::FromString(TEXT("Add ARKit Curves to Skeleton")),
        FText::FromString(TEXT("선택된 스켈레톤에 ARKit 52개 블렌드셰이프 커브를 추가합니다.")),
        FSlateIcon(FAppStyle::GetAppStyleSetName(), "Persona.AnimCurveViewer"),
        FUIAction(FExecuteAction::CreateLambda([this, SelectedAssets]()
        {
            ARKitCurveManager->AddARKitCurvesToSkeletons(SelectedAssets);
        }))
    );
}
```

### 4-4. 커브 추가 핵심 — `ARKitCurveManager.cpp`

가장 중요한 UE API 부분. **`Skeleton->AddCurveMetaData(CurveName)`** 가 실제로 커브를 등록한다.

```cpp
bool FARKitCurveManager::AddCurveToSkeleton(USkeleton* Skeleton, const FName& CurveName)
{
    // 1) 중복 방지: 이미 있으면 skip
    const FCurveMetaData* ExistingCurve = Skeleton->GetCurveMetaData(CurveName);
    if (ExistingCurve) return false;

    // 2) 트랜잭션/undo를 위해 Modify() 호출
    Skeleton->Modify();

    // 3) 커브 메타데이터 추가 (UE 5.5 API)
    const bool bSuccess = Skeleton->AddCurveMetaData(CurveName);

    // 4) 추가된 커브를 "모프타겟 타입"으로 표시
    if (bSuccess)
    {
        FCurveMetaData* AddedCurve = Skeleton->GetCurveMetaData(CurveName);
        if (AddedCurve)
        {
            AddedCurve->Type.bMorphtarget = true;
            AddedCurve->Type.bMaterial = false;
        }
        return true;
    }
    return false;
}
```

마지막에 변경 사항이 있으면 패키지를 dirty 표시:

```cpp
if (AddedCount > 0)
{
    Skeleton->MarkPackageDirty();  // 저장 가능 상태로 만듦
}
```

### 4-5. 52개 이름 데이터 — `ARKitBlendShapeHelper.cpp`

LiveLink Face 앱 데이터 순서와 동일하게 정렬된 52개 `FName` 배열.
지연 초기화(lazy init) + static 캐시로 1회만 생성한다.

```
Eyes   (14): eyeBlinkLeft, eyeBlinkRight, eyeLookDownLeft ... eyeWideRight
Jaw    ( 4): jawForward, jawLeft, jawRight, jawOpen
Mouth  (22): mouthClose, mouthFunnel ... mouthUpperUpRight
Brow   ( 5): browDownLeft, browDownRight, browInnerUp, browOuterUpLeft, browOuterUpRight
Cheek  ( 3): cheekPuff, cheekSquintLeft, cheekSquintRight
Nose   ( 2): noseSneerLeft, noseSneerRight
Tongue ( 1): tongueOut
─────────────
합계 52개
```

---

## 5. 모듈 의존성 (Build.cs)

`MANUEditor.Build.cs`의 `PrivateDependencyModuleNames`:

```csharp
"MANUAnimationEd",  // ARKitCurveManager 사용을 위해
"MANU",             // (다른 기능용)
...
```

- `MANUEditor` → `MANUAnimationEd` (Manager 클래스 사용)
- `MANUAnimationEd` → `MANUAnimation` (`ARKitBlendShapeHelper` 사용)

따라서 의존 방향: **MANUEditor → MANUAnimationEd → MANUAnimation(Runtime)**

---

## 6. 직접 만든다면 — 구현 제안

이 기능을 **처음부터 직접 구현**한다고 가정한 단계별 가이드. (UE 5.5 C++ 기준)

### 방법 A: C++ 에디터 모듈 (현재 MANU 방식, 권장 — 정석)

**전제**: 에디터 전용 모듈이 필요하다 (`Type: Editor`). Runtime 모듈에서는 Content Browser 확장 불가.

#### Step 1 — 에디터 모듈 준비
- `.uplugin` 또는 `.Build.cs`에 에디터 모듈 추가
- `Build.cs` 의존성:
  ```csharp
  PrivateDependencyModuleNames.AddRange(new[] {
      "UnrealEd", "ContentBrowser", "ToolMenus",
      "Slate", "SlateCore", "AssetRegistry", "Engine"
  });
  ```

#### Step 2 — 커브 이름 데이터 정의
- `static const TArray<FName>` 또는 헬퍼 클래스로 52개 이름 정의
- (MANU처럼 Runtime 모듈에 두면 런타임에서도 재사용 가능)

#### Step 3 — Content Browser 메뉴 확장 등록 (`StartupModule`)
```cpp
FContentBrowserModule& CBModule =
    FModuleManager::LoadModuleChecked<FContentBrowserModule>("ContentBrowser");
CBModule.GetAllAssetViewContextMenuExtenders()
    .Add(FContentBrowserMenuExtender_SelectedAssets::CreateRaw(
        this, &FMyModule::OnExtendMenu));
```
> **주의**: `ShutdownModule()`에서 반드시 `RemoveAll`로 익스텐더를 제거해야 핫리로드/언로드 시 크래시가 없다. (MANU도 그렇게 함)

#### Step 4 — 메뉴 항목 추가 + Skeleton 필터링
- 선택 에셋의 `AssetClassPath.GetAssetName() == "Skeleton"` 확인 후 조건부로 메뉴 노출

#### Step 5 — 커브 추가 로직
```cpp
for (const FName& Name : ARKitNames)
{
    if (Skeleton->GetCurveMetaData(Name)) continue;  // 중복 skip
    Skeleton->Modify();
    if (Skeleton->AddCurveMetaData(Name))
    {
        if (FCurveMetaData* Meta = Skeleton->GetCurveMetaData(Name))
            Meta->Type.bMorphtarget = true;
    }
}
Skeleton->MarkPackageDirty();
```

#### Step 6 — 결과 피드백
- `FMessageDialog::Open()`으로 성공/실패 개수 표시 (선택적으로 `FScopedSlowTask` 진행바)

---

### 방법 B: Editor Utility Blueprint / Python (코드 빌드 없이 — 빠른 프로토타입)

C++ 빌드 환경 없이 **에디터 스크립팅**만으로도 거의 동일하게 가능하다.
Maya Python에 익숙하다면 이 방식이 이해가 빠를 수 있다.

#### Python (Unreal Editor의 Python 스크립트)
```python
import unreal

ARKIT_NAMES = [
    "eyeBlinkLeft", "eyeBlinkRight", "eyeLookDownLeft", # ... 총 52개
    "jawOpen", "mouthClose", "tongueOut",
]

# Content Browser에서 선택된 에셋 가져오기
selected = unreal.EditorUtilityLibrary.get_selected_assets()
for asset in selected:
    if isinstance(asset, unreal.Skeleton):
        # UE 버전에 따라 노출 API가 다름.
        # 5.5에서는 AnimationLibrary / SkeletonModifier 또는
        # 커스텀 C++ BlueprintFunctionLibrary를 통해 AddCurveMetaData 호출 필요.
        unreal.log(f"Add ARKit curves to: {asset.get_name()}")
```

> **한계**: `USkeleton::AddCurveMetaData`는 기본적으로 Python에 직접 노출되지 않을 수 있다.
> 그 경우 C++로 `UFUNCTION(BlueprintCallable)` 래퍼 하나만 만들어 Python/BP에서 호출하는
> **하이브리드 방식**이 가장 현실적이다. (얇은 C++ + 두꺼운 스크립트)

#### 우클릭 메뉴로 노출하려면
- **Asset Action Utility** (`AssetActionUtility` 기반 Editor Utility Blueprint)를 만들면
  C++ 없이도 Content Browser 우클릭 → Scripted Asset Actions 에 항목이 생긴다.
- `Get Supported Class`를 `Skeleton`으로 지정하면 Skeleton에서만 표시됨.

---

## 7. 두 방식 비교 / 추천

| 항목 | 방법 A (C++ 모듈) | 방법 B (Python/EUB) |
|------|------------------|---------------------|
| 빌드 필요 | O (C++ 컴파일) | X (또는 얇은 래퍼만) |
| 우클릭 위치 자유도 | 높음 (원하는 섹션에) | 보통 (Scripted Actions 하위) |
| 배포/재사용 | 플러그인으로 깔끔 | 에셋/스크립트 관리 필요 |
| 진입 난이도 | 높음 | 낮음 (Maya Python 경험자 친화) |
| MANU 채택 방식 | **이것** | — |

**추천 경로**:
1. **빠른 검증/학습** → 방법 B(Python + AssetActionUtility)로 동작 원리 체득
2. **실제 팀 배포** → 방법 A(C++ 모듈)로 정식 구현 (MANU 구조 그대로 참고)
3. **절충안** → 커브 추가 로직만 C++ `BlueprintCallable` 함수로 만들고,
   메뉴/반복 처리는 Python에서 호출 (유지보수성 + 노출 용이성 균형)

---

## 8. 참고 파일 경로 (원본)

```
Plugins/MANUEditor/Source/MANUEditor/Private/MANUEditor.cpp              # 메뉴 등록
Plugins/MANUEditor/Source/MANUEditor/MANUEditor.Build.cs                # 의존성
Plugins/MANUAnimation/Source/MANUAnimationEd/Public/ARKitCurveManager.h
Plugins/MANUAnimation/Source/MANUAnimationEd/Private/ARKitCurveManager.cpp  # 커브 추가 로직
Plugins/MANUAnimation/Source/MANUAnimation/Public/ARKitBlendShapeHelper.h
Plugins/MANUAnimation/Source/MANUAnimation/Private/ARKitBlendShapeHelper.cpp  # 52개 이름
```

## 9. 핵심 요약 (한 줄)

> **Content Browser 익스텐더로 Skeleton 우클릭 메뉴를 추가하고, 클릭 시
> `USkeleton::AddCurveMetaData()`로 ARKit 52개 모프타겟 커브 메타데이터를 일괄 등록하는 에디터 툴.**
