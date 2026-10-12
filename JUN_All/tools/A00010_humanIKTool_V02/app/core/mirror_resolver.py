# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-12
# A00010_humanIKTool_V02 - "왼쪽 노드에 대응하는 오른쪽 노드" 를 찾는 해석기.
#
# 조인트 Mirror 와 컨트롤러(Custom Rig) Mirror 가 같은 이 모듈을 쓴다. 대상만 다를 뿐
# "이미 할당된 한쪽 노드를 보고 반대쪽 노드를 고른다" 는 문제는 완전히 동일하기 때문이다.
#
# v02.06 (2026-10-12)
#   - 이름 토큰은 **공용 규칙 `Framework/rules/mirror_tokens.json`**(Framework.core.mirror_tokens)
#     을 쓴다. 이 모듈이 따로 갖던 토큰 표(left/right, lft/rgt, lt/rt, lf/rt, l/r)는 지웠다 -
#     A00110 Mirror Key · A00145 Mirror 와 같은 파일, 같은 경계 판정.
#   - 후보 풀은 "조인트" 로 못 박지 않고 **소스와 같은 노드 타입**(NODE_TYPE_SOURCE) 으로 좁힌다.
#     HIK 슬롯에 조인트가 아니라 컨트롤러(transform)를 할당해 둔 캐릭터는 반대쪽도 컨트롤러에서
#     찾는다. 조인트 소스면 전처럼 조인트만.
#
# -- 무엇을 근거로 짝을 찾을 것인가 -------------------------------------------
#
# (1) 이름 (NAME)  * 기본값
#     리깅 이름에는 사실상 예외 없이 방향 토큰이 들어간다 - arm_l_JNT / arm_lf_ctrl /
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

from Framework.core.mirror_tokens import MirrorTokenStore


#: 후보를 어디서 찾나 (A00010 v02.04, MirrorResolver(search=...))
SEARCH_HIERARCHY = "hierarchy"   # 예전 그대로 (컨트롤러 미러가 쓴다)
SEARCH_ROOTS = "roots"           # 주어진 최상위 노드들 아래만
SEARCH_SCENE = "scene"           # 씬 전체 - 동명이 여럿이면 실패

#: node_type 에 주면 "소스와 같은 노드 타입"(exactType) 으로 후보를 좁힌다 (v02.06).
NODE_TYPE_SOURCE = "<source>"

MODE_NAME = "name"
MODE_POSITION = "position"
MODE_AUTO = "auto"

AXIS_INDEX = {"X": 0, "Y": 1, "Z": 2}


# --------------------------------------------------------------------------
# 이름
# --------------------------------------------------------------------------

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


def load_token_pairs():
    """공용 규칙 파일의 enabled 토큰 쌍. 반환 (pairs, message)."""
    return MirrorTokenStore.load()


def mirror_name_candidates(node, to_side, token_pairs=None):
    """node 이름의 방향 토큰을 뒤집은 후보 이름들(우선순위 순, 중복 제거).

    v02.06 : 토큰 쌍과 경계 판정은 **공용 `MirrorTokenStore.opposite_name`** 그대로다
    (`Framework/rules/mirror_tokens.json`, 위에서 아래 순서로 처음 걸리는 쌍의 경계 occurrence 를
    전부 바꾼다). 후보는 보통 하나지만 목록으로 돌려주는 인터페이스는 유지한다.

    to_side : "Right" 면 왼쪽 토큰이 들어 있어야 하고, "Left" 면 오른쪽 토큰. 반대쪽 토큰만
              들어 있는 이름(이미 반대편인 노드)은 후보를 내지 않는다.
    """
    prefix, leaf = split_name(node)
    if token_pairs is None:
        token_pairs, _ = load_token_pairs()

    to_right = (to_side != "Left")
    mirrored, token = MirrorTokenStore.opposite_name(leaf, token_pairs)
    if not mirrored:
        return []

    # 걸린 토큰이 가고자 하는 방향의 **출발 쪽** 토큰인지 확인한다.
    src_tokens = {(left if to_right else right) for left, right in token_pairs}
    if token not in src_tokens:
        return []
    return [prefix + mirrored]


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


def node_type_of(node):
    """node 의 노드 타입. 없으면 None."""
    try:
        return cmds.nodeType(node)
    except Exception:
        return None


def _ls_typed(node_type, *args, **kwargs):
    """cmds.ls 에 타입 조건을 붙인다. None 이면 모든 트랜스폼."""
    if node_type:
        return cmds.ls(*args, long=True, exactType=node_type, **kwargs) or []
    return cmds.ls(*args, long=True, transforms=True, **kwargs) or []


def candidate_pool(reference, node_type=None):
    """reference 와 같은 계층 아래의 노드들. 없으면 씬 전체로 넓힌다.

    같은 리그 안으로 좁히면 레퍼런스가 여러 개 걸린 씬에서 옆 캐릭터의 조인트를 집는
    사고를 막는다. node_type 은 **정확한 타입**(exactType)으로 본다 - "transform" 이면 조인트는
    빠진다(컨트롤러 소스가 조인트를 집지 않도록, v02.06).
    """
    root = hierarchy_root(reference)
    pool = []
    if root:
        pool = _ls_typed(node_type, root, dag=True)
    if not pool:
        pool = _ls_typed(node_type)
    return pool


def top_joint(node):
    """node 위로 조인트가 이어지는 동안 올라간 맨 위 조인트(풀 패스). node 가 조인트가 아니면 None.

    HIK 스켈레톤의 '최상위 조인트' - 그 위의 그룹 · 트랜스폼에서는 멈춘다 (A00010 v02.04).
    """
    paths = cmds.ls(node, long=True, type="joint") or []
    if not paths:
        return None
    current = paths[0]
    while True:
        parent = (cmds.listRelatives(current, parent=True, fullPath=True) or [None])[0]
        if not parent or cmds.nodeType(parent) != "joint":
            return current
        current = parent


def top_node(node):
    """node 가 속한 '최상위' (풀 패스) - 조인트면 top_joint, 아니면 DAG 최상위 트랜스폼 (v02.06).

    HIK 슬롯에 컨트롤러를 할당한 캐릭터는 컨트롤러가 든 리그 계층의 맨 위가 '같은 루트' 다.
    """
    top = top_joint(node)
    if top:
        return top
    root = hierarchy_root(node)
    if root:
        return root
    paths = cmds.ls(node, long=True) or []
    return paths[0] if paths else None


def under_roots(path, roots):
    """path 가 roots 중 하나이거나 그 아래인가 (풀 패스 비교)."""
    return any(path == r or path.startswith(r + "|") for r in roots)


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
    node_type : 후보 풀을 좁히는 타입. None 이면 모든 트랜스폼, "joint" 처럼 고정 타입,
                NODE_TYPE_SOURCE 면 **소스 노드와 같은 타입**(exactType) - 조인트 소스는 조인트에서,
                컨트롤러(transform) 소스는 조인트가 아닌 트랜스폼에서 찾는다 (v02.06).
    search    : 후보를 어디서 찾나 (A00010 v02.04)
                SEARCH_HIERARCHY (기본) - 예전 그대로: 같은 부모 -> 씬 -> 동명이면 같은 DAG 최상위 아래
                SEARCH_ROOTS     - roots(풀 패스 목록) 아래에서만 (Mirror in same root 켜짐)
                SEARCH_SCENE     - 씬 전체. 동명이 여럿이면 추측하지 않고 실패 (Mirror in same root 꺼짐)
    """

    def __init__(self, mode=MODE_AUTO, to_side="Right", axis="X",
                 tolerance=1.0, node_type=None, search=None, roots=None,
                 token_pairs=None):
        self.mode = mode
        self.to_side = to_side
        self.axis = axis
        self.tolerance = tolerance
        self.node_type = node_type
        self.search = search or SEARCH_HIERARCHY
        self.roots = list(roots or [])
        # 공용 규칙은 한 번만 읽는다 (해석기 하나가 슬롯 수십 개를 푼다).
        self.token_pairs = token_pairs if token_pairs is not None else load_token_pairs()[0]
        self._pool_cache = {}

    def _type_for(self, node):
        """이 소스에 쓸 후보 타입."""
        if self.node_type == NODE_TYPE_SOURCE:
            return node_type_of(node)
        return self.node_type

    def _named(self, leaf, node_type):
        """leaf 이름인 노드들(풀 패스) - node_type 이 있으면 그 타입(exactType)만."""
        if node_type:
            return cmds.ls(leaf, long=True, exactType=node_type) or []
        return cmds.ls(leaf, long=True) or []

    # -------------------------------------------------- 이름

    def _resolve_by_name(self, node):
        if self.search in (SEARCH_ROOTS, SEARCH_SCENE):
            return self._resolve_by_name_scoped(node)
        paths = cmds.ls(node, long=True) or []
        parent_path = paths[0].rsplit("|", 1)[0] if paths else ""

        for cand in mirror_name_candidates(node, self.to_side, self.token_pairs):
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
        return None, "no side token in name (Framework/rules/mirror_tokens.json)"

    def _resolve_by_name_scoped(self, node):
        """SEARCH_ROOTS / SEARCH_SCENE - 범위 안에서 그 이름이 **딱 하나**일 때만 고른다."""
        if self.search == SEARCH_ROOTS and not self.roots:
            return None, "no HIK root to search under"
        node_type = self._type_for(node)
        for cand in mirror_name_candidates(node, self.to_side, self.token_pairs):
            leaf = cand.split("|")[-1]
            found = self._named(leaf, node_type)
            if self.search == SEARCH_ROOTS:
                found = [f for f in found if under_roots(f, self.roots)]
            if len(found) == 1:
                return found[0], "name"
            if len(found) > 1:
                where = "under the HIK root" if self.search == SEARCH_ROOTS else "in the scene"
                return None, "ambiguous name ({0} nodes named '{1}' {2})".format(
                    len(found), leaf, where)
        if self.search == SEARCH_ROOTS:
            return None, "no mirrored name under the HIK root"
        return None, "no side token in name (Framework/rules/mirror_tokens.json)"

    # -------------------------------------------------- 위치

    def _pool(self, node):
        node_type = self._type_for(node)
        if self.search == SEARCH_ROOTS:
            key = ("<roots>", node_type)
            if key not in self._pool_cache:
                pool = []
                for r in self.roots:
                    pool += _ls_typed(node_type, r, dag=True)
                self._pool_cache[key] = pool
            return self._pool_cache[key]
        if self.search == SEARCH_SCENE:
            key = ("<scene>", node_type)
            if key not in self._pool_cache:
                self._pool_cache[key] = _ls_typed(node_type)
            return self._pool_cache[key]
        key = (hierarchy_root(node) or "<scene>", node_type)
        if key not in self._pool_cache:
            self._pool_cache[key] = candidate_pool(node, node_type)
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
