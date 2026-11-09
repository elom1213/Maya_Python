# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-09
# A00610_PmxImporter - PMX 2.0 / 2.1 바이너리 파서 (마야 비의존, 순수 파이썬)
#
# 규격 요약은 docs/plans/A00610_PmxImporter_plan.md §4.
# 값은 PMX 원래 좌표(왼손, MMD 단위) 그대로 담는다 - 마야 좌표 변환은 pmx_convert.py 가 한다.
# 파이썬 3.9 문법(마야 2023 호환), numpy 없음.

import struct


class PmxError(Exception):
    """PMX 를 읽을 수 없을 때(형식이 다름 · 파일이 잘림)."""


# ----------------------------------------------------------------------------
# 상수
# ----------------------------------------------------------------------------

WEIGHT_TYPES = ("BDEF1", "BDEF2", "BDEF4", "SDEF", "QDEF")

MORPH_TYPES = ("group", "vertex", "bone", "uv", "uv1", "uv2", "uv3", "uv4",
               "material", "flip", "impulse")

MORPH_PANELS = ("system", "eyebrow", "eye", "mouth", "other")

RIGID_SHAPES = ("sphere", "box", "capsule")

RIGID_MODES = ("static", "dynamic", "dynamic_bone")   # 0 본 추종 · 1 물리 · 2 물리 + 본 위치 맞춤

SPHERE_MODES = ("off", "multiply", "add", "subtexture")

# 본 플래그
BONE_TAIL_IS_BONE = 0x0001
BONE_ROTATABLE = 0x0002
BONE_MOVABLE = 0x0004
BONE_VISIBLE = 0x0008
BONE_OPERABLE = 0x0010
BONE_IK = 0x0020
BONE_APPEND_LOCAL = 0x0080
BONE_APPEND_ROTATE = 0x0100
BONE_APPEND_MOVE = 0x0200
BONE_FIXED_AXIS = 0x0400
BONE_LOCAL_AXIS = 0x0800
BONE_AFTER_PHYSICS = 0x1000
BONE_EXTERNAL_PARENT = 0x2000

# 재질 플래그
MAT_DOUBLE_SIDED = 0x01
MAT_GROUND_SHADOW = 0x02
MAT_SELF_SHADOW_MAP = 0x04
MAT_SELF_SHADOW = 0x08
MAT_EDGE = 0x10
MAT_VERTEX_COLOR = 0x20
MAT_POINT = 0x40
MAT_LINE = 0x80


# ----------------------------------------------------------------------------
# 데이터
# ----------------------------------------------------------------------------

class PmxHeader(object):
    def __init__(self):
        self.version = 2.0
        self.encoding = 0            # 0 UTF-16LE, 1 UTF-8
        self.additional_uvs = 0
        self.vertex_index_size = 4
        self.texture_index_size = 4
        self.material_index_size = 4
        self.bone_index_size = 4
        self.morph_index_size = 4
        self.rigid_index_size = 4


class PmxVertex(object):
    __slots__ = ("position", "normal", "uv", "add_uvs", "weight_type", "bones", "weights",
                 "sdef_c", "sdef_r0", "sdef_r1", "edge_scale")

    def __init__(self):
        self.position = (0.0, 0.0, 0.0)
        self.normal = (0.0, 1.0, 0.0)
        self.uv = (0.0, 0.0)
        self.add_uvs = ()
        self.weight_type = 0
        self.bones = ()              # 본 인덱스 (BDEF1 = 1개, BDEF2/SDEF = 2개, BDEF4/QDEF = 4개)
        self.weights = ()            # 같은 길이. BDEF2/SDEF 는 (w, 1-w) 로 채운다
        self.sdef_c = None
        self.sdef_r0 = None
        self.sdef_r1 = None
        self.edge_scale = 1.0


class PmxMaterial(object):
    def __init__(self):
        self.name = ""
        self.name_e = ""
        self.diffuse = (1.0, 1.0, 1.0, 1.0)
        self.specular = (0.0, 0.0, 0.0)
        self.specular_power = 0.0
        self.ambient = (0.0, 0.0, 0.0)
        self.flags = 0
        self.edge_color = (0.0, 0.0, 0.0, 1.0)
        self.edge_size = 1.0
        self.texture = -1
        self.sphere = -1
        self.sphere_mode = 0
        self.shared_toon = False
        self.toon = -1               # shared_toon 이면 0~9 (toon01~10.bmp), 아니면 텍스처 인덱스
        self.memo = ""
        self.index_count = 0         # 이 재질이 차지하는 면 인덱스 수 (/3 = 삼각형 수)


class PmxIKLink(object):
    def __init__(self, bone, limit_min=None, limit_max=None):
        self.bone = bone
        self.limit_min = limit_min   # 라디안 (x, y, z), 제한 없으면 None
        self.limit_max = limit_max


class PmxIK(object):
    def __init__(self):
        self.target = -1
        self.loop = 0
        self.limit_angle = 0.0       # 라디안
        self.links = []


class PmxBone(object):
    def __init__(self):
        self.name = ""
        self.name_e = ""
        self.position = (0.0, 0.0, 0.0)
        self.parent = -1
        self.layer = 0
        self.flags = 0
        self.tail_bone = -1
        self.tail_offset = None
        self.append_parent = -1
        self.append_ratio = 0.0
        self.fixed_axis = None
        self.local_x = None
        self.local_z = None
        self.external_parent_key = None
        self.ik = None


class PmxMorph(object):
    def __init__(self):
        self.name = ""
        self.name_e = ""
        self.panel = 4
        self.type = 1
        self.offsets = []
        # 타입별 원소:
        #   group / flip : (morph_index, weight)
        #   vertex       : (vertex_index, (dx, dy, dz))
        #   bone         : (bone_index, (mx, my, mz), (qx, qy, qz, qw))
        #   uv / uv1~4   : (vertex_index, (a, b, c, d))
        #   material     : (material_index, op, values[28])
        #   impulse      : (rigid_index, local, (vx, vy, vz), (tx, ty, tz))

    @property
    def type_name(self):
        return MORPH_TYPES[self.type] if 0 <= self.type < len(MORPH_TYPES) else "unknown"


class PmxDisplayFrame(object):
    def __init__(self):
        self.name = ""
        self.name_e = ""
        self.special = False
        self.items = []              # [(0 본 | 1 모프, index), ...]


class PmxRigid(object):
    def __init__(self):
        self.name = ""
        self.name_e = ""
        self.bone = -1
        self.group = 0
        self.no_collision = 0        # 16 비트 마스크 (비트가 1 = 그 그룹과 충돌 안 함)
        self.shape = 0
        self.size = (0.0, 0.0, 0.0)
        self.position = (0.0, 0.0, 0.0)
        self.rotation = (0.0, 0.0, 0.0)   # 라디안
        self.mass = 0.0
        self.linear_damping = 0.0
        self.angular_damping = 0.0
        self.restitution = 0.0
        self.friction = 0.0
        self.mode = 0


class PmxJoint(object):
    def __init__(self):
        self.name = ""
        self.name_e = ""
        self.type = 0                # 0 = 스프링 6DOF (2.0 은 이것뿐)
        self.rigid_a = -1
        self.rigid_b = -1
        self.position = (0.0, 0.0, 0.0)
        self.rotation = (0.0, 0.0, 0.0)
        self.move_min = (0.0, 0.0, 0.0)
        self.move_max = (0.0, 0.0, 0.0)
        self.rotate_min = (0.0, 0.0, 0.0)
        self.rotate_max = (0.0, 0.0, 0.0)
        self.spring_move = (0.0, 0.0, 0.0)
        self.spring_rotate = (0.0, 0.0, 0.0)


class PmxModel(object):
    def __init__(self):
        self.path = ""
        self.header = PmxHeader()
        self.name = ""
        self.name_e = ""
        self.comment = ""
        self.comment_e = ""
        self.vertices = []
        self.faces = []              # [(a, b, c), ...] PMX 원래 순서
        self.textures = []           # PMX 안의 경로 문자열 그대로 (예: "tex\\颜.png")
        self.materials = []
        self.bones = []
        self.morphs = []
        self.display_frames = []
        self.rigids = []
        self.joints = []
        self.soft_body_count = 0     # 2.1 소프트바디 - 개수만 (본문은 읽지 않는다)
        self.trailing_bytes = 0      # 읽고 남은 바이트 (0 이 정상)

    # -- 요약 ---------------------------------------------------------------
    def weight_type_counts(self):
        counts = dict((name, 0) for name in WEIGHT_TYPES)
        for v in self.vertices:
            counts[WEIGHT_TYPES[v.weight_type]] += 1
        return counts

    def morph_type_counts(self):
        counts = {}
        for m in self.morphs:
            counts[m.type_name] = counts.get(m.type_name, 0) + 1
        return counts

    def material_face_ranges(self):
        """재질마다 (시작 삼각형, 삼각형 수). PMX 는 재질 순서대로 면을 연속으로 차지한다."""
        out = []
        start = 0
        for m in self.materials:
            count = m.index_count // 3
            out.append((start, count))
            start += count
        return out


# ----------------------------------------------------------------------------
# 읽기
# ----------------------------------------------------------------------------

class _Stream(object):
    def __init__(self, data):
        self.data = data
        self.pos = 0
        self._structs = {}

    def _st(self, fmt):
        st = self._structs.get(fmt)
        if st is None:
            st = self._structs[fmt] = struct.Struct("<" + fmt)
        return st

    def read(self, fmt):
        st = self._st(fmt)
        try:
            values = st.unpack_from(self.data, self.pos)
        except struct.error:
            raise PmxError("Unexpected end of file at byte {0}.".format(self.pos))
        self.pos += st.size
        return values

    def one(self, fmt):
        return self.read(fmt)[0]

    def raw(self, n):
        if self.pos + n > len(self.data):
            raise PmxError("Unexpected end of file at byte {0}.".format(self.pos))
        out = self.data[self.pos:self.pos + n]
        self.pos += n
        return out

    def remaining(self):
        return len(self.data) - self.pos


def _index_fmt(size, unsigned=False):
    if size == 1:
        return "B" if unsigned else "b"
    if size == 2:
        return "H" if unsigned else "h"
    if size == 4:
        return "i"
    raise PmxError("Invalid index size {0}.".format(size))


def read_pmx(path, read_physics=True):
    """PMX 파일을 읽어 PmxModel 을 돌려준다.

    read_physics=False 면 강체 · 조인트 본문을 건너뛰지 않고 그냥 멈춘다(빠른 미리보기용).
    """
    with open(path, "rb") as f:
        data = f.read()
    model = parse_pmx(data, read_physics=read_physics)
    model.path = path
    return model


def parse_pmx(data, read_physics=True):
    s = _Stream(data)
    if s.raw(4) != b"PMX ":
        raise PmxError("Not a PMX file (missing 'PMX ' signature).")
    m = PmxModel()
    h = m.header
    h.version = round(s.one("f"), 3)
    if h.version < 2.0 or h.version > 2.1 + 1e-6:
        raise PmxError("Unsupported PMX version {0}.".format(h.version))
    n = s.one("B")
    g = list(s.read("{0}B".format(n)))
    if n < 8:
        raise PmxError("Header has {0} globals (expected 8).".format(n))
    (h.encoding, h.additional_uvs, h.vertex_index_size, h.texture_index_size,
     h.material_index_size, h.bone_index_size, h.morph_index_size, h.rigid_index_size) = g[:8]
    codec = "utf-16-le" if h.encoding == 0 else "utf-8"

    def text():
        length = s.one("i")
        if length <= 0:
            return ""
        return s.raw(length).decode(codec, "replace")

    vi = _index_fmt(h.vertex_index_size, unsigned=True)
    if h.vertex_index_size == 4:
        vi = "i"
    ti = _index_fmt(h.texture_index_size)
    mi = _index_fmt(h.material_index_size)
    bi = _index_fmt(h.bone_index_size)
    moi = _index_fmt(h.morph_index_size)
    ri = _index_fmt(h.rigid_index_size)

    m.name = text()
    m.name_e = text()
    m.comment = text()
    m.comment_e = text()

    # -- 정점 -----------------------------------------------------------------
    add = h.additional_uvs
    head_fmt = "8f" + ("4f" * add) + "B"
    for _ in range(s.one("i")):
        vals = s.read(head_fmt)
        v = PmxVertex()
        v.position = vals[0:3]
        v.normal = vals[3:6]
        v.uv = vals[6:8]
        v.add_uvs = tuple(tuple(vals[8 + 4 * k:12 + 4 * k]) for k in range(add))
        t = vals[-1]
        v.weight_type = t
        if t == 0:
            v.bones = (s.one(bi),)
            v.weights = (1.0,)
        elif t == 1:
            b0, b1, w = s.read(bi + bi + "f")
            v.bones = (b0, b1)
            v.weights = (w, 1.0 - w)
        elif t == 2 or t == 4:
            vals = s.read(bi * 4 + "4f")
            v.bones = vals[0:4]
            v.weights = vals[4:8]
        elif t == 3:
            vals = s.read(bi + bi + "f9f")
            v.bones = vals[0:2]
            v.weights = (vals[2], 1.0 - vals[2])
            v.sdef_c = vals[3:6]
            v.sdef_r0 = vals[6:9]
            v.sdef_r1 = vals[9:12]
        else:
            raise PmxError("Unknown weight type {0} at vertex {1}.".format(t, len(m.vertices)))
        v.edge_scale = s.one("f")
        m.vertices.append(v)

    # -- 면 -------------------------------------------------------------------
    count = s.one("i")
    if count % 3:
        raise PmxError("Face index count {0} is not a multiple of 3.".format(count))
    idx = s.read("{0}{1}".format(count, vi))
    m.faces = [tuple(idx[i:i + 3]) for i in range(0, count, 3)]

    # -- 텍스처 ---------------------------------------------------------------
    m.textures = [text() for _ in range(s.one("i"))]

    # -- 재질 -----------------------------------------------------------------
    for _ in range(s.one("i")):
        mat = PmxMaterial()
        mat.name = text()
        mat.name_e = text()
        vals = s.read("4f3ff3fB4ff")
        mat.diffuse = vals[0:4]
        mat.specular = vals[4:7]
        mat.specular_power = vals[7]
        mat.ambient = vals[8:11]
        mat.flags = vals[11]
        mat.edge_color = vals[12:16]
        mat.edge_size = vals[16]
        mat.texture, mat.sphere, mat.sphere_mode, shared = s.read(ti + ti + "BB")
        mat.shared_toon = bool(shared)
        mat.toon = s.one("B") if shared else s.one(ti)
        mat.memo = text()
        mat.index_count = s.one("i")
        m.materials.append(mat)

    # -- 본 -------------------------------------------------------------------
    for _ in range(s.one("i")):
        b = PmxBone()
        b.name = text()
        b.name_e = text()
        vals = s.read("3f" + bi + "iH")
        b.position = vals[0:3]
        b.parent, b.layer, b.flags = vals[3], vals[4], vals[5]
        fl = b.flags
        if fl & BONE_TAIL_IS_BONE:
            b.tail_bone = s.one(bi)
        else:
            b.tail_offset = s.read("3f")
        if fl & (BONE_APPEND_ROTATE | BONE_APPEND_MOVE):
            b.append_parent, b.append_ratio = s.read(bi + "f")
        if fl & BONE_FIXED_AXIS:
            b.fixed_axis = s.read("3f")
        if fl & BONE_LOCAL_AXIS:
            b.local_x = s.read("3f")
            b.local_z = s.read("3f")
        if fl & BONE_EXTERNAL_PARENT:
            b.external_parent_key = s.one("i")
        if fl & BONE_IK:
            ik = PmxIK()
            ik.target, ik.loop, ik.limit_angle, links = s.read(bi + "ifi")
            for _ in range(links):
                bone, has_limit = s.read(bi + "B")
                if has_limit:
                    lim = s.read("6f")
                    ik.links.append(PmxIKLink(bone, lim[0:3], lim[3:6]))
                else:
                    ik.links.append(PmxIKLink(bone))
            b.ik = ik
        m.bones.append(b)

    # -- 모프 -----------------------------------------------------------------
    for _ in range(s.one("i")):
        mo = PmxMorph()
        mo.name = text()
        mo.name_e = text()
        mo.panel, mo.type, n_off = s.read("BBi")
        t = mo.type
        offs = mo.offsets
        if t == 1:
            vals = s.read((vi + "3f") * n_off)
            for k in range(n_off):
                offs.append((vals[4 * k], vals[4 * k + 1:4 * k + 4]))
        elif t in (0, 9):
            for _ in range(n_off):
                offs.append(s.read(moi + "f"))
        elif t == 2:
            for _ in range(n_off):
                vals = s.read(bi + "3f4f")
                offs.append((vals[0], vals[1:4], vals[4:8]))
        elif 3 <= t <= 7:
            vals = s.read((vi + "4f") * n_off)
            for k in range(n_off):
                offs.append((vals[5 * k], vals[5 * k + 1:5 * k + 5]))
        elif t == 8:
            for _ in range(n_off):
                vals = s.read(mi + "B28f")
                offs.append((vals[0], vals[1], vals[2:]))
        elif t == 10:
            for _ in range(n_off):
                vals = s.read(ri + "B3f3f")
                offs.append((vals[0], vals[1], vals[2:5], vals[5:8]))
        else:
            raise PmxError("Unknown morph type {0} ('{1}').".format(t, mo.name))
        m.morphs.append(mo)

    # -- 표시 프레임 ------------------------------------------------------------
    for _ in range(s.one("i")):
        fr = PmxDisplayFrame()
        fr.name = text()
        fr.name_e = text()
        fr.special = bool(s.one("B"))
        for _ in range(s.one("i")):
            kind = s.one("B")
            fr.items.append((kind, s.one(bi if kind == 0 else moi)))
        m.display_frames.append(fr)

    if not read_physics:
        m.trailing_bytes = s.remaining()
        return m

    # -- 강체 -----------------------------------------------------------------
    for _ in range(s.one("i")):
        r = PmxRigid()
        r.name = text()
        r.name_e = text()
        vals = s.read(bi + "BHB3f3f3f5fB")
        r.bone, r.group, r.no_collision, r.shape = vals[0:4]
        r.size = vals[4:7]
        r.position = vals[7:10]
        r.rotation = vals[10:13]
        r.mass, r.linear_damping, r.angular_damping, r.restitution, r.friction = vals[13:18]
        r.mode = vals[18]
        m.rigids.append(r)

    # -- 조인트 ---------------------------------------------------------------
    for _ in range(s.one("i")):
        j = PmxJoint()
        j.name = text()
        j.name_e = text()
        vals = s.read("B" + ri + ri + "24f")
        j.type, j.rigid_a, j.rigid_b = vals[0:3]
        f = vals[3:]
        j.position, j.rotation = f[0:3], f[3:6]
        j.move_min, j.move_max = f[6:9], f[9:12]
        j.rotate_min, j.rotate_max = f[12:15], f[15:18]
        j.spring_move, j.spring_rotate = f[18:21], f[21:24]
        m.joints.append(j)

    # -- 소프트바디 (2.1) - 개수만 ------------------------------------------------
    if h.version > 2.0 + 1e-6 and s.remaining() >= 4:
        m.soft_body_count = s.one("i")
    m.trailing_bytes = s.remaining()
    return m
