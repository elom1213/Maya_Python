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

# 01.01  Double-click launcher: Run_JaliBatch.bat (first run builds the environment via setup_env.bat, then opens the
#        window without a console) and setup_env.bat (finds 64-bit Python 3.10+ - 3.14 included, PySide6 abi3 wheels;
#        with no usable Python it downloads a private Python 3.11.9 like JUN_JALI; app/selftest.py). Windows 10 / 11.
#        The environment lives in %USERPROFILE%\.jun_jalibatch\venv (JUN_JALIBATCH_HOME overrides) - the PySide6 wheel
#        has a 151-character path, so a venv inside this (86-character) tool folder breaks the Windows 260 limit.
#        requirements.txt = PySide6_Essentials (pyinstaller just for build_exe.bat). Verified on Python 3.14.9 + PySide6 6.12.

VERSION = "01.01"
LAST_UPDATE = "2026-10-26"
