# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-05
# A00600_SceneCleanup - 체크한 항목을 순서대로 실행한다.
#
# - undo 청크 하나 : Ctrl+Z 한 번에 전부 되돌린다.
# - 한 항목이 예외로 실패해도 나머지는 돈다.
# - 끝나면 Layer Editor 를 다시 그린다(GUI 일 때만).
# 로그 문자열은 UI 에 보이므로 영어.

from Framework.core import maya_cleanup
from Framework.core.maya_undo import undo_chunk

_PREVIEW = 12       # 로그에 이름을 몇 개까지 펼칠지


def _names(names):
    if len(names) <= _PREVIEW:
        return ", ".join(names)
    return "{0}, ... (+{1})".format(", ".join(names[:_PREVIEW]), len(names) - _PREVIEW)


def run_items(items, log=None):
    """items 를 순서대로 실행. 반환: [(item, CleanupResult 또는 None, error 문자열 또는 None)]."""
    def _log(msg):
        if log:
            log(msg)

    outcomes = []
    if not items:
        _log("[WARN] Nothing checked - no cleanup ran.")
        return outcomes

    with undo_chunk():
        for item in items:
            try:
                result = item.run()
            except Exception as exc:                      # noqa: BLE001 - 한 항목 실패가 나머지를 막지 않게
                outcomes.append((item, None, str(exc).strip()))
                _log("[ERROR] {0} : {1}".format(item.label, str(exc).strip()))
                continue
            outcomes.append((item, result, None))
            if result.removed:
                _log("{0} : removed {1} ({2})".format(item.label, len(result.removed), _names(result.removed)))
            else:
                _log("{0} : nothing to remove".format(item.label))
            for warning in result.warnings:
                _log("[WARN]   {0}".format(warning))

    maya_cleanup.refresh_layer_editors()

    total = sum(len(r.removed) for _, r, _ in outcomes if r)
    errors = sum(1 for _, _, e in outcomes if e)
    _log("Done : {0} node(s) removed by {1} item(s){2}. Ctrl+Z undoes the whole cleanup.".format(
        total, len(items), ", {0} failed".format(errors) if errors else ""))
    return outcomes
