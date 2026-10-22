# Python Script by Ji Hun Park
# last Update date : 2026-10-22
# A00540_JaliLipSync - version info

# 01.00  VisemeNet viseme curves (txt from JUN_JALI's VisemeNet Converter) -> keys on a JALI
#        rig (angela_JALI.ma: CNT_JaLi / CNT_PHONEMES / CNT_COARTIC). Pick the TXT and the WAV
#        (found automatically from the .visemenet.json or the same name), rig namespace,
#        mapping json, start frame, viseme scale, JaLi from data or fixed. Keys are sampled at
#        the scene fps, the range is cleared first, one undo step. Audio node on the time slider.
# 01.01  Mapping json v2: "nodes" role table (phonemes / coartic / jali), "viseme_scale", "jali" {scale, range,
#        fixed_default} - the rig marker is no longer hard-coded. Target Auto (find by the mapping's phonemes node)
#        / Manual (pick the three nodes, empty roles are skipped). JaLi scale spin box; scales and the Fixed
#        range reset to the mapping's defaults when the mapping changes; warn when a scale exceeds an
#        attribute maximum. New mapping jali_slider_dummy_in (A0020 slider rig, DUMMY_IN_*). tests/.

VERSION = "01.01"
LAST_UPDATE = "2026-10-22"
