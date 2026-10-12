# Driver Tool
# Merge of A00150_remapVal (Remap Value) + A00160_sphericalEye (Spherical Eye)
# into one tabbed PySide tool (pattern follows A00110_animTool).

# 01.27  Seal : lip rigs attached to a NURBS surface (pointOnSurfaceInfo) work in
#        Preview Pairing / Build Seal / Update Rest Pose / Remove Seal. Listing joints
#        now seals at the null (it failed to build before), and the live meeting point
#        is read from what the null really gets, so a Maintain-offset attach no longer jumps.

# 01.28  Seal : double-click a row of the Preview Pairing list to select that pair's
#        upper and lower node in the scene (held by UUID, so renames / duplicate names are fine).

# 01.29  Seal : Mode combo - Attached (v01.28 behaviour, unchanged) / Free (any transform).
#        Free mode seals the listed transforms as they are: u = position along the Corner
#        Axis in the Reference space between the outermost listed nodes; constraint / keyed
#        inputs are kept per axis; nodes with no input get a 'sealBase' attribute that Remove
#        writes back. Joints sealed directly keep their jointOrient out of the rest rotation.

# 01.30  AttachCrv : joints attached with Orient now rotate exactly like a locator at the
#        same spot when the curve / surface deforms, even with a non-zero jointOrient.
#        rotate = rot(frame x parentInverse) x JO^-1 (second multMatrix/decomposeMatrix,
#        JO^-1 from a negated zyx composeMatrix so it follows later jointOrient edits);
#        Maintain offset's local0 includes JO so the joint stays in place at build time.

VERSION = "01.30"
LAST_UPDATE = "2026-10-12"
