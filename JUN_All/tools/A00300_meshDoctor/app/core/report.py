# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-25
# A00300_meshDoctor - 진단 결과를 JSON + 사람이 읽는 TXT 로 0020_out/ 에 저장.
#
# JSON 은 Claude 분석용(구조화), TXT 는 사용자가 바로 읽는 요약.

import os
import json
from datetime import datetime

import maya.cmds as cmds

from Framework.core.path_manager import PathManager
from tools.A00300_meshDoctor.app.config.version import VERSION


# A00300_meshDoctor 툴 루트 (.../tools/A00300_meshDoctor)
_TOOL_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _scene_name():
    try:
        name = cmds.file(q=True, sceneName=True, shortName=True) or ""
    except Exception:
        name = ""
    name = os.path.splitext(name)[0]
    return name or "untitled"


class ReportWriter:
    """진단 결과(list[dict])를 0020_out/ 에 JSON + TXT 로 쓴다."""

    def __init__(self):
        # PathManager 의 root 는 root_file 의 부모 디렉터리. 툴 루트를 가리키게 한다.
        self.pm = PathManager(
            os.path.join(_TOOL_ROOT, "_anchor.py"),
            write_dir="0020_out",
        )

    def write(self, results):
        """returns (json_path, txt_path, out_dir)."""
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = "meshDoctor_{0}_{1}".format(_scene_name(), stamp)

        json_path = str(self.pm.path("write", base + ".json"))
        txt_path = str(self.pm.path("write", base + "_summary.txt"))
        PathManager.ensure_dir(json_path)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.build_json(results), f, ensure_ascii=False, indent=2)

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(self.build_txt(results))

        out_dir = str(self.pm.path("write"))
        return json_path, txt_path, out_dir

    # ------------------------------------------------------------------

    @staticmethod
    def _maya_version():
        try:
            return cmds.about(version=True)
        except Exception:
            return "?"

    def build_json(self, results):
        return {
            "tool": "A00300_meshDoctor",
            "version": VERSION,
            "scene": _scene_name(),
            "maya_version": self._maya_version(),
            "generated": datetime.now().isoformat(timespec="seconds"),
            "mesh_count": len(results),
            "results": results,
        }

    def build_txt(self, results):
        lines = []
        lines.append("=" * 70)
        lines.append("  MESH DOCTOR  (A00300_meshDoctor v{0})".format(VERSION))
        lines.append("  scene : {0}    maya : {1}".format(
            _scene_name(), self._maya_version()))
        lines.append("  time  : {0}".format(datetime.now().isoformat(timespec="seconds")))
        lines.append("  meshes: {0}".format(len(results)))
        lines.append("=" * 70)

        if not results:
            lines.append("\nNo mesh selected. Select a polygon mesh and Diagnose.")
            return "\n".join(lines)

        for r in results:
            c = r.get("counts", {})
            lines.append("")
            lines.append("-" * 70)
            lines.append("MESH : {0}   [shape: {1}]   => {2}".format(
                r["transform"], r["shape"], r["worst"]))
            lines.append("  verts={0}  edges={1}  faces={2}  shells={3}".format(
                c.get("vertices", "?"), c.get("edges", "?"),
                c.get("faces", "?"), c.get("shells", "?")))
            lines.append("-" * 70)

            for cause in r.get("suspected_root_causes", []):
                lines.append("  >> " + cause)
            lines.append("")

            for chk in r["checks"]:
                tag = "[{0}]".format(chk["severity"]).ljust(7)
                head = "  {0} {1}".format(tag, chk["check"])
                if chk["count"]:
                    head += "  (count={0})".format(chk["count"])
                lines.append(head)
                lines.append("        {0}".format(chk["message"]))
                if chk["samples"]:
                    sample = ", ".join(str(s) for s in chk["samples"])
                    more = "" if chk["count"] <= len(chk["samples"]) else "  ..."
                    lines.append("        samples: {0}{1}".format(sample, more))

        lines.append("")
        lines.append("=" * 70)
        lines.append("Severity: FAIL = blocking, WARN = likely problem, "
                     "INFO = context, PASS = ok")
        lines.append("=" * 70)
        return "\n".join(lines)
