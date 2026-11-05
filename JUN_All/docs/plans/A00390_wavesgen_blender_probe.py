# A00390_WindTool - Waves Gen 이식 계획서 7-2 의 블렌더 기준 데이터 측정 스크립트 (우리가 쓴 코드, 애드온 코드 아님).
# 애드온(GPL-3.0)을 불러 **실행만** 하고 결과 숫자를 json 으로 남긴다. 사용자 승인 2026-11-05.
#   blender.exe -b --factory-startup --python A00390_wavesgen_blender_probe.py -- <out.json>
#
# 리그: 직선 메시(길이 2, -Z 로 매달림) + 뼈 12 (애드온 Add Bone Chain). 경우마다 뼈 전부의 월드 행렬(head · 축)을 프레임별로 저장.
# 경우: 프리셋 6벌(3 x 옵션 2) + 끝 따라가기 0 인 기준(바람만) + Random / Cross / Stiff / Direction 을 켠 경우.
import sys
import json
import importlib.util
import bpy

ADDON = r"C:\Users\USER\Desktop\JP\0120_blender_plugin\0010_waveGen\__init__.py"
OUT = sys.argv[sys.argv.index("--") + 1]
NB = 12
FRAMES = list(range(1, 61))

spec = importlib.util.spec_from_file_location("waves_gen", ADDON)
wg = importlib.util.module_from_spec(spec)
sys.modules["waves_gen"] = wg
spec.loader.exec_module(wg)
wg.register()
bpy.context.preferences.filepaths.use_scripts_auto_execute = True

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
scene = bpy.context.scene
scene.render.fps = 24
bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.05, depth=2.0, location=(0, 0, -1.0))
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.subdivide(number_cuts=24)
bpy.ops.object.mode_set(mode='OBJECT')
scene.cf_bones = NB
bpy.ops.chainflex.add_bones(direction='NEG_Z')
rig = bpy.context.active_object
names = ["CF_%02d" % i for i in range(NB)]


def rest_info():
    out = {}
    for nm in names + ["CF_Root", "CF_Tip"]:
        b = rig.data.bones[nm]
        m = rig.matrix_world @ b.matrix_local
        out[nm] = {"matrix": [list(r) for r in m], "head": list(rig.matrix_world @ b.head_local),
                   "tail": list(rig.matrix_world @ b.tail_local), "parent": b.parent.name if b.parent else None}
    return out


def sample():
    frames = []
    for f in FRAMES:
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        r = rig.evaluated_get(dg)
        bones = {}
        for nm in names:
            pb = r.pose.bones[nm]
            m = r.matrix_world @ pb.matrix
            bones[nm] = {"matrix": [[round(x, 7) for x in row] for row in m],
                         "rot": [round(x, 7) for x in pb.rotation_euler]}
        frames.append(bones)
    return frames


def set_vals(vals):
    for k, v in vals.items():
        rig[k] = float(v)
    rig.update_tag()


result = {"blender": bpy.app.version_string, "bones": NB, "fps": 24, "frames": FRAMES,
          "rest": rest_info(), "props": list(wg.PROPS), "cases": {}}
base = {k: v[0] for k, v in wg.PROPS.items()}

for key in ("SLOW", "BREEZE", "FAST"):
    for blend in (0.0, 50.0, 100.0):
        set_vals(base)
        bpy.ops.chainflex.wind_preset(preset=key, blend=blend)
        vals = {k: rig[k] for k in wg.PROPS}
        result["cases"]["%s_%d" % (key, int(blend))] = {"values": vals, "frames": sample()}

extra = {
    "wind_only_q0": dict(base, cf_influence=0.0),
    "random_cross_stiff_dir": dict(base, cf_random=0.7, cf_cross=0.6, cf_stiff=1.3, cf_dir=0.9),
    "breeze_q0": None,
}
for name, vals in extra.items():
    if vals is None:
        set_vals(base)
        bpy.ops.chainflex.wind_preset(preset="BREEZE", blend=0.0)
        vals = {k: rig[k] for k in wg.PROPS}
        vals["cf_influence"] = 0.0
    set_vals(vals)
    result["cases"][name] = {"values": {k: rig[k] for k in wg.PROPS}, "frames": sample()}

json.dump(result, open(OUT, "w"))
print("WG_PROBE_OK", OUT, len(result["cases"]))
