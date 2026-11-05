# A00390_WindTool - Waves Gen 이식 계획서 7-2 의 블렌더 기준 데이터 측정 스크립트 (우리가 쓴 코드, 애드온 코드 아님).
# 애드온(GPL-3.0)을 불러 **실행만** 하고 결과 숫자를 json 으로 남긴다. 아직 실행 승인 전(2026-11-05).
#   blender.exe -b --factory-startup --python A00390_wavesgen_blender_probe.py -- <out.json>
# Blender headless probe: load Waves Gen, rig a straight mesh, apply each preset, sample bone angles.
import sys, json, math, importlib.util
import bpy
from mathutils import Vector

ADDON = r"C:\Users\USER\Desktop\JP\0120_blender_plugin\0010_waveGen\__init__.py"
OUT = sys.argv[sys.argv.index("--") + 1]

spec = importlib.util.spec_from_file_location("waves_gen", ADDON)
wg = importlib.util.module_from_spec(spec)
sys.modules["waves_gen"] = wg
spec.loader.exec_module(wg)
wg.register()

# drivers need auto-run python
bpy.context.preferences.filepaths.use_scripts_auto_execute = True

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
scene = bpy.context.scene
scene.render.fps = 24
bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.05, depth=2.0, location=(0, 0, -1.0))
mesh = bpy.context.active_object
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.subdivide(number_cuts=24)
bpy.ops.object.mode_set(mode='OBJECT')
scene.cf_bones = 12
bpy.ops.chainflex.add_bones(direction='NEG_Z')
rig = bpy.context.active_object

result = {"blender": bpy.app.version_string, "bones": 12, "presets": {}}
for key in ("SLOW", "BREEZE", "FAST"):
    for blend in (0.0, 100.0):
        bpy.ops.chainflex.wind_preset(preset=key, blend=blend)
        frames = []
        for f in range(1, 49):
            scene.frame_set(f)
            dg = bpy.context.evaluated_depsgraph_get()
            r = rig.evaluated_get(dg)
            tip = r.pose.bones["CF_11"]
            head = (r.matrix_world @ tip.tail)
            frames.append([round(head.x, 5), round(head.y, 5), round(head.z, 5)])
        result["presets"]["%s_%d" % (key, int(blend))] = {
            "values": {k: rig[k] for k in wg.PROPS},
            "tip_world": frames,
        }
json.dump(result, open(OUT, "w"), indent=1)
print("WG_PROBE_OK", OUT)
