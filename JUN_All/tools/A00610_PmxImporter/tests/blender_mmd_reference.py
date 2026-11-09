# -*- coding: utf-8 -*-
# A00610_PmxImporter 시험용 - Blender + mmd_tools(CATS zip 안) 로 PMX 를 포즈해 정점 위치를 정답으로 뽑는다.
#   blender.exe -b --factory-startup --python blender_mmd_reference.py -- <mmd_tools 를 담은 폴더> <pmx> <scenarios.json> <out.json>
#
# 좌표: 마야(x, y, z) cm  <->  블렌더(x, -z, y) m  (x 축 +90° 회전 = 고유 회전이라 회전축을 그대로 옮긴다).
# 시나리오(JSON 목록): {"name", "ik": bool, "ops": [["mmdrot", 본 일본어 이름, [축 x, y, z (PMX 좌표)], 각도(도)],
#                                                   ["rotate", 본 이름, [축 (마야 월드)], 각도],
#                                                   ["move", 본 이름, [dx, dy, dz] (마야 cm)]]}
# mmdrot = MMD 로컬 회전(VMD 키와 같은 뜻) - 부여가 걸린 본에도 뜻이 하나다. rotate(월드)는 pose_bone.matrix 대입이라
# 부여 컨스트레인트가 있는 본에 쓰면 부여가 두 번 들어간다(블렌더 규약) - 부여 본에는 mmdrot 을 쓸 것.
# ops 는 순서대로(부모 먼저) 적용 - 본 머리를 중심으로 지금 포즈에 월드 회전을 더한다.
# 출력: {이름: [[x, y, z] (마야 cm), ...]} - 정점 순서 = PMX (clean_model / remove_doubles 끔).
import json
import math
import sys

import bpy
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:]
ext_dir, pmx_path, scen_path, out_path = argv[:4]
sys.path.insert(0, ext_dir)
import mmd_tools_local  # noqa: E402
try:
    mmd_tools_local.register()
except Exception:
    pass
from mmd_tools_local.core.pmx import importer  # noqa: E402

M2B = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))       # 마야 -> 블렌더 방향


def to_b(v):
    return M2B @ Vector(v)


bpy.ops.wm.read_factory_settings(use_empty=True)
importer.PMXImporter().execute(filepath=pmx_path, scale=0.08, types={'MESH', 'ARMATURE', 'MORPHS'},
                               clean_model=False, remove_doubles=False, rename_LR_bones=False, use_mipmap=False,
                               sph_blend_factor=1.0, spa_blend_factor=1.0)
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
mesh = [o for o in bpy.data.objects if o.type == 'MESH'][0]
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')
by_name = dict((pb.name, pb) for pb in arm.pose.bones)
arm_inv = arm.matrix_world.inverted()


def reset():
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()


def set_ik(on):
    """IK 끄기 = IK 컨스트레인트 + mmd_tools 가 IK 링크에 거는 회전 제한(LIMIT_ROTATION)까지.
    회전 제한만 남기면 무릎(제한 X -180 ~ -0.5°)이 레스트에서도 꺾여 다리 D 본 체인이 어긋난다(실측)."""
    for pb in arm.pose.bones:
        for c in pb.constraints:
            if c.type in ('IK', 'LIMIT_ROTATION'):
                c.mute = not on


def vertices():
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(dg)
    mw = ev.matrix_world
    out = []
    for v in ev.data.vertices:
        p = mw @ v.co
        out.append([p.x * 100.0, p.z * 100.0, -p.y * 100.0])
    return out


scenarios = json.load(open(scen_path, encoding="utf-8"))
result = {"_info": {"vertices": len(mesh.data.vertices), "armature_world": [list(r) for r in arm.matrix_world]}}
for sc in scenarios:
    reset()
    set_ik(bool(sc.get("ik")))
    bpy.context.view_layer.update()
    for op in sc["ops"]:
        pb = by_name[op[1]]
        if op[0] == "mmdrot":
            # MMD 로컬 회전(VMD 모션과 같은 규약, PMX 좌표 축 · 도) -> mmd_tools VMD 임포터와 같은 변환으로 basis 에
            from mmd_tools_local.core.vmd.importer import BoneConverter
            ax = Vector(op[2]).normalized()
            h = math.radians(op[3]) * 0.5
            q = (ax.x * math.sin(h), ax.y * math.sin(h), ax.z * math.sin(h), math.cos(h))
            pb.rotation_mode = 'QUATERNION'
            pb.rotation_quaternion = BoneConverter(pb, 0.08).convert_rotation(q)
        elif op[0] == "rotate":
            axis = to_b(op[2]).normalized()
            rot = (arm_inv.to_3x3() @ Matrix.Rotation(math.radians(op[3]), 3, axis) @ arm.matrix_world.to_3x3()).to_4x4()
            head = pb.head.copy()                          # 아마추어 공간(지금 포즈)
            pb.matrix = Matrix.Translation(head) @ rot @ Matrix.Translation(-head) @ pb.matrix
        elif op[0] == "move":
            d = arm_inv.to_3x3() @ (to_b(op[2]) * 0.01)
            m = pb.matrix.copy()
            m.translation = m.translation + d
            pb.matrix = m
        bpy.context.view_layer.update()
    result[sc["name"]] = vertices()
json.dump(result, open(out_path, "w", encoding="utf-8"))
