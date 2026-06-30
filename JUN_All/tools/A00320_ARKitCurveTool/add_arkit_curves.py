# -*- coding: utf-8 -*-
# Copyright MANU. All Rights Reserved.
#
# [배치 위치] 실제 프로젝트에 옮길 때:
#   MANUProject/Content/Python/add_arkit_curves.py
#
# 용도: Content Browser 에서 선택한 Skeleton 들에 ARKit 52개 모프타겟 커브를 일괄 추가.
# 전제: UMANUSkeletonCurveLibrary (C++ 래퍼) 가 빌드되어 있어야 함.
#       (Python Editor Script Plugin 활성 + 프로젝트 C++ 빌드 1회)
#
# 실행 방법 3가지:
#   1) Output Log 하단 Python 입력창:   exec(open(r"...add_arkit_curves.py").read())
#   2) Tools > Execute Python Script... 로 이 파일 선택
#   3) init_unreal.py 가 등록한 우클릭 메뉴에서 호출 (권장)

import unreal


def add_arkit_curves_to_selected():
    """Content Browser 선택 에셋 중 Skeleton 에 ARKit 커브를 추가하고 결과를 반환."""
    selected_assets = unreal.EditorUtilityLibrary.get_selected_assets()

    if not selected_assets:
        _notify(u"스켈레톤을 선택해주세요.")
        return

    total_added = 0
    skeleton_count = 0
    skipped_assets = []

    for asset in selected_assets:
        if isinstance(asset, unreal.Skeleton):
            added = unreal.MANUSkeletonCurveLibrary.add_arkit_curves_to_skeleton(asset)
            total_added += added
            skeleton_count += 1
            unreal.log(u"[ARKit] {0}: {1}개 추가".format(asset.get_name(), added))

            # 변경된 에셋 저장(선택). 자동 저장을 원치 않으면 아래 줄 주석 처리.
            unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=True)
        else:
            skipped_assets.append(asset.get_name())

    # 결과 메시지 구성
    message = u"완료\n\n"
    message += u"처리한 스켈레톤: {0}개\n".format(skeleton_count)
    message += u"새로 추가된 커브: 총 {0}개\n".format(total_added)
    if skeleton_count > 0 and total_added == 0:
        message += u"\n(모든 커브가 이미 존재합니다)"
    if skipped_assets:
        message += u"\n\n스킵된 비-스켈레톤 에셋: {0}개".format(len(skipped_assets))

    unreal.log(message.replace(u"\n", u" "))
    _notify(message)


def _notify(text):
    """에디터 상단 알림 + 로그."""
    try:
        unreal.EditorDialog.show_message(
            u"ARKit Curve Tool",
            text,
            unreal.AppMsgType.OK,
        )
    except Exception:
        # EditorDialog 미지원 환경 fallback
        unreal.log_warning(text)


if __name__ == "__main__":
    add_arkit_curves_to_selected()
