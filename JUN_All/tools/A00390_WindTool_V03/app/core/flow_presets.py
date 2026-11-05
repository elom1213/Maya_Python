# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-05
# A00390_WindTool_V03 core - Flow 모드 바람 프리셋 (UI · Maya 비의존)
#
# 프리셋 값은 블렌더 애드온 **Waves Gen**(Guillaume Bissieres, GPL-3.0-or-later, https://bissieres.gumroad.com/l/WavesGen)의
# 세 프리셋 Slow Flow / Breeze / Fast Flutter (각각 옵션 2개)을 참고했다. 개인 작업용 툴이라 배포하지 않는다(2026-11-05 사용자).
#
# 값의 뜻(Flow 드라이버 어트리뷰트와 같다 - flow_model / flow_manager):
#   lean       바람에 눕는 정도(도, 뼈 12개 기준)        = Waves Gen Strength
#   flutter    파동 크기(도/뼈, 뼈 12개 기준)            = Flutter
#   cross      옆 흔들림 비율 0~1                        = Cross Sway
#   speed      파동 속도(24 fps 기준. 축 방향 파 = 0.13 x speed rad/frame) = Speed
#   wavelength 파장(뼈 12개 기준 단위, 체인 위 파동 수 = 12 / wavelength)   = Wavelength
#   stiffness  뿌리 고정 지수                             = Stiffness
#   random     불규칙 · 돌풍 0~1                         = Randomness
#   follow     끝 따라가기 0~1                           = Influence
#
# 옵션 1 = 드라이버의 *A 어트리뷰트, 옵션 2 = *B, flowMix 0 -> 1 로 섞는다(라이브, 키 가능).

import math

PARAMS = ("lean", "flutter", "cross", "speed", "wavelength", "stiffness", "random", "follow")

PRESET_ORDER = ("Slow Flow", "Breeze", "Fast Flutter")

PRESETS = {
    "Slow Flow": (
        dict(follow=0.662, lean=24.28, flutter=6.83, speed=2.01, wavelength=20.0, stiffness=0.0, random=0.0, cross=0.0),
        dict(follow=0.487, lean=24.28, flutter=7.38, speed=1.17, wavelength=20.0, stiffness=0.0, random=0.0, cross=0.0),
    ),
    "Breeze": (
        dict(follow=0.712, lean=18.241, flutter=15.218, speed=2.58, wavelength=16.109, stiffness=0.0, random=0.0, cross=0.0),
        dict(follow=0.662, lean=24.28, flutter=13.85, speed=2.01, wavelength=20.0, stiffness=0.0, random=0.0, cross=0.0),
    ),
    "Fast Flutter": (
        dict(follow=0.895, lean=20.59, flutter=18.49, speed=4.91, wavelength=8.47, stiffness=0.0, random=0.0, cross=0.33),
        dict(follow=0.662, lean=24.28, flutter=16.29, speed=4.41, wavelength=10.98, stiffness=0.0, random=0.0, cross=0.0),
    ),
}

# 프리셋이 아닌 기본값(애드온의 기본 슬라이더 값과 같다)
DEFAULTS = dict(follow=0.829, lean=33.32, flutter=10.02, speed=6.28, wavelength=9.73,
                stiffness=0.0, random=0.0, cross=0.0)

# 어트리뷰트 범위 (min, max) - 드라이버 addAttr 과 UI 스핀박스가 같이 쓴다.
LIMITS = dict(lean=(0.0, 120.0), flutter=(0.0, 120.0), cross=(0.0, 1.0), speed=(0.0, 40.0),
              wavelength=(0.5, 60.0), stiffness=(0.0, 4.0), random=(0.0, 1.0), follow=(0.0, 0.99))

LABELS = dict(lean="Lean", flutter="Flutter", cross="Cross Sway", speed="Speed", wavelength="Wavelength",
              stiffness="Stiffness", random="Randomness", follow="Tip Follow")

TOOLTIPS = dict(
    lean="Steady push of the wind: how far the chain leans (degrees, for a 12-bone chain).",
    flutter="Size of the wave running along the chain (degrees per bone, for a 12-bone chain).",
    cross="Sideways sway across the wind: makes the end draw loops (0-1).",
    speed="Speed of the wave: low = slow lazy flow, high = fast flutter (24 fps based, same rhythm at any fps).",
    wavelength="Wavelength in bones of a 12-bone chain: low = tight ripples, high = long S curves "
               "(waves on the chain = 12 / wavelength).",
    stiffness="Stiffness of the base: high = only the free end moves, 0 = the whole chain waves.",
    random="Irregular rhythm and gusts (0 = a regular wave).",
    follow="How much every bone turns toward the Tip control (0 = wind only).",
)


def option(name, index):
    """프리셋 옵션 값 dict (index 0 = 옵션 1, 1 = 옵션 2)."""
    return dict(PRESETS[name][index])


def mix(a, b, t):
    t = max(0.0, min(1.0, float(t)))
    return {k: a[k] + (b[k] - a[k]) * t for k in PARAMS}


def matching_preset(a_vals, b_vals, tol=1e-3):
    """드라이버의 A / B 값이 어떤 프리셋과 같은가 - 이름 또는 None."""
    for name in PRESET_ORDER:
        o1, o2 = PRESETS[name]
        if all(abs(a_vals.get(k, -1e9) - o1[k]) < tol and abs(b_vals.get(k, -1e9) - o2[k]) < tol for k in PARAMS):
            return name
    return None


def speed_hz(speed):
    """speed 값 -> 축 방향 파의 주파수(Hz). 24 fps 기준 값이라 fps 와 무관."""
    return 0.13 * speed * 24.0 / (2.0 * math.pi)
