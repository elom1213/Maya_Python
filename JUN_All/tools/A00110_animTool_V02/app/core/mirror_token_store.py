# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-07
# A00110_animTool_V02 - Mirror Key 좌/우 토큰 쌍 (공용 규칙으로 이전)
#
# 실제 구현과 규칙 파일은 **Framework** 로 옮겼다:
#     Framework/core/mirror_tokens.py   (MirrorTokenStore)
#     Framework/rules/mirror_tokens.json
#
# 좌/우 이름 규칙은 리그 전체에 하나뿐인 약속인데 툴마다 JSON 을 들고 있으면 목록이
# 조용히 갈라진다(animTool 에서 토큰을 추가해도 다른 툴은 모른다). 그래서 규칙 파일을
# Framework/rules 로 올려 모든 툴이 같은 파일을 읽고 쓴다.
#
# 이 모듈은 기존 import 경로(`from .mirror_token_store import MirrorTokenStore`)를
# 유지하기 위한 얇은 재노출(re-export)이다. 새 코드는 Framework 쪽을 직접 쓸 것.

from Framework.core.mirror_tokens import MirrorTokenStore


__all__ = ["MirrorTokenStore"]
