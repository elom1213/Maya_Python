# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# A00480_FileTool / Maya 탭 - .ma 헤더의 reference 문장 파서 (UI/DCC 비의존, 순수 파이썬)
#
# Maya ASCII 는 머리글에 레퍼런스를 이렇게 적는다 (2026-10-12 mayapy 2024 실측):
#
#   file -rdi 1 -ns "Ref_maya_02" -rfn "Ref_maya_02RN" -op "VERS|2024|...|"
#        "C:/.../Ref_maya_02.mb";                         <- 중첩까지 깊이(-rdi N)와 함께, 정보용
#   file -r -ns "Ref_maya_02" -dr 1 -rfn "Ref_maya_02RN" -op "..."
#        "C:/.../Ref_maya_02.mb";                         <- 최상위(직접) 레퍼런스
#   file -r -ns "Ref_fbx_01" -dr 1 -rfn "Ref_fbx_01RN" -typ "FBX" "C:/.../Ref_fbx_01.fbx";
#
# **한 문장이 여러 줄**(`-op "..."` 다음 줄에 경로)이라 `;` 까지 이어 붙여 읽는다.
# 씬을 열지 않고 텍스트만 읽으므로 현재 씬을 건드리지 않는다. 머리글은 `createNode` 가 처음
# 나오기 전에 끝나므로 거기서 읽기를 멈춘다(파일이 수백 MB 여도 머리글만 읽는다).

import os
import shlex


# 머리글이 끝났다고 보는 줄 머리. 이 뒤에는 file 문장이 없다.
_BODY_STARTS = ("createNode", "select ", "connectAttr", "setAttr", "relationship")


class MaReference(object):
    """`.ma` 머리글의 레퍼런스 한 줄."""

    __slots__ = ("path", "namespace", "ref_node", "file_type", "depth", "deferred")

    def __init__(self, path, namespace="", ref_node="", file_type="", depth=0, deferred=False):
        self.path = path            # 적힌 그대로의 경로(환경변수 확장 전)
        self.namespace = namespace
        self.ref_node = ref_node
        self.file_type = file_type  # -typ (예: "FBX"), 없으면 ""
        self.depth = depth          # -rdi N. 직접(-r) 레퍼런스는 0
        self.deferred = deferred    # -dr 1 (저장 당시 언로드 상태)

    def __repr__(self):
        return "MaReference({0!r}, ns={1!r}, depth={2})".format(self.path, self.namespace, self.depth)


def iter_file_statements(path, encoding="utf-8"):
    """`.ma` 머리글의 `file ...;` 문장들을 **한 문장씩** (여러 줄이면 이어 붙여) 돌려준다."""
    buf = []
    with open(path, "r", encoding=encoding, errors="replace") as fh:
        for line in fh:
            stripped = line.strip()
            if buf:
                buf.append(stripped)
                if stripped.endswith(";"):
                    yield " ".join(buf)
                    buf = []
                continue
            if stripped.startswith("file "):
                if stripped.endswith(";"):
                    yield stripped
                else:
                    buf = [stripped]
            elif stripped.startswith(_BODY_STARTS):
                break
    if buf:
        yield " ".join(buf)


def parse_statement(statement):
    """`file ... "경로";` 한 문장 -> MaReference. 레퍼런스 문장이 아니면 None."""
    text = statement.strip().rstrip(";").strip()
    if not text.startswith("file "):
        return None
    try:
        tokens = shlex.split(text, posix=True)
    except ValueError:
        return None
    if not tokens or tokens[0] != "file":
        return None

    is_ref = False
    depth = 0
    namespace = ref_node = file_type = ""
    deferred = False
    i = 1
    while i < len(tokens) - 1:          # 마지막 토큰은 경로
        tok = tokens[i]
        if tok in ("-r", "-reference"):
            is_ref = True
        elif tok in ("-rdi", "-referenceDepthInfo"):
            is_ref = True
            depth = int(tokens[i + 1]) if tokens[i + 1].isdigit() else 1
            i += 1
        elif tok in ("-ns", "-namespace"):
            namespace = tokens[i + 1]
            i += 1
        elif tok in ("-rfn", "-referenceNode"):
            ref_node = tokens[i + 1]
            i += 1
        elif tok in ("-typ", "-type"):
            file_type = tokens[i + 1]
            i += 1
        elif tok in ("-dr", "-deferReference"):
            deferred = tokens[i + 1] not in ("0", "false", "off")
            i += 1
        elif tok in ("-op", "-options"):
            i += 1
        i += 1
    if not is_ref:
        return None
    return MaReference(tokens[-1], namespace, ref_node, file_type, depth, deferred)


def direct_references(path):
    """`.ma` 파일이 **직접** 부르는 레퍼런스들(`-r` 문장, 파일 순서대로). 중첩(-rdi) 은 뺀다.

    같은 파일을 두 번 부르면(복사본) 두 줄이 나온다 - 호출부가 경로로 합친다.
    파일을 읽을 수 없으면 OSError 가 그대로 올라간다.
    """
    out = []
    for statement in iter_file_statements(path):
        ref = parse_statement(statement)
        if ref is not None and ref.depth == 0:
            out.append(ref)
    return out


def nested_references(path):
    """정보용 - `-rdi` 문장들(중첩 레퍼런스, 깊이 포함). 현재 스캐너는 쓰지 않는다(재귀로 통일)."""
    out = []
    for statement in iter_file_statements(path):
        ref = parse_statement(statement)
        if ref is not None and ref.depth > 0:
            out.append(ref)
    return out


def resolve_path(raw, base_dir=""):
    """적힌 경로를 절대경로로. 환경변수(`$PROJECT`, `%VAR%`) 를 풀고, 상대경로면 base_dir 기준."""
    text = os.path.expandvars(os.path.expanduser(raw or ""))
    if not text:
        return ""
    if not os.path.isabs(text) and base_dir:
        text = os.path.join(base_dir, text)
    return os.path.normpath(os.path.abspath(text))
