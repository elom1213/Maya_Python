# -*- coding: utf-8 -*-
# A00500_reloader - 셸프 버튼이 리로드할 최상위 패키지 (dev/reload_path_list.py 에서 옮김)
#
# sys.modules 에 올라와 있는 것만 리로드하므로, 여기 적힌 패키지 전체가 import 되는 것은 아니다.

RELOAD_PACKAGES = [
    "Framework",
    "tools",
]
