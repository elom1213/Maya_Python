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

# 01.31  AttachCrv > Default : Mode combo with three modes - Attach Objects to Closest
#        Point (existing) / Distribute New Drivers Evenly (existing) / Create Followers at
#        Live Closest Point (new). The new mode creates one Locator / Null follower per
#        listed object and keeps it on the surface point closest to that object:
#        object.worldMatrix -> decomposeMatrix -> closestPointOnSurface.inPosition and
#        closestPointOnSurface.parameterU/V -> pointOnSurfaceInfo.parameterU/V (live), then
#        the usual matrix network drives the follower (curves use nearestPointOnCurve).
#        Widgets of the other modes are hidden; Orient / Aim / norCrv / set are shared.

# 01.32  Seal (Free mode) : sealing now also returns the ROTATION of every driver to the
#        closed pose. A rotate with no incoming connection gets a 'sealBaseRotate'
#        (doubleAngle3) attribute - its open rotation - feeding pairBlend.inRotate1, with
#        the rest rotation on inRotate2 (same pattern as 'sealBase' for translate). Before,
#        only connected rotates were blended, so a static driver rotated after the build
#        kept that rotation when the lips closed. Remove Seal writes the value back and
#        deletes the attribute; Attached mode is unchanged.

# 01.33  AttachCrv > Default : tidy layout. The Distribute / Follower groups keep their own
#        height (vertical size policy Maximum) and a trailing stretch below them takes the
#        space the hidden Objects list leaves in Distribute mode - no more tall empty group.
#        Count / Driver Type / Surface Axis (and Follower Type / Name Suffix) sit in an
#        aligned label + widget grid, one per row, same widget width.

VERSION = "01.33"
LAST_UPDATE = "2026-10-12"
