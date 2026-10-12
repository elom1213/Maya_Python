# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# A00120_FKIK - Auto 모드 씬 조사 (네임스페이스 단위로 FK/IK 스위칭 가능한 리그를 찾는다)
#
# Manual 모드(Select Objects)는 사용자가 고른 톱 노드를 FKIKSetup.resolve 에 넘긴다. Auto 모드는
# 그 "고르는 일" 을 대신한다 - 씬에서 `BlendFKIKPos_grp` 를 가진 계층을 찾아 **네임스페이스마다 하나의
# 단위(unit)** 로 묶고, 단위마다 resolve 를 돌려 Targets / Followers 를 미리 풀어 둔다.
#
# 단위의 기준이 네임스페이스인 이유 : 레퍼런스로 들어온 캐릭터는 네임스페이스가 곧 캐릭터다.
# 같은 네임스페이스(보통 루트)에 리그가 둘 이상 있어 한 단위로는 개수 검증(24)에 걸리면, 톱 노드마다
# 따로 다시 풀어 `<ns> | <top>` 로 나눈다.
#
# UI 를 모른다 - 결과를 dict 리스트로 돌려주고 표시는 main_window 가 한다.

import maya.cmds as cmds

from tools.A00120_FKIK.app.config import naming
from tools.A00120_FKIK.app.core.fkik_setup import FKIKSetup


ROOT_LABEL = "(root)"


def _leaf(path):
    return path.split("|")[-1]


def _namespace_of(path):
    """긴 경로의 **잎 이름**에서 네임스페이스를 뗀다. 루트면 ""."""
    return _leaf(path).rpartition(":")[0]


def _top_of(path):
    """긴 경로(`|a|b|c`)의 톱 노드(`|a`)."""
    parts = path.split("|")
    return "|" + parts[1] if len(parts) > 1 and parts[1] else path


def _unique(items):
    return list(dict.fromkeys(items))


def find_blend_groups():
    """씬의 모든 네임스페이스에서 `BlendFKIKPos_grp` 를 이름에 가진 transform 들(긴 경로)."""
    pattern = "*%s*" % naming.BLEND_GRP_TOKEN
    # recursive=True : 모든 네임스페이스에서 찾는다 (`ns:*` 패턴을 네임스페이스 깊이마다 쓰지 않아도 된다)
    found = cmds.ls(pattern, recursive=True, type="transform", long=True) or []
    return _unique(found)


def _unit(namespace, tops, result, label=None):
    return {
        "namespace": namespace,
        "label": label or (namespace or ROOT_LABEL),
        "tops": list(tops),
        "ok": bool(result["ok"]),
        "targets": list(result["targets"]),
        "followers": list(result["followers"]),
        "message": result["message"],
    }


class FKIKScanner:

    @staticmethod
    def scan():
        """씬을 네임스페이스 단위로 조사한다.

        반환: {
            "units":   [unit, ...]   # resolve 에 성공한 단위 (label 순)
            "skipped": [unit, ...]   # BlendFKIKPos_grp 는 있는데 검증에 걸린 단위 (message 에 이유)
        }
        unit = {"namespace", "label", "tops", "ok", "targets", "followers", "message"}
        """
        groups = find_blend_groups()

        by_ns = {}
        for grp in groups:
            by_ns.setdefault(_namespace_of(grp), []).append(_top_of(grp))

        units, skipped = [], []
        for namespace in sorted(by_ns):
            tops = sorted(_unique(by_ns[namespace]))

            result = FKIKSetup.resolve(tops)
            if result["ok"]:
                units.append(_unit(namespace, tops, result))
                continue

            if len(tops) <= 1:
                skipped.append(_unit(namespace, tops, result))
                continue

            # 같은 네임스페이스에 리그가 여럿 - 톱 노드마다 따로 푼다
            for top in tops:
                sub = FKIKSetup.resolve([top])
                label = "%s | %s" % (namespace or ROOT_LABEL, _leaf(top))
                (units if sub["ok"] else skipped).append(_unit(namespace, [top], sub, label=label))

        return {"units": units, "skipped": skipped}
