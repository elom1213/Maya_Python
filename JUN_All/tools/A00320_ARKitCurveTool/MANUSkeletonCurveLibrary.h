// Copyright MANU. All Rights Reserved.
//
// [배치 위치] 실제 프로젝트에 옮길 때:
//   MANUProject/Source/MANU/Utilities/MANUSkeletonCurveLibrary.h
// (또는 별도 에디터 모듈. 런타임 MANU 모듈에 둘 경우 WITH_EDITOR 가드 유지)
//
// 목적: USkeleton::AddCurveMetaData() 를 Blueprint/Python 에 노출하는 얇은 래퍼.
//       이것만 있으면 메뉴/순회/결과표시는 전부 Python/EUB 에서 처리 가능(B-2 하이브리드).

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MANUSkeletonCurveLibrary.generated.h"

class USkeleton;

/**
 * 스켈레톤에 모프타겟(블렌드셰이프) 커브 메타데이터를 추가하는 BlueprintFunctionLibrary.
 * ARKit 표준 52개 블렌드셰이프 일괄 추가 및 임의 커브 단건 추가를 지원합니다.
 *
 * Python 사용 예:
 *   import unreal
 *   skeleton = unreal.EditorUtilityLibrary.get_selected_assets()[0]
 *   added = unreal.MANUSkeletonCurveLibrary.add_arkit_curves_to_skeleton(skeleton)
 */
UCLASS()
class MANU_API UMANUSkeletonCurveLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    /**
     * 스켈레톤에 ARKit 52개 모프타겟 커브를 일괄 추가합니다. (이미 있는 커브는 건너뜀)
     * @param Skeleton - 대상 스켈레톤
     * @return 실제로 새로 추가된 커브 개수 (0이면 이미 모두 존재하거나 실패)
     */
    UFUNCTION(BlueprintCallable, CallInEditor, Category = "MANU|Skeleton")
    static int32 AddARKitCurvesToSkeleton(USkeleton* Skeleton);

    /**
     * 스켈레톤에 임의의 모프타겟 커브 1개를 추가합니다.
     * @param Skeleton - 대상 스켈레톤
     * @param CurveName - 추가할 커브 이름
     * @return 새로 추가되었으면 true, 이미 존재하거나 실패면 false
     */
    UFUNCTION(BlueprintCallable, CallInEditor, Category = "MANU|Skeleton")
    static bool AddMorphTargetCurve(USkeleton* Skeleton, FName CurveName);

    /**
     * ARKit 표준 52개 블렌드셰이프 이름 목록을 반환합니다. (Python/BP 에서 조회용)
     * @return 52개 FName 배열
     */
    UFUNCTION(BlueprintPure, Category = "MANU|Skeleton")
    static TArray<FName> GetARKitBlendShapeNames();
};
