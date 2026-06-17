# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-17
# A00200_CSV_tool (ARKit Facial Import) - launch entry point
#
# 셸프 버튼 / 드롭 설치 파일이 호출하는 진입점.
#   import tools.A00200_CSV_tool as A00200_CSV_tool
#   A00200_CSV_tool.run(True)

import importlib


def run(reload_module=True):
    """UI 실행 진입점. 셸프 버튼은 run(True) 로 호출된다.

    reload_module=True 면 본체 모듈(arkit_facial_import)을 리로드한 뒤 UI 를 띄운다.
    이 툴은 Framework 의존이 없는 단일 파일이라 본체 모듈만 리로드하면 충분하다.
    """
    from . import arkit_facial_import

    if reload_module:
        importlib.reload(arkit_facial_import)

    return arkit_facial_import.show()
