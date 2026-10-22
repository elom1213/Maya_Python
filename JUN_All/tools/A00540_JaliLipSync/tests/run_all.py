# -*- coding: utf-8 -*-
# A00540_JaliLipSync - 시험 전부 돌리기 (각 파일을 mayapy 하위 프로세스로)
#   "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" run_all.py
# 종료 코드 = 실패한 파일 수.
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = ["test_mapping.py", "test_sequence.py", "test_keyer.py", "test_ui.py", "test_end_to_end.py"]

failed = 0
for name in TESTS:
    print("=" * 70)
    print(name)
    print("=" * 70)
    env = dict(os.environ, PYTHONUNBUFFERED="1")
    proc = subprocess.run([sys.executable, os.path.join(HERE, name)], env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
    lines = [l for l in proc.stdout.splitlines() if l.startswith(("PASS", "FAIL", "RESULT", "SKIP", "Traceback", "  File", "    ", "Error"))]
    print("\n".join(lines))
    if proc.returncode != 0:
        failed += 1
        print("** {0} exited with {1}".format(name, proc.returncode))
print("=" * 70)
print("ALL DONE - {0} file(s) failed".format(failed))
sys.exit(failed)
