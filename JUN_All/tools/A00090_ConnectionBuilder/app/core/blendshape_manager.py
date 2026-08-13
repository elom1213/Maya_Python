# -*- coding: utf-8 -*-
"""
blendshape_manager - Rule mapping 이름으로 blendShape target 을 만든다.
"""
# 여기서 반드시 지켜야 하는 구분이 하나 있다.
#
#   **타겟 메시의 노드 이름**  !=  **blendShape 웨이트 별칭(alias)**
#
# Rule 의 mapping 이름(`calf_l_default` 등)은 **포즈 이름**이라 모든 메시가 공유한다.
# 그런데 예전 코드는 그 이름을 **타겟 메시의 노드 이름으로 그대로** 썼다. 노드 이름은
# 씬에서 유일해야 하므로, 옷 A 에 타겟을 만든 뒤 옷 B 에 같은 Rule 을 돌리면
# `cmds.objExists("calf_l_default")` 가 True 라서 **A 의 타겟을 B 의 타겟으로 재사용**했고,
# 토폴로지가 달라 Maya 가 이렇게 거절했다:
#
#     Target calf_l_defaultShape does not match with base SIN_Set007_Top2Shape.
#     No deformable objects selected.
#
# 그 이름이 조인트 등 다른 노드에 이미 쓰이고 있으면 `More than one object matches name`
# 으로 죽었다. 어느 쪽이든 `cmds.blendShape` 호출 하나가 통째로 실패해서
# **타겟이 아예 안 생기거나 일부만 생겼다.**
#
# 그래서 이 모듈은
#   1. 타겟 메시를 **메시 이름을 붙여 유일하게**(`<mesh>_<alias>`) 만들고,
#   2. blendShape 의 **alias 를 mapping 이름으로 되돌린다**(`cmds.aliasAttr`).
# alias 는 노드 단위라 blendShape 가 여럿이어도 각각 `calf_l_default` 를 가질 수 있고,
# Connect 기능이 쓰는 주소(`<blendShape>.<mapping이름>`)는 그대로 유지된다.
#
# 재사용은 **토폴로지가 실제로 맞을 때만** 한다(예전에 만들어 둔 타겟, 손으로 조각한 타겟).
# 타겟 하나가 실패해도 나머지는 계속 진행하고, 무엇이 왜 실패했는지 리포트로 돌려준다.

import maya.cmds as cmds

from Framework.core import maya_shape


class BlendShapeManager:

    # --------------------------------------------------
    # helpers
    # --------------------------------------------------

    @staticmethod
    def _resolve(node):
        """이름 하나를 롱네임으로 확정. 없거나 **중복되면** None."""
        found = cmds.ls(node, long=True) or []
        return found[0] if len(found) == 1 else None

    @staticmethod
    def _short(node):
        return node.split("|")[-1].split(":")[-1]

    @staticmethod
    def topology(node):
        """(버텍스, 엣지, 페이스). 메시가 아니면 None.

        셰이프 확정은 공용 `maya_shape` 로 한다. 트랜스폼에 셰이프가 여럿일 때
        `polyEvaluate` 를 트랜스폼에 걸면 정수가 아니라 요약 문자열이 온다.
        """
        try:
            shape = maya_shape.shape_path(node, type_="mesh")
        except Exception:
            return None
        if not shape:
            return None
        try:
            return (int(cmds.polyEvaluate(shape, v=True)),
                    int(cmds.polyEvaluate(shape, e=True)),
                    int(cmds.polyEvaluate(shape, f=True)))
        except Exception:
            return None

    @staticmethod
    def _unique_name(base):
        """씬에서 아직 안 쓰인 이름."""
        if not cmds.objExists(base):
            return base
        idx = 1
        while cmds.objExists("{0}{1}".format(base, idx)):
            idx += 1
        return "{0}{1}".format(base, idx)

    @staticmethod
    def target_name(mesh, alias):
        """이 메시 전용 타겟 이름."""
        return "{0}_{1}".format(BlendShapeManager._short(mesh), alias)

    @staticmethod
    def find_reusable_target(mesh, alias, signature):
        """재사용할 수 있는 기존 타겟. 없으면 None.

        `<mesh>_<alias>` 를 먼저 보고, 없으면 예전 방식으로 만들어진 `<alias>` 도 본다.
        **토폴로지가 base 와 같을 때만** 재사용한다 - 이 검사가 없어서 남의 타겟을
        가져다 쓰다 실패했던 것이 이번 버그다.
        """
        candidates = [BlendShapeManager.target_name(mesh, alias), alias]

        for cand in candidates:
            node = BlendShapeManager._resolve(cand)
            if node is None:
                continue
            if BlendShapeManager.topology(node) != signature:
                continue
            return node
        return None

    @staticmethod
    def find_blendshape(mesh, preferred=None):
        """메시를 실제로 변형하는 blendShape. 없으면 None.

        이름이 아니라 **히스토리**로 찾는다(사용자가 노드를 리네임했어도 찾도록).
        """
        shape = maya_shape.shape_path(mesh, type_="mesh")
        if not shape:
            return None
        found = cmds.ls(cmds.listHistory(shape, pruneDagObjects=True) or [],
                        type="blendShape") or []
        if not found:
            return None
        if preferred:
            for node in found:
                if BlendShapeManager._short(node) == preferred:
                    return node
        return found[0]

    @staticmethod
    def _next_index(bs_name):
        """다음 빈 weight 인덱스.

        `getAttr(size=True)` 를 쓰면 안 된다 - 중간 타겟을 지워 인덱스가 듬성해지면
        size 가 최대 인덱스보다 작아져 **기존 타겟 자리를 덮어쓴다**
        (`Error: Target at given index already exists.` 로 조용히 실패한다).
        """
        indices = cmds.getAttr(bs_name + ".weight", multiIndices=True) or []
        return (max(indices) + 1) if indices else 0

    @staticmethod
    def aliases(bs_name):
        return set(cmds.listAttr(bs_name + ".w", multi=True) or [])

    # --------------------------------------------------
    # targets
    # --------------------------------------------------

    @staticmethod
    def create_targets(rule, mesh):
        """rule.mapping 이름마다 타겟 메시를 준비한다.

        Returns:
            [(alias, target_node, action)] - action 은 "created" | "reused".
        """
        base = BlendShapeManager._resolve(mesh)
        if base is None:
            raise RuntimeError(
                "Mesh not found or the name is ambiguous : {0}".format(mesh))

        signature = BlendShapeManager.topology(base)
        if signature is None:
            raise RuntimeError("Not a polygon mesh : {0}".format(mesh))

        prepared = []

        for alias in rule.mapping:

            reused = BlendShapeManager.find_reusable_target(base, alias, signature)
            if reused is not None:
                print("[Reuse Target] {0} -> {1}".format(alias, reused))
                prepared.append((alias, reused, "reused"))
                continue

            name = BlendShapeManager._unique_name(
                BlendShapeManager.target_name(base, alias))
            dup = cmds.duplicate(base, name=name)[0]
            dup = BlendShapeManager._resolve(dup) or dup

            print("[Create Target] {0} -> {1}".format(alias, dup))
            prepared.append((alias, dup, "created"))

        return prepared

    # --------------------------------------------------
    # blendShape
    # --------------------------------------------------

    @staticmethod
    def create_blendshape(rule, mesh):
        """타겟을 만들고 blendShape 에 붙인다.

        Returns:
            (blendShape 이름, report dict)
            report = {created, reused, skipped, failed(list of (alias, reason))}
        """
        base = BlendShapeManager._resolve(mesh)
        if base is None:
            raise RuntimeError(
                "Mesh not found or the name is ambiguous : {0}".format(mesh))

        prepared = BlendShapeManager.create_targets(rule, base)

        bs_name = "{0}_blendShape".format(BlendShapeManager._short(base))
        bs = BlendShapeManager.find_blendshape(base, preferred=bs_name)

        if bs is None:
            # 타겟 없이 먼저 만들고 아래에서 하나씩 붙인다. 그래야 인덱스와 alias 를
            # 우리가 통제할 수 있고, 타겟 하나가 실패해도 나머지가 살아남는다.
            bs = cmds.blendShape(base, name=bs_name, frontOfChain=True)[0]
            print("[Create BlendShape] {0}".format(bs))

        report = {"blendshape": bs, "created": 0, "reused": 0,
                  "skipped": 0, "failed": []}

        existing = BlendShapeManager.aliases(bs)

        for alias, target, action in prepared:

            if alias in existing:
                print("[Skip] Target exists in blendShape : {0}.{1}".format(bs, alias))
                report["skipped"] += 1
                continue

            index = BlendShapeManager._next_index(bs)

            try:
                cmds.blendShape(bs, edit=True,
                                target=(base, index, target, 1.0))
            except Exception as exc:
                print("[Failed] {0} : {1}".format(alias, exc))
                report["failed"].append((alias, str(exc)))
                continue

            # 붙인 타겟의 alias 를 mapping 이름으로 되돌린다(Connect 가 이 주소를 쓴다).
            plug = "{0}.weight[{1}]".format(bs, index)
            current = cmds.aliasAttr(plug, query=True)
            if current != alias:
                try:
                    cmds.aliasAttr(alias, plug)
                except Exception as exc:
                    report["failed"].append((alias, "alias failed : {0}".format(exc)))
                    continue

            if not cmds.objExists("{0}.{1}".format(bs, alias)):
                report["failed"].append((alias, "target was not added"))
                continue

            existing.add(alias)
            report[action] += 1
            print("[Add Target] {0}.{1} (idx {2}) <- {3}".format(
                bs, alias, index, target))

        return bs, report
