# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-19
# A00550_PoseMapper - 음소 값을 임시로 넣기(Solo preview) · 지금 결과를 포즈로 읽기(Capture). maya.cmds, UI 비의존.
#
# 음소 어트리뷰트가 다른 노드에 연결돼 있으면(예: 테스트 씬의 JALI1:JALI_IN.AAA <- JALI1:CNT_PHONEMES.AAA)
# 직접 setAttr 할 수 없다 -> **값을 넣을 수 있는 위쪽 plug 까지 따라 올라간다**(직결 연결만, 최대 4단계).
# 키(animCurve)로 구동되면 그 plug 에 setAttr 한다 - 시간이 바뀌면 커브 값으로 돌아가지만 미리보기 · 측정에는 충분하다.
# 끝나면 바꾼 plug 를 전부 원래 값으로 되돌린다.

import maya.cmds as cmds

from .library import PoseLibrary, EPS


MAX_HOPS = 4


class CaptureError(Exception):
    pass


def settable_plug(plug_name):
    """값을 넣으면 plug_name 이 그 값이 되는 plug. 못 찾으면 CaptureError."""
    current = plug_name
    for _ in range(MAX_HOPS + 1):
        if cmds.getAttr(current, lock=True):
            raise CaptureError("{0} is locked".format(current))
        src = cmds.listConnections(current, source=True, destination=False, plugs=True) or []
        if not src:
            return current
        node = src[0].split(".", 1)[0]
        if cmds.nodeType(node).startswith("animCurve"):
            return current                         # 키 - 이 plug 에 바로 setAttr
        if cmds.nodeType(node) == "unitConversion":
            raise CaptureError("{0} is driven through a unit conversion".format(plug_name))
        current = src[0]
    raise CaptureError("{0}: no settable attribute within {1} connections".format(plug_name, MAX_HOPS))


def _check_range(plug_name, value):
    node, attr = plug_name.split(".", 1)
    try:
        if cmds.attributeQuery(attr, node=node, maxExists=True):
            mx = cmds.attributeQuery(attr, node=node, maximum=True)[0]
            if value > mx + EPS:
                raise CaptureError("Reference value {0:g} is above the max {1:g} of {2}".format(value, mx, plug_name))
        if cmds.attributeQuery(attr, node=node, minExists=True):
            mn = cmds.attributeQuery(attr, node=node, minimum=True)[0]
            if value < mn - EPS:
                raise CaptureError("Reference value {0:g} is below the min {1:g} of {2}".format(value, mn, plug_name))
    except RuntimeError:
        pass


class PhonemeDriver(object):
    """음소 값을 임시로 바꾸고 되돌린다 (Solo preview 와 Capture 공용)."""

    def __init__(self, source, phonemes):
        self.source = source
        self.phonemes = list(phonemes)
        self.plugs = {}                 # phoneme -> settable plug
        self.problems = []              # [(phoneme, 이유)]
        for p in self.phonemes:
            try:
                self.plugs[p] = settable_plug("{0}.{1}".format(source, p))
            except CaptureError as e:
                self.problems.append((p, str(e)))
        self._saved = None

    def save(self):
        if self._saved is None:
            self._saved = {pl: cmds.getAttr(pl) for pl in self.plugs.values()}

    def solo(self, phoneme, value):
        """phoneme = value, 다른 음소 = 0."""
        if phoneme not in self.plugs:
            raise CaptureError("{0}: {1}".format(phoneme, dict(self.problems).get(phoneme, "not settable")))
        _check_range(self.plugs[phoneme], value)
        self.save()
        for p, pl in self.plugs.items():
            cmds.setAttr(pl, value if p == phoneme else 0.0)

    def all_zero(self):
        self.save()
        for pl in self.plugs.values():
            cmds.setAttr(pl, 0.0)

    def restore(self):
        if self._saved is None:
            return
        for pl, v in self._saved.items():
            try:
                cmds.setAttr(pl, v)
            except RuntimeError:
                pass
        self._saved = None

    @property
    def active(self):
        return self._saved is not None


def capture(source, phonemes, target, targets, ref, name="captured"):
    """지금 씬의 결과를 포즈로 읽는다: 음소 하나씩 ref, 나머지 0 -> 타겟 값 - (전부 0 일 때 값).

    Returns (PoseLibrary, info)  info = {"baseline": {t: v}, "problems": [(phoneme, 이유)]}
    """
    drv = PhonemeDriver(source, phonemes)
    lib = PoseLibrary(name=name, ref_value=ref, source_attrs=list(phonemes))
    plugs = {t: "{0}.{1}".format(target, t) for t in targets}
    try:
        drv.all_zero()
        base = {t: cmds.getAttr(pl) for t, pl in plugs.items()}
        for p in phonemes:
            if p not in drv.plugs:
                continue
            drv.solo(p, ref)
            for t, pl in plugs.items():
                d = cmds.getAttr(pl) - base[t]
                if abs(d) > 1e-4:
                    lib.set(p, t, round(d, 4))
    finally:
        drv.restore()
    return lib, {"baseline": {t: v for t, v in base.items() if abs(v) > 1e-4}, "problems": drv.problems}
