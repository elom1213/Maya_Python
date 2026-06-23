# -*- coding: utf-8 -*-
"""
matrix_constraint_manager - "Matrix Constraint" 기능 로직.

레거시 JUN_PY_MatrixCon_01_01.py 의 JUN_cmd_matrixConstraint_01 포팅.
일반 *Constraint 노드 대신 multMatrix + decomposeMatrix 노드 네트워크로
행렬 기반 컨스트레인트를 만든다. 가볍고(컨스트레인트 노드 누적 없음) 부모공간/
오프셋을 명시적으로 제어할 수 있다.

원본(JUN_PY_MatrixCon_01_01) 대비 수정:
  - [버그] scale 연결이 translate 플래그로 게이팅되던 것 -> scale 플래그로 수정.
  - [버그] maintain_offset 값을 읽기만 하고 안 쓰던 것 -> 실제 분기.
           (False 면 오프셋 미적용 = follower 가 target 에 스냅.)
  - [개선] follower 가 joint 면 jointOrient 역행렬로 rotate 출력만 보정.
           (translate/scale 출력은 보정 전 행렬에서 가져와 위치가 회전되지 않게 한다.)
  - [개선] target 1개 -> 다수 follower 브로드캐스트 지원(constrain_manager 와 동일).
  - [정리] follower.parentInverseMatrix[0] 사용 -> 부모 없으면 단위행렬 그룹을 만들던
           원본 분기 제거(어트리뷰트가 부모 없을 때 항상 단위행렬).
  - [정리] UI 위젯 의존 제거(list/bool 인자만), 항목별 예외는 errors 로 수집.

UI 비의존: 위젯에서 읽은 list/bool 값만 받는다. (app/core ↔ app/ui 분리)
"""

import maya.cmds as cmds


# 구운(baked) offset 행렬 그룹을 모아두는 최상위 정리 그룹.
_ROOT_GROUP = "JUN_matAll_grp"

# fol 채널명 -> decomposeMatrix 출력 attr.
_CHANNEL_OUT = {
    "translate": "outputTranslate",
    "rotate": "outputRotate",
    "scale": "outputScale",
}


def _short(name):
    """네임스페이스/풀패스를 제거한 짧은 노드명."""
    return name.split("|")[-1].split(":")[-1]


def _ensure_parent(child, parent_name):
    """parent_name 그룹이 없으면 만들고 child 를 그 아래로 넣는다. (정리용)"""
    if not cmds.objExists(parent_name):
        cmds.group(empty=True, name=parent_name)
    try:
        return cmds.parent(child, parent_name)[0]
    except Exception:
        return child


def _break_incoming(plug):
    """plug(예: 'fol.translate')로 들어오는 기존 연결을 끊는다(재실행 대비)."""
    srcs = cmds.listConnections(
        plug, source=True, destination=False, plugs=True) or []
    for src in srcs:
        try:
            cmds.disconnectAttr(src, plug)
        except Exception:
            pass


def _make_offset_matrix(follower, target):
    """follower.worldMatrix * target.worldInverseMatrix 를 계산해
    <follower>_offsetMat 그룹의 matrix attr 에 '값으로 구워' 보관하고 그룹명을 반환한다.

    연결 후 즉시 disconnect 해 정적 오프셋 값만 남긴다(원본 동작 유지).
    """
    name = _short(follower) + "_offsetMat"
    if cmds.objExists(name):
        cmds.delete(name)

    grp = cmds.group(empty=True, name=name)
    cmds.addAttr(grp, longName="offsetAttr", attributeType="matrix")
    cmds.setAttr(grp + ".visibility", 0)

    tmp = cmds.createNode("multMatrix")
    cmds.connectAttr(follower + ".worldMatrix[0]", tmp + ".matrixIn[0]")
    cmds.connectAttr(target + ".worldInverseMatrix[0]", tmp + ".matrixIn[1]")
    cmds.connectAttr(tmp + ".matrixSum", grp + ".offsetAttr")
    cmds.disconnectAttr(tmp + ".matrixSum", grp + ".offsetAttr")
    cmds.delete(tmp)

    return _ensure_parent(grp, _ROOT_GROUP)


def _joint_orient_inverse(joint):
    """joint.jointOrient 의 역행렬을 출력하는 inverseMatrix 노드의 출력 plug 를 반환한다.

    jointOrient 를 라이브로 연결해 두므로 이후 jointOrient 가 바뀌어도 보정이 유지된다.
    jointOrient 의 회전 순서는 Maya 에서 항상 XYZ 다.
    """
    base = _short(joint)
    compose = cmds.createNode("composeMatrix", name=base + "_joCompose")
    cmds.connectAttr(joint + ".jointOrient", compose + ".inputRotate")
    inv = cmds.createNode("inverseMatrix", name=base + "_joInverse")
    cmds.connectAttr(compose + ".outputMatrix", inv + ".inputMatrix")
    return inv + ".outputMatrix"


def _build_network(target, follower, maintain_offset, channels):
    """target -> follower 행렬 컨스트레인트 노드 네트워크 1세트를 만든다.

    Args:
        target: 드라이버 오브젝트.
        follower: 구속될 오브젝트.
        maintain_offset: True 면 현재 오프셋을 유지, False 면 follower 가 target 에 스냅.
        channels: 연결할 채널 집합. ("translate"/"rotate"/"scale") 중 일부.

    Returns:
        생성된 multMatrix 노드명.
    """
    base = _short(target)
    mult = cmds.createNode("multMatrix", name=base + "_mtxCon_multMatrix")

    # matrixIn 체인을 순서대로 쌓는다.
    #   (maintain_offset) offset * target.worldMatrix * follower.parentInverseMatrix
    idx = 0
    if maintain_offset:
        offset = _make_offset_matrix(follower, target)
        cmds.connectAttr(offset + ".offsetAttr",
                         "{0}.matrixIn[{1}]".format(mult, idx))
        idx += 1
    cmds.connectAttr(target + ".worldMatrix[0]",
                     "{0}.matrixIn[{1}]".format(mult, idx))
    idx += 1
    # parentInverseMatrix 는 부모가 없으면 단위행렬이라 별도 분기가 필요 없다.
    cmds.connectAttr(follower + ".parentInverseMatrix[0]",
                     "{0}.matrixIn[{1}]".format(mult, idx))

    matrix_sum = mult + ".matrixSum"
    is_joint = cmds.nodeType(follower) == "joint"

    # 보정 전 행렬을 분해하는 메인 decomposeMatrix 는 처음 필요할 때만 생성/재사용한다
    # (rotate 만 + joint 인 경우엔 jointOrient 보정 분기만 쓰므로 메인 분해가 불필요).
    main_decomp = [None]

    def _main_decompose():
        if main_decomp[0] is None:
            node = cmds.createNode(
                "decomposeMatrix", name=base + "_mtxCon_decompose")
            cmds.connectAttr(matrix_sum, node + ".inputMatrix")
            main_decomp[0] = node
        return main_decomp[0]

    for ch in ("translate", "rotate", "scale"):
        if ch not in channels:
            continue
        dst = "{0}.{1}".format(follower, ch)
        _break_incoming(dst)

        if ch == "rotate" and is_joint:
            # joint 는 rotate 가 jointOrient 뒤에 적용되므로 역행렬로 보정한다.
            # 위치/스케일에 영향을 주지 않도록 별도 분기로 rotate 만 보정.
            jo_mult = cmds.createNode(
                "multMatrix", name=base + "_mtxCon_joMult")
            cmds.connectAttr(matrix_sum, jo_mult + ".matrixIn[0]")
            cmds.connectAttr(_joint_orient_inverse(follower),
                             jo_mult + ".matrixIn[1]")
            jo_decomp = cmds.createNode(
                "decomposeMatrix", name=base + "_mtxCon_joDecompose")
            cmds.connectAttr(jo_mult + ".matrixSum", jo_decomp + ".inputMatrix")
            cmds.connectAttr(jo_decomp + ".outputRotate", dst)
        else:
            cmds.connectAttr(
                _main_decompose() + "." + _CHANNEL_OUT[ch], dst)

    return mult


def matrix_constraint(targets, followers, maintain_offset=True,
                      translate=True, rotate=True, scale=True):
    """targets -> followers 를 행렬 노드 네트워크로 구속한다.

    constrain_manager.constrain() 과 동일한 브로드캐스트 규칙:
      - target 이 1개면 모든 follower 에 브로드캐스트.
      - 그 외에는 인덱스 1:1.

    Args:
        targets: 타겟(드라이버) 오브젝트 리스트.
        followers: 팔로워(구속될) 오브젝트 리스트.
        maintain_offset: True 면 현재 오프셋 유지, False 면 follower 가 target 에 스냅.
        translate / rotate / scale: 연결할 채널 토글.

    Returns:
        (made, errors)
          made   : 구속에 성공한 follower 명 리스트.
          errors : "follower: 메시지" 형태의 실패 메시지 리스트.
    """
    if not targets:
        raise ValueError("No target objects. Add objects to the Targets list.")
    if not followers:
        raise ValueError(
            "No follower objects. Add objects to the Followers list.")

    channels = set()
    if translate:
        channels.add("translate")
    if rotate:
        channels.add("rotate")
    if scale:
        channels.add("scale")
    if not channels:
        raise ValueError(
            "No channels selected. Enable Translate, Rotate or Scale.")

    made = []
    errors = []
    all_size = max(len(followers), len(targets))
    for i in range(all_size):
        if i >= len(followers):
            break
        idx_tgt = 0 if len(targets) == 1 else i
        if idx_tgt >= len(targets):
            break

        target = targets[idx_tgt]
        follower = followers[i]
        try:
            if not cmds.objExists(target):
                raise ValueError("target not found: {0}".format(target))
            if not cmds.objExists(follower):
                raise ValueError("follower not found: {0}".format(follower))
            _build_network(target, follower, maintain_offset, channels)
            made.append(follower)
        except Exception as exc:
            errors.append("{0}: {1}".format(follower, exc))

    return made, errors
