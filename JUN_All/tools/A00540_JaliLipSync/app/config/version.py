# Python Script by Ji Hun Park
# last Update date : 2026-10-26
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
# 01.02  Clip list: several TXT (+WAV) files in the order you set (Add / Set WAV / Remove / Up / Down), keyed
#        back to back in one scene - each clip's start frame is shown in the table. "Hold" = frames of pause
#        between clips: the last value of a clip is held until the next clip starts (otherwise Maya would
#        blend across the gap). A clip's length on the timeline is its WAV length (the model output ends
#        0.32 s early). Audio: the clip WAVs are written into one sequence WAV at their frame positions
#        (silence in the holds) and attached as one sound node, so playback follows the clip order.
#        One undo step for the whole sequence. Remove Keys clears the whole sequence range.

# 01.03  Core promoted to Framework/jali (lipsync_data · mapping · sequence · keyer · scene + mappings/*.json) so
#        A00560_JaliBatch and A00570_JaliReview share it. app/core/*.py re-export the Framework modules; mapping json
#        files now live in Framework/jali/mappings. No behaviour change.

VERSION = "01.03"
LAST_UPDATE = "2026-10-26"
