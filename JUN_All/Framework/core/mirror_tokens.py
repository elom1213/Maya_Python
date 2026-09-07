# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-07
# Framework - 좌/우 미러 토큰 쌍 규칙(공용). maya.cmds 비의존.
#
# 규칙 파일 : Framework/rules/mirror_tokens.json  (**모든 툴이 이 파일 하나를 공유**)
#
# 원래는 A00110_animTool_V02 안(app/config/mirror_tokens.json)에 있었는데, 미러가 필요한
# 툴이 늘면서(A00145 Mirror 탭 등) 툴마다 토큰 목록이 갈라지는 문제가 생겼다. 좌/우 이름
# 규칙은 리그 전체에 하나뿐인 약속이므로 Framework 로 올려 한 파일로 관리한다.
#
# 스키마:
#     {
#       "version": 1,
#       "token_pairs": [ {"left": "_l", "right": "_r", "enabled": true}, ... ]
#     }
# JSON 의 위→아래 순서가 매칭 우선순위다(구체적인 토큰을 위에 둘 것).
#
# --------------------------------------------------------------------------
# 경계(boundary) 매칭 — 단순 substring 치환의 함정
# --------------------------------------------------------------------------
# 토큰 "_l" 을 그냥 substring 으로 치환하면 `sample_lip_l_ctl` 의 `_lip` 이 먼저 걸려
# `sample_rip_l_ctl` 이 된다. 이름 매칭은 조용히 틀리는 게 제일 위험하므로,
# `opposite_name()` 은 **토큰 경계**에서 끝나는 occurrence 만 인정한다:
#
#     `_l` + 다음 글자가 `_` / 끝 / 숫자   -> 토큰   (jnt_l_01, arm_L01, wrist_l)
#     `_l` + 다음 글자가 소문자           -> 토큰 아님 (sample_lip)
#     `Left` + 앞뒤가 camelCase 경계      -> 토큰   (armLeft, LeftArm)
#     `Left` + 뒤가 소문자                -> 토큰 아님 (Leftover)
#
# 경계 매칭 덕분에 `_l`(우선순위 위) 이 `jnt_lf_01` 을 잘못 집어삼키지 않고
# `_lf` 쌍까지 내려간다.

import os
import json


# 규칙 파일이 없을 때 쓰는 코드 내장 폴백.
DEFAULT_TOKEN_PAIRS = [
    ("_l", "_r"),
    ("_L", "_R"),
    ("_lf", "_rt"),
    ("Left", "Right"),
]


class MirrorTokenStore:
    """좌↔우 토큰 쌍 규칙의 공용 입출력 + 이름 미러링.

    load()  : enabled 인 (left, right) 쌍만 반환. 파일 없음/파싱 실패/빈 목록이면
              DEFAULT_TOKEN_PAIRS 로 폴백해 **언제나 동작**한다.
    save()  : UI 편집 결과를 같은 JSON 으로 기록(encoding=utf-8).
    opposite_name() : 이름 문자열 하나를 반대쪽 이름으로. 씬을 보지 않는다.
    """

    DEFAULT_TOKEN_PAIRS = DEFAULT_TOKEN_PAIRS

    # Framework/core/ 기준 -> Framework/rules/mirror_tokens.json
    _JSON_PATH = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "rules", "mirror_tokens.json")
    )

    # ------------------------------------------------------------------
    # 파일 입출력
    # ------------------------------------------------------------------

    @staticmethod
    def json_path():
        return MirrorTokenStore._JSON_PATH

    @staticmethod
    def load():
        """규칙 파일에서 enabled 토큰 쌍을 읽는다.

        반환: (pairs, msg)  -  pairs = [(left, right), ...]
        """
        path = MirrorTokenStore._JSON_PATH
        default = list(MirrorTokenStore.DEFAULT_TOKEN_PAIRS)

        if not os.path.exists(path):
            return (default, "[Info] mirror_tokens.json not found. Using built-in defaults.")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            return (default, "[Warning] Failed to read mirror_tokens.json ({0}). Using defaults.".format(e))

        pairs = []
        for row in (data.get("token_pairs") or []):
            if not row.get("enabled", True):
                continue
            left = (row.get("left") or "").strip()
            right = (row.get("right") or "").strip()
            if left and right:
                pairs.append((left, right))

        if not pairs:
            return (default, "[Warning] No enabled token pairs in JSON. Using defaults.")

        return (pairs, "{0} token pair(s) loaded.".format(len(pairs)))

    @staticmethod
    def save(pairs):
        """(left, right) 쌍 리스트를 JSON 으로 기록(모두 enabled=true).

        반환: (count, msg)
        """
        clean = []
        for left, right in pairs:
            left = (left or "").strip()
            right = (right or "").strip()
            if left and right:
                clean.append({"left": left, "right": right, "enabled": True})

        data = {"version": 1, "token_pairs": clean}
        path = MirrorTokenStore._JSON_PATH

        try:
            folder = os.path.dirname(path)
            if folder and not os.path.isdir(folder):
                os.makedirs(folder)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            return (0, "[Warning] Failed to save mirror_tokens.json ({0}).".format(e))

        return (len(clean), "{0} token pair(s) saved.".format(len(clean)))

    # ------------------------------------------------------------------
    # 이름 미러링 (씬 비의존)
    # ------------------------------------------------------------------

    @staticmethod
    def opposite_name(name, token_pairs=None):
        """이름 하나를 반대쪽 이름으로 바꾼다.

        name        : 노드의 **짧은 이름**을 넘기는 게 원칙이다(경로/네임스페이스가 붙어
                      있으면 mirror_node_name() 을 쓸 것).
        token_pairs : [(left, right), ...]. None 이면 load() 로 읽는다.

        반환: (mirrored_name, token)  -  토큰을 못 찾으면 (None, None).

        위→아래 우선순위로 쌍을 보고, **경계에서 끝나는** occurrence 를 가진 첫 쌍이
        이긴다. 그 쌍의 경계 occurrence 는 **전부** 치환한다(l_arm_l_01 -> r_arm_r_01).
        """
        if token_pairs is None:
            token_pairs, _ = MirrorTokenStore.load()

        for left, right in token_pairs:
            for src, dst in ((left, right), (right, left)):
                hits = MirrorTokenStore._boundary_hits(name, src)
                if not hits:
                    continue
                out = name
                # 뒤에서부터 치환해야 앞쪽 인덱스가 밀리지 않는다.
                for idx in reversed(hits):
                    out = out[:idx] + dst + out[idx + len(src):]
                if out != name:
                    return (out, src)

        return (None, None)

    @staticmethod
    def mirror_node_name(node, token_pairs=None):
        """DAG 경로/네임스페이스가 붙은 이름을 안전하게 미러한다.

        경로(`|a|b`)에서 **마지막 조각만** 미러하고, 반환은 짧은 이름이다
        (마야의 rename 은 짧은 이름을 받는다).

        반환: (mirrored_short_name, token) 또는 (None, None).
        """
        short = node.split("|")[-1]
        return MirrorTokenStore.opposite_name(short, token_pairs)

    # ------------------------------------------------------------------
    # 내부 : 경계 판정
    # ------------------------------------------------------------------

    @staticmethod
    def _boundary_hits(name, token):
        """name 안에서 **토큰 경계**를 만족하는 token 의 시작 인덱스 목록."""
        if not token:
            return []

        hits = []
        start = 0
        while True:
            idx = name.find(token, start)
            if idx == -1:
                break
            if (MirrorTokenStore._starts_at_boundary(name, idx, token)
                    and MirrorTokenStore._ends_at_boundary(name, idx, token)):
                hits.append(idx)
            start = idx + 1
        return hits

    @staticmethod
    def _starts_at_boundary(name, idx, token):
        if idx == 0:
            return True
        prev = name[idx - 1]
        first = token[0]
        if not first.isalnum():          # '_l' 처럼 토큰 자체가 구분자로 시작
            return True
        if not prev.isalnum():           # 'ns:Left', 'arm_Left'
            return True
        if first.isupper() and not prev.isupper():   # camelCase 경계 : armLeft
            return True
        return False

    @staticmethod
    def _ends_at_boundary(name, idx, token):
        end = idx + len(token)
        if end == len(name):             # 'wrist_l'
            return True
        nxt = name[end]
        last = token[-1]
        if not nxt.isalnum():            # 'jnt_l_01'
            return True
        if nxt.isdigit() and not last.isdigit():     # 'jnt_L01'
            return True
        if nxt.isupper() and not last.isupper():     # 'LeftArm'
            return True
        return False
