# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-30
# A00410_SecondaryMotion core - 체인 수집 + 프레임별 원본 포즈 샘플링 (maya.cmds/API, UI 비의존).
#
# 왜 "한 번 샘플링해서 캐시" 인가
# ------------------------------
# mayapy 실측(20본 x 300프레임):
#   - 체인 전체 worldMatrix 를 프레임마다 getAttr -time : 0.374 s   <- 유일하게 비싼 단계
#   - 스프링 솔버                                        : 0.006 s
#   - 회전 키 벌크 기록(MFnAnimCurve.addKeys)            : 0.007 s
# 그래서 **씬 샘플링은 한 번만** 하고 캐시에 담아두고, 파라미터를 만질 때는 캐시로부터
# 솔브+기록만 다시 한다(≈13ms). 이것이 이 툴의 "실시간 미리보기"를 가능하게 하는 구조다.
#
# 캐시는 **원본(2차 모션이 적용되지 않은) 애니메이션**이어야 하므로, 프리뷰 레이어가
# 씬에 있는 상태로 다시 샘플링하면 자기 출력을 되먹는다. 그래서 샘플링 시에는
# 프리뷰 레이어를 뮤트한다(bake_manager 가 처리).
#
# 확인된 마야 변환 규칙(mayapy 검증)
#   joint     : local = R * JO          -> R = L * JO^-1        (R 은 노드의 rotateOrder)
#   transform : local = RA * R          -> R = RA^-1 * L
#   공통      : world = local * parentWorld
# (row-vector 규약. 그래서 조인트 직접 모드에서는 jointOrient 를 반드시 벗겨내야 한다.)

import maya.cmds as cmds
from maya.api import OpenMaya as om


# 대상 해석 모드 (A00390_WindTool 의 Bone Chain / Bone Root 와 같은 개념)
#   chain : 리스트업한 노드들이 '하나의 체인' — 리스트 순서가 루트→팁 순서다.
#   root  : 리스트업한 각 노드를 '임의의 체인의 최상위 부모' 로 보고, 그 자손을 따라
#           내려가며 루트마다 체인을 만든다. 분기가 있으면 루트→말단 경로마다 체인이 된다.
MODE_CHAIN = "chain"
MODE_ROOT = "root"

# 예전 이름(호환용). 새 코드는 MODE_CHAIN 을 쓴다.
MODE_LIST = MODE_CHAIN

# 대상 타입
#   ctrl  : FK 컨트롤러(일반 transform). 계층 탐색 시 transform 을 따라간다.
#   joint : 조인트 직접 모드. 계층 탐색을 joint 로 제한하고, 로컬 회전을 구할 때
#           jointOrient 를 벗겨낸다.
TARGET_CTRL = "ctrl"
TARGET_JOINT = "joint"

# Maya rotateOrder(0~5) -> MEulerRotation 열거값. 값이 같은 순서로 대응된다.
_ROTATE_ORDERS = (om.MEulerRotation.kXYZ, om.MEulerRotation.kYZX,
                  om.MEulerRotation.kZXY, om.MEulerRotation.kXZY,
                  om.MEulerRotation.kYXZ, om.MEulerRotation.kZYX)


def _long(name):
    found = cmds.ls(name, long=True) or []
    return found[0] if found else None


def _children(node, target_type):
    """계층 탐색 한 단계. joint 모드면 joint 만, ctrl 모드면 transform 전부(그룹 포함)."""
    kind = "joint" if target_type == TARGET_JOINT else "transform"
    return cmds.listRelatives(node, children=True, type=kind, fullPath=True) or []


def _is_control(node):
    """컨트롤러로 볼 노드인가 = **셰이프를 가진 transform**.

    FK 리그는 보통 `ctl_01 > ctl_01_offset > ctl_02` 처럼 컨트롤 사이에 오프셋/제로
    그룹이 낀다. 그룹까지 체인 노드로 잡으면 그룹에 키가 찍히고 체인 길이가 배로
    늘어나 falloff 도 어긋난다. 그룹은 **지나가되 담지 않는다**.
    셰이프 판정이라 nurbsCurve 컨트롤·로케이터·메시 컨트롤 모두 잡힌다.
    """
    try:
        return bool(cmds.listRelatives(node, shapes=True, fullPath=True))
    except Exception:
        return False


def _paths_from_root(root, target_type, control_filter=True):
    """root 에서 각 말단까지의 **선형 경로** 목록.

    솔버는 "각 i 의 부모가 i-1" 인 선형 체인을 다루므로, 분기가 있으면 루트→말단
    경로마다 체인 하나로 쪼갠다. 공유되는 앞부분(분기 전 구간)은 여러 체인에 중복해서
    들어가는데, 키를 쓸 때 **먼저 계산된(가장 긴) 체인이 이긴다**(bake_manager 에서 중복 제거).

    control_filter=True 이고 ctrl 모드면 **셰이프 없는 그룹은 건너뛰고**(계층은 계속
    타고 내려가되 체인에 담지 않는다) 컨트롤만 모은다. root 는 사용자가 지정한
    '최상위 부모' 이므로 셰이프가 없어도 항상 체인의 첫 노드로 담는다.
    """
    skip_groups = control_filter and target_type != TARGET_JOINT

    out = []
    stack = [(root, [root])]
    while stack:
        node, path = stack.pop()
        kids = _children(node, target_type)
        if not kids:
            out.append(path)
            continue
        for c in kids:
            # 그룹은 경로에 넣지 않고 통과만 한다.
            nxt = path if (skip_groups and not _is_control(c)) else path + [c]
            stack.append((c, nxt))

    # 같은 경로가 여러 번 나올 수 있다(그룹만 있는 가지들) → 중복 제거.
    uniq, seen = [], set()
    for p in out:
        key = tuple(p)
        if key not in seen:
            seen.add(key)
            uniq.append(p)

    # 깊은 경로가 먼저 오도록(공유 구간을 긴 체인이 차지하게)
    uniq.sort(key=len, reverse=True)
    return uniq


class ChainResolveResult(object):
    """체인 해석 결과. 항목이 늘어도 호출부가 깨지지 않도록 튜플 대신 객체로 둔다."""

    def __init__(self):
        self.chains = []        # [[root, ...], ...] 전부 풀패스
        self.missing = []       # 씬에 없는 이름
        self.branched = []      # 분기로 여러 체인이 된 루트(경고용)
        self.empty_roots = []   # 자식이 없어 체인이 안 된 루트(경고용)

    def __iter__(self):
        # 예전 3-튜플 언패킹 호환.
        return iter((self.chains, self.missing, self.branched))


def resolve_chains(nodes, mode, target_type):
    """UI 리스트 -> ChainResolveResult.

    chain 모드: 리스트 순서 그대로 체인 1개.
    root  모드: 리스트업한 각 노드를 최상위 부모로 보고 자손을 따라 체인을 만든다
               (A00390_WindTool 의 Bone Root 와 같은 개념).
    """
    res = ChainResolveResult()

    if mode == MODE_ROOT:
        for n in nodes or []:
            full = _long(n)
            if not full:
                res.missing.append(n)
                continue

            paths = [p for p in _paths_from_root(full, target_type) if len(p) >= 2]
            if not paths:
                # 컨트롤 필터 때문에 아무것도 못 잡은 경우(조인트 계층에 ctrl 모드 등)
                # 필터를 끄고 한 번 더 시도한다.
                paths = [p for p in _paths_from_root(full, target_type,
                                                     control_filter=False)
                         if len(p) >= 2]
            if not paths:
                res.empty_roots.append(full.split("|")[-1])
                continue

            if len(paths) > 1:
                res.branched.append(full.split("|")[-1])
            res.chains.extend(paths)
        return res

    # chain 모드: 리스트 순서 그대로 하나의 체인
    chain = []
    for n in nodes or []:
        full = _long(n)
        if not full:
            res.missing.append(n)
            continue
        chain.append(full)
    if len(chain) >= 2:
        res.chains.append(chain)
    return res


class ChainSample(object):
    """한 체인의 프레임별 원본 포즈 스냅샷(= 솔버 입력 + 회전 재구성 재료)."""

    def __init__(self, nodes, frames):
        self.nodes = list(nodes)
        self.frames = list(frames)
        self.positions = []      # [f][i] = (x,y,z)  원본(강체 FK) 월드 위치
        self.world_quats = []    # [f][i] = MQuaternion  원본 월드 회전
        # [f][i] = MQuaternion — **각 노드의 실제 DAG 부모** 월드 회전.
        # 앞 체인 노드가 아니라 진짜 부모여야 한다: FK 리그는 보통
        # ctl_01 > ctl_01_offset > ctl_02 처럼 중간에 오프셋 그룹이 끼기 때문에,
        # 앞 노드를 부모로 가정하면 그룹의 회전이 컨트롤러에 구워져 하위가 어긋난다.
        self.parent_quats = []
        self.jo_inv = []         # [i] MQuaternion  jointOrient 역(조인트가 아니면 단위)
        self.ra_inv = []         # [i] MQuaternion  rotateAxis 역
        self.orders = []         # [i] MEulerRotation 열거값
        self.rest_local = []     # [i] 원본 로컬 회전(도) — 방향을 못 구할 때 복원용
        # 팁도 회전시키기 위해 마지막 뼈를 한 번 더 연장한 **가상 점**을 붙였는가.
        # (KawaiiPhysics 의 dummy bone 과 같은 역할)
        self.dummy_tip = False

    def count(self):
        """실제 노드 수(가상 팁 제외)."""
        return len(self.nodes)

    def point_count(self):
        """솔버가 다루는 점 개수(가상 팁 포함)."""
        return len(self.positions[0]) if self.positions else 0


def _decompose(matrix_values):
    """flat 16 리스트 -> (위치, 회전 쿼터니언). 스케일이 섞여 있어도 회전만 뽑는다."""
    m = om.MMatrix(matrix_values)
    xf = om.MTransformationMatrix(m)
    t = xf.translation(om.MSpace.kWorld)
    return (t.x, t.y, t.z), xf.rotation(asQuaternion=True)


def _static_info(node, target_type):
    """노드의 정적 정보(jointOrient / rotateAxis / rotateOrder / 원본 로컬 회전)."""
    is_joint = cmds.objectType(node, isAType="joint")

    jo_inv = om.MQuaternion()
    if is_joint and target_type is not None:
        jo = cmds.getAttr(node + ".jointOrient")[0]
        jo_inv = om.MEulerRotation(
            om.MAngle(jo[0], om.MAngle.kDegrees).asRadians(),
            om.MAngle(jo[1], om.MAngle.kDegrees).asRadians(),
            om.MAngle(jo[2], om.MAngle.kDegrees).asRadians(),
            om.MEulerRotation.kXYZ).asQuaternion().inverse()

    ra = cmds.getAttr(node + ".rotateAxis")[0]
    ra_inv = om.MEulerRotation(
        om.MAngle(ra[0], om.MAngle.kDegrees).asRadians(),
        om.MAngle(ra[1], om.MAngle.kDegrees).asRadians(),
        om.MAngle(ra[2], om.MAngle.kDegrees).asRadians(),
        om.MEulerRotation.kXYZ).asQuaternion().inverse()

    order = _ROTATE_ORDERS[int(cmds.getAttr(node + ".rotateOrder"))]
    rest = cmds.getAttr(node + ".rotate")[0]
    return jo_inv, ra_inv, order, tuple(rest)


def sample_chain(chain, frames, target_type=TARGET_CTRL, dummy_tip=True):
    """체인의 프레임별 원본 월드 포즈를 읽어 ChainSample 로 담는다.

    `getAttr -time` 을 쓰므로 현재 시간을 바꾸지 않는다(= 씬 상태를 건드리지 않는다).
    컨스트레인트/애님 레이어/리그가 어떻게 얽혀 있어도 최종 월드 결과를 그대로 읽으므로
    안전하다. 대신 노드 x 프레임 수만큼 호출이 들어가는 유일한 비싼 단계다.

    dummy_tip=True 면 마지막 뼈를 같은 방향으로 한 번 더 연장한 **가상 점**을 붙인다.
    팁 노드도 '자식' 이 생겨 회전을 정의할 수 있게 되므로, 체인의 마지막 컨트롤러/조인트도
    다른 노드처럼 회전한다(KawaiiPhysics 의 dummy bone 과 같은 방식).
    """
    s = ChainSample(chain, frames)

    for node in chain:
        jo_inv, ra_inv, order, rest = _static_info(node, target_type)
        s.jo_inv.append(jo_inv)
        s.ra_inv.append(ra_inv)
        s.orders.append(order)
        s.rest_local.append(rest)

    # 각 노드의 **실제 DAG 부모**. 앞 체인 노드가 아니다(오프셋 그룹이 낄 수 있다).
    parents = []
    for node in chain:
        p = cmds.listRelatives(node, parent=True, fullPath=True) or []
        parents.append(p[0] if p else None)

    # 체인에 없는 부모만 따로 샘플링한다(대부분의 조인트 체인에서는 추가 비용이 없다).
    chain_set = set(chain)
    extra = []
    for p in parents:
        if p and p not in chain_set and p not in extra:
            extra.append(p)

    for f in frames:
        quats = {}
        pos_row, quat_row = [], []
        for node in chain:
            p, q = _decompose(cmds.getAttr(node + ".worldMatrix[0]", time=f))
            pos_row.append(p)
            quat_row.append(q)
            quats[node] = q
        for node in extra:
            _, q = _decompose(cmds.getAttr(node + ".worldMatrix[0]", time=f))
            quats[node] = q

        s.positions.append(pos_row)
        s.world_quats.append(quat_row)
        s.parent_quats.append(
            [quats[pn] if pn else om.MQuaternion() for pn in parents])

    if dummy_tip and len(chain) >= 2:
        s.dummy_tip = True
        for row in s.positions:
            a, b = row[-2], row[-1]
            # 마지막 뼈를 같은 방향/길이로 한 번 더 연장.
            # 길이가 0 이면 가상 점이 팁과 겹쳐 방향을 못 구하는데, 그 경우
            # pose_builder 가 그 프레임의 팁 회전을 원본 그대로 둔다(안전한 폴백).
            row.append((b[0] + (b[0] - a[0]),
                        b[1] + (b[1] - a[1]),
                        b[2] + (b[2] - a[2])))

    return s


def scene_fps():
    """현재 씬의 프레임레이트(fps). 알 수 없으면 24."""
    unit = cmds.currentUnit(query=True, time=True)
    table = {"game": 15.0, "film": 24.0, "pal": 25.0, "ntsc": 30.0,
             "show": 48.0, "palf": 50.0, "ntscf": 60.0}
    if unit in table:
        return table[unit]
    # "30fps", "120fps" 같은 형식
    if unit.endswith("fps"):
        try:
            return float(unit[:-3])
        except ValueError:
            pass
    return 24.0
