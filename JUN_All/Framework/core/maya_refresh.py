# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-19
# Framework - 뷰포트 refresh 억제(suspend) 공용 헬퍼.
#
# cmds.refresh(suspend=True) 는 "씬 전역(session-wide)" 토글이다. 켜진 채로 남으면
# 커브/어트리뷰트를 편집해도 화면이 갱신되지 않고, 프레임을 옮겨야(currentTime 변경이
# 강제 재평가) 결과가 보인다. 따라서 suspend=True 를 쓴 코드는 어떤 예외/조기 종료에도
# 반드시 suspend=False 로 되돌려야 한다.
#
# 과거 버그: 베이크 finally 에서 cmds.delete(임시 컨스트레인트) 가 suspend 복원보다
# "먼저" 실행돼, delete 가 예외를 던지면 suspend=False 가 건너뛰어지고 세션 전체가
# 프리즈됐다. 이 모듈의 컨텍스트 매니저는 복원을 "항상 가장 먼저" 보장한다.

import contextlib

import maya.cmds as cmds


@contextlib.contextmanager
def suspend_refresh():
    """블록 동안 뷰포트 refresh 를 억제하고, 종료 시 "항상 먼저" 복원한다.

    사용 예:
        with suspend_refresh():
            ... 대량 키 작업 / 베이크 ...
        # 여기서 호출부의 delete/currentTime 등 다른 정리를 해도
        # suspend=False 는 이미 끝나 있으므로 그 정리가 실패해도 프리즈되지 않는다.

    주의: cmds.refresh(suspend=...) 는 카운팅이 아니라 단일 불리언 토글이다. 중첩하면
    안쪽 종료에서 바깥쪽이 끝나기 전에 refresh 가 켜질 수 있으나(성능만 손해), 누수는
    없다. 누수의 유일한 원인은 suspend=False 미실행이므로 이 매니저로 그것을 막는다.
    """
    cmds.refresh(suspend=True)
    try:
        yield
    finally:
        # 어떤 예외에도 무조건, 그리고 호출부의 다른 정리보다 먼저 실행된다.
        cmds.refresh(suspend=False)


def force_refresh():
    """복구용: 어딘가에서 막혀버린 전역 suspend 를 풀고 한 번 강제로 그린다.

    뷰포트가 멈춰(커브 편집이 프레임 이동 전까지 안 보임) 있을 때 호출하면 즉시 풀린다.
    suspend 가 이미 꺼져 있어도 무해하다(False 를 다시 줄 뿐).
    """
    cmds.refresh(suspend=False)
    cmds.refresh()
