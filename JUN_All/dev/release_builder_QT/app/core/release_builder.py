# -*- coding: utf-8 -*-
# release_builder.py - 릴리즈 복사 로직 (Qt 비의존)
#
# 이 파일 경로:
#   JUN_All/dev/release_builder_QT/app/core/release_builder.py
# parents[4] == JUN_All  (core -> app -> release_builder_QT -> dev -> JUN_All)

import shutil
from pathlib import Path

# 기존 dev/build_release.py 의 IGNORE_DIRS 와 동일
IGNORE_PATTERNS = [
    "__pycache__",
    "*.pyc",
    "dev",
    ".git",
    ".vs",
]


class ReleaseBuilder:

    def __init__(self):

        # __file__ 기준으로 JUN_All 루트를 자동 산출 (하드코딩 G: 경로 제거)
        self.dev_root = Path(__file__).resolve().parents[4]   # JUN_All
        self.tools_root = self.dev_root / "tools"
        self.framework_root = self.dev_root / "Framework"

    def list_tools(self):
        # tools/ 하위 디렉터리 이름 목록 (__pycache__ 등 제외)
        if not self.tools_root.is_dir():
            return []

        return sorted(
            p.name
            for p in self.tools_root.iterdir()
            if p.is_dir() and not p.name.startswith("__")
        )

    def release(self, tool_names, dest_parent, include_framework=True, log=print):

        results = []

        dest_parent = Path(dest_parent)

        for name in tool_names:

            src = self.tools_root / name
            dst = dest_parent / name

            if not src.is_dir():
                log(f"[skip] not found: {src}")
                continue

            # 기존 릴리즈 선삭제
            if dst.exists():
                shutil.rmtree(dst)

            # 툴 폴더 복사
            shutil.copytree(
                src,
                dst,
                ignore=shutil.ignore_patterns(*IGNORE_PATTERNS),
            )

            # Framework 동봉
            if include_framework:
                shutil.copytree(
                    self.framework_root,
                    dst / "Framework",
                    ignore=shutil.ignore_patterns(*IGNORE_PATTERNS),
                )

            log(f"[ok] {dst}")
            results.append(str(dst))

        return results
