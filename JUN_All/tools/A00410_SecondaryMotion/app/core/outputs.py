# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-07-30
# A00410_SecondaryMotion core - 출력 백엔드 레지스트리.
#
# 왜 레지스트리인가
# ----------------
# A00390_WindTool 이 출력을 **Curve(키 굽기) / Node(라이브 노드망)** 로 나눈 것처럼,
# 이 툴도 나중에 "라이브" 출력이 붙을 수 있다. 그때 솔버·샘플러·회전 재구성을 건드리지
# 않도록 출력 쪽을 이 파일 하나로 몰아둔다.
#
# 새 출력을 추가하는 절차 = **이 파일에 spec 하나 register() 하는 것뿐**이다.
#   - `app/core/chain_solver.py`   : 출력 방식을 모른다 (순수 물리)
#   - `app/core/pose_builder.py`   : 출력 방식을 모른다 (점 -> 로컬 회전)
#   - `app/core/scene_sampler.py`  : 출력 방식을 모른다 (체인 해석 + 샘플링)
#   - `app/ui/main_window.py`      : Output 라디오를 이 레지스트리에서 **자동 생성**한다
#                                    (spec 을 추가하면 UI 에 저절로 나타난다)
#
# 계열(family)
#   curve : 프레임별 해를 구해 **키로 굽는다**(현재 Layer / Bake Keys 둘 다 이 계열).
#           needs_solve=True 이므로 세션이 먼저 solve() 를 돌려 회전값을 만들어 넘긴다.
#   node  : 어트리뷰트를 가진 드라이버 + 노드망으로 **라이브 재현**한다(예약, 미구현).
#           needs_solve=False 로 두면 프레임별 해 없이 체인 토폴로지 + 파라미터만 받는다.
#
# 주의: 노드 계열을 실제로 만들 때는 이 툴의 솔버가 **상태를 시간 순으로 누적**한다는 점을
# 고려해야 한다(스프링은 이전 프레임 속도가 필요하다). A00390 의 싸인 파형은 t 만으로
# 값이 정해져 노드망으로 바로 옮길 수 있었지만, 2차 모션은 그렇지 않다 —
# 적분 표현식(A00390 windPhaseTime 방식)이나 커스텀 노드가 필요하다.

# 출력 id (씬/설정에 저장될 수 있으니 값은 바꾸지 말 것)
OUTPUT_LAYER = "layer"
OUTPUT_KEYS = "keys"
OUTPUT_NODE = "node"        # 예약 — 라이브 노드망(미구현)

# 계열
FAMILY_CURVE = "curve"
FAMILY_NODE = "node"


class OutputSpec(object):
    """출력 백엔드 1종의 명세.

    apply_fn(session, params, writes, **kw) -> (노드 수, 사용자에게 보여줄 메시지)
        session : SecondaryMotionSession (frames / samples / 레이어 헬퍼 제공)
        params  : SolverParams
        writes  : needs_solve=True 면 {node: [(rx,ry,rz), ...프레임별]}, 아니면 None
    """

    def __init__(self, id, label, family, apply_fn,
                 needs_solve=True, tooltip="", implemented=True):
        self.id = id
        self.label = label
        self.family = family
        self.apply_fn = apply_fn
        self.needs_solve = needs_solve
        self.tooltip = tooltip
        self.implemented = implemented

    def apply(self, session, params, writes, **kw):
        if not self.implemented or self.apply_fn is None:
            raise RuntimeError(
                "Output '{0}' is not implemented yet.".format(self.label))
        return self.apply_fn(session, params, writes, **kw)


# id -> OutputSpec (등록 순서 유지)
_REGISTRY = []


def register(spec):
    """출력 spec 등록. 같은 id 가 이미 있으면 교체한다."""
    for i, s in enumerate(_REGISTRY):
        if s.id == spec.id:
            _REGISTRY[i] = spec
            return spec
    _REGISTRY.append(spec)
    return spec


def get(output_id):
    for s in _REGISTRY:
        if s.id == output_id:
            return s
    raise RuntimeError("Unknown output '{0}'.".format(output_id))


def all_specs():
    return list(_REGISTRY)


def implemented_specs():
    """UI 가 라디오로 만들 대상(구현된 것만)."""
    return [s for s in _REGISTRY if s.implemented]


def default_id():
    specs = implemented_specs()
    return specs[0].id if specs else None


# ======================================================================
# curve 계열 — 프레임별 해를 키로 굽는다
# ======================================================================

def _apply_layer(session, params, writes, layer_name=None, **kw):
    """override 애님 레이어에 절대 회전값 기록. 원본 보존 + weight 로 강도 조절."""
    if not writes:
        raise RuntimeError("Nothing to apply.")

    name = layer_name or session.default_layer_name()

    if session.has_preview():
        # 프리뷰 레이어를 그대로 최종 레이어로 승격 — 다시 계산하지 않는다.
        final = session.promote_preview(name)
        return len(writes), (
            "Applied to override anim layer '{0}' ({1} nodes). "
            "Use the layer weight to dial the amount.".format(final, len(writes)))

    final = session.ensure_layer(name, writes.keys(), unique=True)
    session.write_curves(final, writes)
    session.forget_layer()
    return len(writes), (
        "Applied to override anim layer '{0}' ({1} nodes). "
        "Use the layer weight to dial the amount.".format(final, len(writes)))


def _apply_keys(session, params, writes, **kw):
    """컨트롤러/조인트 커브에 직접 굽는다(undo 가능한 cmds 경로)."""
    if not writes:
        raise RuntimeError("Nothing to apply.")

    session.clear_preview()
    session.bake_keys(writes)
    return len(writes), (
        "Baked keys onto {0} nodes, frames {1}~{2}.".format(
            len(writes), session.frames[0], session.frames[-1]))


register(OutputSpec(
    OUTPUT_LAYER, "Override Layer", FAMILY_CURVE, _apply_layer,
    tooltip="Write absolute rotations into an override anim layer. The original\n"
            "animation stays untouched and the layer weight dials the amount."))

register(OutputSpec(
    OUTPUT_KEYS, "Bake Keys", FAMILY_CURVE, _apply_keys,
    tooltip="Replace the keys on the nodes themselves inside the range."))

# 예약된 노드 출력 — UI 에 나타나지 않는다(implemented=False).
# 구현할 때는 apply_fn 을 채우고 implemented=True 로 바꾸면 UI 에 자동으로 라디오가 생긴다.
register(OutputSpec(
    OUTPUT_NODE, "Live Node", FAMILY_NODE, None,
    needs_solve=False, implemented=False,
    tooltip="Reserved: reproduce the secondary motion live with a driver node\n"
            "network instead of baked keys (not implemented yet)."))
