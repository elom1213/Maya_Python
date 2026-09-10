# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-18
# A00440_SetTool - 연산 실행 (검증 -> 계산 -> 씬 반영)
#
# UI 는 여기 있는 run_* 만 부르고 결과 리포트를 로그에 뿌린다.
# 씬을 바꾸는 연산은 전부 undo_chunk 로 묶어 Ctrl+Z 한 번에 되돌아가게 한다.

import maya.cmds as cmds

from tools.A00440_SetTool.app.core import maya_sets, set_ops


class OpResult(object):
    """연산 한 번의 결과. UI 는 이것만 보고 로그를 그린다."""

    def __init__(self, ok, message, created=None, warnings=None, members=None,
                 created_many=None):
        self.ok = ok
        self.message = message
        self.created = created          # 새로 만들어진 세트 이름 (없으면 None)
        self.warnings = warnings or []
        self.members = members or []    # 결과 원소
        self.created_many = created_many or []   # 여러 개를 만든 연산의 결과 이름들

    def __repr__(self):
        return "OpResult(ok={0}, message={1!r}, created={2!r})".format(
            self.ok, self.message, self.created)


def _fail(message):
    return OpResult(False, message)


def _validate_sets(set_names, minimum):
    """세트 이름들을 검사한다. (에러 메시지, 경고 목록) 를 돌려준다."""
    if len(set_names) < minimum:
        return "Need at least {0} sets, got {1}.".format(minimum, len(set_names)), []

    warnings = []

    for name in set_names:
        if not name:
            return "Empty set name in the list.", warnings

        # 세트가 지워졌거나 이름이 바뀐 경우
        if not maya_sets.is_object_set(name):
            return "'{0}' is not an object set (missing or wrong node type).".format(name), warnings

        nested = maya_sets.nested_sets(name)
        if nested:
            # 세트 안의 세트는 펼치지 않고 원소 하나로 센다. 조용히 넘어가지 않도록 알린다.
            warnings.append(
                "'{0}' contains {1} nested set(s); each counts as a single element: {2}".format(
                    name, len(nested), ", ".join(nested)))

    return None, warnings


def _type_warnings(labelled_groups):
    """묶음마다 컴포넌트 종류를 보고, 섞여 있으면 경고를 만든다.

    지금은 "모든 세트가 같은 종류" 를 가정하지만, 섞여도 연산 자체는 성립하므로
    막지 않고 **알리기만** 한다.
    """
    warnings = []

    for name, members in labelled_groups:
        if set_ops.is_mixed(members):
            warnings.append("'{0}' mixes component types: {1}".format(
                name, set_ops.type_summary(members)))

    groups = [members for _name, members in labelled_groups if members]

    if groups and set_ops.common_type(groups) is None:
        warnings.append(
            "Sets do not share one component type ({0}). "
            "The result is still mathematically correct, but check that it is what you want.".format(
                " / ".join("{0}: {1}".format(n, set_ops.type_summary(m))
                           for n, m in labelled_groups)))

    return warnings


def _gather(set_names):
    """[(세트이름, 정규화된 멤버)] 목록."""
    return [(name, maya_sets.set_members(name)) for name in set_names]


def _run_binary(set_names, result_name, operation, symbol):
    """union / intersection / difference 공통 흐름."""
    error, warnings = _validate_sets(set_names, minimum=2)

    if error:
        return _fail(error)

    labelled = _gather(set_names)
    warnings.extend(_type_warnings(labelled))

    groups = [members for _name, members in labelled]
    result = operation(*groups)

    with maya_sets.undo_chunk():
        created = maya_sets.create_set(result, result_name)

    message = "{0}  {1}  ->  '{2}' ({3} elements, {4})".format(
        symbol,
        " , ".join("{0}[{1}]".format(n, len(m)) for n, m in labelled),
        created,
        len(result),
        set_ops.type_summary(result),
    )

    return OpResult(True, message, created=created, warnings=warnings, members=result)


# ==========================================================================
# 공개 연산
# ==========================================================================

def run_union(set_names, result_name):
    """A ∪ B ∪ ..."""
    return _run_binary(set_names, result_name, set_ops.union, "Union ( ∪ )")


def run_intersection(set_names, result_name):
    """A ∩ B ∩ ..."""
    return _run_binary(set_names, result_name, set_ops.intersection, "Intersection ( ∩ )")


def run_difference(set_names, result_name):
    """A ∖ B ∖ ... — **리스트의 첫 항목이 감수(minuend)** 다."""
    return _run_binary(set_names, result_name, set_ops.difference, "Difference ( ∖ )")


def run_split(set_name, result_name, remove_from_source=True, picked=None):
    """A 와 선택 S 로 A∖S / A∩S 를 만든다.

    picked 를 주지 않으면 실행 시점의 씬 선택을 쓴다. UI 는 리스트 클릭으로 씬 선택이
    바뀌는 것을 피하려고 미리 붙잡아 둔 S 를 넘긴다.

    remove_from_source=True 면 A 에서 A∩S 를 실제로 빼내 A 를 A∖S 로 만든다
    (= A 를 두 조각으로 분할). False 면 A 는 그대로 두고 B = A∩S 만 만든다(복사).
    """
    error, warnings = _validate_sets([set_name], minimum=1)

    if error:
        return _fail(error)

    members = maya_sets.set_members(set_name)

    # 넘어온 S 도 정규화한다 — 호출자가 어떤 형태로 모았든 비교가 되도록.
    picked = maya_sets.canonicalize(picked) if picked else maya_sets.current_selection()

    if not picked:
        return _fail("Nothing is selected in the scene. Select the elements to extract first.")

    warnings.extend(_type_warnings([(set_name, members), ("<scene selection>", picked)]))

    kept, extracted = set_ops.split(members, picked)

    if not extracted:
        return _fail(
            "None of the {0} selected element(s) belong to '{1}'. Nothing to extract.".format(
                len(picked), set_name))

    with maya_sets.undo_chunk():
        created = maya_sets.create_set(extracted, result_name)

        if remove_from_source:
            maya_sets.remove_from_set(set_name, extracted)

    if remove_from_source:
        message = ("Split  '{0}' [{1}]  by scene selection [{2}]  ->  "
                   "'{0}' keeps {3}, new '{4}' takes {5} ({6})").format(
            set_name, len(members), len(picked), len(kept), created, len(extracted),
            set_ops.type_summary(extracted))
    else:
        message = ("Copy  '{0}' ∩ selection  ->  '{1}' ({2} elements, {3})  "
                   "-- source set left untouched").format(
            set_name, created, len(extracted), set_ops.type_summary(extracted))

    if not kept and remove_from_source:
        warnings.append(
            "'{0}' is now empty (every element was extracted). The set node still exists.".format(
                set_name))

    return OpResult(True, message, created=created, warnings=warnings, members=extracted)


def run_create_per_object(objects, suffix=maya_sets.SET_SUFFIX):
    """오브젝트 **하나마다** 그것만 담은 세트를 만든다. 이름은 `<오브젝트 이름>_Set`.

    세트 개수 = 오브젝트 개수다. 전체가 **undo 한 스텝**.

    ★ **요청한 이름과 실제로 붙은 이름이 다를 수 있다.** 같은 이름이 이미 있으면 마야가
      뒤에 번호를 붙인다(`pCube1_Set` -> `pCube1_Set1`). 세트가 아닌 노드가 그 이름을
      쓰고 있어도 마찬가지다. 밀린 것은 **하나하나 경고로 짚는다** - 이름을 보고 찾을
      사람에게는 조용히 밀리는 것이 가장 나쁘다.

    ★ **경로와 네임스페이스는 이름에서 뗀다** (`set_name_for`). 남겨 두면 마야가 그
      네임스페이스 **안에** 세트를 만든다.
    """
    objects = [o for o in (objects or []) if o]
    if not objects:
        return _fail("The list is empty. Add the objects to make sets from.")

    warnings = []
    missing = [o for o in objects if not cmds.objExists(o)]
    if missing:
        warnings.append("{0} item(s) are not in the scene and were skipped: {1}".format(
            len(missing), ", ".join(missing)))
    objects = [o for o in objects if cmds.objExists(o)]
    if not objects:
        return OpResult(False, "Nothing in the list is in the scene.", warnings=warnings)

    created = []
    with maya_sets.undo_chunk():
        for obj in objects:
            wanted = maya_sets.set_name_for(obj, suffix)
            made = maya_sets.create_set([obj], wanted)
            created.append(made)
            if made != wanted:
                warnings.append(
                    "'{0}' was taken, so the set for {1} is '{2}'.".format(
                        wanted, obj.split("|")[-1], made))

    message = "Create  {0} object(s)  ->  {1} set(s) : {2}".format(
        len(objects), len(created), ", ".join(created))

    return OpResult(True, message, warnings=warnings, created_many=created,
                    members=list(created))


def describe_set(set_name):
    """리스트에 곁들일 한 줄 설명. 세트가 아니면 사유를 돌려준다."""
    if not maya_sets.is_object_set(set_name):
        return "not an object set"

    members = maya_sets.set_members(set_name)

    return "{0} elements ({1})".format(len(members), set_ops.type_summary(members))
