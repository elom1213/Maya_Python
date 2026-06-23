# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-17
# A00010_humanIKTool_V02 - HumanIK 캐릭터라이제이션 핵심 로직 (maya.cmds / mel, UI 비의존)
#
# 레거시 A00010_humanIKTool(maya.cmds UI)의 JUN_get_HIK_node / JUN_assign_joints 를
# UI 비의존 정적 메서드로 옮기면서 다음 버그를 수정했다.
#   - HIK 노드 0개 / 미선택, 조인트 리스트 비었을 때의 IndexError 가드
#   - 조인트 수와 슬롯 수 불일치 시 조용히 잘리던 zip → mismatch 를 명시 경고
#   - 실패해도 무조건 "succeeded" 출력하던 문제 → 성공/실패 카운트로 정확히 보고
#   - cmds.ls(fl=True) 전체 노드 순회 → cmds.ls(type="HIKCharacterNode") 직접 조회
#
# CopyKeyManager(A00110) 와 동일한 스타일: 정적 메서드 + undoInfo 청크 + (count, msg) 반환.

import maya.cmds as cmds
import maya.mel as mel

from Framework.core.maya_undo import undo_chunk


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
        "Shoulder to hand : Left":  [18, 9, 10, 11],
        "Fingers : Left":           [50, 51, 52, 54, 55, 56, 58, 59, 60, 62, 63, 64, 66, 67, 68],
        "Shoulder to hand : Right": [19, 12, 13, 14],
        "Fingers : Right":          [74, 75, 76, 78, 79, 80, 82, 83, 84, 86, 87, 88, 90, 91, 92],
        "Neck 1 to head":           [20, 15],
        "Neck 2 to head":           [20, 32, 15],
        "Leg : Left":               [2, 3, 4, 16],
        "Leg : Right":              [5, 6, 7, 17],
    }

    @staticmethod
    def chain_labels():
        """UI 라디오/콤보가 그대로 쓰는 본 체인 라벨 목록(정의 순서 유지)."""
        return list(HIKManager.BONE_CHAINS.keys())

    @staticmethod
    def get_hik_nodes():
        """씬의 모든 HIKCharacterNode 이름을 반환. 없으면 빈 리스트."""
        return cmds.ls(type="HIKCharacterNode") or []

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

        slot_ids = HIKManager.BONE_CHAINS[chain_label]

        # 매칭 가능한 쌍 수(짧은 쪽 기준). 레거시 zip 은 여기서 조용히 잘렸으므로 경고로 노출.
        pair_count = min(len(joints), len(slot_ids))

        done = 0
        failed = 0

        with undo_chunk():
            for i in range(pair_count):
                jnt = joints[i]
                slot_id = slot_ids[i]
                try:
                    mel.eval('setCharacterObject("{0}","{1}",{2},0)'.format(jnt, hik_node, slot_id))
                    done += 1
                except Exception as e:
                    failed += 1
                    print("[HIK assign] FAILED {0} -> slot {1}: {2}".format(jnt, slot_id, e))

        msg = "[{0}] {1} joint(s) assigned to '{2}'.".format(chain_label, done, hik_node)
        if failed:
            msg += " {0} failed (see script editor).".format(failed)
        if len(joints) != len(slot_ids):
            msg += " [Warning] Joint count ({0}) != chain slot count ({1}); {2} matched.".format(
                len(joints), len(slot_ids), pair_count)

        return (done, msg)
