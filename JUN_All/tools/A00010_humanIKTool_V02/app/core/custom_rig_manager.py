# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-25
# A00010_humanIKTool_V02 - HumanIK Custom Rig(컨트롤러 매핑) 미러.
#
# 조인트 쪽(hik_manager.mirror_joints)과 짝을 이루는 기능이다. 캐릭터 정의가 조인트를
# 슬롯에 붙이는 것이라면, Custom Rig 는 **리그 컨트롤러**를 이펙터에 붙인다. 왼쪽 컨트롤러를
# 다 매핑한 뒤 오른쪽을 하나씩 다시 찍는 수고가 조인트와 똑같이 반복되므로 같은 해석기
# (mirror_resolver)로 자동화한다.
#
# ── 씬 안의 구조 (Maya 2024 에서 실측) ───────────────────────────────────────
#
#   HIKCharacterNode ──message──> CustomRigRetargeterNode
#                                   .mappings[i] <──message── CustomRigDefaultMappingNode
#
#   CustomRigDefaultMappingNode
#     .bodyPart         "LeftHand"   (= HumanIK 슬롯 이름. hik_nodes 의 테이블과 같은 이름)
#     .type             0 = Translation, 1 = Rotation   (한 이펙터가 T/R 두 매핑을 갖는다)
#     .id               11            (= 슬롯 ID)
#     .destinationRig   ──> 컨트롤러 트랜스폼
#     .offsetX/Y/Z      사용자가 HIK UI 에서 잡은 오프셋
#
# 읽기는 cmds 로 직접 한다(위 구조가 전부라 MEL 이 필요 없다). 쓰기는 HumanIK 의
# RetargeterAddMapping 을 그대로 쓴다 - 매핑 노드 생성이 파이썬 헬퍼(maya.app.hik.retargeter)
# 를 타기 때문에 손으로 노드를 만들면 재현이 안 된다.
#
# ── 주의 ────────────────────────────────────────────────────────────────────
# * RetargeterAddMapping 은 대상 컨트롤러의 translate / rotate 가 잠겨 있으면
#   confirmDialog 를 띄운다(= 배치 처리가 모달에서 멈춘다). 그래서 호출 전에 잠금을 직접
#   확인하고, 잠긴 채널은 건너뛴다.
# * 매핑을 추가할 때마다 리타게터를 끊었다 다시 잇는다. 배치 전체를 한 번만 끊고 마지막에
#   다시 잇는 편이 훨씬 빠르다.

import maya.cmds as cmds
import maya.mel as mel

from Framework.core.maya_undo import undo_chunk

from tools.A00010_humanIKTool_V02.app.core.hik_nodes import HIKNodes
from tools.A00010_humanIKTool_V02.app.core.mirror_resolver import MirrorResolver, MODE_AUTO


class CustomRigManager:

    TYPE_T = "T"   # translation
    TYPE_R = "R"   # rotation

    # .type 어트리뷰트 값 -> 위 문자열
    _TYPE_FROM_ENUM = {0: TYPE_T, 1: TYPE_R}

    TYPE_LABEL = {TYPE_T: "Translation", TYPE_R: "Rotation"}

    # ----------------------------------------------------------
    # 조회
    # ----------------------------------------------------------

    @staticmethod
    def get_retargeter(character):
        """캐릭터에 붙은 CustomRigRetargeterNode. 커스텀 리그가 없으면 ""."""
        if not character or not cmds.objExists(character):
            return ""
        conns = cmds.listConnections(character + ".message",
                                     destination=True,
                                     type="CustomRigRetargeterNode") or []
        return conns[0] if conns else ""

    @staticmethod
    def get_mappings(retargeter):
        """리타게터의 매핑 전부를 dict 리스트로."""
        out = []
        if not retargeter or not cmds.objExists(retargeter):
            return out
        for node in (cmds.listConnections(retargeter + ".mappings") or []):
            dest = cmds.listConnections(node + ".destinationRig") or []
            out.append({
                "node": node,
                "body": cmds.getAttr(node + ".bodyPart"),
                "type": CustomRigManager._TYPE_FROM_ENUM.get(cmds.getAttr(node + ".type")),
                "id": cmds.getAttr(node + ".id"),
                "dest": dest[0] if dest else None,
                "offset": list(cmds.getAttr(node + ".offset")[0]),
            })
        return out

    @staticmethod
    def find_mapping(retargeter, body, type_):
        """(bodyPart, type) 으로 매핑 노드 하나를 찾는다. 없으면 None."""
        for m in CustomRigManager.get_mappings(retargeter):
            if m["body"] == body and m["type"] == type_:
                return m
        return None

    # ----------------------------------------------------------
    # 잠금 확인 (모달 다이얼로그 회피)
    # ----------------------------------------------------------

    @staticmethod
    def _is_locked(node, attr):
        """HumanIK 의 isLocked 와 같은 판정 - 부모 어트리뷰트와 XYZ 자식 전부를 본다."""
        for plug in (attr, attr + "X", attr + "Y", attr + "Z"):
            full = "{0}.{1}".format(node, plug)
            if not cmds.objExists(full):
                continue
            try:
                if cmds.getAttr(full, lock=True):
                    return True
            except Exception:
                pass
        return False

    @staticmethod
    def _locked_for(node, type_):
        attr = "translate" if type_ == CustomRigManager.TYPE_T else "rotate"
        return CustomRigManager._is_locked(node, attr)

    # ----------------------------------------------------------
    # Mirror
    # ----------------------------------------------------------

    @staticmethod
    def mirror_mappings(character, direction, scope_slot_ids=None,
                        mode=MODE_AUTO, axis="X", tolerance=1.0,
                        overwrite=False, copy_offset=True, dry_run=False):
        """이미 매핑된 한쪽 컨트롤러를 근거로 반대쪽 이펙터를 자동 매핑한다.

        character       : HIKCharacterNode.
        direction       : HIKManager.DIRECTION_L2R / DIRECTION_R2L 와 같은 문자열.
        scope_slot_ids  : 대상 슬롯 ID 집합. None 이면 방향이 있는 이펙터 전부.
        copy_offset     : 소스 매핑의 offset 을 그대로 복사할지.
        dry_run         : True 면 아무것도 바꾸지 않고 계획만 돌려준다(Preview).

        반환 : (records, message)
          record = {body, type, src, dst_body, dst_id, dst, status, reason}
          status = ok / ready / skip / fail
        """
        retargeter = CustomRigManager.get_retargeter(character)
        if not retargeter:
            return ([], "[Warning] '{0}' has no Custom Rig. Create it in the HumanIK window "
                        "(Custom Rig tab) and map one side first.".format(character or "-"))

        from_side = HIKNodes.LEFT if direction.startswith("Left") else HIKNodes.RIGHT
        to_side = HIKNodes.RIGHT if from_side == HIKNodes.LEFT else HIKNodes.LEFT

        mappings = CustomRigManager.get_mappings(retargeter)
        existing_keys = set((m["body"], m["type"]) for m in mappings)

        resolver = MirrorResolver(mode=mode, to_side=to_side, axis=axis,
                                  tolerance=tolerance, node_type=None)

        records = []
        for m in mappings:
            body = m["body"]
            if HIKNodes.side_of(HIKNodes.slot_id(body)) != from_side:
                # 슬롯 이름이 아니거나(예: 마지막 Spine) 방향이 없는 이펙터.
                continue
            if scope_slot_ids is not None and m["id"] not in scope_slot_ids:
                continue

            dst_body = HIKNodes.mirror_name(body)
            dst_id = HIKNodes.slot_id(dst_body) if dst_body else None

            rec = {
                "body": body,
                "type": m["type"],
                "src": m["dest"],
                "dst_body": dst_body,
                "dst_id": dst_id,
                "dst": None,
                "offset": m["offset"],
                "status": "fail",
                "reason": "",
            }

            if not dst_body or dst_id is None:
                rec["reason"] = "no mirrored effector for '{0}'".format(body)
                records.append(rec)
                continue
            if not m["dest"]:
                rec["reason"] = "source mapping has no controller"
                records.append(rec)
                continue

            found, why = resolver.resolve(m["dest"])
            rec["reason"] = why
            if not found:
                records.append(rec)
                continue

            short = found.split("|")[-1]
            rec["dst"] = short

            if short == m["dest"].split("|")[-1]:
                rec["reason"] = "resolved to the source itself"
                records.append(rec)
                continue

            if (dst_body, m["type"]) in existing_keys:
                cur = CustomRigManager.find_mapping(retargeter, dst_body, m["type"])
                cur_dest = (cur or {}).get("dest")
                if cur_dest and cur_dest.split("|")[-1] == short:
                    rec["status"] = "skip"
                    rec["reason"] = "already mapped"
                    records.append(rec)
                    continue
                if not overwrite:
                    rec["status"] = "skip"
                    rec["reason"] = "already mapped to '{0}' (enable Overwrite)".format(cur_dest)
                    records.append(rec)
                    continue
                rec["reason"] += " / replacing '{0}'".format(cur_dest)

            if CustomRigManager._locked_for(short, m["type"]):
                rec["status"] = "skip"
                rec["reason"] = "'{0}' has locked {1} channels".format(
                    short, "translate" if m["type"] == CustomRigManager.TYPE_T else "rotate")
                records.append(rec)
                continue

            rec["status"] = "ready"
            records.append(rec)

        # --- 적용 ---
        if not dry_run:
            todo = [r for r in records if r["status"] == "ready"]
            if todo:
                was_connected = CustomRigManager._is_connected(retargeter)
                with undo_chunk():
                    # 매 호출마다 끊었다 잇는 대신 배치 전체를 한 번만 끊는다.
                    if was_connected:
                        CustomRigManager._disconnect(retargeter)
                    try:
                        for r in todo:
                            CustomRigManager._apply(retargeter, r, copy_offset)
                    finally:
                        if was_connected:
                            CustomRigManager._connect(retargeter)
                CustomRigManager.refresh_custom_rig_ui()

        return (records, CustomRigManager.summarize(records, character, dry_run))

    @staticmethod
    def _apply(retargeter, rec, copy_offset):
        """레코드 하나를 실제 매핑으로 만든다. rec["status"] 를 갱신한다."""
        body = rec["dst_body"]
        type_ = rec["type"]
        try:
            # 덮어쓰기면 기존 매핑을 먼저 지운다 - 같은 (body, type) 이 두 개 생기지 않도록.
            if CustomRigManager.find_mapping(retargeter, body, type_):
                mel.eval('RetargeterDeleteMapping("{0}","{1}","{2}")'.format(
                    retargeter, body, type_))

            mel.eval('RetargeterAddMapping("{0}","{1}","{2}","{3}","{4}")'.format(
                retargeter, body, type_, rec["dst"], rec["dst_id"]))
        except Exception as e:
            rec["status"] = "fail"
            rec["reason"] = str(e)
            return

        created = CustomRigManager.find_mapping(retargeter, body, type_)
        if not created:
            rec["status"] = "fail"
            rec["reason"] = "RetargeterAddMapping produced no mapping"
            return

        if copy_offset:
            ox, oy, oz = rec["offset"]
            for axis_name, value in (("X", ox), ("Y", oy), ("Z", oz)):
                try:
                    cmds.setAttr("{0}.offset{1}".format(created["node"], axis_name), value)
                except Exception:
                    pass

        rec["status"] = "ok"

    # ----------------------------------------------------------
    # 리타게터 연결 상태
    # ----------------------------------------------------------

    @staticmethod
    def _is_connected(retargeter):
        try:
            return bool(cmds.getAttr(retargeter + ".connected"))
        except Exception:
            return False

    @staticmethod
    def _disconnect(retargeter):
        try:
            mel.eval('RetargeterDisconnect("{0}")'.format(retargeter))
        except Exception:
            pass

    @staticmethod
    def _connect(retargeter):
        try:
            mel.eval('RetargeterConnect("{0}")'.format(retargeter))
        except Exception:
            pass

    # ----------------------------------------------------------
    # 보고 / UI 갱신
    # ----------------------------------------------------------

    @staticmethod
    def summarize(records, character, dry_run=False):
        if not records:
            return ("[Mirror] Nothing to mirror - no Custom Rig mapping on the source side "
                    "within the chosen scope.")
        counts = {"ok": 0, "ready": 0, "skip": 0, "fail": 0}
        for r in records:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
        if dry_run:
            return "[Preview] {0} to map, {1} skipped, {2} unresolved (of {3}).".format(
                counts["ready"], counts["skip"], counts["fail"], len(records))
        return "[Mirror] {0} mapping(s) created on '{1}', {2} skipped, {3} failed (of {4}).".format(
            counts["ok"], character, counts["skip"], counts["fail"], len(records))

    @staticmethod
    def refresh_custom_rig_ui():
        """HumanIK 창이 떠 있으면 Custom Rig 표시를 갱신한다(없으면 조용히 넘어간다)."""
        try:
            mel.eval('catchQuiet( `hikUpdateCustomRigUI` );')
        except Exception:
            pass
