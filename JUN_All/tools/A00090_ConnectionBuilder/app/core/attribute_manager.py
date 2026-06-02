import maya.cmds as cmds


class AttributeManager:


    @staticmethod
    def create(rule, target_node):

        if not cmds.objExists(target_node):

            raise RuntimeError(
                f"Node not found : {target_node}"
            )

        for attr_name in rule.mapping:

            if cmds.attributeQuery(
                attr_name,
                node=target_node,
                exists=True
            ):
                continue

            cmds.addAttr(
                target_node,
                longName=attr_name,
                attributeType="double",
                keyable=True
            )

            print(
                f"[Create] {target_node}.{attr_name}"
            )

    @staticmethod
    def delete(rule, target_node):

        if not cmds.objExists(target_node):

            raise RuntimeError(
                f"Node not found : {target_node}"
            )

        for attr_name in rule.mapping:

            if not cmds.attributeQuery(
                attr_name,
                node=target_node,
                exists=True
            ):
                continue

            cmds.deleteAttr(
                f"{target_node}.{attr_name}"
            )

            print(
                f"[Delete] {target_node}.{attr_name}"
            )

        @staticmethod
        def validate(rule, target_node):

            missing = []

            for attr_name in rule.mapping:

                if not cmds.attributeQuery(
                    attr_name,
                    node=target_node,
                    exists=True
                ):

                    missing.append(attr_name)

            return missing