# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-21
# A00110_animTool_V02 - Create > Noise : 노이즈 노드 생성 · 발견 · 커브 재계산 (maya.cmds, UI 비의존)
#
# 노이즈 유닛 하나 = 노드 2개
#
#   JUN_noise1      (transform)    설정 어트리뷰트 + output
#   JUN_noise1_crv  (animCurveTU)  output 을 구동하는 진짜 애니메이션 커브
#
# **왜 animCurve 인가 (설계의 전부)**
#   마야 그래프 에디터는 animCurve 노드만 그린다. 표현식이나 유틸리티 노드, 플러그인
#   노드(MPxNode)로 값을 계산하면 채널은 보여도 **곡선이 없다.** 그래서 "노이즈를 그래프
#   에디터에서 보고 싶다" 는 요구를 지키려면 노이즈가 **animCurve 여야만** 한다.
#   설정이 바뀌면 커브를 다시 채우는데, 1000키 재기록이 2ms 라 슬라이더로 흔들어도 문제없다.
#   (계획서 §2 / docs/plans/A00110_animTool_V02_noise_tab_plan.md)
#
# 덤으로 얻는 것: 재생 중 평가 비용이 0(그냥 커브 조회), 플러그인 배포 불필요,
# 애니메이터가 결과 커브를 직접 손볼 수 있음.

import contextlib

import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma

from Framework.core.maya_undo import undo_chunk

from . import noise_generator as ng


# ------------------------------------------------------------------ 이름 · 어트리뷰트

# 씬에서 노이즈 노드를 찾아내는 마커. 값에 버전을 넣어 나중에 마이그레이션할 여지를 둔다.
MARKER_ATTR = "junNoiseNode"
MARKER_VALUE = "A00110:1"

ATTR_OUTPUT = "output"
ATTR_TYPE = "noiseType"
ATTR_SMOOTHNESS = "smoothness"
ATTR_OFFSET = "noiseOffset"
ATTR_MIN = "outMin"
ATTR_MAX = "outMax"
ATTR_SEED = "seed"
ATTR_LENGTH = "loopLength"

# 설정 어트리뷰트 전부(채널박스 표시 순서이기도 하다)
SETTING_ATTRS = (ATTR_TYPE, ATTR_SMOOTHNESS, ATTR_OFFSET,
                 ATTR_MIN, ATTR_MAX, ATTR_SEED, ATTR_LENGTH)

DEFAULT_NAME = "JUN_noise#"
CURVE_SUFFIX = "_crv"

# animCurve 의 infinity 열거값. 3 = cycle (반복). 이게 seamless 의 두 번째 겹이다.
INFINITY_CYCLE = 3


class NoiseNodeManager(object):
    """노이즈 노드를 만들고 찾고 다시 굽는다. 전부 정적 메서드 (다른 manager 들과 같은 스타일).

    씬을 바꾸는 메서드는 (개수, 메시지) 를 돌려주는 이 툴의 관례를 따르되,
    UI 가 노드를 계속 다뤄야 하는 create 만 노드 이름을 함께 돌려준다.
    """

    # ============================================================== 발견 · 판별

    @staticmethod
    def is_noise_node(node):
        """이 노드가 우리가 만든 노이즈 노드인가."""
        if not node or not cmds.objExists(node):
            return False
        return bool(cmds.attributeQuery(MARKER_ATTR, node=node, exists=True))

    @staticmethod
    def find_all():
        """씬 전체의 노이즈 노드를 이름순으로 돌려준다.

        `ls` 로 transform 을 전부 훑는 대신 **마커 어트리뷰트로 바로 찾는다** —
        `ls("*." + MARKER_ATTR)` 는 어트리뷰트를 가진 노드만 골라내므로 씬이 커도 싸다.
        """
        plugs = cmds.ls("*." + MARKER_ATTR, recursive=True) or []
        found = []
        for plug in plugs:
            node = plug.rsplit(".", 1)[0]
            if node not in found:
                found.append(node)
        return sorted(found)

    @staticmethod
    def curve_of(node):
        """노드의 output 을 구동하는 animCurve. 없으면 None."""
        if not node or not cmds.objExists(node + "." + ATTR_OUTPUT):
            return None
        curves = cmds.listConnections(node + "." + ATTR_OUTPUT,
                                      source=True, destination=False,
                                      type="animCurve") or []
        return curves[0] if curves else None

    # ============================================================== 설정 읽기 · 쓰기

    @staticmethod
    def read_settings(node):
        """노드의 설정을 generate() 에 그대로 넘길 수 있는 dict 로 읽는다."""
        get = lambda a: cmds.getAttr(node + "." + a)
        return {
            "kind": ng.type_from_index(get(ATTR_TYPE)),
            "smoothness": float(get(ATTR_SMOOTHNESS)),
            "offset": float(get(ATTR_OFFSET)),
            "out_min": float(get(ATTR_MIN)),
            "out_max": float(get(ATTR_MAX)),
            "seed": int(get(ATTR_SEED)),
            "length": int(get(ATTR_LENGTH)),
        }

    @staticmethod
    def write_settings(node, kind=None, smoothness=None, offset=None,
                       out_min=None, out_max=None, seed=None, length=None):
        """설정 어트리뷰트에 값을 쓴다(커브는 건드리지 않는다). None 인 항목은 그대로 둔다."""
        if kind is not None:
            cmds.setAttr(node + "." + ATTR_TYPE, ng.type_index(kind))
        if smoothness is not None:
            cmds.setAttr(node + "." + ATTR_SMOOTHNESS, float(smoothness))
        if offset is not None:
            cmds.setAttr(node + "." + ATTR_OFFSET, float(offset))
        if out_min is not None:
            cmds.setAttr(node + "." + ATTR_MIN, float(out_min))
        if out_max is not None:
            cmds.setAttr(node + "." + ATTR_MAX, float(out_max))
        if seed is not None:
            cmds.setAttr(node + "." + ATTR_SEED, int(seed))
        if length is not None:
            cmds.setAttr(node + "." + ATTR_LENGTH, int(length))

    # ============================================================== 생성

    @staticmethod
    def create(name=None, kind=ng.VALUE, smoothness=ng.DEFAULT_SMOOTHNESS,
               offset=0.0, out_min=ng.DEFAULT_MIN, out_max=ng.DEFAULT_MAX,
               seed=None, length=ng.DEFAULT_LOOP_LENGTH):
        """노이즈 노드 하나를 만든다. 반환: (노드 이름, 메시지)"""

        if seed is None:
            # 노드마다 다른 파형이 나오도록 기존 개수에서 시드를 뽑는다.
            # (결정론은 '같은 시드 -> 같은 파형' 이면 되고, 시드 자체는 달라야 한다.)
            seed = (len(NoiseNodeManager.find_all()) + 1) * 7919 % 100000

        with undo_chunk():
            node = cmds.createNode("transform", name=name or DEFAULT_NAME)

            # 트랜스폼 채널은 쓰지 않는다. 채널박스에서 치워 설정만 보이게 한다.
            for base in ("translate", "rotate", "scale"):
                for axis in "XYZ":
                    cmds.setAttr("{0}.{1}{2}".format(node, base, axis),
                                 lock=True, keyable=False, channelBox=False)
            cmds.setAttr(node + ".visibility", lock=True, keyable=False, channelBox=False)

            # --- 설정 어트리뷰트 ---
            # minValue/maxValue 를 걸지 않는다: 마야의 min/max 는 범위 밖 setAttr 을
            # 잘라내는 게 아니라 RuntimeError 를 던진다. 요청상 Smoothness/Offset 에는
            # 한계가 없어야 하고, outMin > outMax 도 허용해야 한다.
            cmds.addAttr(node, longName=ATTR_TYPE, attributeType="enum",
                         enumName=":".join(ng.NOISE_TYPE_TOKENS),
                         defaultValue=ng.type_index(kind), keyable=True)
            cmds.addAttr(node, longName=ATTR_SMOOTHNESS, attributeType="double",
                         defaultValue=float(smoothness), keyable=True)
            cmds.addAttr(node, longName=ATTR_OFFSET, attributeType="double",
                         defaultValue=float(offset), keyable=True)
            cmds.addAttr(node, longName=ATTR_MIN, attributeType="double",
                         defaultValue=float(out_min), keyable=True)
            cmds.addAttr(node, longName=ATTR_MAX, attributeType="double",
                         defaultValue=float(out_max), keyable=True)
            cmds.addAttr(node, longName=ATTR_SEED, attributeType="long",
                         defaultValue=int(seed), keyable=True)
            cmds.addAttr(node, longName=ATTR_LENGTH, attributeType="long",
                         defaultValue=int(length), keyable=True)

            # --- 출력 ---
            cmds.addAttr(node, longName=ATTR_OUTPUT, attributeType="double", keyable=True)

            # --- 마커 ---
            cmds.addAttr(node, longName=MARKER_ATTR, dataType="string")
            cmds.setAttr(node + "." + MARKER_ATTR, MARKER_VALUE, type="string")
            cmds.setAttr(node + "." + MARKER_ATTR, lock=True)

            NoiseNodeManager.rebuild(node)

        return (node, "Noise node '{0}' created ({1}, {2}f loop, seed {3}).".format(
            node, kind, int(length), int(seed)))

    @staticmethod
    def delete(nodes):
        """노이즈 노드(와 딸린 커브)를 지운다. 반환: (지운 수, 메시지)"""
        targets = [n for n in (nodes or []) if NoiseNodeManager.is_noise_node(n)]
        if not targets:
            return (0, "[Warning] No noise node to delete.")

        with undo_chunk():
            for node in targets:
                curve = NoiseNodeManager.curve_of(node)
                if curve and cmds.objExists(curve):
                    cmds.delete(curve)
                cmds.setAttr(node + "." + MARKER_ATTR, lock=False)
                cmds.delete(node)

        return (len(targets), "{0} noise node(s) deleted.".format(len(targets)))

    # ============================================================== 커브 재계산

    @staticmethod
    def _anim_fn(curve):
        sel = om.MSelectionList()
        sel.add(curve)
        return oma.MFnAnimCurve(sel.getDependNode(0))

    @staticmethod
    def _add_keys(curve, values):
        """values 를 프레임 0..len-1 에 통째로 깐다. 탄젠트는 linear.

        **탄젠트를 spline/auto 로 두면 안 된다.** 키 사이에서 곡선이 튀어(overshoot)
        사용자가 지정한 Min/Max 를 넘어가 버린다. linear 는 키 값이 곧 구간의 극값이라
        범위가 정확히 지켜지고, 서브프레임 평가도 정직하다.
        """
        fn = NoiseNodeManager._anim_fn(curve)
        unit = om.MTime.uiUnit()

        times = om.MTimeArray()
        vals = om.MDoubleArray()
        for i, v in enumerate(values):
            times.append(om.MTime(float(i), unit))
            vals.append(float(v))

        fn.addKeys(times, vals,
                   oma.MFnAnimCurve.kTangentLinear,
                   oma.MFnAnimCurve.kTangentLinear)

    @staticmethod
    def rebuild(node):
        """커브를 **통째로 새로 만들어** output 에 연결한다(기존 커브는 지운다). 반환: 키 수

        이게 **undo 가 되는 유일한 경로**다. 이유가 중요하다:
        `MFnAnimCurve.setValue()` 는 (MAnimCurveChange 없이 부르면) **undo 정보를 남기지
        않는다.** 파이썬에서는 MAnimCurveChange 를 마야의 undo 큐에 걸 방법이 없다
        (MPxCommand 플러그인이 있어야 한다). 그래서 확정(commit)은 setValue 가 아니라
        `cmds.delete` + `cmds.createNode` + `cmds.connectAttr` 로 한다 — 셋 다 cmds 라
        undo 가 되고, 새 노드를 통째로 되돌리면 옛 커브가 키까지 그대로 복구된다.

        반대로 미리보기(refresh)는 **undo 를 남기지 않는 게 목적**이라 setValue 를 쓴다.
        """
        settings = NoiseNodeManager.read_settings(node)
        values = ng.generate(**settings)

        old = NoiseNodeManager.curve_of(node)
        if old and cmds.objExists(old):
            cmds.delete(old)

        curve = cmds.createNode("animCurveTU", name=node + CURVE_SUFFIX)
        NoiseNodeManager._add_keys(curve, values)

        # seamless 의 두 번째 겹. 커브를 무한히 반복시킨다.
        cmds.setAttr(curve + ".preInfinity", INFINITY_CYCLE)
        cmds.setAttr(curve + ".postInfinity", INFINITY_CYCLE)

        cmds.connectAttr(curve + ".output", node + "." + ATTR_OUTPUT, force=True)
        return len(values)

    @staticmethod
    def refresh(node):
        """노드 설정대로 커브 값을 **제자리에서** 덮어쓴다(미리보기용). 반환: 채운 키 수

        키 1000개 재기록이 2ms 라 슬라이더로 흔들어도 충분하다. undo 는 남지 않는다
        (그게 미리보기의 요구사항이다 — 확정은 rebuild 가 한다).

        [!] `cutKey(clear=True)` 로 비우고 다시 깔면 안 된다 — 키가 0개가 된 animCurve 는
            **마야가 노드째로 지워버려서** output 연결이 끊긴다(실측). 그래서 개수가 같으면
            setValue 로 덮어쓰고, 달라질 때만 커브를 통째로 새로 만들어 다시 연결한다.
        """
        if not NoiseNodeManager.is_noise_node(node):
            return 0

        settings = NoiseNodeManager.read_settings(node)
        values = ng.generate(**settings)

        curve = NoiseNodeManager.curve_of(node)
        if not curve or not cmds.objExists(curve):
            return NoiseNodeManager.rebuild(node)

        fn = NoiseNodeManager._anim_fn(curve)
        if fn.numKeys != len(values):
            return NoiseNodeManager.rebuild(node)

        for i, v in enumerate(values):
            fn.setValue(i, float(v))
        return len(values)

    @staticmethod
    def apply(node, **settings):
        """설정을 쓰고 커브를 다시 구운다(undo 한 항목). 반환: (키 수, 메시지)"""
        if not NoiseNodeManager.is_noise_node(node):
            return (0, "[Warning] '{0}' is not a noise node.".format(node))

        with undo_chunk():
            NoiseNodeManager.write_settings(node, **settings)
            count = NoiseNodeManager.rebuild(node)

        cur = NoiseNodeManager.read_settings(node)
        return (count, "'{0}' updated: {1}, smoothness {2:g}, offset {3:g}, "
                       "range [{4:g}, {5:g}], seed {6}, loop {7}f.".format(
                           node, cur["kind"], cur["smoothness"], cur["offset"],
                           cur["out_min"], cur["out_max"], cur["seed"], cur["length"]))

    # ============================================================== 출력 연결

    @staticmethod
    def connect_output(node, plugs):
        """node.output 을 대상 어트리뷰트들에 연결한다. 반환: (연결 수, 메시지)

        이미 뭔가 연결돼 있으면 force 로 갈아끼운다 — 노이즈를 이 채널에 걸겠다는 뜻이
        분명하고, 그러지 않으면 '아무 일도 안 일어난 것처럼' 보이기 때문이다.
        """
        if not NoiseNodeManager.is_noise_node(node):
            return (0, "[Warning] Select a noise node first.")

        targets = [p for p in (plugs or []) if cmds.objExists(p)]
        if not targets:
            return (0, "[Warning] Select target attributes in the Channel Box first.")

        src = node + "." + ATTR_OUTPUT
        done, failed = 0, []

        with undo_chunk():
            for plug in targets:
                try:
                    if cmds.getAttr(plug, lock=True):
                        failed.append(plug + " (locked)")
                        continue
                    cmds.connectAttr(src, plug, force=True)
                    done += 1
                except Exception as exc:
                    failed.append("{0} ({1})".format(plug, exc))

        msg = "{0} connected to {1} attribute(s).".format(src, done)
        if failed:
            msg += " {0} failed: {1}".format(len(failed), ", ".join(failed[:4]))
        return (done, msg)

    @staticmethod
    def disconnect_output(node):
        """node.output 이 물고 있는 연결을 전부 끊는다. 반환: (끊은 수, 메시지)"""
        if not NoiseNodeManager.is_noise_node(node):
            return (0, "[Warning] Select a noise node first.")

        src = node + "." + ATTR_OUTPUT
        plugs = cmds.listConnections(src, source=False, destination=True,
                                     plugs=True) or []
        if not plugs:
            return (0, "'{0}' is not connected to anything.".format(src))

        # 각도 채널에 걸렸던 unitConversion 은 끊고 나면 아무것도 안 하는 쓰레기 노드가 된다.
        strays = [p.rsplit(".", 1)[0] for p in plugs
                  if cmds.objExists(p.rsplit(".", 1)[0])
                  and cmds.nodeType(p.rsplit(".", 1)[0]) == "unitConversion"]

        with undo_chunk():
            for plug in plugs:
                try:
                    cmds.disconnectAttr(src, plug)
                except Exception:
                    pass
            for stray in strays:
                if cmds.objExists(stray):
                    cmds.delete(stray)

        return (len(plugs), "{0} disconnected from {1} attribute(s).".format(src, len(plugs)))

    @staticmethod
    def output_targets(node):
        """node.output 이 구동 중인 **최종** 대상 플러그 목록.

        각도(rotate 등)에 연결하면 마야가 `unitConversion` 노드를 사이에 끼워 넣는다.
        그대로 열거하면 사용자에게 `unitConversion1.input` 이 보여 무엇에 걸렸는지 알 수 없다.
        그래서 unitConversion 은 **통과해서** 그 너머의 진짜 대상을 돌려준다.
        (값 자체는 손해가 없다 — 변환 계수가 deg<->rad 라 `getAttr(rotateZ)` 은 output 과
         같은 수를 도(degree)로 돌려준다. 즉 Min/Max 를 도 단위로 쓰면 그대로 맞는다.)
        """
        if not NoiseNodeManager.is_noise_node(node):
            return []

        found = []
        pending = cmds.listConnections(node + "." + ATTR_OUTPUT,
                                       source=False, destination=True, plugs=True) or []
        # unitConversion 은 한 번만 끼지만, 혹시 모를 연쇄를 대비해 깊이를 제한한 루프로 푼다.
        for _ in range(4):
            if not pending:
                break
            nxt = []
            for plug in pending:
                target_node = plug.rsplit(".", 1)[0]
                if cmds.objExists(target_node) and cmds.nodeType(target_node) == "unitConversion":
                    nxt.extend(cmds.listConnections(target_node + ".output",
                                                    source=False, destination=True,
                                                    plugs=True) or [])
                elif plug not in found:
                    found.append(plug)
            pending = nxt

        return found

    # ============================================================== UI 보조

    @staticmethod
    def summary(node):
        """리스트에 한 줄로 보여줄 요약 문자열."""
        if not NoiseNodeManager.is_noise_node(node):
            return node
        s = NoiseNodeManager.read_settings(node)
        return "{0}   {1}   smooth {2:g}   [{3:g}, {4:g}]   {5}f".format(
            node, s["kind"], s["smoothness"], s["out_min"], s["out_max"], s["length"])

    @staticmethod
    def seed_from_name(node):
        """Randomize 용 시드. 노드 이름과 현재 시드를 섞어 '다음 시드' 를 만든다.

        시각(time)에 기대지 않아서, 같은 노드에서 같은 횟수만큼 누르면 같은 시드가 나온다.
        """
        cur = 0
        if NoiseNodeManager.is_noise_node(node):
            cur = int(cmds.getAttr(node + "." + ATTR_SEED))
        return ng.hash32(cur + 1, sum(ord(c) for c in str(node))) % 100000


# ==================================================================== 슬라이더 세션


@contextlib.contextmanager
def _undo_disabled():
    """블록 안의 cmds 호출을 undo 큐에 남기지 않는다 (미리보기용).

    stateWithoutFlush 는 "큐를 비우지 않고" undo 기록만 잠시 끈다. state=False 를 쓰면
    지금까지 쌓인 undo 히스토리가 통째로 날아가므로 반드시 이쪽을 쓴다.
    (A00110 Stagger / A00380 Peak 에서 검증한 패턴과 동일.)
    """
    cmds.undoInfo(stateWithoutFlush=False)
    try:
        yield
    finally:
        cmds.undoInfo(stateWithoutFlush=True)


class NoiseSession(object):
    """노이즈 노드 하나를 슬라이더로 만지는 '한 세션'.

    조작 모델은 이 툴의 Stagger Offset · Curve Filters 와 같다.
      - 드래그 중에는 `preview()` 로 즉시 반영하되 **undo 큐에 남기지 않는다.**
      - 조작이 멎으면 `settle()` 이 그때까지의 결과를 **한 항목으로** 기록한다.
      - 그래서 **드래그 한 번 = Ctrl+Z 한 번**이다.

    `settle()` 이 기록하기 전에 반드시 **마지막 확정 상태로 되돌린 뒤** 다시 적용한다.
    undo 는 '그 명령의 역연산을 현재 상태에 적용' 하는 것이라, 미리보기 값이 남은 채로
    기록하면 Ctrl+Z 가 미리보기 상태로 돌아가 버린다(restore-before-commit).

    `kind` 와 `length` 는 **확정 전용**이다(콤보 박스라 조작이 한 번에 끝나고,
    length 가 바뀌면 키 개수가 달라져 미리보기의 제자리 갱신 경로를 쓸 수 없다).
    """

    # 미리보기로 만질 수 있는 항목. 나머지는 settle 로만 바뀐다.
    PREVIEW_KEYS = ("smoothness", "offset", "out_min", "out_max")

    def __init__(self, node):
        self.node = node
        # 세션을 시작할 때의 설정 (Reset 이 돌아갈 자리)
        self.origin = NoiseNodeManager.read_settings(node)
        # 마지막으로 undo 큐에 기록된 설정
        self.settled = dict(self.origin)
        # 지금 씬에 반영돼 있는 설정(미리보기 포함)
        self.applied = dict(self.origin)

    # ---------------------------------------------------------------- 상태

    def valid(self):
        """노드가 아직 살아 있나."""
        return NoiseNodeManager.is_noise_node(self.node)

    def in_sync(self):
        """씬이 세션의 가정과 일치하나.

        사용자가 Ctrl+Z 를 눌렀거나 채널박스에서 값을 직접 고치면 세션의 `applied` 가
        거짓이 된다. 그 상태로 계속 밀면 엉뚱한 값을 기준으로 되돌리게 되므로,
        어긋나면 호출측(UI)이 세션을 버리고 새로 만든다.
        """
        if not self.valid():
            return False
        cur = NoiseNodeManager.read_settings(self.node)
        for key, val in self.applied.items():
            other = cur.get(key)
            if isinstance(val, float):
                if abs(val - float(other)) > 1e-9:
                    return False
            elif val != other:
                return False
        return True

    def _merged(self, base, changes):
        params = dict(base)
        for key, val in (changes or {}).items():
            if val is not None:
                params[key] = val
        return params

    @staticmethod
    def _same(a, b):
        for key in a:
            va, vb = a[key], b.get(key)
            if isinstance(va, float):
                if abs(va - float(vb)) > 1e-12:
                    return False
            elif va != vb:
                return False
        return True

    # ---------------------------------------------------------------- 조작

    def preview(self, **changes):
        """슬라이더를 움직이는 동안의 즉시 반영. undo 큐에 안 올라간다. 반환: 다시 채운 키 수"""
        if not self.valid():
            return 0

        params = self._merged(self.applied, changes)
        if self._same(params, self.applied):
            return 0

        with _undo_disabled():
            NoiseNodeManager.write_settings(self.node, **params)
            count = NoiseNodeManager.refresh(self.node)

        self.applied = params
        return count

    def settle(self, **changes):
        """지금까지의 미리보기를 undo 큐에 **한 항목으로** 기록한다. 반환: (키 수, 메시지)"""
        if not self.valid():
            return (0, "[Warning] The noise node is gone.")

        params = self._merged(self.settled, changes)

        if self._same(params, self.settled):
            # 기록할 변화가 없다. 미리보기가 떠 있으면 조용히 확정 상태로 맞춰만 둔다.
            if not self._same(self.applied, self.settled):
                with _undo_disabled():
                    NoiseNodeManager.write_settings(self.node, **self.settled)
                    NoiseNodeManager.refresh(self.node)
                self.applied = dict(self.settled)
            return (0, "")

        # restore-before-commit: 기록 전에 마지막 확정 상태로 되돌린다.
        if not self._same(self.applied, self.settled):
            with _undo_disabled():
                NoiseNodeManager.write_settings(self.node, **self.settled)
                NoiseNodeManager.refresh(self.node)
            self.applied = dict(self.settled)

        count, msg = NoiseNodeManager.apply(self.node, **params)

        self.settled = params
        self.applied = dict(params)
        return (count, msg)

    def restore(self):
        """세션을 시작할 때의 설정으로 되돌린다(undo 큐에 기록된다)."""
        return self.settle(**self.origin)
