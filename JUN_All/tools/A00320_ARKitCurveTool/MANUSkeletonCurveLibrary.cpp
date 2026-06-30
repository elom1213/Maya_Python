// Copyright MANU. All Rights Reserved.
//
// [배치 위치] 실제 프로젝트에 옮길 때:
//   MANUProject/Source/MANU/Utilities/MANUSkeletonCurveLibrary.cpp
//
// 의존성: 런타임 MANU 모듈에 두는 경우 추가 모듈 의존성 불필요
//         (52개 이름을 이 파일에 자체 정의 → MANUAnimation 결합 회피).
//         만약 기존 FARKitBlendShapeHelper 를 재사용하려면:
//           - MANU.Build.cs 에 "MANUAnimation" 의존성 추가
//           - 아래 GetARKitBlendShapeNames() 본문을
//             return FARKitBlendShapeHelper::GetARKitBlendShapeNames(); 로 교체

#include "MANUSkeletonCurveLibrary.h"
#include "Animation/Skeleton.h"

namespace
{
    // ARKit 표준 52개 블렌드셰이프 — LiveLink Face 앱 데이터 순서와 동일.
    // (프로젝트 기존 ARKitBlendShapeHelper.cpp 와 동일한 목록)
    const TArray<FName>& GetCachedARKitNames()
    {
        static const TArray<FName> Names = {
            // Eyes (14)
            TEXT("eyeBlinkLeft"),    TEXT("eyeBlinkRight"),
            TEXT("eyeLookDownLeft"), TEXT("eyeLookDownRight"),
            TEXT("eyeLookInLeft"),   TEXT("eyeLookInRight"),
            TEXT("eyeLookOutLeft"),  TEXT("eyeLookOutRight"),
            TEXT("eyeLookUpLeft"),   TEXT("eyeLookUpRight"),
            TEXT("eyeSquintLeft"),   TEXT("eyeSquintRight"),
            TEXT("eyeWideLeft"),     TEXT("eyeWideRight"),
            // Jaw (4)
            TEXT("jawForward"), TEXT("jawLeft"), TEXT("jawRight"), TEXT("jawOpen"),
            // Mouth (23)
            TEXT("mouthClose"),       TEXT("mouthFunnel"),       TEXT("mouthPucker"),
            TEXT("mouthLeft"),        TEXT("mouthRight"),
            TEXT("mouthSmileLeft"),   TEXT("mouthSmileRight"),
            TEXT("mouthFrownLeft"),   TEXT("mouthFrownRight"),
            TEXT("mouthDimpleLeft"),  TEXT("mouthDimpleRight"),
            TEXT("mouthStretchLeft"), TEXT("mouthStretchRight"),
            TEXT("mouthRollLower"),   TEXT("mouthRollUpper"),
            TEXT("mouthShrugLower"),  TEXT("mouthShrugUpper"),
            TEXT("mouthPressLeft"),   TEXT("mouthPressRight"),
            TEXT("mouthLowerDownLeft"), TEXT("mouthLowerDownRight"),
            TEXT("mouthUpperUpLeft"),   TEXT("mouthUpperUpRight"),
            // Brow (5)
            TEXT("browDownLeft"),  TEXT("browDownRight"), TEXT("browInnerUp"),
            TEXT("browOuterUpLeft"), TEXT("browOuterUpRight"),
            // Cheek (3)
            TEXT("cheekPuff"), TEXT("cheekSquintLeft"), TEXT("cheekSquintRight"),
            // Nose (2)
            TEXT("noseSneerLeft"), TEXT("noseSneerRight"),
            // Tongue (1)
            TEXT("tongueOut"),
        };
        return Names;
    }
}

TArray<FName> UMANUSkeletonCurveLibrary::GetARKitBlendShapeNames()
{
    return GetCachedARKitNames();
}

bool UMANUSkeletonCurveLibrary::AddMorphTargetCurve(USkeleton* Skeleton, FName CurveName)
{
    if (!Skeleton)
    {
        return false;
    }

    // 이미 존재하면 추가하지 않음 (idempotent)
    if (Skeleton->GetCurveMetaData(CurveName))
    {
        return false;
    }

#if WITH_EDITOR
    Skeleton->Modify();
#endif

    const bool bSuccess = Skeleton->AddCurveMetaData(CurveName);
    if (bSuccess)
    {
        if (FCurveMetaData* AddedCurve = Skeleton->GetCurveMetaData(CurveName))
        {
            AddedCurve->Type.bMorphtarget = true;
            AddedCurve->Type.bMaterial = false;
        }
        return true;
    }

    UE_LOG(LogTemp, Warning, TEXT("MANUSkeletonCurveLibrary: '%s' 커브 추가 실패 (%s)"),
        *CurveName.ToString(), *Skeleton->GetName());
    return false;
}

int32 UMANUSkeletonCurveLibrary::AddARKitCurvesToSkeleton(USkeleton* Skeleton)
{
    if (!Skeleton)
    {
        return 0;
    }

    int32 AddedCount = 0;
    for (const FName& CurveName : GetCachedARKitNames())
    {
        if (AddMorphTargetCurve(Skeleton, CurveName))
        {
            ++AddedCount;
        }
    }

    if (AddedCount > 0)
    {
        Skeleton->MarkPackageDirty();
        UE_LOG(LogTemp, Log, TEXT("MANUSkeletonCurveLibrary: %s 에 ARKit 커브 %d개 추가"),
            *Skeleton->GetName(), AddedCount);
    }

    return AddedCount;
}
