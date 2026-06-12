import maya.cmds as cmds

from .attribute_manager import AttributeManager


# 모든 RBF solver 의 outputs 를 모으는 공통 null(empty transform) 노드 이름.
NULL_NODE = "WRK_intermediate"
# null 노드를 담는 상위 그룹 노드 이름.
PARENT_NODE = "WRK_All"


class IntermediateManager:
    """각 RBF solver 의 outputs[idx] 를 공통 null 노드의 mapping attr 로 연결한다.

    예) WRK_calf_l_UERBFSolver.outputs[0] -> WRK_intermediate.calf_l_default
        WRK_calf_l_UERBFSolver.outputs[1] -> WRK_intermediate.calf_l_back_50
    null 노드의 attr 이름은 rule.mapping 값과 동일하다.
    null 노드(WRK_intermediate)는 상위 그룹 WRK_All 의 자식으로 둔다.
    """

    @staticmethod
    def ensure_parent(parent_name=PARENT_NODE):
        """상위 그룹 노드가 없으면 empty transform 으로 생성하고 이름을 반환."""
        if not cmds.objExists(parent_name):
            cmds.createNode("transform", name=parent_name)
        return parent_name

    @staticmethod
    def ensure_null(null_name=NULL_NODE, parent_name=PARENT_NODE):
        """null 노드가 없으면 parent_name 의 자식으로 생성한다.

        - parent_name(WRK_All) 이 없으면 먼저 생성한다.
        - null 노드가 이미 있고 부모가 parent_name 이 아니면 그 아래로 옮긴다.
        """
        IntermediateManager.ensure_parent(parent_name)

        if not cmds.objExists(null_name):
            cmds.createNode("transform", name=null_name, parent=parent_name)
        else:
            current_parents = cmds.listRelatives(null_name, parent=True) or []
            if parent_name not in current_parents:
                cmds.parent(null_name, parent_name)

        return null_name

    @staticmethod
    def connect(rules, null_name=NULL_NODE):
        """rules 의 각 solver outputs 를 null_name 의 mapping attr 로 연결.

        - null 노드가 없으면 생성한다.
        - 각 solver 의 mapping 이름으로 null 노드에 double attr 를 보장한다(AttributeManager 재사용).
        - 씬에 없는 solver / output 은 건너뛴다.
        Returns: (connected_count, skipped_solvers) 튜플.
        """
        IntermediateManager.ensure_null(null_name)

        connected = 0
        skipped = []

        for rule in rules:

            solver = rule.solver_node

            if not cmds.objExists(solver):
                skipped.append(solver)
                print(f"[Skip] Solver not found : {solver}")
                continue

            # null 노드에 mapping 이름으로 attr 생성(존재 시 skip).
            AttributeManager.create(rule, null_name)

            for idx, attr_name in enumerate(rule.mapping):

                src = f"{solver}.outputs[{idx}]"
                dst = f"{null_name}.{attr_name}"

                if not cmds.objExists(src):
                    print(f"[Skip] Missing source : {src}")
                    continue

                cmds.connectAttr(src, dst, force=True)
                connected += 1
                print(f"[Connect] {src} -> {dst}")

        return connected, skipped
