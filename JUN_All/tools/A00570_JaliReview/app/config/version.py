# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00570_JaliReview - version info

# 01.00  In-Maya PySide tool (drag & drop shelf install). Review scene = empty scene + avatar reference + one JALI clip .mb
#        (made by A00560_JaliBatch) referenced as namespace CLIP. Clips: list from jali_clips.manifest.json, Prev / Next /
#        Swap (file -loadReference, only when the clip has no pending review edits), playback range + sound from the
#        manifest / referenced sound node. Edits: "Allow edits on referenced animation curves" toggle
#        (animDisplay -refAnimCurvesEditable), pending edit count (stored on the CLIP reference node), Save Clip Edits
#        (file -saveReference -> written into the clip .mb, manifest status 'edited'), Discard (unload / removeEdits / load).
#        Connect: CLIP:JALI:ARKIT_OUT.<target> -> <blendShape>.<target> by alias name, connected targets skipped, report;
#        optional rules json (A00145 connect rule shape) for renamed targets. Open Clip: open the clip .mb itself with a
#        temporary avatar reference, Save Clip & Close removes it before saving.

VERSION = "01.00"
LAST_UPDATE = "2026-10-26"
