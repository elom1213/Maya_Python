# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# A00240_PathTool - "Tree" tab (Qt, standalone)
#
# 본체는 Framework 공용 위젯 `JUN_mod_fileTree_qt_v01` 로 승격됨 (v01.20, 2026-10-12) -
# A00480_FileTool 의 Maya 탭이 같은 트리로 마야 파일을 고른다. 동작은 v01.19 와 같다.
# 기존 호출부(`from .tree_tab import TreeTab`) 가 그대로 동작하도록 re-export 만 남긴다.
# 기능 설명과 상수(JUNCTION_COLOR · OMIT_MIN · ROLE_OMIT …)는 그 모듈에 있다.
from Framework.qt.MOD_fileTree_qt_v01 import (  # noqa: F401  (re-export)
    JUN_mod_fileTree_qt_v01 as TreeTab,
    PREFETCH_MAX_PER_FOLDER, PREFETCH_TICK_MS, JUNCTION_COLOR,
    OMIT_MIN, OMIT_LABEL, ROLE_OMIT,
    _tinted_icon, _CheckableMenu,
)
