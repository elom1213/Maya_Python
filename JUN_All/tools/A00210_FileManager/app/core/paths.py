# Python Script by Ji Hun Park
# last Update date : 2026-11-04
# A00210_FileManager - 화면에 보이는 경로 표기를 하나로 (UI/DCC 비의존)
#
# v01.46 : 같은 경로가 `C:\Users\...` 와 `C:/Users/...` 로 섞여 보이던 것을 통일한다.
#   규칙 = **슬래시(/)**. Qt 파일 대화상자가 돌려주는 표기이자 기존 프로파일 대부분의 표기.
#   NAS(UNC) 는 `//172.30.1.93/MANUTeam/...`. Windows 파일 함수 · git · subprocess 는 / 도 그대로 받는다.
#   `..` · 중복 구분자는 정리(normpath)하고, 끝의 구분자는 뗀다. 대소문자는 바꾸지 않는다.

import os
import re


def ui_path(path):
    """경로 문자열 -> 화면 · 저장용 표기(슬래시). 빈 값은 "" 그대로."""
    if not path:
        return ""
    s = str(path).strip()
    if not s:
        return ""
    unc = s.startswith("\\\\") or s.startswith("//")
    out = os.path.normpath(s).replace("\\", "/")
    if unc and not out.startswith("//"):
        out = "//" + out.lstrip("/")
    return out


# 드라이브 경로(C:\...) · UNC(\\server\...) 가 시작되는 곳부터 그 줄 끝(또는 따옴표 · <>|*? 앞)까지.
# 공백이 든 경로("C:\Program Files\Autodesk")도 끊기지 않게 줄 끝까지 본다 - 경로 뒤 글자에 역슬래시가 있을 일은 드물다.
_PATH_RUN = re.compile(r"(?:\b[A-Za-z]:[\\/]|\\\\(?=[\w.$-]))[^\r\n\"'<>|*?]*")


def ui_text(text):
    """로그 · 안내문 안의 Windows 경로 표기를 슬래시로. 경로가 시작되지 않는 줄은 그대로 둔다."""
    if not text or "\\" not in text:
        return text
    return _PATH_RUN.sub(lambda m: m.group(0).replace("\\", "/"), text)
