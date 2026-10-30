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
# 01.34  창 높이 자동 맞춤 - 탭(중첩 포함)을 바꿀 때마다 창 높이를 지금 보이는 페이지에 맞춘다.
#        스크롤 없이 다 보이고 짧은 페이지로 가면 줄어든다. 페이지가 화면보다 길면 화면 높이에서 멈춤.
#        공용 Framework/qt/MOD_tabFit_qt_v01 (A00275 v01.38 과 같은 방식)

# 01.35  Remap Value · Spherical Eye · AttachCrv > Default 가 너무 길게 열리던 것 수정 (사용자: "세로가 절반이 되게").
#        원인 1 - Qt 5.15 QTabWidget.sizeHint 는 숨은 페이지의 Ignored 정책을 안 봐 모든 탭이 가장 긴 Seal 높이로
#        열렸다 → 공용 tabFit 에 tab_correction(현재 페이지 - 가장 긴 페이지) 보정. 원인 2 - QListWidget 기본
#        sizeHint 192px 이 리스트의 처음 높이가 됨 → 세 탭의 TSL 에 list_hint_height=LIST_HINT(100).
#        창을 늘리면 리스트는 예전처럼 따라 늘어난다. tests/test_tab_fit_ui.py 45/45.

VERSION = "01.35"
LAST_UPDATE = "2026-10-30"
