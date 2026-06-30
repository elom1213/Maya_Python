# -*- coding: utf-8 -*-
# Copyright MANU. All Rights Reserved.
#
# [목적] C++ 프로젝트 빌드(컴파일) 없이 ARKit 커브를 스켈레톤에 인식시키는
#        "빌드 프리(build-free)" 경로를 탐색/실행하는 스크립트.
#
# 전제: Python Editor Script Plugin 활성 (그 외 C++ 컴파일 불필요)
#
# 사용:
#   1) Content Browser 에서 대상 Skeleton 1개 또는 AnimSequence 선택
#   2) Output Log 하단 Python 입력창에서:
#        exec(open(r"...nobuild_arkit_curves.py").read())
#   3) 먼저 discover_api() 로 "내 엔진이 무엇을 노출하는지" 실측 → 경로 선택
#
# 핵심: USkeleton.AddCurveMetaData 는 UFUNCTION 이 아니라 Python 미노출.
#       그래서 (A) AnimSequence 에 커브를 심거나 (B) 커브 포함 애니를 임포트하는
#       우회로를 쓴다. 둘 다 컴파일 0.

import unreal


# ---------------------------------------------------------------------------
# ARKit 52 blendshape names (LiveLink Face 순서)
# ---------------------------------------------------------------------------
ARKIT_NAMES = [
    "eyeBlinkLeft", "eyeBlinkRight", "eyeLookDownLeft", "eyeLookDownRight",
    "eyeLookInLeft", "eyeLookInRight", "eyeLookOutLeft", "eyeLookOutRight",
    "eyeLookUpLeft", "eyeLookUpRight", "eyeSquintLeft", "eyeSquintRight",
    "eyeWideLeft", "eyeWideRight",
    "jawForward", "jawLeft", "jawRight", "jawOpen",
    "mouthClose", "mouthFunnel", "mouthPucker", "mouthLeft", "mouthRight",
    "mouthSmileLeft", "mouthSmileRight", "mouthFrownLeft", "mouthFrownRight",
    "mouthDimpleLeft", "mouthDimpleRight", "mouthStretchLeft", "mouthStretchRight",
    "mouthRollLower", "mouthRollUpper", "mouthShrugLower", "mouthShrugUpper",
    "mouthPressLeft", "mouthPressRight", "mouthLowerDownLeft", "mouthLowerDownRight",
    "mouthUpperUpLeft", "mouthUpperUpRight",
    "browDownLeft", "browDownRight", "browInnerUp", "browOuterUpLeft", "browOuterUpRight",
    "cheekPuff", "cheekSquintLeft", "cheekSquintRight",
    "noseSneerLeft", "noseSneerRight",
    "tongueOut",
]
assert len(ARKIT_NAMES) == 52


# ---------------------------------------------------------------------------
# 0) API 탐색 — 내 엔진이 실제로 무엇을 노출하는지 출력 (추측 대신 실측)
# ---------------------------------------------------------------------------
def discover_api():
    """현재 에디터에서 커브 관련으로 호출 가능한 API를 출력한다."""
    unreal.log("================ API DISCOVERY ================")

    # USkeleton 에 curve/metadata 관련 노출 메서드가 있나?
    sk_methods = [m for m in dir(unreal.Skeleton)
                  if ("curve" in m.lower() or "metadata" in m.lower())]
    unreal.log("unreal.Skeleton curve/metadata methods: {0}".format(sk_methods or "(없음)"))

    # AnimationLibrary 의 curve 함수 (경로 2 가능 여부)
    has_anim_lib = hasattr(unreal, "AnimationLibrary")
    unreal.log("unreal.AnimationLibrary 존재: {0}".format(has_anim_lib))
    if has_anim_lib:
        curve_fns = [m for m in dir(unreal.AnimationLibrary) if "curve" in m.lower()]
        unreal.log("  AnimationLibrary curve 함수: {0}".format(curve_fns or "(없음)"))

    # AssetImportTask (경로 1: 임포트 자동화 가능 여부)
    unreal.log("unreal.AssetImportTask 존재: {0}".format(hasattr(unreal, "AssetImportTask")))
    unreal.log("===============================================")


# ---------------------------------------------------------------------------
# 경로 2) AnimSequence 에 52개 커브를 심기 (순수 Python, 컴파일 0)
#   - 선택한 AnimSequence(들)에 ARKit 커브를 추가.
#   - 엔진/버전에 따라 스켈레톤 메타데이터로 전파되는지는 discover 후 검증할 것.
# ---------------------------------------------------------------------------
def add_curves_to_selected_animsequences():
    selected = unreal.EditorUtilityLibrary.get_selected_assets()
    targets = [a for a in selected if isinstance(a, unreal.AnimSequence)]

    if not targets:
        unreal.log_warning("AnimSequence 를 선택해주세요. (경로 2 는 애니메이션에 커브를 심습니다)")
        return

    if not hasattr(unreal, "AnimationLibrary"):
        unreal.log_error("unreal.AnimationLibrary 미노출 — 경로 2 사용 불가. 경로 1(임포트) 사용.")
        return

    for anim in targets:
        added = 0
        for name in ARKIT_NAMES:
            try:
                # metadata=True → 상수(메타데이터) 커브로 추가. (값 변동 없는 등록 목적)
                unreal.AnimationLibrary.add_curve(
                    anim,
                    name,
                    unreal.AnimationCurveType.ATTRIBUTE_CURVE,
                    True,  # metadata
                )
                added += 1
            except Exception as exception_error:
                unreal.log_warning("  '{0}' 추가 실패: {1}".format(name, exception_error))
        unreal.EditorAssetLibrary.save_loaded_asset(anim, only_if_is_dirty=True)
        unreal.log("[경로2] {0}: {1}개 커브 추가".format(anim.get_name(), added))


# ---------------------------------------------------------------------------
# 경로 1) 커브 포함 FBX/애니 임포트로 스켈레톤 자동 등록 (코드/컴파일 0)
#   - 아래는 자동화 골격. fbx_path 와 target_skeleton 만 채우면 동작.
#   - 임포트되는 애니에 52개 모프타겟 커브가 들어있어야 스켈레톤이 등록함.
# ---------------------------------------------------------------------------
def import_arkit_anim(fbx_path, destination_path, target_skeleton_path):
    """ARKit 커브가 든 FBX 애니를 대상 스켈레톤으로 임포트한다."""
    task = unreal.AssetImportTask()
    task.filename = fbx_path
    task.destination_path = destination_path
    task.automated = True
    task.save = True
    task.replace_existing = True

    options = unreal.FbxImportUI()
    options.import_animations = True
    options.import_mesh = False
    options.skeleton = unreal.load_asset(target_skeleton_path)
    task.options = options

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    unreal.log("[경로1] 임포트 완료 → 스켈레톤이 커브 이름을 자동 등록했는지 확인하세요.")


# ---------------------------------------------------------------------------
# 진입점
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # 1단계: 먼저 내 엔진이 무엇을 노출하는지 확인
    discover_api()
    # 2단계: 결과를 보고 아래 중 하나를 직접 호출
    #   add_curves_to_selected_animsequences()          # 경로 2
    #   import_arkit_anim(r"D:/arkit.fbx", "/Game/Anim", "/Game/.../SK_Skeleton")  # 경로 1
