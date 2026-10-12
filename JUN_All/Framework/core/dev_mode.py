# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# Framework - 개발자 모드 판정 (툴 공용).
#
# A00330_NamingTool 의 app/config/dev_mode.py (v01.14) 를 공용으로 올린 것이다. 어느 툴이든
# 자기 파일 경로(`__file__`) 하나만 넘기면 **개발자 모드인지**를 같은 규칙으로 판정한다.
#
# 규칙은 launch.py 와 같다 (docs/Release_Layout.md):
#   릴리즈본 : 툴 폴더 안에 Framework 가 동봉돼 있다 -> 항상 False (config.py 가 실리지 않는다)
#   dev 트리 : JUN_All/config.py 의 DEV_MODE
#
# 쓰는 곳
#   - Framework.qt.MOD_devMode_qt_v01 (메뉴 바의 `Dev Mode` 메뉴) 가 이 판정으로 메뉴를 만들지 정한다.
#   - 툴이 "개발자에게만 보이는 버튼" 을 둘 때 (A00330 Token 탭의 `Values...`).
#
# 이 모듈은 maya / Qt 를 import 하지 않는다 - standalone 툴이나 mayapy 에서도 import 만으로 깨지지 않는다.

import os
import importlib.util

from Framework.core import tool_menu


def tool_root(tool_file):
    """툴 안의 아무 파일 경로에서 **툴 폴더**를 찾는다. 못 찾으면 None.

    판정은 `tool_menu.tool_dir_from_path` 와 같다 - 부모가 `tools` 인 폴더, 없으면 `app` 을 담은 폴더.
    """
    return tool_menu.tool_dir_from_path(tool_file) if tool_file else None


def is_release(tool_file):
    """릴리즈본이면 True - 툴 폴더 안에 `Framework` 가 동봉돼 있다.

    툴 폴더를 못 찾으면(경로가 이상하면) 안전한 쪽인 릴리즈본으로 본다 - 배포본에서 개발자 메뉴가
    보이는 것보다 개발 트리에서 메뉴가 없는 쪽이 낫다.
    """
    root = tool_root(tool_file)
    if not root:
        return True
    return os.path.isdir(os.path.join(root, "Framework"))


def _jun_all_config_path(tool_file):
    """dev 트리의 `JUN_All/config.py` 경로. 툴 폴더(`JUN_All/tools/<툴>`)에서 두 단계 위다."""
    root = tool_root(tool_file)
    if not root:
        return None
    return os.path.join(os.path.dirname(os.path.dirname(root)), "config.py")


def read_dev_mode_flag(tool_file):
    """`JUN_All/config.py` 의 DEV_MODE 를 **경로로** 읽는다. 없거나 못 읽으면 False.

    `import config` 는 흔한 이름이라 다른 툴 폴더의 config.py 를 집을 수 있다(Release_Layout.md).
    그래서 spec_from_file_location 으로 그 파일만 읽는다. 부를 때마다 다시 읽으므로 DEV_MODE 를
    바꾸고 툴만 다시 열면 된다.
    """
    path = _jun_all_config_path(tool_file)
    if not path or not os.path.isfile(path):
        return False
    try:
        spec = importlib.util.spec_from_file_location("_jun_all_config_for_dev_mode", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception:
        return False
    return bool(getattr(module, "DEV_MODE", False))


def is_dev_mode(tool_file):
    """개발자 모드면 True.

    릴리즈본이면 언제나 False. dev 트리에서는 JUN_All/config.py 의 DEV_MODE 를 따른다.
    """
    if is_release(tool_file):
        return False
    return read_dev_mode_flag(tool_file)
