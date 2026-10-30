# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-30
# A00110_animTool_V02 - View > Layers : 씬의 애니메이션 레이어 목록 + 어느 레이어를 볼지(선택 · mute · solo · lock) (v02.31)
#
# 마야의 Animation Layer Editor 와 같은 것을 툴 안에서(그리고 Expand 로 띄운 작은 창에서) 다룬다.
#   - 목록   : 레이어 에디터 순서 - **맨 위부터**(마지막에 만든 레이어가 위), 자식 레이어는 부모 아래 들여쓰기,
#              BaseAnimation 은 맨 아래. 상태는 Merge Layers 가 쓰는 `LayerMergeManager.layer_info` 를 그대로 쓴다.
#   - 선택   : 행을 고르면 그 레이어가 에디터에서 **선택**되고, 하나만 고르면 **활성(preferred)** 도 된다(에디터의 클릭과 같다).
#              그래프 에디터의 레이어 필터가 'Selected' 면 그 레이어의 커브만 보인다 → 아래 graph_editor_filter.
#   - 토글   : Mute / Solo / Lock 체크. BaseAnimation 은 Lock 만.
#   - 선택 질의는 전역 플래그가 없어 레이어마다 묻는다([[animlayer-no-global-selected-query]]).
#
# 로직만 있고 UI 는 main_window `_build_layers_page`. 결과 메시지는 UI 가 영어로 만든다.

import maya.cmds as cmds

from .layer_merge_manager import LayerMergeManager
from .graph_view_manager import GraphViewManager

# 행에서 켜고 끌 수 있는 플래그 (animLayer -e 플래그 이름 그대로)
FLAGS = ("mute", "solo", "lock")
# layer_info 의 키 이름 ↔ 플래그
FLAG_KEYS = {"mute": "muted", "solo": "solo", "lock": "locked"}


class AnimLayerManager:
    """애니메이션 레이어 목록 · 선택 · 토글 · 그래프 에디터 필터."""

    @staticmethod
    def root_layer():
        return LayerMergeManager.root_layer()

    @staticmethod
    def layer_info(layer, root=None):
        """`LayerMergeManager.layer_info` + preferred(활성) 여부."""
        info = LayerMergeManager.layer_info(layer, root)
        try:
            info["preferred"] = bool(cmds.animLayer(layer, q=True, preferred=True))
        except Exception:                                   # noqa: BLE001
            info["preferred"] = False
        return info

    @staticmethod
    def tree():
        """레이어 에디터 순서의 트리 : [{"info": layer_info, "children": [...]}, ...] 맨 위부터, BaseAnimation 마지막.

        root 직계는 `stack()`(바닥부터)을 뒤집어 맨 위부터, 자식도 같은 규칙. 레이어가 없으면 [].
        """
        root = LayerMergeManager.root_layer()
        if not root:
            return []

        def node(layer, depth):
            info = AnimLayerManager.layer_info(layer, root)
            info["depth"] = depth
            kids = [node(c, depth + 1) for c in reversed(cmds.animLayer(layer, q=True, children=True) or [])]
            return {"info": info, "children": kids}

        out = [node(layer, 0) for layer in reversed(LayerMergeManager.stack(root))]
        base = AnimLayerManager.layer_info(root, root)
        base["depth"] = 0
        out.append({"info": base, "children": []})
        return out

    @staticmethod
    def rows(tree=None):
        """tree() 를 위에서 아래로 펼친 layer_info 목록(부모 다음에 자식, depth 로 들여쓰기)."""
        out = []

        def walk(nodes):
            for n in nodes:
                out.append(n["info"])
                walk(n["children"])

        walk(AnimLayerManager.tree() if tree is None else tree)
        return out

    @staticmethod
    def set_selected(names):
        """에디터 선택을 `names` 로(나머지는 해제). 하나만 고르면 활성(preferred) 레이어도 그것으로 - 에디터의 클릭과 같다.

        반환 : 실제로 선택한 이름들(씬에 없는 이름은 건너뜀).
        """
        wanted = [n for n in dict.fromkeys(names or []) if n and cmds.objExists(n)]
        for layer in cmds.ls(type="animLayer") or []:
            want = layer in wanted
            try:
                if bool(cmds.animLayer(layer, q=True, selected=True)) != want:
                    cmds.animLayer(layer, e=True, selected=want)
            except Exception:                               # noqa: BLE001
                pass
        if len(wanted) == 1:
            # 활성(preferred)은 하나만 - 마야는 preferred=True 가 다른 레이어의 것을 끄지 않으므로 직접 끈다.
            for layer in cmds.ls(type="animLayer") or []:
                try:
                    want = layer == wanted[0]
                    if bool(cmds.animLayer(layer, q=True, preferred=True)) != want:
                        cmds.animLayer(layer, e=True, preferred=want)
                except Exception:                           # noqa: BLE001
                    pass
        return wanted

    @staticmethod
    def set_flag(layer, flag, value):
        """mute / solo / lock 을 켜거나 끈다. BaseAnimation 은 lock 만 된다. 성공하면 True."""
        if flag not in FLAGS or not layer or not cmds.objExists(layer):
            return False
        if layer == LayerMergeManager.root_layer() and flag != "lock":
            return False
        try:
            cmds.animLayer(layer, e=True, **{flag: bool(value)})
            return True
        except Exception:                                   # noqa: BLE001
            return False

    @staticmethod
    def graph_editor_filter(selected_only):
        """열린 그래프 에디터마다 View > Animation Layer Filter 를 'selected'(선택 레이어만) / 'allAffecting' 으로.

        반환 (바꾼(또는 이미 그 값인) 에디터 수, 건 필터). 그래프 에디터가 없으면 (0, 필터).
        """
        layer_filter = "selected" if selected_only else "allAffecting"
        count = 0
        for outliner in GraphViewManager.graph_outliners():
            if GraphViewManager.apply_editor_layer_filter(outliner, layer_filter):
                count += 1
        return count, layer_filter

    @staticmethod
    def snapshot(rows=None):
        """변화 감지용 - 행마다 (이름, depth, mute, solo, lock, selected, preferred) 튜플."""
        rows = AnimLayerManager.rows() if rows is None else rows
        return tuple((r["name"], r["depth"], r["muted"], r["solo"], r["locked"], r["selected"], r["preferred"])
                     for r in rows)
