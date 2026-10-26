# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00560_JaliBatch - manifest 재노출. 본체는 Framework/jali/clip_manifest.py (A00570_JaliReview 도 읽으므로 공용).

from Framework.jali.clip_manifest import *  # noqa: F401,F403
from Framework.jali import clip_manifest as _impl

for _name in dir(_impl):
    if _name not in globals():
        globals()[_name] = getattr(_impl, _name)
del _name
