# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-10
# A00275_skinTool_V01 - Move Joints (조인트 편집 모드) 로직 (maya.cmds / maya.api, UI 비의존)
#
# "바인드된 메시를 건드리지 않고 조인트를 옮긴 뒤, 그 자리에서 다시 바인드한다."
#
#   Edit ON  -> 조인트를 아무리 움직여도 메시는 화면에서 1픽셀도 안 움직인다.
#   (조인트 이동/회전)
#   Edit OFF -> 지금 조인트 배치가 새 바인드 상태로 굳는다. 웨이트는 손대지 않는다.
#
# ## 원리
#
# skinCluster 의 인플루언스별 스킨 행렬은 `bindPreMatrix[i] * matrix[i]` 다
# (matrix[i] = 조인트의 worldMatrix). 편집 중 이 곱을 **상수로 유지**하면 조인트가 어디로
# 가든 출력이 변하지 않는다. 그래서 편집 시작 시점의 값을 C_i 로 잡고
#
#     C_i             = bindPreMatrix_i(0) * worldMatrix_i(0)          (상수)
#     bindPreMatrix_i(t) = C_i * worldInverseMatrix_i(t)               (라이브)
#
# 를 multMatrix 노드 하나로 걸어 준다. t=0 이면 원래 값 그대로라 **켜는 순간에도 무변화**다.
#
# 왜 `worldInverseMatrix` 를 bindPreMatrix 에 그냥 직결하지 않는가:
#   그러면 스킨 행렬이 항등이 되어 메시가 rest 셰이프로 튄다. 리그가 바인드 포즈에 있을
#   때만 우연히 같은 결과이고, **포즈된 리그에서는 눈에 띄게 점프한다**(실측: 3.6 유닛).
#   위 C_i 보정은 포즈와 무관하게 항상 무변화다(실측 오차 1e-16).
#
# Edit OFF 는 multMatrix 의 현재 출력을 bindPreMatrix 에 정적으로 굽고 임시 노드를 지운다.
# **weightList 는 어느 단계에서도 건드리지 않으므로 버텍스별 웨이트는 정의상 동일하다.**
#
# 취소(Cancel)를 위해 편집 시작 시점의 bindPreMatrix 와 조인트 트랜스폼을 skinCluster 의
# 문자열 어트리뷰트에 JSON 으로 저장해 둔다(씬을 저장했다 열어도 남는다).

import json

import maya.cmds as cmds
import maya.api.OpenMaya as om

from Framework.core.maya_undo import undo_chunk

# 인플루언스 인덱스 매핑 / bindPose 재생성은 Bind Pose 탭과 규칙이 완전히 같아 재사용한다.
from . import bind_pose_manager as bp


# 편집용 multMatrix 노드를 표시하는 부울 어트리뷰트. 이름이 바뀌어도 찾을 수 있게
# 이름 규칙이 아니라 어트리뷰트로 표시한다.
EDIT_TAG_ATTR = "JUN_jointEdit"

# 편집 시작 시점의 bindPreMatrix / 조인트 트랜스폼 백업(JSON). skinCluster 에 붙는다.
BACKUP_ATTR = "JUN_jointEditBackup"

# 백업/복원 대상 트랜스폼 어트리뷰트 (rotateOrder 는 rotate 보다 먼저 복원해야 한다)
_XFORM_ATTRS = (("t", "translate"), ("r", "rotate"), ("s", "scale"),
                ("jo", "jointOrient"), ("ra", "rotateAxis"))


# =========================
# 상태 조회
# =========================

def _edit_nodes(sc):
    """[(matrix 인덱스, 편집용 multMatrix 노드), ...] — 지금 편집 중인 슬롯들."""

    found = []

    for i in (cmds.getAttr(sc + ".matrix", mi=True) or []):
        plug = "{0}.bindPreMatrix[{1}]".format(sc, i)
        for src in (cmds.listConnections(plug, s=True, d=False) or []):
            if cmds.attributeQuery(EDIT_TAG_ATTR, node=src, exists=True):
                found.append((i, src))

    return found


def is_editing(sc):
    """이 skinCluster 가 편집 모드인가."""
    return bool(_edit_nodes(sc))


def editing_of(skin_clusters):
    """주어진 목록 중 편집 모드인 skinCluster 들."""
    return [sc for sc in (skin_clusters or []) if is_editing(sc)]


def find_editing_in_scene():
    """씬 전체에서 편집 모드인 skinCluster 를 찾는다.

    툴을 닫았다 다시 열어도 편집 중이던 대상을 되찾기 위한 것. 편집 상태는 씬(노드)에
    있고 UI 에 있지 않으므로, 화면 상태를 씬에 맞춰야 한다.
    """
    return [sc for sc in (cmds.ls(type="skinCluster") or []) if is_editing(sc)]


def influences_of(skin_clusters):
    """대상들의 인플루언스 목록(중복 제거). 'Select Influences' 용."""

    found = []

    for sc in (skin_clusters or []):
        for _idx, name in sorted(bp._influence_index_map(sc).items()):
            if name not in found:
                found.append(name)

    return found


# =========================
# 백업 (Cancel 용)
# =========================

def _read_xform(node):
    """조인트/트랜스폼의 로컬 포즈 값."""

    data = {}

    for key, attr in _XFORM_ATTRS:
        if not cmds.attributeQuery(attr, node=node, exists=True):
            continue
        try:
            data[key] = list(cmds.getAttr("{0}.{1}".format(node, attr))[0])
        except Exception:
            pass

    try:
        data["ro"] = cmds.getAttr(node + ".rotateOrder")
    except Exception:
        pass

    return data


def _restore_xform(node, data):
    """_read_xform 로 담아 둔 값을 되돌린다. 못 쓴 어트리뷰트 이름들을 반환."""

    failed = []

    # rotateOrder 를 먼저 — 오일러 값의 해석이 달라진다.
    if "ro" in data:
        try:
            cmds.setAttr(node + ".rotateOrder", data["ro"])
        except Exception:
            failed.append("rotateOrder")

    for key, attr in _XFORM_ATTRS:
        if key not in data:
            continue
        plug = "{0}.{1}".format(node, attr)
        try:
            if cmds.getAttr(plug, lock=True) or cmds.listConnections(
                    plug, s=True, d=False, p=True):
                failed.append(attr)
                continue
            cmds.setAttr(plug, *data[key], type="double3")
        except Exception:
            failed.append(attr)

    return failed


def _write_backup(sc, payload):
    plug = "{0}.{1}".format(sc, BACKUP_ATTR)
    if not cmds.attributeQuery(BACKUP_ATTR, node=sc, exists=True):
        cmds.addAttr(sc, ln=BACKUP_ATTR, dt="string")
    cmds.setAttr(plug, json.dumps(payload), type="string")


def _read_backup(sc):
    if not cmds.attributeQuery(BACKUP_ATTR, node=sc, exists=True):
        return None
    try:
        return json.loads(cmds.getAttr("{0}.{1}".format(sc, BACKUP_ATTR)) or "")
    except Exception:
        return None


def _clear_backup(sc):
    if cmds.attributeQuery(BACKUP_ATTR, node=sc, exists=True):
        try:
            cmds.deleteAttr("{0}.{1}".format(sc, BACKUP_ATTR))
        except Exception:
            pass


# =========================
# Edit ON
# =========================

def begin_edit(skin_clusters):
    """편집 모드 진입. 조인트를 옮겨도 메시가 변형되지 않게 만든다.

    반환: (처리한 skinCluster 수, 메시지 리스트)
    """

    messages = []

    if not skin_clusters:
        return 0, ["[Warning] No skinCluster found. Select a bound mesh or its joints."]

    done = 0

    with undo_chunk():

        for sc in skin_clusters:

            try:
                if is_editing(sc):
                    messages.append("[Info] {0}: already in edit mode.".format(sc))
                    continue

                index_map = bp._influence_index_map(sc)
                if not index_map:
                    messages.append(
                        "[Warning] {0}: no influence connection found, skipped.".format(sc))
                    continue

                backup = {"pre": {}, "xf": {}}
                blocked = []

                for idx, inf in sorted(index_map.items()):

                    plug = "{0}.bindPreMatrix[{1}]".format(sc, idx)

                    if (cmds.getAttr(plug, lock=True)
                            or cmds.listConnections(plug, s=True, d=False)):
                        blocked.append(inf)
                        continue

                    pre0 = cmds.getAttr(plug)
                    world0 = cmds.getAttr(inf + ".worldMatrix[0]")
                    # C = bindPreMatrix(0) * worldMatrix(0)  (스킨 행렬을 상수로 묶는다)
                    const = om.MMatrix(pre0) * om.MMatrix(world0)

                    node = cmds.createNode(
                        "multMatrix", n="{0}_jointEdit{1}".format(sc, idx))
                    cmds.addAttr(node, ln=EDIT_TAG_ATTR, at="bool")

                    cmds.setAttr(node + ".matrixIn[0]", *list(const), type="matrix")
                    cmds.connectAttr(inf + ".worldInverseMatrix[0]",
                                     node + ".matrixIn[1]", f=True)
                    cmds.connectAttr(node + ".matrixSum", plug, f=True)

                    backup["pre"][str(idx)] = list(pre0)
                    backup["xf"][str(idx)] = _read_xform(inf)

                if not backup["pre"]:
                    messages.append(
                        "[Warning] {0}: every bindPreMatrix is locked or already "
                        "connected - nothing to edit.".format(sc))
                    continue

                if blocked:
                    messages.append(
                        "[Warning] {0}: bindPreMatrix is locked or connected for {1}. "
                        "Moving those joints WILL deform the mesh.".format(
                            sc, ", ".join(blocked)))

                _write_backup(sc, backup)
                done += 1

                messages.append(
                    "[OK] {0}: edit mode ON ({1} influence(s) held).".format(
                        sc, len(backup["pre"])))

            except Exception as e:
                messages.append("[Error] {0}: {1}".format(sc, e))

    return done, messages


# =========================
# Edit OFF (확정)
# =========================

def end_edit(skin_clusters, rebuild_dag_pose=True):
    """편집 모드 종료. 지금 조인트 배치를 새 바인드 상태로 굳힌다.

    weightList 는 건드리지 않으므로 버텍스별 웨이트는 편집 전과 동일하다.

    반환: (처리한 skinCluster 수, 메시지 리스트)
    """

    messages = []

    if not skin_clusters:
        return 0, ["[Warning] Nothing loaded."]

    done = 0

    with undo_chunk():

        for sc in skin_clusters:

            try:
                nodes = _edit_nodes(sc)
                if not nodes:
                    messages.append("[Info] {0}: not in edit mode, skipped.".format(sc))
                    continue

                # 노드를 지우면 연결이 끊기고 bindPreMatrix 는 **연결 전 값**으로 돌아간다.
                # 그러니 지우기 전에 현재 출력을 읽어 두었다가 정적 값으로 다시 쓴다.
                baked = [(idx, cmds.getAttr(node + ".matrixSum")) for idx, node in nodes]

                cmds.delete([node for _idx, node in nodes])

                for idx, value in baked:
                    cmds.setAttr("{0}.bindPreMatrix[{1}]".format(sc, idx),
                                 *value, type="matrix")

                _clear_backup(sc)

                if rebuild_dag_pose:
                    note = bp._rebuild_bind_pose(
                        sc, list(bp._influence_index_map(sc).values()))
                    if note:
                        messages.append(note)

                done += 1
                messages.append(
                    "[OK] {0}: edit mode OFF - re-bound at the current joint "
                    "positions ({1} influence(s), weights unchanged).".format(
                        sc, len(baked)))

            except Exception as e:
                messages.append("[Error] {0}: {1}".format(sc, e))

    return done, messages


# =========================
# 취소
# =========================

def cancel_edit(skin_clusters):
    """편집을 버리고 조인트와 바인드 행렬을 편집 시작 시점으로 되돌린다.

    반환: (처리한 skinCluster 수, 메시지 리스트)
    """

    messages = []

    if not skin_clusters:
        return 0, ["[Warning] Nothing loaded."]

    done = 0

    with undo_chunk():

        for sc in skin_clusters:

            try:
                nodes = _edit_nodes(sc)
                if not nodes:
                    messages.append("[Info] {0}: not in edit mode, skipped.".format(sc))
                    continue

                backup = _read_backup(sc)
                index_map = bp._influence_index_map(sc)

                cmds.delete([node for _idx, node in nodes])

                if not backup:
                    messages.append(
                        "[Warning] {0}: no backup found - joints were left where they "
                        "are and the bind matrices were rebuilt from them.".format(sc))
                    for idx, inf in sorted(index_map.items()):
                        plug = "{0}.bindPreMatrix[{1}]".format(sc, idx)
                        if not cmds.getAttr(plug, lock=True):
                            cmds.setAttr(plug,
                                         *cmds.getAttr(inf + ".worldInverseMatrix[0]"),
                                         type="matrix")
                    done += 1
                    continue

                for key, value in (backup.get("pre") or {}).items():
                    plug = "{0}.bindPreMatrix[{1}]".format(sc, int(key))
                    if cmds.getAttr(plug, lock=True):
                        continue
                    cmds.setAttr(plug, *value, type="matrix")

                stuck = []
                for key, data in (backup.get("xf") or {}).items():
                    inf = index_map.get(int(key))
                    if not inf or not cmds.objExists(inf):
                        continue
                    failed = _restore_xform(inf, data)
                    if failed:
                        stuck.append("{0} ({1})".format(inf, ", ".join(failed)))

                if stuck:
                    messages.append(
                        "[Warning] {0}: could not restore {1} - locked or "
                        "connected.".format(sc, "; ".join(stuck)))

                _clear_backup(sc)
                done += 1
                messages.append(
                    "[OK] {0}: edit cancelled - joints and bind matrices "
                    "restored.".format(sc))

            except Exception as e:
                messages.append("[Error] {0}: {1}".format(sc, e))

    return done, messages


# =========================
# 조회 (UI 표시용)
# =========================

def resolve_targets(nodes=None):
    """선택에서 대상 skinCluster 를 모은다 (Bind Pose 탭과 동일 규칙)."""
    return bp.resolve_targets(nodes)


def describe(skin_clusters):
    """대상 요약 문자열 + 편집 중 표시."""

    text = bp.describe(skin_clusters)

    editing = editing_of(skin_clusters)
    if editing:
        text += "   [editing: {0}]".format(", ".join(editing))

    return text
