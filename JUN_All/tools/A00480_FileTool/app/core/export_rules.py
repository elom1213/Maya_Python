# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-18
# A00480_FileTool - Export 규칙 (내보내기 전에 씬을 검사한다) (v01.03)
#
# 규칙은 **내보내기 전에** 돈다. 켜 둔 규칙을 **전부** 돌리고, 하나라도 걸리면 내보내기를
# **시작하지 않는다** - 첫 실패에서 멈추지 않는 이유는 한 번에 모든 문제를 보여 주기 위해서다.
#
# ── 규칙을 늘리는 법 ─────────────────────────────────────────────────────
# 1) 검사 함수를 쓴다   def check_xxx(ctx) -> RuleResult
#       ctx     : RuleContext (내보내기 설정 - 세트 목록, 경로, 필터 ...)
#       반환    : RuleResult(passed, logs)   passed=False 면 내보내기가 막힌다
# 2) EXPORT_RULES 에 ExportRule(...) 한 줄을 더한다
# 그러면 Export 탭의 `Rules` 드롭다운에 체크 항목이 생기고, Export / Check 가 그대로 돌린다.
# UI 는 이 목록만 읽는다 - 규칙마다 UI 코드를 고치지 않는다.
#
# maya.cmds 는 export_ops 와 같이 lazy import 한다(Maya 밖에서도 import 가능).


class RuleContext(object):
    """규칙이 볼 수 있는 내보내기 설정. 규칙이 늘면 필요한 값을 여기에 더한다."""

    def __init__(self, set_names, export_path="", excluded_keys=None,
                 keep_hierarchy=False, joints_only=True):
        self.set_names = list(set_names or [])
        self.export_path = export_path
        self.excluded_keys = list(excluded_keys or [])
        self.keep_hierarchy = keep_hierarchy
        self.joints_only = joints_only


class RuleResult(object):
    """규칙 하나의 결과. passed=False 면 내보내기를 막는다."""

    def __init__(self, passed, logs=None):
        self.passed = bool(passed)
        self.logs = list(logs or [])


class ExportRule(object):
    """등록된 규칙 하나.

    key     : 코드에서 부르는 이름 (바뀌지 않는다)
    label   : 드롭다운에 보이는 이름 (영어 - UI 문자열)
    tooltip : 드롭다운 항목 툴팁 (영어)
    check   : check(ctx) -> RuleResult
    default : 창을 열었을 때 켜져 있는가
    """

    def __init__(self, key, label, tooltip, check, default=False):
        self.key = key
        self.label = label
        self.tooltip = tooltip
        self.check = check
        self.default = default


def _cmds():
    try:
        import maya.cmds as cmds
        return cmds
    except Exception:
        return None


# ================================================================
# 규칙 1 : Check Hide Mesh
# ================================================================

def _set_nodes(set_name, cmds, seen=None):
    """세트 멤버 -> DAG 노드(전체 경로). 컴포넌트는 그 오브젝트로, 하위 세트는 펼친다."""
    seen = set() if seen is None else seen
    if set_name in seen:
        return []
    seen.add(set_name)
    nodes = []
    for member in cmds.sets(set_name, q=True) or []:
        try:
            if cmds.objectType(member) == "objectSet":
                nodes.extend(_set_nodes(member, cmds, seen))
                continue
        except Exception:
            pass
        nodes.extend(cmds.ls(member, objectsOnly=True, long=True) or [])
    return nodes


def _meshes_below(node, cmds):
    """node 아래 메시 쉐입을 **아웃라이너 순서**로 (위에서 아래, 형제는 적힌 순서).

    `listRelatives(allDescendents=True)` 의 순서는 아웃라이너와 달라(뒤집어도 맞지 않았다, 실측)
    로그를 읽기 어렵다 - 자식을 직접 따라 내려간다.
    """
    out = []
    stack = [node]
    while stack:
        current = stack.pop()
        for shape in cmds.listRelatives(current, shapes=True, fullPath=True) or []:
            if cmds.objectType(shape) == "mesh":
                out.append(shape)
        kids = cmds.listRelatives(current, children=True, type="transform",
                                  fullPath=True) or []
        stack.extend(reversed(kids))
    return out


def _is_intermediate(shape, cmds):
    try:
        return bool(cmds.getAttr(shape + ".intermediateObject"))
    except Exception:
        return False


def meshes_in_set(set_name):
    """세트 안의 모든 메시 쉐입(전체 경로, 중복 없이, 세트 순서). intermediate 쉐입은 뺀다.

    멤버가 트랜스폼(그룹 · 조인트 포함)이면 **그 아래 전부**를 본다 - 내보내기도 멤버의
    하위를 함께 내보내기 때문이다. 멤버가 쉐입이면 그 쉐입, 컴포넌트면 그 오브젝트.
    """
    cmds = _cmds()
    out, seen = [], set()
    for node in _set_nodes(set_name, cmds):
        if cmds.objectType(node) == "mesh":
            candidates = [node]
        else:
            candidates = _meshes_below(node, cmds)
        for shape in candidates:
            if shape in seen or _is_intermediate(shape, cmds):
                continue
            seen.add(shape)
            out.append(shape)
    return out


def _short(path):
    return path.split("|")[-1]


def _node_hidden_reasons(node, cmds):
    """이 노드 하나가 자기 아래를 안 보이게 만드는 이유들 (없으면 빈 목록)."""
    reasons = []

    def attr(name, default=True):
        try:
            return cmds.getAttr("{0}.{1}".format(node, name))
        except Exception:
            return default

    if not attr("visibility"):
        reasons.append("{0}.visibility is off".format(_short(node)))
    if not attr("lodVisibility"):
        reasons.append("{0}.lodVisibility is off".format(_short(node)))
    if attr("overrideEnabled", False) and not attr("overrideVisibility"):
        layers = cmds.listConnections(node + ".drawOverride", source=True,
                                      destination=False, type="displayLayer") or []
        if layers:
            reasons.append("display layer '{0}' is hidden".format(layers[0]))
        else:
            reasons.append("{0} is hidden by its drawing override".format(_short(node)))
    return reasons


def hidden_reasons(shape):
    """메시 쉐입이 **마야 뷰포트에서 안 보이는** 이유들. 보이면 빈 목록.

    쉐입 자신과 그 위의 **모든 조상**(트랜스폼 · 그룹 · 조인트)을 본다 - 부모 하나만 꺼져도
    그 아래는 전부 안 보인다. visibility / lodVisibility / 드로잉 오버라이드(디스플레이 레이어 포함).
    """
    cmds = _cmds()
    reasons = list(_node_hidden_reasons(shape, cmds))
    parent = cmds.listRelatives(shape, parent=True, fullPath=True) or []
    while parent:
        reasons.extend(_node_hidden_reasons(parent[0], cmds))
        parent = cmds.listRelatives(parent[0], parent=True, fullPath=True) or []
    return reasons


def check_hidden_mesh(ctx):
    """Set's Name 의 세트 안 메시 중 숨겨진 것이 있으면 막는다. 어떤 세트의 어떤 메시인지 적는다."""
    cmds = _cmds()
    if cmds is None:
        return RuleResult(False, ["[FAIL] Check Hide Mesh : Maya not available."])

    logs = []
    hidden_total = 0
    hidden_sets = 0
    checked = 0
    for set_name in ctx.set_names:
        if not cmds.objExists(set_name) or cmds.objectType(set_name) != "objectSet":
            continue                       # 없는 세트는 내보내기가 [SKIP] 으로 알린다
        meshes = meshes_in_set(set_name)
        checked += len(meshes)
        hidden = [(m, hidden_reasons(m)) for m in meshes]
        hidden = [(m, r) for m, r in hidden if r]
        if not hidden:
            continue
        hidden_sets += 1
        hidden_total += len(hidden)
        logs.append("[WARN]   {0} : {1} hidden mesh(es)".format(set_name, len(hidden)))
        for mesh, reasons in hidden:
            transform = (cmds.listRelatives(mesh, parent=True) or [_short(mesh)])[0]
            logs.append("[WARN]     - {0}  ({1})".format(transform, "; ".join(reasons)))

    if hidden_total:
        head = ("[WARN] Check Hide Mesh : {0} hidden mesh(es) in {1} set(s).".format(
            hidden_total, hidden_sets))
        return RuleResult(False, [head] + logs)
    return RuleResult(True, ["[OK] Check Hide Mesh : {0} mesh(es) checked, none hidden.".format(
        checked)])


# ================================================================
# 레지스트리 - 규칙을 늘릴 때는 여기에 한 줄
# ================================================================

EXPORT_RULES = [
    ExportRule(
        key="check_hidden_mesh",
        label="Check Hide Mesh",
        tooltip=("Before exporting, look at every mesh in the listed sets. If any of them\n"
                 "is hidden in the scene (its own or a parent's visibility is off, or a\n"
                 "display layer hides it), the export does not start and the log lists\n"
                 "each hidden mesh with its set and the reason."),
        check=check_hidden_mesh,
        default=False,
    ),
]


def rule_by_key(key):
    for rule in EXPORT_RULES:
        if rule.key == key:
            return rule
    return None


def run_rules(keys, ctx):
    """keys 의 규칙을 **전부** 돌린다. `(passed, logs)`.

    passed 는 모든 규칙이 통과했을 때만 True. 첫 실패에서 멈추지 않는다 - 문제를 한 번에 보인다.
    규칙이 예외를 던지면 그 규칙은 실패로 친다(내보내기를 안전한 쪽으로 막는다).
    """
    logs = []
    passed = True
    for key in keys:
        rule = rule_by_key(key)
        if rule is None:
            logs.append("[WARN] Unknown export rule '{0}' - skipped.".format(key))
            continue
        try:
            result = rule.check(ctx)
        except Exception as e:
            result = RuleResult(False, ["[FAIL] {0} : {1}".format(rule.label, e)])
        passed = passed and result.passed
        logs.extend(result.logs)
    return passed, logs
