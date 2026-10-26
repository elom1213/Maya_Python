# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00480_FileTool - FBX 플러그인 로드 헬퍼 (Export · Import 공용) - **재노출**
"""
fbx_plugin - 본체는 2026-10-26 부터 `Framework.core.maya_fbx` (A00210_FileManager Maya > Export 가 같은 코드를 쓴다).
동작은 그대로다: `ensure_fbx_plugin()` -> (성공 여부, 로그 리스트).
"""

from Framework.core.maya_fbx import FBX_PLUGIN, ensure_fbx_plugin  # noqa: F401
