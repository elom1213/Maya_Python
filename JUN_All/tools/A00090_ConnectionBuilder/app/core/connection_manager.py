import maya.cmds as cmds


class ConnectionManager:


    # --------------------------------------------------
    # Private
    # --------------------------------------------------

    def _get_connections(self, rule):

        connections = []

        for idx, attr_name in enumerate(rule.mapping):

            solver_attr = (
                f"{rule.solver_node}.outputs[{idx}]"
            )

            driver_attr = (
                f"{rule.driver_node}.{attr_name}"
            )

            blendshape_attr = (
                f"{rule.blendshape_node}.{attr_name}"
            )

            connections.append(
                (solver_attr, driver_attr)
            )

            connections.append(
                (driver_attr, blendshape_attr)
            )

        return connections


    # --------------------------------------------------
    # Connect
    # --------------------------------------------------

    def connect(self, rule):

        connections = self._get_connections(rule)

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