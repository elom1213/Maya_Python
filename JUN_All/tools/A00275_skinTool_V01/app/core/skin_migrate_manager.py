# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-24
# A00275_skinTool_V01 - 스킨 마이그레이션 핵심 로직 (maya.cmds / maya.api, UI 비의존)
#
# 토폴로지가 다른 두 리깅 메시 A, B 사이에서 다음 2단계를 버튼 한 번으로 처리한다.
#   1) Transfer : mesh A 의 웨이트(+본)를 mesh B 로 전이 → B 가 A 의 joints 에 바인드
#   2) Move     : B 의 웨이트를 joints_a[i] → joints_b[i] 로 정확히 이동
# 결과적으로 B 는 자신의 본 joints_b 에 올바르게 바인드된다.
#
# 엔진 2종:
#   "kangaroo" : kangarooTabTools.weights 의 transferSkinCluster / moveSkinClusterWeights
#                를 체이닝 (사용자가 수동으로 누르던 Transfer/Move 버튼과 동일 결과).
#                Kangaroo Builder 플러그인이 import 가능해야 한다.
#   "native"   : cmds.copySkinWeights + maya.api setWeights 로 자체 구현 (플러그인 무의존).
#                Move 는 본 1:1 컬럼 이동(per-vertex 최근접 본/스무딩 없음)이라 단순하다.

import maya.cmds as cmds

from Framework.core.maya_undo import undo_chunk


class SkinMigrateManager:

    # UI 콤보와 인덱스 일치 (Kangaroo TransferMode 와 동일 순서)
    TRANSFER_MODES = [
        "Vertex Index",      # 0
        "Closest Vertex",    # 1
        "Closest Point",     # 2
        "Closest UV",        # 3
        "Closest UV Point",  # 4
        "Spikes",            # 5
    ]
    DEFAULT_TRANSFER_MODE = 2  # Closest Point

    # native 엔진에서 copySkinWeights 의 surfaceAssociation 으로 매핑.
    # (네이티브는 UV/Spikes 전용 모드가 없어 근사치로 대체한다.)
    _NATIVE_SURFACE_ASSOC = {
        0: "closestComponent",  # Vertex Index (근사)
        1: "closestComponent",  # Closest Vertex
        2: "closestPoint",      # Closest Point
        3: "closestPoint",      # Closest UV (근사)
        4: "closestPoint",      # Closest UV Point (근사)
        5: "closestPoint",      # Spikes (근사)
    }

    # ==================================================
    # Public
    # ==================================================

    @staticmethod
    def migrate(mesh_a, mesh_b, joints_a, joints_b, *,
                engine="kangaroo", transfer_mode=2,
                remove_unused=True, select_result=False, strict_joints=True):
        """A → B 스킨 마이그레이션을 한 번에 수행.

        반환: (성공 여부(bool 처럼 쓰는 처리 본 수 int), 메시지 str)
        """

        ok, msg = SkinMigrateManager._validate(
            mesh_a, mesh_b, joints_a, joints_b, strict_joints)
        if not ok:
            return (0, msg)

        logs = []

        try:
            with undo_chunk():
                if engine == "kangaroo":
                    SkinMigrateManager._run_kangaroo(
                        mesh_a, mesh_b, joints_a, joints_b, transfer_mode, logs)
                else:
                    SkinMigrateManager._run_native(
                        mesh_a, mesh_b, joints_a, joints_b, transfer_mode, logs)

                # 이동 후 weight 0 이 된 A 본을 정리 → B 는 B 본만 남는다.
                if remove_unused:
                    sc_b = SkinMigrateManager._find_skincluster(mesh_b)
                    if sc_b:
                        removed = cmds.skinCluster(
                            sc_b, edit=True, removeUnusedInfluence=True) or []
                        logs.append("Removed unused influences.")

                if select_result:
                    cmds.select(mesh_b, replace=True)
                else:
                    cmds.select(clear=True)
        except Exception as exc:
            return (0, "[Error] {0}".format(exc))

        head = "[{0}] {1} -> {2} : weights migrated to {3} joint(s).".format(
            engine, mesh_a, mesh_b, len(joints_b))
        return (1, head + ("  " + "  ".join(logs) if logs else ""))

    # ==================================================
    # Classic ops (legacy JUN_PY_move_skinWeightTool_v01_04 의 원본 2버튼 이식)
    # ==================================================

    @staticmethod
    def move_joints_in_mesh(joints_from, joints_to, engine="kangaroo"):
        """Classic 'joints to joints in single mesh'.

        현재 Maya 선택의 메시 위에서 joints_from[i] → joints_to[i] 로 스킨
        웨이트를 이동한다(레거시 JUN_move_each_skin_weight 충실 이식). 메시는
        호출 전 사용자가 선택해 둔 것을 그대로 쓴다.

        engine="kangaroo" : Kangaroo moveSkinClusterWeights (플러그인 필요).
        engine="native"   : maya.api 로 본 컬럼 1:1 이동 (플러그인 무의존).
        """
        if not joints_from or not joints_to:
            return (0, "[Warning] Fill both From and To joint lists.")
        if len(joints_from) != len(joints_to):
            return (0, "[Warning] From ({0}) / To ({1}) joint count mismatch.".format(
                len(joints_from), len(joints_to)))

        if engine == "native":
            return SkinMigrateManager._move_joints_native(joints_from, joints_to)

        try:
            ktw = SkinMigrateManager._import_kangaroo(
                extra=" or switch the engine to 'Native'")
        except RuntimeError as exc:
            return (0, "[Error] {0}".format(exc))

        # A00020 검증 포맷: 키/값을 list-literal 문자열로 주면 Kangaroo 가
        # evalValueFromString 으로 풀어 본 이름으로 해석한다.
        x_joints = {
            "['{0}']".format(jf): "['{0}']".format(jt)
            for jf, jt in zip(joints_from, joints_to)
        }
        try:
            with undo_chunk():
                ktw.moveSkinClusterWeights(
                    xJoints=x_joints,
                    bDisableIslandCheck=True,
                    sChooseSkinCluster=None,
                    iSmoothBorderMask=1,
                )
        except Exception as exc:
            return (0, "[Error] {0}".format(exc))

        return (1, "[classic/kangaroo] Moved weights for {0} joint pair(s) on the "
                   "selected mesh.".format(len(joints_from)))

    @staticmethod
    def _move_joints_native(joints_from, joints_to):
        """Native: 현재 선택 메시의 skinCluster 에서 From 본 컬럼을 To 본 컬럼으로 이동."""
        sel = cmds.ls(sl=True, o=True, l=True) or []
        mesh = next((SkinMigrateManager._as_mesh(s) for s in sel
                     if SkinMigrateManager._as_mesh(s)), None)
        if not mesh:
            return (0, "[Warning] Select the skinned mesh in the scene first.")

        sc = SkinMigrateManager._find_skincluster(mesh)
        if not sc:
            return (0, "[Warning] '{0}' has no skinCluster.".format(mesh))

        missing = [j for j in (joints_from + joints_to)
                   if not cmds.objExists(j) or "joint" not in cmds.nodeType(j)]
        if missing:
            return (0, "[Warning] Not existing joint(s): {0}".format(", ".join(missing)))

        try:
            with undo_chunk():
                existing = set(SkinMigrateManager._leaf(n)
                               for n in (cmds.skinCluster(sc, q=True, influence=True) or []))
                for jt in joints_to:
                    if SkinMigrateManager._leaf(jt) not in existing:
                        cmds.skinCluster(sc, edit=True, addInfluence=jt, weight=0.0)
                        existing.add(SkinMigrateManager._leaf(jt))
                moved = SkinMigrateManager._native_move_columns(
                    sc, mesh, list(zip(joints_from, joints_to)))
        except Exception as exc:
            return (0, "[Error] {0}".format(exc))

        return (1, "[classic/native] Moved {0} joint pair(s) on '{1}'. "
                   "(uses maya.api setWeights; undo is one step)".format(
                       moved, SkinMigrateManager._leaf(mesh)))

    @staticmethod
    def transfer_meshes(meshes_from, meshes_to, transfer_mode=2, engine="kangaroo"):
        """Classic 'meshes to meshes'.

        각 쌍에 대해 meshes_from[i] 의 skinCluster 를 meshes_to[i] 로 전이한다
        (레거시 JUN_transfer_meshes_to_meshes 충실 이식). 인덱스 순서로 짝짓는다.

        engine="kangaroo" : Kangaroo transferSkinCluster (플러그인 필요).
        engine="native"   : rebind + cmds.copySkinWeights (플러그인 무의존).
        """
        if not meshes_from or not meshes_to:
            return (0, "[Warning] Fill both From and To mesh lists.")
        if len(meshes_from) != len(meshes_to):
            return (0, "[Warning] From ({0}) / To ({1}) mesh count mismatch.".format(
                len(meshes_from), len(meshes_to)))

        if engine == "native":
            return SkinMigrateManager._transfer_meshes_native(
                meshes_from, meshes_to, transfer_mode)

        try:
            ktw = SkinMigrateManager._import_kangaroo(
                extra=" or switch the engine to 'Native'")
        except RuntimeError as exc:
            return (0, "[Error] {0}".format(exc))

        done = 0
        try:
            with undo_chunk():
                for mesh_from, mesh_to in zip(meshes_from, meshes_to):
                    cmds.select(clear=True)
                    cmds.select(mesh_to)
                    ktw.transferSkinCluster(
                        iMode=transfer_mode,
                        sChooseSkinCluster=None,
                        iSmoothBorderMask=1,
                        sFrom=[mesh_from],
                    )
                    done += 1
        except Exception as exc:
            return (0, "[Error] {0} (after {1} mesh(es))".format(exc, done))

        return (1, "[classic/kangaroo] Transferred {0} mesh pair(s) (mode={1}).".format(
            done, SkinMigrateManager.TRANSFER_MODES[transfer_mode]))

    @staticmethod
    def _transfer_meshes_native(meshes_from, meshes_to, transfer_mode):
        """Native: 각 쌍을 rebind + copySkinWeights 로 전이."""
        done = 0
        try:
            with undo_chunk():
                for mesh_from, mesh_to in zip(meshes_from, meshes_to):
                    if not SkinMigrateManager._is_mesh(mesh_from):
                        return (0, "[Warning] '{0}' is not a mesh.".format(mesh_from))
                    if not SkinMigrateManager._is_mesh(mesh_to):
                        return (0, "[Warning] '{0}' is not a mesh.".format(mesh_to))
                    sc_from = SkinMigrateManager._find_skincluster(mesh_from)
                    if not sc_from:
                        return (0, "[Warning] '{0}' has no skinCluster.".format(mesh_from))
                    SkinMigrateManager._native_transfer_mesh(
                        mesh_from, mesh_to, transfer_mode)
                    done += 1
        except Exception as exc:
            return (0, "[Error] {0} (after {1} mesh(es))".format(exc, done))

        return (1, "[classic/native] Transferred {0} mesh pair(s) (mode={1}).".format(
            done, SkinMigrateManager.TRANSFER_MODES[transfer_mode]))

    @staticmethod
    def _native_transfer_mesh(mesh_from, mesh_to, transfer_mode):
        """mesh_from 의 skinCluster 를 mesh_to 로 전이(B 를 A 본으로 새로 바인드)."""
        sc_from = SkinMigrateManager._find_skincluster(mesh_from)
        inf_from = cmds.skinCluster(sc_from, q=True, influence=True) or []

        sc_to_old = SkinMigrateManager._find_skincluster(mesh_to)
        if sc_to_old:
            cmds.delete(sc_to_old)

        sc_to = cmds.skinCluster(
            inf_from + [mesh_to], toSelectedBones=True,
            name=SkinMigrateManager._leaf(mesh_to) + "_skinCluster")[0]

        surface_assoc = SkinMigrateManager._NATIVE_SURFACE_ASSOC.get(
            transfer_mode, "closestPoint")
        cmds.copySkinWeights(
            sourceSkin=sc_from, destinationSkin=sc_to,
            noMirror=True, surfaceAssociation=surface_assoc,
            influenceAssociation=["name", "closestJoint", "oneToOne"])
        return sc_to

    @staticmethod
    def _as_mesh(node):
        """노드가 메시(또는 메시 트랜스폼)면 트랜스폼을, 아니면 None."""
        if not cmds.objExists(node):
            return None
        if cmds.objectType(node) == "mesh":
            p = cmds.listRelatives(node, p=True, f=True)
            return p[0] if p else node
        if cmds.listRelatives(node, s=True, type="mesh", f=True):
            return node
        return None

    # ==================================================
    # Validation
    # ==================================================

    @staticmethod
    def _validate(mesh_a, mesh_b, joints_a, joints_b, strict_joints):

        if not mesh_a or not mesh_b:
            return (False, "[Warning] Set both Source Mesh A and Target Mesh B.")

        if not SkinMigrateManager._is_mesh(mesh_a):
            return (False, "[Warning] Source A '{0}' is not a polygon mesh.".format(mesh_a))
        if not SkinMigrateManager._is_mesh(mesh_b):
            return (False, "[Warning] Target B '{0}' is not a polygon mesh.".format(mesh_b))

        if mesh_a == mesh_b:
            return (False, "[Warning] Source A and Target B are the same mesh.")

        sc_a = SkinMigrateManager._find_skincluster(mesh_a)
        if not sc_a:
            return (False, "[Warning] Source A '{0}' has no skinCluster.".format(mesh_a))

        if not joints_a or not joints_b:
            return (False, "[Warning] Fill both Joints A (From) and Joints B (To).")

        if len(joints_a) != len(joints_b):
            return (False, "[Warning] Joints A ({0}) / Joints B ({1}) count mismatch.".format(
                len(joints_a), len(joints_b)))

        missing = [j for j in (joints_a + joints_b)
                   if not cmds.objExists(j) or "joint" not in cmds.nodeType(j)]
        if missing:
            return (False, "[Warning] Not existing joint(s): {0}".format(", ".join(missing)))

        # joints_a 가 실제로 A 의 인플루언스인지 확인 (순서 실수/오타 조기 발견).
        inf_a = set(SkinMigrateManager._leaf(n)
                    for n in (cmds.skinCluster(sc_a, q=True, influence=True) or []))
        not_bound = [j for j in joints_a if SkinMigrateManager._leaf(j) not in inf_a]
        if not_bound and strict_joints:
            return (False,
                    "[Warning] These From-joints are not bound to A "
                    "(check order/names, or turn off Strict): {0}".format(
                        ", ".join(not_bound)))

        return (True, "")

    # ==================================================
    # Engine : Kangaroo (사용자 수동 워크플로우와 동일)
    # ==================================================

    @staticmethod
    def _run_kangaroo(mesh_a, mesh_b, joints_a, joints_b, transfer_mode, logs):

        ktw = SkinMigrateManager._import_kangaroo(
            extra=" or switch the engine to 'Native'")

        # --- Step 1 : Transfer A -> B (B 를 A 의 본으로 새로 바인드) ---
        ktw.transferSkinCluster(
            _pSelection=[mesh_b],
            sFrom=[mesh_a],
            iMode=transfer_mode,
            bAutoCreateNewSkinCluster=True,
        )
        logs.append("Transfer done (mode={0}).".format(
            SkinMigrateManager.TRANSFER_MODES[transfer_mode]))

        # --- Step 2 : Move joints A[] -> B[] ---
        # A00020 검증된 포맷: 키/값을 list-literal 문자열로 주면 Kangaroo 가
        # evalValueFromString 으로 풀어 본 이름으로 해석한다.
        x_joints = {
            "['{0}']".format(ja): "['{0}']".format(jb)
            for ja, jb in zip(joints_a, joints_b)
        }
        ktw.moveSkinClusterWeights(
            _pSelection=[mesh_b],
            xJoints=x_joints,
            bDisableIslandCheck=True,
            sChooseSkinCluster=None,
            iSmoothBorderMask=1,
        )
        logs.append("Move done ({0} joint pair(s)).".format(len(joints_a)))

    # ==================================================
    # Engine : Native (cmds.copySkinWeights + maya.api setWeights)
    # ==================================================

    @staticmethod
    def _run_native(mesh_a, mesh_b, joints_a, joints_b, transfer_mode, logs):

        sc_a = SkinMigrateManager._find_skincluster(mesh_a)
        inf_a = cmds.skinCluster(sc_a, q=True, influence=True) or []

        # --- Step 1 : Transfer A -> B ---
        # B 에 기존 skinCluster 가 있으면 제거하고, A 의 본으로 새로 바인드.
        # (skinCluster 명령에는 unbind 플래그가 없으므로 노드를 직접 삭제해 디태치한다.)
        sc_b_old = SkinMigrateManager._find_skincluster(mesh_b)
        if sc_b_old:
            cmds.delete(sc_b_old)

        sc_b = cmds.skinCluster(
            inf_a + [mesh_b], toSelectedBones=True,
            name=SkinMigrateManager._leaf(mesh_b) + "_skinCluster")[0]

        surface_assoc = SkinMigrateManager._NATIVE_SURFACE_ASSOC.get(
            transfer_mode, "closestPoint")
        cmds.copySkinWeights(
            sourceSkin=sc_a, destinationSkin=sc_b,
            noMirror=True,
            surfaceAssociation=surface_assoc,
            influenceAssociation=["name", "closestJoint", "oneToOne"],
        )
        logs.append("Transfer done (copySkinWeights, surface={0}).".format(surface_assoc))

        # --- Step 2 : Move joints A[] -> B[] (본 1:1 컬럼 이동) ---
        # B 에 To 본을 인플루언스로 추가(weight 0)한 뒤, 가중치 컬럼을 옮긴다.
        existing = set(SkinMigrateManager._leaf(n)
                       for n in (cmds.skinCluster(sc_b, q=True, influence=True) or []))
        for jb in joints_b:
            if SkinMigrateManager._leaf(jb) not in existing:
                cmds.skinCluster(sc_b, edit=True, addInfluence=jb, weight=0.0)
                existing.add(SkinMigrateManager._leaf(jb))

        moved = SkinMigrateManager._native_move_columns(
            sc_b, mesh_b, list(zip(joints_a, joints_b)))
        logs.append("Move done (native column move, {0} pair(s)).".format(moved))
        logs.append("(Native move uses maya.api setWeights; not granularly undoable.)")

    @staticmethod
    def _native_move_columns(sc_name, mesh, pairs):
        """maya.api 로 전체 웨이트 행렬을 읽어, From 본 컬럼을 To 본 컬럼에 더하고
        From 컬럼을 0 으로 만든 뒤 다시 쓴다 (본 1:1 이동).

        주의: MFnSkinCluster.setWeights 는 일반적으로 Ctrl+Z 로 세밀하게 되돌릴 수 없다.
        세밀한 undo 가 필요하면 Kangaroo 엔진을 권장한다.
        """
        from maya.api import OpenMaya as om
        from maya.api import OpenMayaAnim as oma

        sel = om.MSelectionList()
        sel.add(sc_name)
        fn = oma.MFnSkinCluster(sel.getDependNode(0))

        # 메시 dagPath + 전체 버텍스 컴포넌트
        msel = om.MSelectionList()
        msel.add(mesh)
        dag = msel.getDagPath(0)
        dag.extendToShape()

        n_verts = cmds.polyEvaluate(mesh, vertex=True)
        comp_fn = om.MFnSingleIndexedComponent()
        comp = comp_fn.create(om.MFn.kMeshVertComponent)
        comp_fn.addElements(list(range(n_verts)))

        # influenceObjects() 순서(=getWeights 컬럼 순서)와 logical index 매핑
        infl_dags = fn.influenceObjects()
        inf_count = len(infl_dags)
        leaf_to_col = {}
        infl_indices = om.MIntArray()
        for i in range(inf_count):
            leaf_to_col[infl_dags[i].partialPathName().split("|")[-1].split(":")[-1]] = i
            infl_indices.append(int(fn.indexForInfluenceObject(infl_dags[i])))

        weights, _ = fn.getWeights(dag, comp)   # MDoubleArray, 길이 = n_verts * inf_count

        moved = 0
        for ja, jb in pairs:
            ca = leaf_to_col.get(SkinMigrateManager._leaf(ja))
            cb = leaf_to_col.get(SkinMigrateManager._leaf(jb))
            if ca is None or cb is None:
                continue
            for v in range(n_verts):
                base = v * inf_count
                w = weights[base + ca]
                if w != 0.0:
                    weights[base + cb] += w
                    weights[base + ca] = 0.0
            moved += 1

        fn.setWeights(dag, comp, infl_indices, weights, False)
        return moved

    # ==================================================
    # Helpers
    # ==================================================

    @staticmethod
    def _import_kangaroo(extra=""):
        """kangarooTabTools.weights 를 lazy import. 실패 시 RuntimeError.

        외부 3rd-party Kangaroo Builder 플러그인이라 import 가능해야 한다.
        """
        try:
            import kangarooTabTools.weights as ktw
            return ktw
        except Exception:
            raise RuntimeError(
                "Kangaroo plugin not importable (kangarooTabTools). "
                "Load Kangaroo Builder first{0}.".format(extra))

    @staticmethod
    def _leaf(name):
        """fullpath/namespace 를 떼어낸 leaf 본 이름."""
        return name.split("|")[-1].split(":")[-1]

    @staticmethod
    def _is_mesh(node):
        if not cmds.objExists(node):
            return False
        if cmds.objectType(node) == "mesh":
            return True
        shapes = cmds.listRelatives(node, shapes=True, type="mesh", fullPath=True) or []
        return bool(shapes)

    @staticmethod
    def _find_skincluster(mesh):
        """메시 히스토리에서 skinCluster 노드를 찾아 반환(없으면 None)."""
        if not cmds.objExists(mesh):
            return None
        history = cmds.listHistory(mesh, pruneDagObjects=True) or []
        skins = cmds.ls(history, type="skinCluster") or []
        return skins[0] if skins else None
