import maya.cmds as cmds


class ConnectionRule:

    def __init__(
        self,
        solver_node,
        driver_node,
        blendshape_node,
        mapping
    ):

        self.solver_node = solver_node
        self.driver_node = driver_node
        self.blendshape_node = blendshape_node

        self.mapping = mapping

    def connect(self):

        for idx, attr_name in enumerate(self.mapping):

            solver_attr = (
                f"{self.solver_node}.outputs[{idx}]"
            )

            driver_attr = (
                f"{self.driver_node}.{attr_name}"
            )

            blendshape_attr = (
                f"{self.blendshape_node}.{attr_name}"
            )

            if cmds.objExists(driver_attr):
                cmds.connectAttr(
                    solver_attr,
                    driver_attr,
                    force=True
                )

            if cmds.objExists(blendshape_attr):
                cmds.connectAttr(
                    driver_attr,
                    blendshape_attr,
                    force=True
                )