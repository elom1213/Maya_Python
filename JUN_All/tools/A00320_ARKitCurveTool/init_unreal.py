# -*- coding: utf-8 -*-
# Copyright MANU. All Rights Reserved.
#
# [배치 위치] 실제 프로젝트에 옮길 때:
#   MANUProject/Content/Python/init_unreal.py
#   (이 파일명은 약속된 이름 — 에디터 시작 시 자동 실행됨)
#
# 용도: Skeleton 우클릭 컨텍스트 메뉴에 "Add ARKit Curves to Skeleton" 항목을
#       순수 Python(ToolMenus API)으로 등록. C++ 메뉴 익스텐더 없이 우클릭 노출.
#
# 전제:
#   - Python Editor Script Plugin 활성
#   - UMANUSkeletonCurveLibrary (C++ 래퍼) 빌드됨
#   - 같은 폴더의 add_arkit_curves.py 가 import 가능해야 함

import unreal

MENU_PATH = "ContentBrowser.AssetContextMenu.Skeleton"  # Skeleton 전용 컨텍스트 메뉴
SECTION_NAME = "MANUTools"
ENTRY_NAME = "MANUAddARKitCurves"


@unreal.uclass()
class MANUAddARKitCurvesEntry(unreal.ToolMenuEntryScript):
    """우클릭 메뉴 클릭 시 실행되는 엔트리."""

    @unreal.ufunction(override=True)
    def execute(self, context):
        # 지연 import: 에디터 부팅 순서 안전성 확보
        try:
            import add_arkit_curves
            import importlib
            importlib.reload(add_arkit_curves)
            add_arkit_curves.add_arkit_curves_to_selected()
        except Exception as exception_error:
            unreal.log_error(u"[ARKit] 실행 실패: {0}".format(exception_error))


def register_menu():
    tool_menus = unreal.ToolMenus.get()
    menu = tool_menus.find_menu(MENU_PATH)
    if not menu:
        unreal.log_warning(u"[ARKit] 메뉴를 찾지 못함: {0}".format(MENU_PATH))
        return

    menu.add_section(SECTION_NAME, unreal.Text.from_string(u"MANU Tools"))

    entry = MANUAddARKitCurvesEntry()
    entry.init_entry(
        owner_name=ENTRY_NAME,
        menu=MENU_PATH,
        section=SECTION_NAME,
        name=ENTRY_NAME,
        label=unreal.Text.from_string(u"Add ARKit Curves to Skeleton"),
        tool_tip=unreal.Text.from_string(
            u"선택된 스켈레톤에 ARKit 52개 블렌드셰이프 커브를 추가합니다."
        ),
    )
    entry.register_menu_entry()

    tool_menus.refresh_all_widgets()
    unreal.log(u"[ARKit] 우클릭 메뉴 등록 완료")


# init_unreal.py 는 에디터 시작 시 자동 실행됨
register_menu()
