# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-13
# A00430_DemBone core - 알렘빅 캐시 임포트 헬퍼 (maya.cmds 의존)
#
# 캐시 메시는 보통 씬에 이미 임포트되어 있다. 파일만 있는 경우를 위해 임포트 버튼을 둔다.
# gpuCache 가 아니라 **실제 polyMesh**(AlembicNode.time 구동)여야 버텍스를 읽을 수 있다.
#
# (A00280_correctiveFromCache 의 같은 헬퍼를 **복사**한 것이다 - 툴끼리 import 하면
#  릴리스 빌더가 툴 하나 + Framework 만 복사할 때 패키지가 깨진다.)

import os

import maya.cmds as cmds


def ensure_plugin():
    if not cmds.pluginInfo("AbcImport", q=True, loaded=True):
        cmds.loadPlugin("AbcImport")


def import_file(abc_path):
    """.abc 를 임포트하고 새로 생긴 메시 트랜스폼 목록을 돌려준다."""
    if not abc_path or not os.path.isfile(abc_path):
        raise ValueError("Alembic file not found: {0}".format(abc_path))

    ensure_plugin()

    before = set(cmds.ls(type="mesh", long=True))
    cmds.AbcImport(abc_path.replace("\\", "/"), mode="import")
    after = set(cmds.ls(type="mesh", long=True))

    new_shapes = sorted(after - before)
    if not new_shapes:
        raise RuntimeError("No mesh was imported from '{0}'.".format(abc_path))

    transforms = []
    for shape in new_shapes:
        parents = cmds.listRelatives(shape, parent=True, fullPath=True) or []
        transforms.append(parents[0] if parents else shape)
    return transforms


def frame_range(nodes=None):
    """알렘빅 노드가 알려주는 (start, end). 못 찾으면 None."""
    alembic_nodes = cmds.ls(nodes or [], type="AlembicNode") or \
        cmds.ls(type="AlembicNode") or []
    if not alembic_nodes:
        return None
    starts = []
    ends = []
    for node in alembic_nodes:
        try:
            starts.append(cmds.getAttr("{0}.startFrame".format(node)))
            ends.append(cmds.getAttr("{0}.endFrame".format(node)))
        except Exception:
            continue
    if not starts:
        return None
    return int(min(starts)), int(max(ends))
