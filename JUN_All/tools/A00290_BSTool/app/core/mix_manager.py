# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-06
# A00290_BSTool - Mix Targets 탭 핵심 로직 (maya.cmds, UI 비의존)
#
# 목적: 몇몇 타겟(소스)을 원하는 비율로 섞은 모양을 **다른 타겟들에 한꺼번에 더한다**.
#
#   예) 소스 [a, b, c] 를 [1.0, 0.5, 0.8] 로 섞고, 대상으로 나머지 타겟들을 고르면
#       대상 타겟마다:  new_delta = old_delta + (1.0*delta(a) + 0.5*delta(b) + 0.8*delta(c))
#
#   즉 "a 를 100%, b 를 50%, c 를 80% 로 섞은 만큼" 대상 타겟들의 모양이 변형된다.
#   weight 를 그만큼 올려 눈으로 보던 모양이, 그대로 그 타겟의 모양에 굳는 셈이다.
#
# 왜 델타를 그냥 더하면 되는가:
#   blendShape 평가 자체가 base + Σ(weight_i * delta_i) 다. 즉 **같은 지오메트리의 델타는
#   서로 같은 공간에 있고 그대로 더할 수 있다** — 마야가 매 프레임 하는 일과 같다.
#   그래서 소스 델타의 가중합이 곧 "그만큼의 변형"이다.
#
# 쓰는 곳:
#   - 여러 셰이프에 공통으로 들어가야 할 보정(예: 입 벌림 보정)을 관련 타겟 전체에 한 번에 반영
#   - 기준 셰이프가 바뀌었을 때 그 차이를 나머지 타겟에 일괄 이식
#
# 손대는 방법은 대상 타겟이 어떻게 저장돼 있느냐에 따라 갈린다(delta_utils 참고).
#   baked  — inputPointsTarget / inputComponentsTarget 을 새로 써 넣는다(정점 집합이
#            늘어날 수 있으므로 컴포넌트 목록도 함께 갱신).
#   live   — 타겟 메시의 정점을 옮긴다. 델타 공간을 되돌려 옮기고 검증까지 한다.
#
# 인비트윈: 타겟의 **완성 모양(weight 1.0 아이템)** 만 바꾼다. 인비트윈 아이템까지 같은
#   오프셋을 더하면 중간 단계가 통째로 어긋나기 때문이다. 인비트윈이 있는 타겟은 로그로 알린다.
#
# ==========================================================================
# 베이스(최종) 메시도 함께 변형하기 — BASE_* 모드
# ==========================================================================
#
# 규칙은 하나다: **체크한 것은 믹스만큼 변형되고, 체크하지 않은 것은 모양이 그대로다.**
#
# 베이스를 건드리면 셈이 달라진다. 타겟은 "베이스로부터의 오프셋(델타)"으로 저장되므로
#   최종 모양 = 베이스 + 델타
# 즉 **베이스를 M 만큼 옮기면 델타를 그대로 둔 타겟은 자동으로 M 만큼 따라 움직인다.**
# 그래서 모드마다 손대는 곳이 다르다.
#
#   BASE_NONE (기본) — 베이스는 그대로. 체크한 타겟만 델타에 M 을 더한다.
#                      (체크한 타겟의 모양 +M, 나머지·베이스 그대로)
#
#   BASE_EDIT — 중립(바인드) 셰이프를 M 만큼 옮긴다. 그러면
#       · 체크한 타겟   : 델타를 **그대로 두면** 베이스를 따라 +M (원하는 결과).
#                         단 live 타겟은 씬의 타겟 메시도 같이 옮겨야 델타가 유지된다.
#       · 체크 안 한 타겟: 그냥 두면 덩달아 +M 이 되므로, baked 는 델타에서 M 을 빼
#                         **모양이 제자리에 남게** 보정한다(live 는 메시가 안 움직였으니
#                         델타가 알아서 줄어 제자리다). 소스도 여기 해당한다.
#
#   BASE_NEW — 리그는 전혀 건드리지 않고 '중립 + M' 모양의 **새 메시**를 하나 만든다.
#              타겟 처리는 BASE_NONE 과 같다. 스킨/바인드 셰이프를 손대기 부담스러울 때.
#
# 중립에 닿는 법 (v01.18 에서 고침):
#   · BASE_NEW 는 blendShape 입력 플러그의 메시 **데이터**를 그대로 읽는다. 상류가 무엇이든
#     (orig 셰이프 · tweak · skinCluster · 래티스 …) 언제나 읽히므로 **항상 만들 수 있다**.
#   · BASE_EDIT 는 옮길 수 있는 셰이프가 필요하다. 상류를 **한 단계만 보면 안 된다** —
#     정점을 한 번이라도 건드린 메시에는 tweak 노드가 끼어 있어 `tweak1.outputGeometry[0]`
#     이 잡힌다(v01.17 이 여기서 실패했다). geometryFilter 는 모두 input[N].inputGeometry 로
#     거슬러 올라갈 수 있으므로 메시가 나올 때까지 따라간다.
#   · 옮긴 뒤에는 blendShape 이 **실제로 받는 중립**을 다시 읽어 M 만큼 움직였는지 확인한다.
#     사이에 낀 디포머가 오프셋을 바꿔 버리면(스킨이 앞에 있는 경우 등) 되돌리고 BASE_NEW 를
#     쓰라고 알린다. tweak 처럼 오프셋을 그대로 통과시키는 노드면 그대로 성공한다.

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk

from . import blendshape_utils as bsu
from . import delta_utils as du


#: 베이스(최종) 메시를 어떻게 할지
BASE_NONE = "none"      # 건드리지 않는다
BASE_EDIT = "edit"      # 중립(바인드) 셰이프를 함께 옮긴다
BASE_NEW = "new"        # '중립 + 믹스' 새 메시를 만든다 (리그는 그대로)

BASE_MODES = (BASE_NONE, BASE_EDIT, BASE_NEW)

#: 중립 셰이프와 blendShape 사이에 있어도 **오프셋을 그대로 통과시키는** 노드.
#  tweak 은 정점마다 값을 더하기만 하므로 상류에서 옮긴 만큼이 그대로 내려온다.
#  (정점을 한 번이라도 건드린 메시에는 거의 항상 이 노드가 끼어 있다.)
PASS_THROUGH_TYPES = ("tweak",)


class MixManager:

    # UI 가 `from ... import MixManager` 하나로 모드까지 쓰게 클래스에도 붙여 둔다.
    BASE_NONE = BASE_NONE
    BASE_EDIT = BASE_EDIT
    BASE_NEW = BASE_NEW

    # ==================================================
    # 조회
    # ==================================================

    @staticmethod
    def list_targets(bs_node):
        """blendShape 타겟 이름 목록(weight 인덱스 순)."""
        return bsu.get_blendshape_targets(bs_node)

    @staticmethod
    def current_weight(bs_node, target_name):
        """타겟의 현재 weight 값(못 읽으면 None). 'Use Scene Weights' 용."""
        try:
            return cmds.getAttr("{0}.{1}".format(bs_node, target_name))
        except Exception:
            return None

    @staticmethod
    def _short(name):
        return (name or "").split("|")[-1]

    @staticmethod
    def _new_mesh_name(bs_node, geo_idx):
        """새로 만들 메시 이름. 베이스 메시 이름을 따르고, 여러 지오메트리면 번호를 붙인다."""
        base = du.base_shape_for_geo(bs_node, geo_idx)
        parents = cmds.listRelatives(base, parent=True) or [] if base else []
        stem = MixManager._short(parents[0] if parents else (base or bs_node))
        geos = cmds.getAttr(bs_node + ".inputTarget", multiIndices=True) or [0]
        return "{0}_mixed{1}".format(stem, geo_idx if len(geos) > 1 else "")

    @staticmethod
    def base_mesh_info(bs_node):
        """UI 라벨용 — blendShape 이 물고 있는 베이스 메시와 중립을 옮길 수 있는지.

        반환: (표시 문자열, 중립을 직접 옮길 수 있는가)
        """
        if not bsu.is_blendshape(bs_node):
            return "Base mesh: -", False

        geo_indices = cmds.getAttr(bs_node + ".inputTarget", multiIndices=True) or [0]
        parts = []
        editable_all = True

        for geo_idx in geo_indices:
            shape = du.base_shape_for_geo(bs_node, geo_idx)
            parents = cmds.listRelatives(shape, parent=True) or [] if shape else []
            name = MixManager._short(parents[0] if parents else (shape or "?"))

            neutral, between = du.base_input_chain(bs_node, geo_idx)
            # 오프셋을 그대로 통과시키지 못할 수 있는 디포머만 걸러 보여 준다.
            blockers = [n for n in between
                        if cmds.nodeType(n) not in PASS_THROUGH_TYPES]

            if neutral is None:
                editable_all = False
                parts.append("{0} - neutral not reachable, use 'New mesh'".format(name))
            elif blockers:
                # 바인드 포즈처럼 아무 변형도 안 걸린 상태면 되기도 한다. 실제로 되는지는
                # Apply 때 검증하므로 여기서는 주의만 준다.
                editable_all = False
                parts.append("{0} (neutral: {1}) - {2} in between, 'Deform it too' may"
                             " not reach it; 'New mesh' always works".format(
                                 name, MixManager._short(neutral), ", ".join(blockers)))
            else:
                parts.append("{0} (neutral: {1})".format(
                    name, MixManager._short(neutral)))

        return "Base mesh: " + " | ".join(parts), editable_all

    # ==================================================
    # 소스 믹스
    # ==================================================

    @staticmethod
    def combined_offsets(bs_node, geo_idx, sources, name_to_idx):
        """소스들의 델타 가중합 {정점: (x, y, z)}.

        Args:
            sources : [(타겟 이름, 배율), ...] — 배율 0 은 건너뛴다
        반환: (오프셋 dict, 못 읽은 소스 이름 목록)
        """
        combined = {}
        unreadable = []

        for name, amount in sources:
            if not amount:
                continue
            grp_idx = name_to_idx.get(name)
            if grp_idx is None:
                unreadable.append(name)
                continue

            group = du.group_plug(bs_node, geo_idx, grp_idx)
            item = du.primary_item_index(group)
            if item is None:
                continue                       # 이 지오메트리에는 델타가 없는 소스

            deltas = du.read_item_deltas(du.item_plug(group, item))
            if deltas is None:
                unreadable.append(name)
                continue

            for vtx, d in deltas.items():
                bx, by, bz = combined.get(vtx, (0.0, 0.0, 0.0))
                combined[vtx] = (bx + d[0] * amount,
                                 by + d[1] * amount,
                                 bz + d[2] * amount)

        return combined, unreadable

    # ==================================================
    # 적용
    # ==================================================

    @staticmethod
    def _follow_base(bs_node, geo_idx, grp_idx, offsets, checked):
        """베이스가 M 만큼 움직였을 때 이 타겟의 **모양**을 원하는 자리에 두는 처리.

        checked=True  : 베이스를 따라 +M 되어야 한다 -> 델타는 그대로.
                        live 타겟은 씬의 메시도 같이 옮겨야 델타가 유지된다.
        checked=False : 제자리에 남아야 한다 -> baked 는 델타에서 M 을 뺀다.
                        live 는 메시가 안 움직였으니 델타가 알아서 줄어 제자리다.

        반환: (손댔는가, live 였는가, 실패 사유 또는 None)
        """
        group = du.group_plug(bs_node, geo_idx, grp_idx)
        item = du.primary_item_index(group)
        if item is None:
            return False, False, None           # 델타가 없는 타겟은 따라올 것도 없다
        plug = du.item_plug(group, item)
        shape = du.live_target_shape(plug)

        if checked:
            if not shape:
                return False, False, None       # baked 는 그대로 두면 알아서 따라온다
            old = du.read_item_deltas(plug)
            if old is None:
                return False, True, "component list did not match delta count"
            # 베이스가 이미 움직인 뒤라 지금 읽은 델타는 M 만큼 줄어 있다.
            # 메시를 M 만큼 옮겨 원래 델타로 되돌린다.
            expected = {}
            for vtx in set(old) | set(offsets):
                o = old.get(vtx, (0.0, 0.0, 0.0))
                a = offsets.get(vtx, (0.0, 0.0, 0.0))
                expected[vtx] = (o[0] + a[0], o[1] + a[1], o[2] + a[2])
            ok, problem = du.apply_live_offsets(
                bs_node, geo_idx, plug, shape, offsets, expected)
            return ok, True, problem

        if shape:
            return False, True, None            # live 는 가만 두면 제자리

        old = du.read_item_deltas(plug)
        if old is None:
            return False, False, "component list did not match delta count"
        if not old:
            return False, False, None
        kept = {}
        for vtx in set(old) | set(offsets):
            o = old.get(vtx, (0.0, 0.0, 0.0))
            a = offsets.get(vtx, (0.0, 0.0, 0.0))
            kept[vtx] = (o[0] - a[0], o[1] - a[1], o[2] - a[2])
        try:
            du.write_baked_deltas(plug, kept)
        except Exception as exc:
            return False, False, "could not write deltas ({0})".format(exc)
        return True, False, None

    @staticmethod
    def _add_offsets_to_target(bs_node, geo_idx, grp_idx, offsets):
        """한 타겟(그룹)의 완성 모양에 offsets 를 더한다.

        반환: (바뀐 정점 수, live 였는가, 인비트윈이 있었는가, 실패 사유 또는 None)
        """
        group = du.group_plug(bs_node, geo_idx, grp_idx)
        items = du.item_indices(group)
        # 아이템이 아예 없는 타겟(한 번도 편집되지 않음)에는 완성 모양을 새로 만들어 준다.
        item = du.primary_item_index(group)
        if item is None:
            item = du.FULL_ITEM
        plug = du.item_plug(group, item)
        has_inbetween = len(items) > 1

        old = du.read_item_deltas(plug)
        if old is None:
            return 0, False, has_inbetween, "component list did not match delta count"

        expected = {}
        for vtx in set(old) | set(offsets):
            o = old.get(vtx, (0.0, 0.0, 0.0))
            a = offsets.get(vtx, (0.0, 0.0, 0.0))
            expected[vtx] = (o[0] + a[0], o[1] + a[1], o[2] + a[2])

        shape = du.live_target_shape(plug)
        if shape:
            ok, problem = du.apply_live_offsets(
                bs_node, geo_idx, plug, shape, offsets, expected)
            return (len(offsets) if ok else 0), True, has_inbetween, problem

        try:
            du.write_baked_deltas(plug, expected)
        except Exception as exc:
            return 0, False, has_inbetween, "could not write deltas ({0})".format(exc)
        return len(offsets), False, has_inbetween, None

    @staticmethod
    def mix_into_targets(bs_node, sources, target_names, base_mode=BASE_NONE):
        """소스들을 준 비율로 섞은 만큼 대상 타겟들(+ 선택 시 베이스 메시)을 변형한다.

        규칙은 하나다 — **체크한 것은 믹스만큼 변형되고, 체크하지 않은 것은 모양이 그대로다.**

        Args:
            bs_node      : blendShape 노드 이름
            sources      : [(타겟 이름, 배율), ...]  예) [("a", 1.0), ("b", 0.5)]
            target_names : 변형할 타겟 이름 리스트 (소스는 자동으로 빠진다)
            base_mode    : BASE_NONE / BASE_EDIT / BASE_NEW (위 헤더 주석 참고)

        반환: (처리한 타겟 수, 메시지)
        """
        if not bsu.is_blendshape(bs_node):
            return 0, "[Warning] '{0}' is not a valid blendShape node.".format(bs_node)

        if base_mode not in BASE_MODES:
            base_mode = BASE_NONE

        sources = [(n, float(a)) for n, a in (sources or []) if a]
        if not sources:
            return 0, ("[Warning] Check at least one mix source with a non-zero"
                       " amount.")

        source_names = {n for n, _a in sources}
        # 소스 자신은 대상에서 뺀다 — 자기 자신을 자기에게 더하는 것은 의도가 아니다.
        dropped = [n for n in (target_names or []) if n in source_names]
        target_names = [n for n in (target_names or []) if n not in source_names]
        if not target_names and base_mode == BASE_NONE:
            return 0, "[Warning] Check at least one target to modify."

        name_to_idx = bsu.target_index_map(bs_node)
        geo_indices = cmds.getAttr(bs_node + ".inputTarget", multiIndices=True) or [0]
        checked = set(target_names)

        done = 0
        live_targets = 0
        compensated = 0
        base_edited = False
        inbetween_targets = []
        unknown = [n for n in target_names if n not in name_to_idx]
        unreadable_sources = []
        problems = []
        base_notes = []
        new_meshes = []

        with undo_chunk():
            for geo_idx in geo_indices:
                offsets, bad = MixManager.combined_offsets(
                    bs_node, geo_idx, sources, name_to_idx)
                for name in bad:
                    if name not in unreadable_sources:
                        unreadable_sources.append(name)
                if not offsets:
                    continue

                # 이 지오메트리에서 실제로 성립한 모드. 중립을 못 옮기면 타겟만 처리한다.
                geo_mode = base_mode

                # --- 베이스(최종) 메시 ---------------------------------
                if base_mode == BASE_NEW:
                    # 중립을 지오메트리 **데이터**에서 읽으므로 상류가 무엇이든 만들 수 있다.
                    made, why = du.new_mesh_with_offsets(
                        bs_node, geo_idx, offsets,
                        MixManager._new_mesh_name(bs_node, geo_idx))
                    if made:
                        new_meshes.append(made)
                    else:
                        base_notes.append(
                            "could not build a new mesh for geometry {0} ({1})".format(
                                geo_idx, why))

                elif base_mode == BASE_EDIT:
                    base_shape, between = du.base_input_chain(bs_node, geo_idx)
                    if base_shape is None:
                        base_notes.append(
                            "could not reach the neutral mesh of geometry {0}"
                            " - use the 'New mesh' option instead".format(geo_idx))
                        geo_mode = BASE_NONE           # 타겟은 종전 방식으로 처리
                    else:
                        before = du.input_geometry_points(bs_node, geo_idx)
                        saved = du.offset_base_mesh(base_shape, offsets)
                        if not du.neutral_moved_by(bs_node, geo_idx, before, offsets):
                            # 사이에 낀 디포머가 오프셋을 바꿔 버렸다. 되돌린다.
                            du.write_tweaks(base_shape, saved)
                            base_notes.append(
                                "the neutral of geometry {0} could not be moved -"
                                " '{1}' sits between '{2}' and the blendShape and"
                                " changes the offset. Use the 'New mesh' option"
                                " instead".format(geo_idx,
                                                  ", ".join(between) or "a deformer",
                                                  base_shape))
                            geo_mode = BASE_NONE
                        else:
                            base_edited = True

                # --- 타겟 ----------------------------------------------
                if geo_mode == BASE_EDIT:
                    # 베이스가 이미 움직였다. 모든 타겟의 **모양**을 원하는 자리에 둔다.
                    for name, grp_idx in name_to_idx.items():
                        touched, live, problem = MixManager._follow_base(
                            bs_node, geo_idx, grp_idx, offsets, name in checked)
                        if problem:
                            problems.append("{0}: {1}".format(name, problem))
                        if name in checked:
                            if live and touched:
                                live_targets += 1
                        elif touched:
                            compensated += 1
                    done = len([n for n in checked if n in name_to_idx])
                else:
                    for name in target_names:
                        grp_idx = name_to_idx.get(name)
                        if grp_idx is None:
                            continue

                        pts, live, inbetween, problem = MixManager._add_offsets_to_target(
                            bs_node, geo_idx, grp_idx, offsets)
                        if problem:
                            problems.append("{0}: {1}".format(name, problem))
                        if inbetween and name not in inbetween_targets:
                            inbetween_targets.append(name)
                        if pts:
                            done += 1
                            if live:
                                live_targets += 1

        recipe = ", ".join("{0} x{1:g}".format(n, a) for n, a in sources)
        msg = "[Mix Targets] '{0}' : {1} target(s) modified by [{2}].".format(
            bs_node, done, recipe)
        if base_edited:
            msg += (" The base (neutral) mesh was deformed too, so the checked targets"
                    " move with it.")
            if compensated:
                msg += (" {0} unchecked target(s) were compensated so their shape stays"
                        " exactly where it was.".format(compensated))
        elif new_meshes:
            msg += " New mesh with the mix applied: {0}.".format(", ".join(new_meshes))
        if live_targets:
            msg += (" {0} live target mesh(es) were moved so the change sticks.".format(
                live_targets))
        if dropped:
            msg += " Sources are never modified, so these were skipped: {0}.".format(
                ", ".join(dropped))
        if inbetween_targets:
            msg += (" Only the full (weight 1.0) shape was changed on these"
                    " in-between targets: {0}.".format(", ".join(inbetween_targets)))
        if unreadable_sources:
            msg += " Could not read source deltas: {0}.".format(
                ", ".join(unreadable_sources))
        if unknown:
            msg += " Unknown target(s): {0}.".format(", ".join(unknown))
        if base_notes:
            msg += " Base mesh: {0}.".format("; ".join(base_notes))
        if problems:
            msg += " Problems: {0}".format("; ".join(problems))

        return done, msg
