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

#           Orient (v02.24) - clavicles get an A1 rule: +X at the upperarm, +Y toward world +Y
#                            (the right one is its behavior mirror).

#           Orient (v02.25) - helper_hand_l turns to match helper_lowerarm_l (arm tail "parent"),
#                            helper_hand_r is the behavior mirror of it (arm tail "mirror").

VERSION = "02.25"
LAST_UPDATE = "2026-09-18"
