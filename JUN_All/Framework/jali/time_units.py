# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# Framework.jali.time_units - 마야 시간 단위 이름 <-> fps (순수 파이썬, standalone 과 in-Maya 둘 다 쓴다)
#
# A00560(standalone UI · 워커) 과 A00570(in-Maya) 이 같은 표를 써야 "30 = ntsc" 가 어긋나지 않는다. keyer.scene_fps 의 표와 같다.

FPS_UNITS = ((15.0, "game"), (24.0, "film"), (25.0, "pal"), (30.0, "ntsc"), (48.0, "show"), (50.0, "palf"), (60.0, "ntscf"),
             (23.976, "23.976fps"), (29.97, "29.97fps"), (59.94, "59.94fps"))


def unit_name(fps):
    """fps 숫자 -> cmds.currentUnit(time=...) 이름. 표에 없으면 '<n>fps' (마야가 받는 형식)."""
    fps = float(fps)
    for value, name in FPS_UNITS:
        if abs(fps - value) < 1e-6:
            return name
    if abs(fps - round(fps)) < 1e-9:
        return "{0}fps".format(int(round(fps)))
    return "{0:g}fps".format(fps)


def fps_of_unit(unit):
    """단위 이름 -> fps. 모르는 이름이면 None."""
    for value, name in FPS_UNITS:
        if unit == name:
            return value
    try:
        return float(str(unit).replace("fps", ""))
    except ValueError:
        return None
