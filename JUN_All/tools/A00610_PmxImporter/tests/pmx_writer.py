# -*- coding: utf-8 -*-
# A00610_PmxImporter 시험용 - 작은 PMX 를 직접 쓴다 (모델 파일은 저장소에 넣지 않는다: 재배포 금지).
# 규격은 docs/plans/A00610_PmxImporter_plan.md §4. 파서와 독립적으로 바이트를 조립한다.

import struct


class Writer(object):
    def __init__(self, encoding=0, add_uv=0, sizes=(2, 1, 1, 2, 1, 2), version=2.0):
        self.enc = encoding
        self.add_uv = add_uv
        self.vs, self.ts, self.ms, self.bs, self.mos, self.rs = sizes
        self.version = version
        self.buf = bytearray()

    def p(self, fmt, *vals):
        self.buf += struct.pack("<" + fmt, *vals)

    def text(self, s):
        b = s.encode("utf-16-le" if self.enc == 0 else "utf-8")
        self.p("i", len(b))
        self.buf += b

    def idx(self, size, v, unsigned=False):
        fmt = {1: "B" if unsigned else "b", 2: "H" if unsigned else "h", 4: "i"}[size]
        self.p(fmt, v)

    def vi(self, v):
        self.idx(self.vs, v, unsigned=self.vs < 4)

    def ti(self, v):
        self.idx(self.ts, v)

    def mi(self, v):
        self.idx(self.ms, v)

    def bi(self, v):
        self.idx(self.bs, v)

    def moi(self, v):
        self.idx(self.mos, v)

    def ri(self, v):
        self.idx(self.rs, v)


def build(w, vertices, faces, textures, materials, bones, morphs, frames=(), rigids=(), joints=(),
          soft_bodies=None, name="Model", name_e="Model_e"):
    """vertices: dict(pos, normal, uv, add_uvs, type, bones, weights, sdef) ..."""
    w.buf += b"PMX "
    w.p("f", w.version)
    w.p("B", 8)
    w.p("8B", w.enc, w.add_uv, w.vs, w.ts, w.ms, w.bs, w.mos, w.rs)
    w.text(name)
    w.text(name_e)
    w.text(u"comment ✔")
    w.text("comment e")
    w.p("i", len(vertices))
    for v in vertices:
        w.p("3f", *v["pos"])
        w.p("3f", *v.get("normal", (0, 0, -1)))
        w.p("2f", *v.get("uv", (0, 0)))
        for k in range(w.add_uv):
            w.p("4f", *v.get("add_uvs", [(0, 0, 0, 0)] * w.add_uv)[k])
        t = v.get("type", 0)
        w.p("B", t)
        bs = v.get("bones", (0,))
        ws = v.get("weights", (1.0,))
        if t == 0:
            w.bi(bs[0])
        elif t == 1:
            w.bi(bs[0])
            w.bi(bs[1])
            w.p("f", ws[0])
        elif t in (2, 4):
            for b in bs:
                w.bi(b)
            w.p("4f", *ws)
        elif t == 3:
            w.bi(bs[0])
            w.bi(bs[1])
            w.p("f", ws[0])
            w.p("9f", *v.get("sdef", (0.0,) * 9))
        w.p("f", v.get("edge", 1.0))
    w.p("i", len(faces) * 3)
    for f in faces:
        for i in f:
            w.vi(i)
    w.p("i", len(textures))
    for t in textures:
        w.text(t)
    w.p("i", len(materials))
    for m in materials:
        w.text(m["name"])
        w.text(m.get("name_e", ""))
        w.p("4f", *m.get("diffuse", (1, 1, 1, 1)))
        w.p("3f", 0, 0, 0)
        w.p("f", 1)
        w.p("3f", 0.5, 0.5, 0.5)
        w.p("B", m.get("flags", 0x1f))
        w.p("4f", 0, 0, 0, 1)
        w.p("f", 1)
        w.ti(m.get("texture", -1))
        w.ti(m.get("sphere", -1))
        w.p("B", m.get("sphere_mode", 0))
        if "shared_toon" in m:
            w.p("B", 1)
            w.p("B", m["shared_toon"])
        else:
            w.p("B", 0)
            w.ti(m.get("toon", -1))
        w.text(m.get("memo", ""))
        w.p("i", m["faces"] * 3)
    w.p("i", len(bones))
    for b in bones:
        w.text(b["name"])
        w.text(b.get("name_e", ""))
        w.p("3f", *b["pos"])
        w.bi(b.get("parent", -1))
        w.p("i", b.get("layer", 0))
        fl = b.get("flags", 0x1e)
        w.p("H", fl)
        if fl & 0x1:
            w.bi(b.get("tail", -1))
        else:
            w.p("3f", 0, 1, 0)
        if fl & 0x300:
            w.bi(b["append"][0])
            w.p("f", b["append"][1])
        if fl & 0x400:
            w.p("3f", 1, 0, 0)
        if fl & 0x800:
            w.p("3f", 1, 0, 0)
            w.p("3f", 0, 0, 1)
        if fl & 0x2000:
            w.p("i", 7)
        if fl & 0x20:
            ik = b["ik"]
            w.bi(ik["target"])
            w.p("i", 40)
            w.p("f", 0.5)
            w.p("i", len(ik["links"]))
            for link, limited in ik["links"]:
                w.bi(link)
                w.p("B", 1 if limited else 0)
                if limited:
                    w.p("6f", -1, 0, 0, 0, 0, 0)
    w.p("i", len(morphs))
    for m in morphs:
        w.text(m["name"])
        w.text(m.get("name_e", ""))
        w.p("B", m.get("panel", 4))
        t = m["type"]
        w.p("B", t)
        w.p("i", len(m["offsets"]))
        for o in m["offsets"]:
            if t == 1:
                w.vi(o[0])
                w.p("3f", *o[1])
            elif t in (0, 9):
                w.moi(o[0])
                w.p("f", o[1])
            elif t == 2:
                w.bi(o[0])
                w.p("3f", 1, 2, 3)
                w.p("4f", 0, 0, 0, 1)
            elif 3 <= t <= 7:
                w.vi(o[0])
                w.p("4f", 0.1, 0.2, 0, 0)
            elif t == 8:
                w.mi(o[0])
                w.p("B", 0)
                w.p("28f", *([0.5] * 28))
            elif t == 10:
                w.ri(o[0])
                w.p("B", 1)
                w.p("6f", 1, 2, 3, 4, 5, 6)
    w.p("i", len(frames))
    for fr in frames:
        w.text(fr[0])
        w.text("")
        w.p("B", 0)
        w.p("i", len(fr[1]))
        for kind, i in fr[1]:
            w.p("B", kind)
            w.bi(i) if kind == 0 else w.moi(i)
    w.p("i", len(rigids))
    for r in rigids:
        w.text(r)
        w.text("")
        w.bi(0)
        w.p("B", 1)
        w.p("H", 0xFFFE)
        w.p("B", 2)
        w.p("9f", 1, 2, 0, 0, 10, 0, 0.1, 0.2, 0.3)
        w.p("5f", 1, 0.5, 0.5, 0, 0.5)
        w.p("B", 1)
    w.p("i", len(joints))
    for j in joints:
        w.text(j)
        w.text("")
        w.p("B", 0)
        w.ri(0)
        w.ri(0)
        w.p("24f", *([0.0] * 24))
    if soft_bodies is not None:
        w.p("i", soft_bodies)
        w.buf += b"\0" * 16          # 본문은 읽지 않는다
    return bytes(w.buf)
