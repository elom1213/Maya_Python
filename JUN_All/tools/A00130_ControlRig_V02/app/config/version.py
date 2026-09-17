# Control Rig Tool V02 (template joint paradigm)
# Phase 1 : Match  - cage set members onto their paired template joint.
#           Length - template joint distances onto the option controller.
#           Match brackets the run with an IK edit session (D01_IK_handle).
#           Orient & Place - A1 spine / A2 limbs + tail / A3 mirror
#                            + place the foot and toe pole targets.

#           Match (v02.20) - parents are matched before children, and anything another
#                            match pushed away is matched again - one press is enough.

#           Check Position (v02.21) - in every cage set, are all objects at the same
#                            world position and rotation? Green OK / red what differs.

#           Length Total (v02.22) - 'sum' is the default and the first item.

#           Match list (v02.23) - double-click a row to select its cage set in Maya.

VERSION = "02.23"
LAST_UPDATE = "2026-09-17"
