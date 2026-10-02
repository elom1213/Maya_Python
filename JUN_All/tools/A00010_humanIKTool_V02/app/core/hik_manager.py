# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-02
# A00010_humanIKTool_V02 - HumanIK 캐릭터라이제이션 핵심 로직 (maya.cmds / mel, UI 비의존)
#
# 레거시 A00010_humanIKTool(maya.cmds UI)의 JUN_get_HIK_node / JUN_assign_joints 를
# UI 비의존 정적 메서드로 옮기면서 다음 버그를 수정했다.
#   - HIK 노드 0개 / 미선택, 조인트 리스트 비었을 때의 IndexError 가드
#   - 조인트 수와 슬롯 수 불일치 시 조용히 잘리던 zip -> mismatch 를 명시 경고
#   - 실패해도 무조건 "succeeded" 출력하던 문제 -> 성공/실패 카운트로 정확히 보고
#   - cmds.ls(fl=True) 전체 노드 순회 -> cmds.ls(type="HIKCharacterNode") 직접 조회
#
# v02.01 : 좌 -> 우 Mirror Assign 추가 (mirror_joints). 슬롯 테이블은 hik_nodes.py,
#          반대쪽 노드를 고르는 규칙은 mirror_resolver.py 에 있다.
#
# v02.04 : Neck 1 to head / Neck 2 to head -> **Neck to head** 하나. 조인트 n 개 중 앞 n-1 개 = 목 체인
#          (Neck, Neck1, Neck2 ... 슬롯 순서), 마지막 1 개 = Head. 목 슬롯은 HumanIK 에 10 개(Neck ~ Neck9).
#          Mirror : same_root - HIK 에 할당된 조인트의 최상위 조인트 아래에서만 반대쪽을 찾는다.
#
# CopyKeyManager(A00110) 와 동일한 스타일: 정적 메서드 + undoInfo 청크 + (count, msg) 반환.

import maya.cmds as cmds
import maya.mel as mel

from Framework.core.maya_undo import undo_chunk

from tools.A00010_humanIKTool_V02.app.core.hik_nodes import HIKNodes
from tools.A00010_humanIKTool_V02.app.core.mirror_resolver import (
    MirrorResolver, MODE_AUTO, SEARCH_ROOTS, SEARCH_SCENE, top_joint)


class HIKManager:
    """
    조인트 리스트를 선택한 본 체인의 HumanIK 슬롯 ID 에 순서대로 할당한다.
    리스트의 i 번째 조인트 -> 본 체인 슬롯 ID 의 i 번째 값으로 매칭.
    """

    # 본 체인 라벨 -> HumanIK characterization 슬롯 ID 목록.
    # 값은 mel setCharacterObject(joint, hikNode, slotId, 0) 의 3번째 인자(슬롯 인덱스)다.
    # 리스트 순서가 곧 조인트 매칭 순서이므로 순서를 바꾸지 말 것.
    BONE_CHAINS = {
        "Spine":                    [1, 8, 23, 24, 25, 26, 27, 28],
        "Neck to head":             [20, 32, 33, 34, 35, 36, 37, 38, 39, 40, 15],
        # 목 체인 + 머리. 실제 할당 슬롯은 조인트 수로 정한다 - chain_slots() (v02.04).
        # 여기 값은 목 슬롯 전부 + Head (Mirror 의 Selected Chain 범위용).
        "Shoulder to hand : Left":  [18, 9, 10, 11],
        "Fingers : Left":           [50, 51, 52, 54, 55, 56, 58, 59, 60, 62, 63, 64, 66, 67, 68],
        "Leg : Left":               [2, 3, 4, 16],
        "Shoulder to hand : Right": [19, 12, 13, 14],
        "Fingers : Right":          [74, 75, 76, 78, 79, 80, 82, 83, 84, 86, 87, 88, 90, 91, 92],
        "Leg : Right":              [5, 6, 7, 17],
    }

    # Neck to head (v02.04) : 목 슬롯은 Neck(20) 다음 Neck1 ~ Neck9(32 ~ 40) - 최대 10 개, 머리는 Head(15).
    NECK_TO_HEAD = "Neck to head"
    NECK_SLOTS = [20, 32, 33, 34, 35, 36, 37, 38, 39, 40]
    HEAD_SLOT = 15

    # Mirror 대상 범위. 값은 슬롯 ID 목록이고 None 이면 "방향이 있는 슬롯 전부".
    SCOPE_ALL = "All Sided Slots"
    SCOPE_ARMS_LEGS = "Arms & Legs"
    SCOPE_CHAIN = "Selected Chain"

    MIRROR_SCOPES = [SCOPE_ALL, SCOPE_ARMS_LEGS, SCOPE_CHAIN]

    DIRECTION_L2R = "Left -> Right"
    DIRECTION_R2L = "Right -> Left"

    DIRECTIONS = [DIRECTION_L2R, DIRECTION_R2L]

    @staticmethod
    def chain_labels():
        """UI 라디오/콤보가 그대로 쓰는 본 체인 라벨 목록(정의 순서 유지)."""
        return list(HIKManager.BONE_CHAINS.keys())

    @staticmethod
    def chain_slots(chain_label, joint_count):
        """조인트 joint_count 개를 할당할 슬롯 ID 목록. 못 하면 (None, 이유).

        고정 체인은 BONE_CHAINS 그대로. **Neck to head** 는 조인트 수로 정한다 (v02.04):
          [jnt_01 ... jnt_(n-1)] = 목 체인 -> NECK_SLOTS 앞에서부터 n-1 개 (Neck, Neck1, Neck2 ...)
          jnt_n                  = 머리   -> HEAD_SLOT
        반환 : (slot_ids, "") / (None, 이유)
        """
        if chain_label != HIKManager.NECK_TO_HEAD:
            return HIKManager.BONE_CHAINS.get(chain_label), ""
        neck_count = joint_count - 1
        if neck_count < 0:
            return None, "no joints"
        if neck_count > len(HIKManager.NECK_SLOTS):
            return None, ("{0} neck joints - HumanIK has only {1} neck slots (Neck ~ Neck9). "
                          "List at most {2} joints (necks + head).".format(
                              neck_count, len(HIKManager.NECK_SLOTS),
                              len(HIKManager.NECK_SLOTS) + 1))
        return HIKManager.NECK_SLOTS[:neck_count] + [HIKManager.HEAD_SLOT], ""

    @staticmethod
    def get_hik_nodes():
        """씬의 모든 HIKCharacterNode 이름을 반환. 없으면 빈 리스트."""
        return cmds.ls(type="HIKCharacterNode") or []

    @staticmethod
    def control_rig(hik_node):
        """캐릭터에 붙어 있는 Control Rig 이름. 없으면 "".

        HumanIK 의 hikSetCharacterObject 는 컨트롤 리그가 있으면 **경고만 찍고 아무것도 하지
        않는다**(예외도 없다). 그대로 두면 "할당했다" 고 잘못 보고하게 되므로 미리 확인한다.
        """
        if not hik_node:
            return ""
        try:
            return mel.eval('hikGetControlRig("{0}")'.format(hik_node)) or ""
        except Exception:
            return ""

    # ----------------------------------------------------------
    # 할당
    # ----------------------------------------------------------

    @staticmethod
    def _set_slot(joint, hik_node, slot_id):
        """슬롯 하나 할당 후 연결을 되읽어 실제로 붙었는지 확인한다.

        setCharacterObject 는 실패해도 조용한 경로가 여럿이라(컨트롤 리그 존재 등)
        되읽기가 유일하게 믿을 수 있는 성공 판정이다.
        """
        try:
            mel.eval('setCharacterObject("{0}","{1}",{2},0)'.format(joint, hik_node, slot_id))
        except Exception as e:
            return False, str(e)

        assigned = HIKNodes.assigned_node(hik_node, slot_id)
        if not assigned:
            return False, "slot stayed empty after setCharacterObject"
        # v02.04 : 같은 이름의 조인트가 여럿일 수 있으니 이름이 아니라 **풀 패스**로 비교한다.
        if not HIKManager._same_node(assigned, joint):
            return False, "slot holds '{0}'".format(assigned)
        return True, ""

    @staticmethod
    def _same_node(a, b):
        """두 이름(짧은 이름 · 부분 경로 · 풀 패스)이 같은 노드인가. 하나라도 못 찾으면 이름으로 비교."""
        pa = cmds.ls(a, long=True) or []
        pb = cmds.ls(b, long=True) or []
        if len(pa) == 1 and len(pb) == 1:
            return pa[0] == pb[0]
        return a.split("|")[-1].split(":")[-1] == b.split("|")[-1].split(":")[-1]

    @staticmethod
    def assign_joints(joints, hik_node, chain_label):
        """
        joints[i] 를 BONE_CHAINS[chain_label][i] 슬롯에 setCharacterObject 로 할당한다.

        joints       : 조인트 이름 리스트. 리스트 순서가 슬롯 순서와 매칭됨.
        hik_node     : 대상 HIKCharacterNode 이름.
        chain_label  : BONE_CHAINS 의 키.
        반환         : (할당 성공 수, 메시지)
        """
        # --- 입력 가드 (레거시에서 IndexError 나던 지점들) ---
        if not hik_node:
            return (0, "[Warning] No HIK node selected. Click 'Get HIK Nodes' and select one.")
        if not joints:
            return (0, "[Warning] Joint list is empty. Add joints to assign.")
        if chain_label not in HIKManager.BONE_CHAINS:
            return (0, "[Warning] Unknown bone chain: {0}".format(chain_label))

        rig = HIKManager.control_rig(hik_node)
        if rig:
            return (0, "[Warning] '{0}' has a Control Rig ('{1}'). HumanIK refuses definition "
                       "edits while a rig exists - delete it first.".format(hik_node, rig))

        slot_ids, why = HIKManager.chain_slots(chain_label, len(joints))
        if slot_ids is None:
            return (0, "[Warning] [{0}] {1}".format(chain_label, why))

        # 매칭 가능한 쌍 수(짧은 쪽 기준). 레거시 zip 은 여기서 조용히 잘렸으므로 경고로 노출.
        pair_count = min(len(joints), len(slot_ids))

        done = 0
        failed = 0

        with undo_chunk():
            for i in range(pair_count):
                jnt = joints[i]
                slot_id = slot_ids[i]
                ok, why = HIKManager._set_slot(jnt, hik_node, slot_id)
                if ok:
                    done += 1
                else:
                    failed += 1
                    print("[HIK assign] FAILED {0} -> slot {1}: {2}".format(jnt, slot_id, why))

        msg = "[{0}] {1} joint(s) assigned to '{2}'.".format(chain_label, done, hik_node)
        if failed:
            msg += " {0} failed (see script editor).".format(failed)
        if len(joints) != len(slot_ids):
            msg += " [Warning] Joint count ({0}) != chain slot count ({1}); {2} matched.".format(
                len(joints), len(slot_ids), pair_count)

        return (done, msg)

    # ----------------------------------------------------------
    # Mirror
    # ----------------------------------------------------------

    @staticmethod
    def scope_slots(scope, chain_label=None):
        """Mirror 범위 라벨 -> 대상 슬롯 ID 집합. None 이면 방향이 있는 슬롯 전부."""
        if scope == HIKManager.SCOPE_ARMS_LEGS:
            ids = []
            for label in ("Shoulder to hand : Left", "Shoulder to hand : Right",
                          "Leg : Left", "Leg : Right"):
                ids.extend(HIKManager.BONE_CHAINS[label])
            return set(ids)
        if scope == HIKManager.SCOPE_CHAIN:
            return set(HIKManager.BONE_CHAINS.get(chain_label, []))
        return None

    @staticmethod
    def hik_root_joints(hik_node, assigned=None):
        """HIK 에 할당된 조인트들의 **최상위 조인트**(풀 패스, 정렬). 할당된 게 없으면 [].

        보통 하나(Reference 또는 Hips 위로 이어진 맨 위 조인트)다. 정의가 여러 계층에 걸쳐 있으면
        그 계층마다 하나씩 - Mirror in same root 는 그 아래를 모두 본다.
        """
        assigned = assigned if assigned is not None else HIKNodes.definition(hik_node)
        roots = set()
        for node in assigned.values():
            top = top_joint(node)
            if top:
                roots.add(top)
        return sorted(roots)

    @staticmethod
    def mirror_joints(hik_node, direction=DIRECTION_L2R, scope=SCOPE_ALL, chain_label=None,
                      mode=MODE_AUTO, axis="X", tolerance=1.0,
                      overwrite=False, dry_run=False, same_root=True):
        """이미 할당된 한쪽 슬롯을 근거로 반대쪽 슬롯을 자동 할당한다.

        hik_node   : 대상 HIKCharacterNode.
        direction  : DIRECTION_L2R / DIRECTION_R2L.
        scope      : SCOPE_* 라벨. SCOPE_CHAIN 이면 chain_label 이 필요하다.
        mode       : mirror_resolver 의 MODE_NAME / MODE_POSITION / MODE_AUTO.
        overwrite  : 반대쪽 슬롯에 이미 뭔가 있을 때 덮어쓸지.
        dry_run    : True 면 아무것도 바꾸지 않고 계획만 돌려준다(Preview).
        same_root  : True(Mirror in same root) 면 HIK 에 할당된 조인트의 최상위 조인트 **아래에서만**
                     반대쪽을 찾는다 - 같은 이름의 조인트가 씬에 더 있어도 이 캐릭터 것만 (v02.04).
                     False 면 씬의 모든 조인트에서 찾고, 같은 이름이 여럿이면 실패로 보고한다.

        반환 : (records, message)
          record = {slot, slot_name, src, dst_slot, dst_slot_name, dst, status, reason}
          status = ok / ready / skip / fail
        """
        if not hik_node or not cmds.objExists(hik_node):
            return ([], "[Warning] No HIK node selected. Click 'Get HIK Nodes' and select one.")

        if not dry_run:
            rig = HIKManager.control_rig(hik_node)
            if rig:
                return ([], "[Warning] '{0}' has a Control Rig ('{1}'). HumanIK refuses "
                            "definition edits while a rig exists - delete it first.".format(
                                hik_node, rig))

        from_side = HIKNodes.LEFT if direction == HIKManager.DIRECTION_L2R else HIKNodes.RIGHT
        to_side = HIKNodes.RIGHT if from_side == HIKNodes.LEFT else HIKNodes.LEFT

        allowed = HIKManager.scope_slots(scope, chain_label)

        assigned = HIKNodes.definition(hik_node)
        roots = HIKManager.hik_root_joints(hik_node, assigned) if same_root else []
        resolver = MirrorResolver(mode=mode, to_side=to_side, axis=axis,
                                  tolerance=tolerance, node_type="joint",
                                  search=SEARCH_ROOTS if same_root else SEARCH_SCENE,
                                  roots=roots)

        records = []
        for slot_id in sorted(assigned):
            if allowed is not None and slot_id not in allowed:
                continue
            if HIKNodes.side_of(slot_id) != from_side:
                continue

            dst_slot = HIKNodes.mirror_slot(slot_id)
            if dst_slot is None:
                continue

            src = assigned[slot_id]
            rec = {
                "slot": slot_id,
                "slot_name": HIKNodes.name(slot_id),
                "src": src,
                "dst_slot": dst_slot,
                "dst_slot_name": HIKNodes.name(dst_slot),
                "dst": None,
                "dst_path": None,
                "status": "fail",
                "reason": "",
            }

            existing = HIKNodes.assigned_node(hik_node, dst_slot)

            found, why = resolver.resolve(src)
            rec["reason"] = why

            if not found:
                records.append(rec)
                continue

            short = found.split("|")[-1]
            rec["dst"] = short          # 표시용
            # v02.04 : 할당은 **풀 패스**로 - 짧은 이름은 같은 이름의 조인트가 씬에 여럿이면
            # setCharacterObject 가 "No object matches name" 으로 실패한다(실측).
            rec["dst_path"] = found

            if HIKManager._same_node(found, src):
                rec["status"] = "fail"
                rec["reason"] = "resolved to the source itself"
                records.append(rec)
                continue

            if existing:
                if HIKManager._same_node(existing, found):
                    rec["status"] = "skip"
                    rec["reason"] = "already assigned"
                    records.append(rec)
                    continue
                if not overwrite:
                    rec["status"] = "skip"
                    rec["reason"] = "slot already holds '{0}' (enable Overwrite)".format(existing)
                    records.append(rec)
                    continue
                rec["reason"] += " / replacing '{0}'".format(existing)

            rec["status"] = "ready"
            records.append(rec)

        # --- 적용 ---
        if not dry_run:
            todo = [r for r in records if r["status"] == "ready"]
            if todo:
                with undo_chunk():
                    for r in todo:
                        ok, why = HIKManager._set_slot(r.get("dst_path") or r["dst"],
                                                       hik_node, r["dst_slot"])
                        if ok:
                            r["status"] = "ok"
                        else:
                            r["status"] = "fail"
                            r["reason"] = why
                HIKManager.refresh_hik_ui()

        msg = HIKManager.summarize(records, hik_node, dry_run)
        if same_root:
            msg += " Searched under: {0}.".format(
                ", ".join(r.split("|")[-1] for r in roots) if roots else "(no HIK root joint)")
        else:
            msg += " Searched: every joint in the scene."
        return (records, msg)

    @staticmethod
    def summarize(records, hik_node, dry_run=False):
        """Mirror 결과 한 줄 요약."""
        if not records:
            return ("[Mirror] Nothing to mirror - no assigned slot on the source side "
                    "within the chosen scope.")
        counts = {"ok": 0, "ready": 0, "skip": 0, "fail": 0}
        for r in records:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
        if dry_run:
            return "[Preview] {0} to assign, {1} skipped, {2} unresolved (of {3}).".format(
                counts["ready"], counts["skip"], counts["fail"], len(records))
        return "[Mirror] {0} assigned to '{1}', {2} skipped, {3} failed (of {4}).".format(
            counts["ok"], hik_node, counts["skip"], counts["fail"], len(records))

    @staticmethod
    def refresh_hik_ui():
        """HumanIK Character Controls 창이 떠 있으면 정의 표시를 갱신한다.

        창이 없을 때 호출하면 MEL 이 에러를 내므로 catchQuiet 으로 감싼다.
        """
        try:
            mel.eval('catchQuiet( `hikUpdateDefinitionUI` );')
        except Exception:
            pass
