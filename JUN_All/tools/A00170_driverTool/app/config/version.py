# Driver Tool
# Merge of A00150_remapVal (Remap Value) + A00160_sphericalEye (Spherical Eye)
# into one tabbed PySide tool (pattern follows A00110_animTool).

# 01.27  Seal : lip rigs attached to a NURBS surface (pointOnSurfaceInfo) work in
#        Preview Pairing / Build Seal / Update Rest Pose / Remove Seal. Listing joints
#        now seals at the null (it failed to build before), and the live meeting point
#        is read from what the null really gets, so a Maintain-offset attach no longer jumps.

# 01.28  Seal : double-click a row of the Preview Pairing list to select that pair's
#        upper and lower node in the scene (held by UUID, so renames / duplicate names are fine).

VERSION = "01.28"
LAST_UPDATE = "2026-09-28"
