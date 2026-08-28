# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-28
# A00130_ControlRig_V02 - 씬 조회 헬퍼 (네임스페이스 · 세트 멤버 · 쓰기 가능 판정).
#
# 계획서 7-11 · 1-11 · 1-13 을 구현한다.

import maya.cmds as cmds


#: 네임스페이스를 고르지 않았을 때 UI 가 보여 주는 항목
NO_NAMESPACE = "(none)"


# =========================
# 네임스페이스
# =========================

def list_namespaces():
    """씬의 네임스페이스 목록. 마야 내장(`UI` · `shared`)은 뺀다.

    계획서 1-13 — 규칙으로 정하지 않고 **사용자가 고른다**. 그래서 규칙 없이
    씬에 있는 것을 그대로 보여 준다.
    """
    found = cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True) or []
    out = []
    for ns in found:
        clean = ns.lstrip(":")
        if not clean or clean in ("UI", "shared"):
            continue
        out.append(clean)
    return sorted(out)


def qualify(name, namespace):
    """이름에 네임스페이스를 붙인다."""
    if not namespace or namespace == NO_NAMESPACE:
        return name
    return "{0}:{1}".format(namespace.rstrip(":"), name)


def candidates(name, namespace):
    """이 이름이 씬에서 가질 수 있는 후보들. 앞이 우선순위."""
    out = []
    qualified = qualify(name, namespace)
    if qualified != name:
        out.append(qualified)
    out.append(name)
    return out


def resolve(name, namespace):
    """이름을 실제 씬 노드로 푼다. `(찾은 이름 또는 None, 실제로 있는 후보 전부)`.

    **네임스페이스를 붙인 쪽을 먼저 보고, 없으면 이름 그대로 본다.**

    ── 왜 둘 다 보나 (2026-08-28 버그) ────────────────────────────────────
    처음에는 "템플릿 조인트는 작업 씬에 로컬, 케이지 세트만 레퍼런스" 라고 보고
    **세트에만** 네임스페이스를 붙였다. 그런데 실제 케이지 파일에는 **템플릿 조인트도
    함께 들어 있다.** 그래서 케이지를 **임포트**하면(네임스페이스 없음) 다 찾아지는데
    **레퍼런스**하면 조인트가 `CAGE:helper_pelvis` 가 되어 전부
    `joint missing` 이 됐다 — 네임스페이스를 제대로 골라도 마찬가지였다.

    한쪽만 고르는 대신 **둘 다 후보로 두면** 세 경우가 모두 된다:
      - 케이지를 레퍼런스     -> `CAGE:helper_pelvis`
      - 케이지를 임포트       -> `helper_pelvis`
      - 툴이 만든 로컬 조인트 -> `helper_pelvis`

    둘 다 있으면 호출부가 **모호하다고 알린다**(어느 쪽을 골랐는지 감추지 않는다).
    """
    found = [c for c in candidates(name, namespace) if cmds.objExists(c)]
    return (found[0] if found else None), found


# =========================
# 세트
# =========================

def is_set(node):
    """objectSet / shadingEngine / partition 이면 True.

    `nodeType(inherited=True)` 로 본다 — `shadingEngine` 은 `objectSet` 의 하위 타입이라
    `nodeType()` 문자열 비교로는 놓친다.
    """
    if not node or not cmds.objExists(node):
        return False
    inherited = cmds.nodeType(node, inherited=True) or []
    return "objectSet" in inherited or "partition" in inherited


def resolve_members(node):
    """매칭 대상이 될 노드 목록을 돌려준다.

    돌려주는 것: `(members, skipped_sets)`

    - **세트면** 멤버를 편다. 단 **멤버 중 또 다른 세트는 통째로 무시**한다(계획서 1-11).
      재귀하지 않는다 — 하위 세트 안의 오브젝트도 건드리지 않는다.
    - **세트가 아니면** 그 노드 자신이 유일한 멤버다(자료 A 가 "세트, 혹은 오브젝트" 라고
      했으므로 둘 다 받는다).

    > `cmds.sets(<세트가 아닌 노드>, q=True)` 는 **None 을 돌려주고 경고를 낸다**(실측).
    > 그래서 먼저 `is_set()` 으로 갈라야 한다.
    """
    if not cmds.objExists(node):
        return [], []

    if not is_set(node):
        return [node], []

    members = cmds.sets(node, q=True) or []
    keep, skipped = [], []
    for m in members:
        (skipped if is_set(m) else keep).append(m)
    return keep, skipped


# =========================
# 쓰기 가능 판정
# =========================

def plug_writable(plug):
    """이 플러그에 `setAttr`/`xform` 이 실제로 '먹는지'.

    Match(트랜스폼 채널)와 Length(옵션 컨트롤러 어트리뷰트) 두 곳이 쓴다 —
    그래서 밑줄 없는 공개 이름이다.

    잠겨 있거나 무언가에 구동되면 안 먹는다. **`getAttr(settable=True)` 는 믿을 수 없다**
    — 컨스트레인트가 구동하는 트랜스폼에도 True 를 돌려준다(A00060 에서 실측).
    잠금과 입력 연결을 직접 본다.
    """
    if not cmds.objExists(plug):
        return False
    try:
        if cmds.getAttr(plug, lock=True):
            return False
        if cmds.connectionInfo(plug, isDestination=True):
            return False
    except Exception:
        return False
    return True


def blocked_channels(node, translate=True, rotate=True):
    """지금 쓰려는 채널 중 막혀 있는 것들의 이름. 없으면 빈 목록.

    **`matchTransform` 은 잠긴 채널을 조용히 건너뛴다**(실측: `translateX` 만 잠근
    오브젝트가 X 만 안 움직이고 에러도 없었다). 그래서 미리 보고 막힌 것이 있으면
    아예 건드리지 않고 알린다 — 반쯤 옮겨진 상태가 제일 나쁘다.
    """
    axes = []
    if translate:
        axes += ["translateX", "translateY", "translateZ"]
    if rotate:
        axes += ["rotateX", "rotateY", "rotateZ"]

    blocked = []
    for attr in axes:
        plug = "{0}.{1}".format(node, attr)
        if not plug_writable(plug):
            blocked.append(attr)
    return blocked


#: 채널 그룹의 상태
GROUP_FREE = "free"          # 전부 쓸 수 있다
GROUP_DRIVEN = "driven"      # 전부 막혔다 - 리그가 이 채널을 갖고 있다
GROUP_PARTIAL = "partial"    # 일부만 막혔다 - 건드리면 반쪽이 된다

#: 그룹 이름 -> 채널
CHANNEL_GROUPS = {
    "translate": ("translateX", "translateY", "translateZ"),
    "rotate": ("rotateX", "rotateY", "rotateZ"),
}


def channel_group_state(node, group):
    """이 그룹을 지금 쓸 수 있나. `(상태, 막힌 채널 이름들)`.

    ── 왜 그룹으로 보나 (2026-08-28) ─────────────────────────────────────────
    처음에는 채널 하나라도 막히면 **그 오브젝트를 통째로 건너뛰었다.** "반쯤 옮겨진
    상태가 제일 나쁘다" 는 이유였는데, 실제 케이지에서 그게 과했다.

    실측하면 **컨스트레인트는 그룹을 통째로** 막는다:

        pointConstraint    -> translate 3/3,  rotate 0/3
        orientConstraint   -> translate 0/3,  rotate 3/3
        aimConstraint      -> translate 0/3,  rotate 3/3
        parentConstraint   -> 양쪽 3/3

    즉 `pointConstraint` 가 걸린 컨트롤러는 **위치를 리그가 갖고 있을 뿐 회전은 비어 있다.**
    통째로 건너뛰면 **회전이 매칭 안 된 채 방치된다** (사용자 보고:
    `A01_Arm_L_01_UpperArm` 안의 오브젝트들).

    반면 **축 하나만 잠긴 경우**는 다르다 — `translateX` 만 잠그고 위치를 맞추면
    `t=[90, 2, 3]` 처럼 **X 만 안 가고 Y·Z 만 간다**(실측). 이것이 진짜 반쪽 상태다.

    → **그룹 단위로 all-or-nothing.** 전부 막혔으면 깨끗이 건너뛰고(리그 몫),
      일부만 막혔으면 **건드리지 않고 크게 알린다.**
    """
    channels = CHANNEL_GROUPS.get(group, ())
    blocked = [c for c in channels
               if not plug_writable("{0}.{1}".format(node, c))]
    if not blocked:
        return GROUP_FREE, []
    if len(blocked) == len(channels):
        return GROUP_DRIVEN, blocked
    return GROUP_PARTIAL, blocked


def short_name(node):
    """DAG 경로/네임스페이스를 떼고 leaf 이름만."""
    return (node or "").split("|")[-1].split(":")[-1]
