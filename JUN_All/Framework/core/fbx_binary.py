# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-27
# Framework.core.fbx_binary - 순수 파이썬 바이너리 FBX 리더 (maya · numpy 없이, 마야 밖에서도 import 가능)
#
# A00480_FileTool `Mocap FBX Import (Exact Rotation)` 가 마야 FBX 임포터가 망가뜨린 회전 커브를 **파일의 원본 키**로
# 다시 쓰려고 만들었다 (계획서 docs/plans/A00480_FileTool_fbx_exact_import_plan.md). 108MB 파일을 1초 안쪽에 읽는다.
#
# 읽는 것 - GlobalSettings(축 · 단위 · fps), Model(LimbNode · Null ...)의 Properties70, AnimationStack/Layer/CurveNode/Curve,
# Connections(OO 부모 · OP 속성). 지오메트리 · 머티리얼 · 스킨은 노드만 건너뛴다.
#
# 포맷 메모
#   header 27 B : "Kaydara FBX Binary  \x00\x1a\x00" + uint32 version
#   node record : endOffset, numProps, propListLen (version >= 7500 이면 uint64 x3, 아니면 uint32 x3), uint8 nameLen, name
#   props       : Y i16 · C bool · I i32 · F f32 · D f64 · L i64 · S/R (u32 len + bytes)
#                 f/d/l/i/b 배열 : u32 count, u32 encoding(1 = zlib), u32 compressedLen, data  -> 쓸 때 푼다(lazy)
#   자식 노드는 endOffset 까지, 끝은 null record (13 B / 25 B)
#
# numpy 를 쓰지 않는 이유 - 이 PC 의 numpy 는 Maya 번들이 아니라 사용자 site-packages 에 있다(2026-10-27 확인).

import array
import struct
import sys
import zlib

MAGIC = b"Kaydara FBX Binary  \x00"

#: FBX 시간 단위 - 1초 = 46186158000 tick
KTIME_PER_SECOND = 46186158000

#: GlobalSettings TimeMode -> fps (0 / 14 = CustomFrameRate)
TIME_MODE_FPS = {
    1: 120.0, 2: 100.0, 3: 60.0, 4: 50.0, 5: 48.0, 6: 30.0, 7: 30.0, 8: 29.97, 9: 29.97,
    10: 25.0, 11: 24.0, 12: 1000.0, 13: 23.976, 15: 96.0, 16: 72.0, 17: 59.94,
}

#: FBX EFbxRotationOrder -> 축 순서 문자열 (앞 글자가 먼저 적용)
ROTATION_ORDERS = {0: "XYZ", 1: "XZY", 2: "YZX", 3: "YXZ", 4: "ZXY", 5: "ZYX"}

#: KeyAttrFlags 의 보간 비트
INTERP_CONSTANT = 0x02
INTERP_LINEAR = 0x04
INTERP_CUBIC = 0x08

_ARRAY_CODES = {"f": "f", "d": "d", "l": "q", "i": "i", "b": "b"}


class FbxError(Exception):
    pass


# ================================================================
# 저수준 - 노드 트리
# ================================================================

class FbxArray(object):
    """배열 속성. values() 를 부를 때 푼다."""
    __slots__ = ("type", "count", "encoding", "data")

    def __init__(self, type_code, count, encoding, data):
        self.type, self.count, self.encoding, self.data = type_code, count, encoding, data

    def values(self):
        raw = zlib.decompress(self.data) if self.encoding == 1 else self.data
        arr = array.array(_ARRAY_CODES[self.type])
        arr.frombytes(raw)
        if sys.byteorder != "little":
            arr.byteswap()
        return arr

    def __len__(self):
        return self.count


class FbxNode(object):
    __slots__ = ("name", "props", "children")

    def __init__(self, name, props, children):
        self.name, self.props, self.children = name, props, children

    def find(self, name):
        return [c for c in self.children if c.name == name]

    def first(self, name):
        for c in self.children:
            if c.name == name:
                return c
        return None


def _read_props(buf, pos, count):
    out = []
    unpack = struct.unpack_from
    for _ in range(count):
        t = chr(buf[pos])
        pos += 1
        if t == "Y":
            out.append(unpack("<h", buf, pos)[0]); pos += 2
        elif t == "C":
            out.append(bool(buf[pos])); pos += 1
        elif t == "I":
            out.append(unpack("<i", buf, pos)[0]); pos += 4
        elif t == "F":
            out.append(unpack("<f", buf, pos)[0]); pos += 4
        elif t == "D":
            out.append(unpack("<d", buf, pos)[0]); pos += 8
        elif t == "L":
            out.append(unpack("<q", buf, pos)[0]); pos += 8
        elif t in "fdlib":
            n, enc, clen = unpack("<III", buf, pos)
            pos += 12
            out.append(FbxArray(t, n, enc, bytes(buf[pos:pos + clen])))
            pos += clen
        elif t in "SR":
            ln = unpack("<I", buf, pos)[0]
            pos += 4
            raw = bytes(buf[pos:pos + ln])
            pos += ln
            out.append(raw.decode("utf-8", "replace") if t == "S" else raw)
        else:
            raise FbxError("Unknown property type {0!r} at byte {1}".format(t, pos - 1))
    return out, pos


def _read_node(buf, pos, wide):
    if wide:
        end, nprops, _plen = struct.unpack_from("<QQQ", buf, pos)
        pos += 24
    else:
        end, nprops, _plen = struct.unpack_from("<III", buf, pos)
        pos += 12
    name_len = buf[pos]
    pos += 1
    if end == 0:
        return None, pos
    name = bytes(buf[pos:pos + name_len]).decode("ascii", "replace")
    pos += name_len
    props, pos = _read_props(buf, pos, nprops)
    children = []
    while pos < end:
        child, pos = _read_node(buf, pos, wide)
        if child is None:
            break
        children.append(child)
    return FbxNode(name, props, children), end


def read_tree(data):
    """bytes -> (version, 최상위 FbxNode 리스트)."""
    if not data.startswith(MAGIC):
        if data[:200].lstrip().startswith(b";") or b"FBXHeaderExtension:" in data[:4096]:
            raise FbxError("ASCII FBX is not supported yet.")
        raise FbxError("Not a binary FBX file.")
    buf = memoryview(data)
    version = struct.unpack_from("<I", buf, 23)[0]
    wide = version >= 7500
    pos, top = 27, []
    size = len(data)
    while pos < size:
        node, pos = _read_node(buf, pos, wide)
        if node is None:
            break
        top.append(node)
    return version, top


def properties70(node):
    """Properties70 -> {이름: [타입, 라벨, 플래그, 값...]}."""
    out = {}
    p70 = node.first("Properties70") if node is not None else None
    if p70 is not None:
        for c in p70.children:
            if c.props:
                out[c.props[0]] = c.props[1:]
    return out


def _p70_value(props, key, default=None):
    """Properties70 값(4번째부터). 하나면 스칼라, 여럿이면 튜플."""
    if key not in props:
        return default
    vals = props[key][3:]
    if not vals:
        return default
    return vals[0] if len(vals) == 1 else tuple(vals)


# ================================================================
# 이름
# ================================================================

def strip_namespace(name):
    """'CHOEUN:Hips' -> 'Hips' (마야 FBX 임포터도 접두사를 떼고 만든다, 2026-10-27 실측)."""
    return name.split(":")[-1]


def maya_node_name(name):
    """마야 FBX 임포터가 만드는 노드 이름 - [A-Za-z0-9_] 밖의 바이트는 FBXASC%03d."""
    out = []
    for byte in name.encode("utf-8"):
        ch = chr(byte)
        if ch.isalnum() and byte < 128 or ch == "_":
            out.append(ch)
        else:
            out.append("FBXASC{0:03d}".format(byte))
    return "".join(out)


# ================================================================
# 문서
# ================================================================

class Track(object):
    """한 축의 애니메이션 커브. frames 는 파일 fps 기준 프레임, values 는 파일 단위(회전 = 도)."""
    __slots__ = ("frames", "values", "interp")

    def __init__(self, frames, values, interp):
        self.frames, self.values, self.interp = frames, values, interp

    def interp_kind(self):
        """키 전체의 보간 - 'linear' / 'constant' / 'cubic' / 'mixed'."""
        kinds = set(self.interp) if isinstance(self.interp, list) else {self.interp}
        return kinds.pop() if len(kinds) == 1 else "mixed"

    def value_at(self, frame):
        """frame 에서의 값 (Linear / Constant 보간, 범위 밖은 끝 값)."""
        frames, values = self.frames, self.values
        if frame <= frames[0]:
            return values[0]
        if frame >= frames[-1]:
            return values[-1]
        lo, hi = 0, len(frames) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if frames[mid] <= frame:
                lo = mid
            else:
                hi = mid
        if frames[lo] == frame:
            return values[lo]
        kind = self.interp[lo] if isinstance(self.interp, list) else self.interp
        if kind == "constant":
            return values[lo]
        f = (frame - frames[lo]) / (frames[hi] - frames[lo])
        return values[lo] + f * (values[hi] - values[lo])


class FbxModel(object):
    __slots__ = ("id", "name", "kind", "props")

    def __init__(self, id_, name, kind, props):
        self.id, self.name, self.kind, self.props = id_, name, kind, props

    @property
    def short(self):
        return strip_namespace(self.name)


class FbxDocument(object):
    """read() 결과. 모델 · 계층 · 애니 커브를 이름 대신 id 로 다룬다."""

    def __init__(self, version, top, path=""):
        self.path = path
        self.version = version
        self.models = {}            # id -> FbxModel
        self.parent = {}            # model id -> parent id (0 = 씬 루트)
        self.children = {}          # model id -> [child ids] (파일 순서)
        self._curve_nodes = {}      # id -> FbxNode
        self._curves = {}           # id -> FbxNode
        self._cn_target = {}        # curve node id -> (model id, 속성 이름)
        self._cn_curves = {}        # curve node id -> {'d|X': curve id}
        self._layer_of_cn = {}      # curve node id -> layer id
        self.stacks = []            # [(id, name, props70)]
        self.layers = {}            # layer id -> stack id
        self.counts = {}            # Model 종류 -> 개수
        self.settings = {}
        self._parse(top)

    # ---- 파싱 ----------------------------------------------------------

    def _parse(self, top):
        by_name = {n.name: n for n in top}
        gs = properties70(by_name.get("GlobalSettings"))
        objects = by_name.get("Objects")
        if objects is None:
            raise FbxError("No Objects section.")
        stack_props = {}
        for node in objects.children:
            name = node.name
            if name == "Model":
                id_, label, kind = node.props[0], node.props[1], node.props[2]
                model = FbxModel(id_, label.split("\x00")[0], kind, properties70(node))
                self.models[id_] = model
                self.counts[kind] = self.counts.get(kind, 0) + 1
            elif name == "AnimationCurveNode":
                self._curve_nodes[node.props[0]] = node
            elif name == "AnimationCurve":
                self._curves[node.props[0]] = node
            elif name == "AnimationStack":
                p = properties70(node)
                self.stacks.append((node.props[0], node.props[1].split("\x00")[0], p))
                stack_props[node.props[0]] = p
            elif name == "AnimationLayer":
                self.layers[node.props[0]] = None

        conns = by_name.get("Connections")
        for c in (conns.children if conns is not None else []):
            if len(c.props) < 3:
                continue
            kind, src, dst = c.props[0], c.props[1], c.props[2]
            if kind == "OO":
                if src in self.models:
                    self.parent[src] = dst
                elif src in self._curve_nodes and dst in self.layers:
                    self._layer_of_cn[src] = dst
                elif src in self.layers:
                    self.layers[src] = dst
            elif kind == "OP" and len(c.props) > 3:
                if src in self._curve_nodes and dst in self.models:
                    self._cn_target[src] = (dst, c.props[3])
                elif src in self._curves and dst in self._curve_nodes:
                    self._cn_curves.setdefault(dst, {})[c.props[3]] = src
        for mid in self.models:
            self.children.setdefault(self.parent.get(mid, 0), []).append(mid)

        fps = TIME_MODE_FPS.get(_p70_value(gs, "TimeMode", 0))
        if not fps:
            fps = float(_p70_value(gs, "CustomFrameRate", 0.0) or 0.0)
        if fps <= 0:
            fps = 30.0
        up = {0: "X", 1: "Y", 2: "Z"}.get(_p70_value(gs, "UpAxis", 1), "Y")
        start = stop = None
        if self.stacks:
            p = self.stacks[0][2]
            start_t = _p70_value(p, "LocalStart", _p70_value(p, "ReferenceStart"))
            stop_t = _p70_value(p, "LocalStop", _p70_value(p, "ReferenceStop"))
            if start_t is not None:
                start = self.ticks_to_frame(start_t, fps)
            if stop_t is not None:
                stop = self.ticks_to_frame(stop_t, fps)
        if start is None:
            start = self.ticks_to_frame(_p70_value(gs, "TimeSpanStart", 0) or 0, fps)
        if stop is None:
            stop = self.ticks_to_frame(_p70_value(gs, "TimeSpanStop", 0) or 0, fps)
        self.settings = {
            "up_axis": up,
            "unit_cm": float(_p70_value(gs, "UnitScaleFactor", 1.0) or 1.0),
            "fps": fps,
            "start": start,
            "stop": stop,
        }
        # 첫 스택의 첫 레이어만 쓴다 (레이어가 없는 옛 파일은 전부).
        self.active_layer = None
        if self.stacks:
            first_stack = self.stacks[0][0]
            for layer_id, stack_id in self.layers.items():
                if stack_id == first_stack:
                    self.active_layer = layer_id
                    break
        self.n_layers = len(self.layers)

    @staticmethod
    def ticks_to_frame(ticks, fps):
        frame = ticks * fps / KTIME_PER_SECOND
        rounded = round(frame)
        return float(rounded) if abs(frame - rounded) < 1e-6 else frame

    # ---- 모델 ----------------------------------------------------------

    def skeleton_roots(self):
        """자손에 LimbNode 가 있는 최상위 Model -> [(id, 이름, LimbNode 개수)] (파일 순서)."""
        out = []
        for mid in self.children.get(0, []):
            n = sum(1 for d in self.descendants(mid) if self.models[d].kind == "LimbNode")
            if self.models[mid].kind == "LimbNode":
                n += 1
            if n:
                out.append((mid, self.models[mid].short, n))
        return out

    def descendants(self, mid):
        """mid 아래 전부(깊이 우선, 파일 순서). mid 자신은 빼고."""
        out, stack = [], list(reversed(self.children.get(mid, [])))
        while stack:
            cur = stack.pop()
            out.append(cur)
            stack.extend(reversed(self.children.get(cur, [])))
        return out

    def path_from(self, root_id, mid):
        """root 아래 mid 까지의 짧은 이름 목록 (root 제외)."""
        names = []
        cur = mid
        while cur in self.models and cur != root_id:
            names.append(self.models[cur].short)
            cur = self.parent.get(cur, 0)
        return list(reversed(names))

    def rotation_order(self, mid):
        return ROTATION_ORDERS.get(_p70_value(self.models[mid].props, "RotationOrder", 0) or 0, "XYZ")

    def vector(self, mid, prop, default=(0.0, 0.0, 0.0)):
        v = _p70_value(self.models[mid].props, prop)
        if isinstance(v, tuple) and len(v) == 3:
            return tuple(float(x) for x in v)
        return tuple(default)

    def pre_rotation(self, mid):
        return self.vector(mid, "PreRotation")

    def post_rotation(self, mid):
        return self.vector(mid, "PostRotation")

    # ---- 애니 ----------------------------------------------------------

    def _curve_node_for(self, mid, prop):
        for cn, (target, p) in self._cn_target.items():
            if target == mid and p == prop:
                if self.active_layer is None or self._layer_of_cn.get(cn, self.active_layer) == self.active_layer:
                    return cn
        return None

    def build_channel_index(self):
        """(model id, 속성) -> curve node id. 큰 파일에서 channel() 을 여러 번 부르기 전에 한 번."""
        index = {}
        for cn, (target, p) in self._cn_target.items():
            if self.active_layer is not None and self._layer_of_cn.get(cn, self.active_layer) != self.active_layer:
                continue
            index[(target, p)] = cn
        self._channel_index = index
        return index

    def channel(self, mid, prop):
        """{'X': Track, ...} - 커브가 있는 축만. 없으면 {}."""
        index = getattr(self, "_channel_index", None)
        cn = index.get((mid, prop)) if index is not None else self._curve_node_for(mid, prop)
        if cn is None:
            return {}
        out = {}
        fps = self.settings["fps"]
        for key, cid in self._cn_curves.get(cn, {}).items():
            axis = key.split("|")[-1].upper()
            if axis not in ("X", "Y", "Z"):
                continue
            out[axis] = self._track(self._curves[cid], fps)
        return out

    def _track(self, curve, fps):
        times = curve.first("KeyTime").props[0].values()
        values = list(curve.first("KeyValueFloat").props[0].values())
        k = fps / KTIME_PER_SECOND
        frames = []
        for t in times:
            f = t * k
            r = round(f)
            frames.append(float(r) if abs(f - r) < 1e-6 else f)
        flags_node, refs_node = curve.first("KeyAttrFlags"), curve.first("KeyAttrRefCount")
        flags = list(flags_node.props[0].values()) if flags_node is not None else [INTERP_LINEAR]
        refs = list(refs_node.props[0].values()) if refs_node is not None else [len(frames)]

        def kind(flag):
            if flag & INTERP_CUBIC:
                return "cubic"
            if flag & INTERP_CONSTANT:
                return "constant"
            return "linear"

        if len(flags) == 1:
            interp = kind(flags[0])
        else:
            interp = []
            for flag, count in zip(flags, refs):
                interp.extend([kind(flag)] * count)
            interp = (interp + [interp[-1] if interp else "linear"] * len(frames))[:len(frames)]
        return Track(frames, values, interp)

    def static(self, mid, prop, default=(0.0, 0.0, 0.0)):
        """커브가 없을 때의 값 (Properties70)."""
        return self.vector(mid, prop, default)

    def value_at(self, mid, prop, frame, default=(0.0, 0.0, 0.0), channel=None):
        """frame 에서의 (x, y, z) - 커브 있는 축은 커브, 없는 축은 정적 값."""
        base = list(self.static(mid, prop, default))
        tracks = channel if channel is not None else self.channel(mid, prop)
        for i, axis in enumerate(("X", "Y", "Z")):
            if axis in tracks:
                base[i] = tracks[axis].value_at(frame)
        return tuple(base)


def read(path):
    """경로 -> FbxDocument. 바이너리 FBX 만 (ASCII 는 FbxError)."""
    with open(path, "rb") as handle:
        data = handle.read()
    version, top = read_tree(data)
    return FbxDocument(version, top, path=path)
