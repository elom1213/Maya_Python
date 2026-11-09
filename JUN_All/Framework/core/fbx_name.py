# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-09
# Framework.core.fbx_name - 마야 FBX 임포터의 FBXASC 이름 인코딩 / 디코딩 (순수 파이썬, 마야 불필요)
#
# 마야 이름에는 [A-Za-z0-9_] 만 쓸 수 있고 숫자로 시작할 수 없다. 그래서 FBX 임포터는 그 밖의 글자를
# **UTF-8 바이트 하나마다** `FBXASC` + 10진수 3자리로 바꿔 노드 이름 · 블렌드셰이프 alias 를 만든다.
#
#   "あ"         -> FBXASC227FBXASC129FBXASC130        (UTF-8 E3 81 82)
#   "Left ankle" -> LeftFBXASC032ankle
#   "1abc"       -> FBXASC049abc                       (맨 앞 숫자만 - 가운데 숫자는 그대로)
#
# 실측 (mayapy 2024 FBX 임포트, 2026-11-09): 위 규칙 그대로. '-' '.' '😀'(4바이트) 'é' 도 같은 방식.
# 마야 FBX 익스포터는 거꾸로 FBXASC 를 원래 글자로 되돌려 쓴다(Model::あ) - FBXASC 이름은 손실 없는 왕복 형식이다.
# 계획서: docs/plans/A00620_NameDecoder_plan.md

import re

PREFIX = "FBXASC"

# FBXASC 토큰이 하나 이상 붙어 있는 구간
_RUN = re.compile(r"(?:FBXASC\d{3})+")
_TOKEN = re.compile(r"FBXASC(\d{3})")


def _is_plain(byte):
    """마야 이름에 그대로 둘 수 있는 바이트 - ASCII 영문 · 숫자 · '_'."""
    return (48 <= byte <= 57) or (65 <= byte <= 90) or (97 <= byte <= 122) or byte == 95


def encode(text):
    """원래 이름 -> 마야 FBX 임포터가 만드는 이름. 맨 앞 숫자도 FBXASC 로 바꾼다(마야 이름 규칙)."""
    out = []
    for i, byte in enumerate(bytearray(text.encode("utf-8"))):
        if _is_plain(byte) and not (i == 0 and 48 <= byte <= 57):
            out.append(chr(byte))
        else:
            out.append("{0}{1:03d}".format(PREFIX, byte))
    return "".join(out)


def is_encoded(name):
    """이름에 FBXASC 토큰이 하나라도 있으면 True."""
    return bool(name) and _TOKEN.search(name) is not None


def _decode_run(run):
    """FBXASC 토큰만 붙은 구간 하나 -> (글자, 성공). 값 > 255 이거나 깨진 UTF-8 이면 원래 구간 그대로."""
    values = [int(v) for v in _TOKEN.findall(run)]
    if any(v > 255 for v in values):
        return run, False
    try:
        return bytes(bytearray(values)).decode("utf-8"), True
    except UnicodeDecodeError:
        return run, False


def decode_parts(name):
    """이름을 조각으로 - [(raw, text, kind)], kind = "plain" | "decoded" | "invalid".

    글자 하나가 2~4 바이트(토큰 여러 개)에 걸치므로 붙어 있는 토큰 구간을 **한 번에** 디코드한다.
    깨진 구간은 추측하지 않고 raw 그대로 둔다(kind = "invalid").
    """
    parts = []
    pos = 0
    for m in _RUN.finditer(name or ""):
        if m.start() > pos:
            parts.append((name[pos:m.start()], name[pos:m.start()], "plain"))
        text, ok = _decode_run(m.group(0))
        parts.append((m.group(0), text, "decoded" if ok else "invalid"))
        pos = m.end()
    if name and pos < len(name):
        parts.append((name[pos:], name[pos:], "plain"))
    return parts


def decode(name):
    """마야 이름 -> 원래 글자. FBXASC 가 없으면 그대로. '|' ':' 는 ASCII 라 경로 · 네임스페이스도 그대로 풀린다."""
    return "".join(text for _raw, text, _kind in decode_parts(name))


def decode_ok(name):
    """(원래 글자, 깨진 구간 없음) - 깨진 구간은 raw 그대로 남는다."""
    parts = decode_parts(name)
    return "".join(p[1] for p in parts), all(p[2] != "invalid" for p in parts)


# 마야 이름으로 쓸 수 있는 문자열 - Rename to ASCII 의 새 이름 검사
_VALID_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def is_valid_maya_name(name):
    return bool(_VALID_NAME.match(name or ""))
