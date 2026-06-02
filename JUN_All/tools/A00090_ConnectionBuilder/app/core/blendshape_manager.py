import maya.cmds as cmds


class BlendShapeManager:


    @staticmethod
    def create_targets(rule, mesh):
        """
        rule.mapping 에 있는 이름으로
        blendshape target 생성
        """

        if not cmds.objExists(mesh):
            raise RuntimeError(
                f"Mesh not found : {mesh}"
            )

        targets = []

        for target_name in rule.mapping:

            if cmds.objExists(target_name):

                print(
                    f"[Skip] Exists : {target_name}"
                )

                targets.append(target_name)

                continue

            dup = cmds.duplicate(
                mesh,
                name=target_name
            )[0]

            targets.append(dup)

            print(
                f"[Create Target] {dup}"
            )

        return targets
    
    @staticmethod
    def create_blendshape(rule, mesh):

        targets = BlendShapeManager.create_targets(
            rule,
            mesh
        )

        bs_name = f"{mesh}_blendShape"

        if cmds.objExists(bs_name):

            print(
                f"[Skip] BlendShape Exists : {bs_name}"
            )

            return bs_name

        bs = cmds.blendShape(
            targets,
            mesh,
            name=bs_name,
            frontOfChain=True
        )[0]

        print(
            f"[Create BlendShape] {bs}"
        )

        return bs