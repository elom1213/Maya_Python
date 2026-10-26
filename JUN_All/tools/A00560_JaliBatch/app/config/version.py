# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00560_JaliBatch - version info

# 01.00  Standalone (PySide, outside Maya). Batch tab: a VisemeNet Converter output folder (22-column txt + .visemenet.json
#        + wav, N clips) -> N clip .mb files, each = empty scene at the chosen fps + the JALI slider controller rig referenced
#        as namespace "JALI" + keys on DUMMY_IN_* (Framework.jali.keyer) baked onto the controllers (copy mode, DUMMY_IN
#        curves removed, curves renamed JALI_<ctl>_<attr>) + the wav copied next to the clip as a sound node + a fileInfo
#        stamp (controller path / mtime, mapping, fps, start, frames) + jali_clips.manifest.json in the output folder.
#        One mayapy worker process runs all clips in order (cancel at clip boundaries, failed clips do not stop the rest).
#        Start frame = one value for all clips, editable per clip in the table (never read from the file name).
#        Existing clips: Skip (default) / Overwrite / Overwrite with backup (backup/<name>_NN.mb); edited clips ask again.
#        Validate tab: open every clip in mayapy and report controller path, load state, failed edits, baked channels,
#        keys, DUMMY_IN leftovers and whether the controller file changed since the stamp; Repath switches the controller.
#        Shrink / Pin, File > Add to Start Menu, shared log, prefs in ~/.jun_jalibatch.

VERSION = "01.00"
LAST_UPDATE = "2026-10-26"
