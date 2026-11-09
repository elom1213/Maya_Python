# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-09
# A00610_PmxImporter - PMX -> 마야 변환 규칙 + 이름 규칙 (마야 비의존, 순수 함수)
#
# 좌표 · UV · 감기 규칙은 기준 mb(CATS -> FBX) 와 수치 대조로 확정했다 (계획서 §2-4, §5):
#   위치  (x, y, -z) * scale      UV (u, 1 - v)      삼각형 (a, b, c) -> (c, b, a)
# 이름은 PMX 고유 이름(일본어 이름)을 쓰고, 마야 이름에 못 쓰는 글자는 FBX 와 같은
# FBXASC### (UTF-8 바이트 10진수) 로 바꾼다 (사용자 결정 2026-11-09). decode_name 으로 원래대로 돌아온다.

import re

DEFAULT_SCALE = 8.0          # MMD 1 단위 = 8 cm (CATS 의 0.08 m 와 같음)

_VALID_CHAR = re.compile(r"[A-Za-z0-9_]")
_FBXASC = re.compile(r"FBXASC(\d{3})")


# ----------------------------------------------------------------------------
# 좌표
# ----------------------------------------------------------------------------

def to_maya_point(p, scale=DEFAULT_SCALE):
    return (p[0] * scale, p[1] * scale, -p[2] * scale)


def to_maya_vector(v):
    """방향 벡터(노멀 · 축). 길이는 바꾸지 않는다."""
    return (v[0], v[1], -v[2])


def to_maya_uv(uv):
    return (uv[0], 1.0 - uv[1])


def to_maya_triangle(tri):
    a, b, c = tri
    return (c, b, a)


def to_maya_euler(r):
    """PMX 오일러(라디안) -> 마야 좌표의 오일러(라디안). z 반전 거울이라 x · y 각이 뒤집힌다.
    (강체 · 조인트 보존용. 회전 순서 확정은 2차 - 계획서 §5)"""
    return (-r[0], -r[1], r[2])


def normalized(v):
    length = (v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) ** 0.5
    if length < 1e-12:
        return (0.0, 1.0, 0.0)
    return (v[0] / length, v[1] / length, v[2] / length)


# ----------------------------------------------------------------------------
# 이름 (FBXASC)
# ----------------------------------------------------------------------------

def encode_name(text):
    """마야 이름으로 쓸 수 있게 바꾼다 - FBX 와 같은 FBXASC### 규칙.

    [A-Za-z0-9_] 는 그대로, 나머지 글자는 UTF-8 바이트마다 FBXASC + 3자리 10진수.
    첫 글자가 숫자면 그 숫자도 바꾼다 (마야 이름은 숫자로 시작할 수 없다. FBX: "1" -> "FBXASC049").
    """
    out = []
    for i, ch in enumerate(text or ""):
        if _VALID_CHAR.match(ch) and not (i == 0 and ch.isdigit()):
            out.append(ch)
        else:
            out.extend("FBXASC{0:03d}".format(b) for b in ch.encode("utf-8"))
    return "".join(out)


def decode_name(name):
    """encode_name 의 역. FBXASC### 를 바이트로 모아 UTF-8 로 되돌린다."""
    data = bytearray()
    pos = 0
    for m in _FBXASC.finditer(name):
        data += name[pos:m.start()].encode("utf-8")
        data.append(int(m.group(1)) & 0xFF)
        pos = m.end()
    data += name[pos:].encode("utf-8")
    return data.decode("utf-8", "replace")


class NameBook(object):
    """한 번의 임포트에서 만드는 노드 이름이 서로 겹치지 않게 나눠 준다.

    taken(name) 콜백으로 씬에 이미 있는 이름도 피한다(마야에서는 cmds.objExists).
    겹치면 _1, _2 ... 를 붙인다.
    """

    def __init__(self, taken=None, prefix=""):
        self._used = set()
        self._taken = taken
        self.prefix = prefix or ""

    def _free(self, name):
        if name.lower() in self._used:
            return False
        if self._taken is not None and self._taken(name):
            return False
        return True

    def unique(self, base):
        base = self.prefix + base
        name = base
        n = 1
        while not self._free(name):
            name = "{0}_{1}".format(base, n)
            n += 1
        self._used.add(name.lower())
        return name

    def item_name(self, name, name_e, fallback, suffix=""):
        """PMX 이름 -> 노드 이름. 일본어 이름 우선, 비었으면 영어 이름, 그것도 비었으면 fallback."""
        src = name if (name or "").strip() else (name_e or "")
        base = encode_name(src.strip()) if src.strip() else fallback
        return self.unique(base + suffix)


# ----------------------------------------------------------------------------
# 웨이트
# ----------------------------------------------------------------------------

def vertex_weights(vertex, bone_count):
    """PmxVertex -> 정리한 {본 인덱스: 웨이트}, 정규화 여부.

    같은 본은 더하고, -1 · 범위 밖 · 0 이하 웨이트는 버리고, 합이 1 이 아니면 정규화한다.
    """
    acc = {}
    for b, w in zip(vertex.bones, vertex.weights):
        if b is None or b < 0 or b >= bone_count or w <= 0.0:
            continue
        acc[b] = acc.get(b, 0.0) + w
    total = sum(acc.values())
    if total <= 0.0:
        return {}, False
    if abs(total - 1.0) > 1e-5:
        return dict((b, w / total) for b, w in acc.items()), True
    return acc, False


# ----------------------------------------------------------------------------
# 본 계층
# ----------------------------------------------------------------------------

def bone_creation_order(bones):
    """부모가 먼저 오도록 본 인덱스를 정렬한다(PMX 는 부모가 뒤에 올 수 있다).

    순환 · 잘못된 부모 인덱스는 루트로 본다. 돌려주는 값: (순서, 고친 부모 목록).
    """
    n = len(bones)
    parents = []
    for i, b in enumerate(bones):
        p = b.parent
        parents.append(p if (0 <= p < n and p != i) else -1)
    # 순환 끊기
    for i in range(n):
        seen = set([i])
        p = parents[i]
        while p >= 0:
            if p in seen:
                parents[i] = -1
                break
            seen.add(p)
            p = parents[p]
    order = []
    done = [False] * n

    def visit(i):
        stack = []
        while i >= 0 and not done[i]:
            stack.append(i)
            i = parents[i]
        for k in reversed(stack):
            if not done[k]:
                done[k] = True
                order.append(k)

    for i in range(n):
        visit(i)
    return order, parents
