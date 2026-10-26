# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00540_JaliLipSync - keyer 재노출. 본체는 Framework/jali/keyer.py (2026-10-26 공용 승격, v01.03).
# tests/ 와 옛 import 경로(tools.A00540_JaliLipSync.app.core.keyer)가 그대로 동작하도록 남겨 둔 얇은 모듈이다.

from Framework.jali.keyer import *  # noqa: F401,F403
from Framework.jali import keyer as _impl

# import * 가 건너뛰는 이름(밑줄 · 모듈 상수)도 같은 객체를 가리키게 한다.
for _name in dir(_impl):
    if _name not in globals():
        globals()[_name] = getattr(_impl, _name)
del _name
