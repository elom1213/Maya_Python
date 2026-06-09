import maya.cmds as cmds


class ConnectionManager:


    # --------------------------------------------------
    # Private
    # --------------------------------------------------

    def is_exist_attr(self, node_name, attr):
        if not cmds.objExists(node_name):
            return False
        return cmds.objExists(f"{node_name}.{attr}")
    
        return cmds.attributeQuery(attr, node=node_name, exists=True)

    def _get_connections(self, rule, is_solver_node = True):

        connections = []

        for idx, attr_name in enumerate(rule.mapping):
            
            if is_solver_node :
                attr_name_solver = f"outputs[{idx}]"
            else :
                attr_name_solver = attr_name

            solver_attr = (
                f"{rule.solver_node}.{attr_name_solver}"
            )
            driver_attr = (
                f"{rule.driver_node}.{attr_name}"
            )
            blendshape_attr = (
                f"{rule.blendshape_node}.{attr_name}"
            )

            is_exist_slvr_attr = self.is_exist_attr(rule.solver_node, attr_name_solver)
            is_exist_driver_attr = self.is_exist_attr(rule.driver_node, attr_name)
            is_exist_bs_attr = self.is_exist_attr(rule.blendshape_node, attr_name)
            
            if is_exist_slvr_attr and is_exist_driver_attr:
                connections.append(
                    (solver_attr, driver_attr)
                )
                # print("solver => driver  :  "+ str(solver_attr) + "   "+ str(driver_attr))

            if is_exist_driver_attr and is_exist_bs_attr:
                connections.append(
                    (driver_attr, blendshape_attr)
                )
                # print("driver => bs  :  "+ str(driver_attr) + "   " +  str(blendshape_attr))
        return connections


    # --------------------------------------------------
    # Connect
    # --------------------------------------------------

    def connect(self, rule, is_solver = True):

        connections = self._get_connections(rule, is_solver)

        for src, dst in connections:

            if not cmds.objExists(src):
                print(f"Missing source : {src}")
                continue

            if not cmds.objExists(dst):
                print(f"Missing target : {dst}")
                continue

            cmds.connectAttr(
                src,
                dst,
                force=True
            )

            print(f"Connected : {src} -> {dst}")


    # --------------------------------------------------
    # Disconnect
    # --------------------------------------------------

    def disconnect(self, rule):

        connections = self._get_connections(rule)

        for src, dst in connections:

            if not cmds.objExists(dst):
                continue

            if cmds.isConnected(src, dst):

                cmds.disconnectAttr(
                    src,
                    dst
                )

                print(
                    f"Disconnected : {src} -> {dst}"
                )


    # --------------------------------------------------
    # Validate
    # --------------------------------------------------

    def validate(self, rule):

        connections = self._get_connections(rule)

        result = True

        for src, dst in connections:

            if not cmds.objExists(src):

                print(
                    f"[ERROR] Missing source : {src}"
                )

                result = False

                continue

            if not cmds.objExists(dst):

                print(
                    f"[ERROR] Missing target : {dst}"
                )

                result = False

                continue

            if not cmds.isConnected(src, dst):

                print(
                    f"[ERROR] Not connected : "
                    f"{src} -> {dst}"
                )

                result = False

            else:

                print(
                    f"[OK] {src} -> {dst}"
                )

        return result