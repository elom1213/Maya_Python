# -*- coding: utf-8 -*-
"""
undo_bridge - undo_cmd 플러그인과 툴 코드 사이의 staging 채널.

`cmds.loadPlugin` 으로 로드된 undo_cmd 플러그인은 별도 모듈 인스턴스로 적재되므로,
플러그인 모듈의 전역변수는 툴 코드가 import 한 것과 동일하지 않다.
이 bridge 는 일반 import 경로(tools.A00180_abSymMesh.core.undo_bridge)로만 접근하므로
양쪽이 같은 단일 모듈 객체를 공유한다 -> 페이로드 전달이 안전하다.

PENDING 규약:
    {"mesh": str, "points": [(x, y, z), ...], "world": bool}
set_points_undoable() 가 채우고, abSymSetPoints 커맨드의 doIt() 가 소비(pop)한다.
"""

PENDING = None


def take():
    """현재 PENDING 을 반환하고 비운다."""
    global PENDING
    payload = PENDING
    PENDING = None
    return payload
