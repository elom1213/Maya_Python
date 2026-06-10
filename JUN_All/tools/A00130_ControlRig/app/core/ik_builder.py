# -*- coding: utf-8 -*-
"""
ik_builder - IK handle + pole vector 생성.

원본 JUN_create_ik_with_polevector 이식.
정리: `solver is "ikRPsolver"` (문자열 is 비교) → `==` 교정. 동작 동일.
"""

from .maya_scene import MayaScene


def create_ik_with_polevector(start_joint, end_joint, pv_object,
                              solver="ikRPsolver", pole_name="pole_defualt"):
    """
    두 조인트 사이에 IK handle 을 만들고 pole vector 컨트롤을 연결한다.

    Args:
        start_joint (str): IK chain 시작 조인트.
        end_joint   (str): IK chain 끝 조인트.
        pv_object   (str): pole vector 컨트롤로 쓸 오브젝트.
        solver      (str): IK solver 종류 (기본 'ikRPsolver'). single chain : 'ikSCsolver'.

    Returns:
        tuple: (ik_handle, effector, pv_constraint, pv_object_new)
    """
    pv_constraint = ""
    pv_object_new = ""

    if solver == "ikRPsolver":
        pv_object_new = MayaScene.duplicate(pv_object)[0]
        pv_object_new = MayaScene.rename(pv_object_new, pole_name)
        MayaScene.parent_to_world(pv_object_new)

    ik_handle, effector = MayaScene.ik_handle(start_joint, end_joint, solver)
    ik_handle = MayaScene.rename(ik_handle, "{0}_ikHandle".format(end_joint))

    if solver == "ikRPsolver":
        pv_constraint = MayaScene.pole_vector_constraint(pv_object_new, ik_handle)[0]

    return ik_handle, effector, pv_constraint, pv_object_new
