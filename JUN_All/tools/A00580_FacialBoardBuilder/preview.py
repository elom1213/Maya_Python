# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00580_FacialBoardBuilder - 보드 미리보기 png (시스템 python + PIL, maya 비의존)
#
#   python preview.py [spec.json] <out.png>
#
# 명세만으로 보드를 그린다 - 자리 · 이름을 빌드 전에 확인하는 용도 (M1). 색 · 트랙 · 패드 · 라벨은 Maya 와 같은 규칙.

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.abspath(os.path.join(HERE, "..", "..")) not in sys.path:
    sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))

from PIL import Image, ImageDraw, ImageFont

from tools.A00580_FacialBoardBuilder import board_spec as bsx

PX = 44            # 1 cm -> px
BG = (38, 38, 42)
FRAME = (120, 120, 125)
TEXT = (210, 210, 215)


def _rgb(c):
    return tuple(int(round(v * 255)) for v in c)


def render(spec, out_path):
    board = spec["board"]
    fr = board["frame"]
    unit = float(board["unit"])
    margin = 1.2
    w = int((fr[2] - fr[0] + 2 * margin) * PX)
    h = int((fr[3] - fr[1] + 2 * margin) * PX)
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 13)
        font_s = ImageFont.truetype("arial.ttf", 11)
        font_b = ImageFont.truetype("arialbd.ttf", 15)
    except OSError:
        font = font_s = font_b = ImageFont.load_default()

    def P(x, y):
        return ((x - fr[0] + margin) * PX, (fr[3] - y + margin) * PX)

    d.rectangle([P(fr[0], fr[3]), P(fr[2], fr[1])], outline=FRAME, width=2)
    for text, pos in (board.get("region_labels") or {}).items():
        tw = d.textlength(text, font=font_b)
        x, y = P(pos[0], pos[1])
        d.text((x - tw / 2, y - 8), text, fill=FRAME, font=font_b)

    rad = float(board["ctl_radius"]) * PX
    m = float(board.get("pad_margin", 0.3))
    for ctl in bsx.expand_controls(spec):
        cx, cy = ctl["pos"]
        lim = ctl.get("limits") or {}
        tx, ty = lim.get("tx", [0, 0]), lim.get("ty", [0, 0])
        col = _rgb(spec["colors"][ctl.get("color", "C")])
        kind = ctl["type"]
        if kind == "pad":
            x0, y0 = P(cx + (tx[0] - m) * unit, cy + (ty[1] + m) * unit)
            x1, y1 = P(cx + (tx[1] + m) * unit, cy + (ty[0] - m) * unit)
            d.rectangle([x0, y0, x1, y1], outline=FRAME, width=1)
            d.line([P(cx + (tx[0] - m) * unit, cy), P(cx + (tx[1] + m) * unit, cy)], fill=FRAME)
            d.line([P(cx, cy + (ty[0] - m) * unit), P(cx, cy + (ty[1] + m) * unit)], fill=FRAME)
            bottom = cy + (ty[0] - m) * unit
        elif kind == "slider_x":
            d.line([P(cx + tx[0] * unit, cy), P(cx + tx[1] * unit, cy)], fill=FRAME, width=2)
            for v in set([tx[0], 0, tx[1]]):
                d.line([P(cx + v * unit, cy - 0.25 * unit), P(cx + v * unit, cy + 0.25 * unit)], fill=FRAME)
            bottom = cy - m * unit
        else:
            d.line([P(cx, cy + ty[0] * unit), P(cx, cy + ty[1] * unit)], fill=FRAME, width=2)
            for v in set([ty[0], 0, ty[1]]):
                d.line([P(cx - 0.25 * unit, cy + v * unit), P(cx + 0.25 * unit, cy + v * unit)], fill=FRAME)
            bottom = cy + (min(ty[0], 0) - m) * unit
        x, y = P(cx, cy)
        d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=col, outline=(20, 20, 20))
        if board.get("labels", True) and ctl.get("label"):
            tw = d.textlength(ctl["label"], font=font_s)
            lx, ly = P(cx, bottom - 0.7 * unit)
            d.text((lx - tw / 2, ly - 6), ctl["label"], fill=TEXT, font=font_s)
        # 컨트롤 이름 (작게, 위쪽)
        nm = ctl["name"].replace("CTRL_", "")
        tw = d.textlength(nm, font=font_s)
        top = cy + (max(ty[1], 0) + (m if kind == "pad" else 0)) * unit + 0.25
        nx, ny = P(cx, top)
        d.text((nx - tw / 2, ny - 14), nm, fill=(150, 150, 155), font=font_s)

    legend = [("L (character left)", "L"), ("R", "R"), ("C", "C"), ("not connected", "unused")]
    lx, ly = 10, h - 22
    for text, key in legend:
        d.ellipse([lx, ly, lx + 12, ly + 12], fill=_rgb(spec["colors"][key]))
        d.text((lx + 16, ly - 1), text, fill=TEXT, font=font_s)
        lx += 20 + int(d.textlength(text, font=font_s)) + 14
    d.text((10, 6), "ARKit 52 face board v{0} - {1} controls, viewer side (right = character Left)".format(
        spec["version"], len(bsx.expand_controls(spec))), fill=TEXT, font=font)
    img.save(out_path)
    return out_path


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        print("usage: python preview.py [spec.json] <out.png>")
        return 2
    spec = bsx.load_spec(args[0] if len(args) > 1 else None)
    print("written", render(spec, args[-1]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
