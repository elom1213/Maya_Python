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

        # 이미 blendShape 가 있으면 새 target 만 추가한다.
        # (여러 Rule 을 누적 생성하는 "Create All" 에서 모든 target 이 들어가도록.)
        if cmds.objExists(bs_name):
            BlendShapeManager._append_targets(bs_name, mesh, targets)
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

    @staticmethod
    def _append_targets(bs_name, mesh, targets):
        """기존 blendShape 노드에 아직 없는 target 만 다음 인덱스로 추가한다."""
        # blendShape weight alias 이름 = target 이름. 이미 있는 것은 건너뛴다.
        existing = set(cmds.listAttr(bs_name + ".w", multi=True) or [])
        next_idx = cmds.getAttr(bs_name + ".weight", size=True)

        for tgt in targets:
            alias = tgt.split("|")[-1]

            if alias in existing:
                print(f"[Skip] Target exists in blendShape : {alias}")
                continue

            cmds.blendShape(
                bs_name,
                edit=True,
                target=(mesh, next_idx, tgt, 1.0)
            )

            print(f"[Append Target] {bs_name}.{alias} (idx {next_idx})")
            next_idx += 1