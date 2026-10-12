# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# A00240_PathTool - directory tree scanner
#
# 구현은 Framework 로 승격됨(A00480_FileTool Maya 탭과 공유, v01.20). 기존 호출부
# (`from ..core import tree_scanner`) 가 그대로 동작하도록 re-export 만 남긴다.
from Framework.core.tree_scanner import *  # noqa: F401,F403  (re-export)
from Framework.core.tree_scanner import (  # noqa: F401  (밑줄 이름도 - 테스트 · 디버그용)
    build_tree, build_tree_lazy, scan_children, collect_extensions,
    _root_node, _dir_node, _lstat, _mark_junction, _safe_is_dir, _safe_is_file,
    _norm_exts, _walk, _same_or_inside,
)
