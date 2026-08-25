# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-25
# A00010_humanIKTool_V02 - "왼쪽 노드에 대응하는 오른쪽 노드" 를 찾는 해석기.
#
# 조인트 Mirror 와 컨트롤러(Custom Rig) Mirror 가 같은 이 모듈을 쓴다. 대상만 다를 뿐
# "이미 할당된 한쪽 노드를 보고 반대쪽 노드를 고른다" 는 문제는 완전히 동일하기 때문이다.
#
# -- 무엇을 근거로 짝을 찾을 것인가 -------------------------------------------
#
# (1) 이름 (NAME)  * 기본값
#     리깅 이름에는 사실상 예외 없이 방향 토큰이 들어간다 - L_arm_JNT / arm_lf_ctrl /
#     LeftArm / arm_L. 그 토큰만 뒤집으면 짝이 나온다.
#     - 포즈에 의존하지 않는다. 애님이 들어가 있든 T 포즈가 아니든 결과가 같다.
#     - 좌우가 비대칭인 리그(한쪽에만 보조 조인트가 있는 등)에서도 맞는다.
#     - 결과가 이름으로 확인되므로 사람이 로그만 보고 검수할 수 있다.
#     한계: 방향 토큰이 없는 이름(joint1 / joint12)에는 쓸 수 없다.
#
# (2) 위치 (POSITION)  - 폴백
#     월드 좌표를 미러 축(기본 X) 기준으로 뒤집고 가장 가까운 후보를 고른다.
#     - 이름 규칙이 전혀 없는 리그를 구제한다.
#     한계: 스켈레톤이 좌우 대칭 포즈일 때만 맞다. 포즈가 들어가 있으면 조용히 엉뚱한
#     조인트를 고를 수 있어서, 허용 오차(tolerance) 안에 들어온 것만 채택하고 실제 거리를
#     같이 보고한다.
#
# (3) 계층 / 조인트 라벨 - 쓰지 않는다
#     계층 대칭은 부모가 먼저 풀려야 하므로 순환이고, .side / .type 라벨은 세팅해 둔
#     리그가 드물다(HumanIK 이 할당 *뒤에* 써 주는 값이라 짝을 찾는 근거로는 늦다).
#
# 기본 모드 AUTO 는 (1) 을 먼저 시도하고 실패한 항목만 (2) 로 넘긴다. 각 항목이 어느
# 근거로 풀렸는지 결과에 남기므로, 위치로 풀린 줄만 골라 검수하면 된다.

import maya.cmds as cmds


# 이름 안의 방향 토큰 쌍. (왼쪽, 오른쪽) 이고 전부 소문자로 적는다 - 실제 이름의 대소문자는
# 매칭된 글자에서 그대로 복원한다. 긴 토큰이 먼저 와야 "left" 가 "l" 로 잘못 잡히지 않는다.
SIDE_TOKEN_PAIRS = [
    ("left", "right"),
    ("lft", "rgt"),
    ("lt", "rt"),
    ("lf", "rt"),
    ("l", "r"),
]

MODE_NAME = "name"
MODE_POSITION = "position"
MODE_AUTO = "auto"

AXIS_INDEX = {"X": 0, "Y": 1, "Z": 2}


# --------------------------------------------------------------------------
# 이름
# --------------------------------------------------------------------------

def _token_spans(text, token, blockers=()):
    """text 안에서 token 이 독립된 방향 토큰으로 등장하는 (start, end) 목록.

    단순 문자열 치환을 쓰면 elbow 의 l, clavicle 의 l 까지 바뀐다. 그래서 토큰의
    앞뒤 경계를 직접 본다.
      - 앞: 문자열 시작 / 숫자 / 구분자(_ : - 등) / 카멜 경계(소문자 뒤의 대문자 토큰)
      - 뒤: 문자열 끝 / 숫자 / 구분자 / 대문자(카멜 경계)
    즉 L_arm, arm_L, arm01L, LeftArm, myLeftArm 은 잡고,
    Larm, elbow, leftover, ARMLeft 는 잡지 않는다.

    blockers 는 "더 긴 방향 토큰" 목록이다. LEFT_arm 의 첫 글자 L 은 뒤가 대문자 E 라
    경계 판정만으로는 통과해 버려 REFT_arm 이라는 헛 후보가 나온다. 그 자리에서 더 긴
    토큰(left)이 시작하면 짧은 토큰의 매칭으로 보지 않는다.
    """
    spans = []
    low = text.lower()
    tlen = len(token)
    start = 0
    while True:
        i = low.find(token, start)
        if i < 0:
            break
        start = i + 1
        j = i + tlen

        if any(low.startswith(b, i) for b in blockers):
            continue

        prev = text[i - 1] if i > 0 else ""
        if prev and prev.isalpha():
            # 알파벳 뒤라면 카멜 경계(소문자 + 대문자 토큰) 일 때만 인정한다.
            if not (prev.islower() and text[i].isupper()):
                continue

        nxt = text[j] if j < len(text) else ""
        if nxt and nxt.isalpha() and nxt.islower():
            # 뒤에 소문자가 이어지면 더 긴 단어의 일부다 (Leftover, Larm).
            continue

        spans.append((i, j))
    return spans


def _match_case(sample, replacement):
    """sample 의 대소문자 꼴을 replacement 에 입힌다. (LEFT -> RIGHT, Left -> Right)"""
    if sample.isupper():
        return replacement.upper()
    if sample.islower():
        return replacement.lower()
    if sample[0].isupper():
        return replacement.capitalize()
    return replacement


def split_name(node):
    """DAG 패스/네임스페이스를 분리해 (prefix, leaf) 로. 미러는 leaf 만 건드린다.

    네임스페이스에 방향 토큰이 들어가는 리그는 사실상 없고, 건드리면 char_L:... 같은
    이름에서 존재하지 않는 네임스페이스를 만들어 낸다.
    """
    short = node.split("|")[-1]
    if ":" in short:
        ns, leaf = short.rsplit(":", 1)
        return ns + ":", leaf
    return "", short


def mirror_name_candidates(node, to_side):
    """node 이름의 방향 토큰을 뒤집은 후보 이름들(우선순위 순, 중복 제거).

    to_side : "Right" 면 왼쪽 토큰 -> 오른쪽 토큰. "Left" 면 반대.
    rt 처럼 한 토큰이 두 쌍에 걸치는 경우가 있어 후보를 여러 개 돌려주고,
    실제로 존재하는 노드를 만드는 첫 후보를 호출부가 고른다.
    """
    prefix, leaf = split_name(node)

    to_right = (to_side != "Left")
    src_tokens = [p[0] if to_right else p[1] for p in SIDE_TOKEN_PAIRS]

    out = []
    for left_tok, right_tok in SIDE_TOKEN_PAIRS:
        src_tok, dst_tok = (left_tok, right_tok) if to_right else (right_tok, left_tok)
        blockers = [t for t in src_tokens if len(t) > len(src_tok)]
        spans = _token_spans(leaf, src_tok, blockers)
        if not spans:
            continue
        # 찾은 토큰을 전부 바꾼다 (L_arm_L_end).
        buf = []
        cursor = 0
        for s, e in spans:
            buf.append(leaf[cursor:s])
            buf.append(_match_case(leaf[s:e], dst_tok))
            cursor = e
        buf.append(leaf[cursor:])
        cand = prefix + "".join(buf)
        if cand != prefix + leaf and cand not in out:
            out.append(cand)
    return out


# --------------------------------------------------------------------------
# 후보 풀 / 위치
# --------------------------------------------------------------------------

def hierarchy_root(node):
    """node 가 속한 DAG 최상위 트랜스폼(풀 패스). 후보 풀을 같은 리그로 좁히는 데 쓴다."""
    paths = cmds.ls(node, long=True) or []
    if not paths:
        return None
    parts = paths[0].split("|")
    return "|" + parts[1] if len(parts) > 1 else None


def candidate_pool(reference, node_type=None):
    """reference 와 같은 계층 아래의 노드들. 없으면 씬 전체로 넓힌다.

    같은 리그 안으로 좁히면 레퍼런스가 여러 개 걸린 씬에서 옆 캐릭터의 조인트를 집는
    사고를 막는다.
    """
    root = hierarchy_root(reference)
    pool = []
    if root:
        if node_type:
            pool = cmds.ls(root, dag=True, long=True, type=node_type) or []
        else:
            pool = cmds.ls(root, dag=True, long=True, transforms=True) or []
    if not pool:
        if node_type:
            pool = cmds.ls(long=True, type=node_type) or []
        else:
            pool = cmds.ls(long=True, transforms=True) or []
    return pool


def _world_position(node):
    try:
        return cmds.xform(node, q=True, ws=True, t=True)
    except Exception:
        return None


def nearest_mirrored(node, pool, axis="X", tolerance=1.0):
    """node 의 월드 위치를 axis 기준으로 미러한 지점에서 가장 가까운 후보.

    반환 : (노드, 거리). 못 찾으면 (None, 최근접 거리 or None)
    """
    src = _world_position(node)
    if src is None:
        return None, None

    idx = AXIS_INDEX.get(str(axis).upper(), 0)
    target = list(src)
    target[idx] = -target[idx]

    src_paths = set(cmds.ls(node, long=True) or [])

    best = None
    best_dist = None
    for cand in pool:
        if cand in src_paths:
            continue
        pos = _world_position(cand)
        if pos is None:
            continue
        d = ((pos[0] - target[0]) ** 2 +
             (pos[1] - target[1]) ** 2 +
             (pos[2] - target[2]) ** 2) ** 0.5
        if best_dist is None or d < best_dist:
            best_dist = d
            best = cand

    if best is None or best_dist > tolerance:
        return None, best_dist
    return best, best_dist


# --------------------------------------------------------------------------
# 해석기
# --------------------------------------------------------------------------

class MirrorResolver:
    """한쪽 노드 -> 반대쪽 노드.

    mode      : MODE_NAME / MODE_POSITION / MODE_AUTO
    to_side   : "Left" / "Right" (이름 토큰을 어느 쪽으로 뒤집을지)
    axis      : 위치 미러 축
    tolerance : 위치 모드에서 허용할 최대 거리(씬 단위)
    node_type : 후보 풀을 좁히는 타입("joint" / None 이면 모든 트랜스폼)
    """

    def __init__(self, mode=MODE_AUTO, to_side="Right", axis="X",
                 tolerance=1.0, node_type=None):
        self.mode = mode
        self.to_side = to_side
        self.axis = axis
        self.tolerance = tolerance
        self.node_type = node_type
        self._pool_cache = {}

    # -------------------------------------------------- 이름

    def _resolve_by_name(self, node):
        paths = cmds.ls(node, long=True) or []
        parent_path = paths[0].rsplit("|", 1)[0] if paths else ""

        for cand in mirror_name_candidates(node, self.to_side):
            leaf = cand.split("|")[-1]
            # 같은 부모 아래를 먼저 본다 - 동명 노드가 있어도 제 짝을 집는다.
            if parent_path:
                sib = parent_path + "|" + leaf
                if cmds.objExists(sib):
                    return sib, "name"
            found = cmds.ls(leaf, long=True) or []
            if len(found) == 1:
                return found[0], "name"
            if len(found) > 1:
                # 동명 노드가 여럿이면 소스와 같은 계층에 있는 것을 고른다.
                root = hierarchy_root(node)
                same = [f for f in found if root and f.startswith(root + "|")]
                if len(same) == 1:
                    return same[0], "name"
                return None, "ambiguous name ({0} nodes named '{1}')".format(len(found), leaf)
        return None, "no side token in name"

    # -------------------------------------------------- 위치

    def _pool(self, node):
        key = hierarchy_root(node) or "<scene>"
        if key not in self._pool_cache:
            self._pool_cache[key] = candidate_pool(node, self.node_type)
        return self._pool_cache[key]

    def _resolve_by_position(self, node):
        found, dist = nearest_mirrored(node, self._pool(node),
                                       axis=self.axis, tolerance=self.tolerance)
        if found:
            return found, "position (d={0:.4f})".format(dist)
        if dist is None:
            return None, "position: no candidate"
        return None, "position: nearest is {0:.4f} away (> tolerance {1:g})".format(
            dist, self.tolerance)

    # -------------------------------------------------- 공개

    def resolve(self, node):
        """반환 : (찾은 노드 or None, 근거 문자열)"""
        if not node or not cmds.objExists(node):
            return None, "source does not exist"

        if self.mode == MODE_NAME:
            return self._resolve_by_name(node)
        if self.mode == MODE_POSITION:
            return self._resolve_by_position(node)

        found, why = self._resolve_by_name(node)
        if found:
            return found, why
        found2, why2 = self._resolve_by_position(node)
        if found2:
            return found2, why2
        return None, "{0} / {1}".format(why, why2)

    def clear_cache(self):
        self._pool_cache = {}
