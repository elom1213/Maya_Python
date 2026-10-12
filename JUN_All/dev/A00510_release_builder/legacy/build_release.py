# dev/build_release.py

import os
import shutil
import remove_pycache as rmv_pyc

# =========================
# CONFIG
# =========================

DEV_ROOT = r"G:/D_link_dir/02_Maya_python_Jun/JUN_All"
RELEASE_ROOT_PARENT = r"G:/D_link_dir/02_Maya_python_Jun_Release/Maya_Tool_Release/tools"
TOOL_PATH = "A00050_uvTool"

IGNORE_DIRS = [
    "__pycache__",
    "*.pyc",
    "dev",
    ".git",
    ".vs"
]

FRAMEWORK_ROOT = os.path.join(
    DEV_ROOT,
    "Framework"
)

TOOL_ROOT = os.path.join(
    DEV_ROOT,
    "tools",
    TOOL_PATH
)

RELEASE_ROOT = os.path.join(
    RELEASE_ROOT_PARENT,
    # "RELEASE",
    TOOL_PATH
)


# =========================
# DELETE OLD RELEASE
# =========================

if os.path.exists(RELEASE_ROOT):
    shutil.rmtree(RELEASE_ROOT)


# =========================
# COPY TOOL
# =========================

shutil.copytree(
    TOOL_ROOT,
    RELEASE_ROOT,
    ignore=shutil.ignore_patterns(*IGNORE_DIRS)
)


# =========================
# COPY FRAMEWORK
# =========================

framework_dst = os.path.join(
    RELEASE_ROOT,
    "Framework"
)


shutil.copytree(
    FRAMEWORK_ROOT,
    framework_dst,
    ignore=shutil.ignore_patterns(*IGNORE_DIRS)
)

print("==================================================")
print(f"Release : {RELEASE_ROOT}")
print("Release Build Complete")
print("==================================================")