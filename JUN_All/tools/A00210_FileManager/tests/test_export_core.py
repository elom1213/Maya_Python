# -*- coding: utf-8 -*-
# A00210_FileManager - Maya > Export 코어 시험 (set_rules · export_naming · export_jobs, Maya 비의존)
#   python -I test_export_core.py
import os
import sys
import json
import tempfile
import shutil

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00210_FileManager.app.maya.core import set_rules, export_naming, export_jobs   # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


# ---------------------------------------------------------------- export_naming
spec = export_naming.NamingSpec.from_dict(export_naming.DEFAULT_SPEC)
check("default spec = token 0 'bake'", spec.mode == "token" and spec.position == 0 and spec.text == "bake")
check("anim_01 -> bake_anim_01 (default)", export_naming.output_stem("anim_01", spec)[0] == "bake_anim_01")
s1 = export_naming.NamingSpec(mode="token", position=1, text="bake")
check("token 1 -> anim_bake_01", export_naming.output_stem("anim_01", s1)[0] == "anim_bake_01")
s2 = export_naming.NamingSpec(mode="char", position=4, text="_bake")
check("char 4 '_bake' -> anim_bake_01", export_naming.output_stem("anim_01", s2)[0] == "anim_bake_01")
check("token -1 -> end", export_naming.insert_token("anim_01", -1, "bake")[0] == "anim_01_bake")
check("token -2 -> before last", export_naming.insert_token("anim_01", -2, "bake")[0] == "anim_bake_01")
out, clamped = export_naming.insert_token("anim_01", 9, "bake")
check("token beyond count -> end + clamped", out == "anim_01_bake" and clamped)
out, clamped = export_naming.insert_char("abc", -10, "X")
check("char far negative -> start + clamped", out == "Xabc" and clamped)
check("char 0 / -1 pair", export_naming.insert_char("arm_jnt", 0, "X")[0] == "Xarm_jnt"
      and export_naming.insert_char("arm_jnt", -1, "X")[0] == "arm_jntX"
      and export_naming.insert_char("arm_jnt", -4, "X")[0] == "arm_Xjnt" and export_naming.insert_char("arm_jnt", 3, "X")[0] == "armX_jnt")
check("no tokens name", export_naming.insert_token("anim", 0, "bake")[0] == "bake_anim")
check("empty text keeps", export_naming.insert_token("anim_01", 0, "")[0] == "anim_01")
check("replace all, case", export_naming.replace_text("anim_Anim_anim", "anim", "walk") == "walk_Anim_walk")
check("replace ignore case", export_naming.replace_text("anim_Anim", "anim", "walk", case_sensitive=False) == "walk_walk")
s3 = export_naming.NamingSpec(find="anim", replace="walk", mode="token", position=0, text="bake")
check("replace then insert", export_naming.output_stem("anim_01", s3)[0] == "bake_walk_01")
s4 = export_naming.NamingSpec(mode="token", position=0, text="ba:ke")
rows = export_naming.preview([r"C:\x\anim_01.mb"], s4)
check("invalid characters flagged", rows[0].invalid and ":" in rows[0].notes[-1])
s5 = export_naming.NamingSpec(find="_01", replace="", mode="token", position=0, text="")
rows = export_naming.preview([r"C:\x\anim_01.mb", r"C:\x\anim.ma"], s5, out_dir=r"D:\out")
check("collision flagged on both", all(r.collision for r in rows) and all(r.out_path.lower() == r"d:\out\anim.fbx" for r in rows))
rows = export_naming.preview([r"C:\x\anim_01.mb", r"C:\y\anim_01.ma"], spec)
check("no out_dir -> next to source, no collision", not any(r.collision for r in rows)
      and rows[0].out_path.lower() == r"c:\x\bake_anim_01.fbx" and rows[1].out_path.lower() == r"c:\y\bake_anim_01.fbx")
check("ext always .fbx", all(r.out_name.endswith(".fbx") for r in rows))
check("spec dict round trip", export_naming.NamingSpec.from_dict(s3.to_dict()).to_dict() == s3.to_dict())
tmpd = tempfile.mkdtemp(prefix="a00210_exp_")
open(os.path.join(tmpd, "bake_anim_01.fbx"), "w").close()
rows = export_naming.preview([r"C:\x\anim_01.mb", r"C:\x\anim_02.mb"], spec, out_dir=tmpd)
check("existing_outputs finds the one on disk", [os.path.basename(p) for p in export_naming.existing_outputs(rows)] == ["bake_anim_01.fbx"])

# ---------------------------------------------------------------- set_rules
rdir = os.path.join(tmpd, "rules")
rules, errors = set_rules.load_rules(rdir)
check("empty folder -> default Bake rule created", len(rules) == 1 and rules[0].name == "Bake" and os.path.isfile(os.path.join(rdir, "Bake.json")) and not errors)
r = set_rules.SetRule("Face Set", "FaceCtl", "contains", False, "desc")
p = set_rules.save_rule(r, rdir)
check("save -> file name sanitized from name", os.path.basename(p) == "Face Set.json")
rules, errors = set_rules.load_rules(rdir)
check("load 2 rules sorted", [x.name for x in rules] == ["Bake", "Face Set"])
fr = set_rules.find_rule(rules, "Face Set")
check("fields round trip", fr.set_name == "FaceCtl" and fr.match == "contains" and fr.ignore_namespace is False and fr.description == "desc")
set_rules.rename_rule(fr, "Face:Set*2", rdir)
check("rename -> json name + file (sanitized)", fr.name == "Face:Set*2" and os.path.isfile(os.path.join(rdir, "Face_Set_2.json"))
      and not os.path.exists(os.path.join(rdir, "Face Set.json")))
try:
    set_rules.rename_rule(fr, "Bake", rdir)
    check("rename onto existing refused", False)
except ValueError:
    check("rename onto existing refused", True)
bad = os.path.join(rdir, "broken.json")
open(bad, "w").write("{not json")
rules, errors = set_rules.load_rules(rdir)
check("broken json -> errors, others load", len(rules) == 2 and len(errors) == 1 and errors[0][0] == bad)
os.remove(bad)
try:
    set_rules.delete_rule(set_rules.SetRule("x", "x", path=os.path.join(tmpd, "outside.json")), rdir)
    check("delete outside folder refused", False)
except ValueError:
    check("delete outside folder refused", True)
set_rules.delete_rule(fr, rdir)
check("delete removes file", not os.path.exists(fr.path))
check("validate regex error", any("Regex" in e for e in set_rules.validate("n", "[", "regex")))
check("validate empty", set_rules.validate("", "", "exact") == ["Name is empty.", "Set name is empty."])
try:
    set_rules.save_rule(set_rules.SetRule("n", "", "exact"), rdir)
    check("save invalid raises", False)
except ValueError:
    check("save invalid raises", True)
# matching
rule = {"set_name": "Bake", "match": "exact", "ignore_namespace": True}
check("match exact leaf ignoring ns", set_rules.name_matches("CHN:rig:Bake", rule) and set_rules.name_matches("Bake", rule)
      and not set_rules.name_matches("Bake2", rule))
rule_ns = dict(rule, ignore_namespace=False)
check("match with namespace matters", not set_rules.name_matches("CHN:Bake", rule_ns) and set_rules.name_matches("Bake", rule_ns))
check("match contains", set_rules.name_matches("CHN:ExportBakeSet", dict(rule, match="contains")))
check("match regex fullmatch", set_rules.name_matches("Bake_02", dict(rule, set_name=r"Bake_\d+", match="regex"))
      and not set_rules.name_matches("xBake_02", dict(rule, set_name=r"Bake_\d+", match="regex")))
check("rules_dir default", set_rules.rules_dir("").lower().endswith(os.path.join(".jun_filemanager", "export_rules").lower()))
check("summary line", rules[0].summary() == 'set "Bake" \u00b7 exact \u00b7 ignore namespace')

# ---------------------------------------------------------------- export_jobs
try:
    export_jobs.probe_job([], rule)
    check("probe_job no files raises", False)
except ValueError:
    check("probe_job no files raises", True)
j = export_jobs.probe_job(["a.mb"], rule)
check("probe_job shape", j["job"] == "probe" and j["files"] == ["a.mb"] and j["rule"] == rule)
rows = [{"file": "a.mb", "start": "0", "end": 6000.0, "out_fbx": "o/a.fbx"}]
ej = export_jobs.export_job(rule, rows, bake=True, channels=["translate", "rotate", "scale"], joints_only=True,
                            euler_filter=False, import_references=True, report_path="o/r.json")
check("export_job ints + fields", ej["items"][0] == {"file": "a.mb", "start": 0, "end": 6000, "out_fbx": "o/a.fbx"}
      and ej["bake"] and ej["channels"] == ["translate", "rotate", "scale"] and ej["report"] == "o/r.json")
for bad_rows, why in (([{"file": "a.mb", "start": 10, "end": 5, "out_fbx": "x"}], "start after end"),
                      ([{"file": "a.mb", "start": "x", "end": 5, "out_fbx": "x"}], "not a number"),
                      ([{"file": "a.mb", "start": 0, "end": 5, "out_fbx": ""}], "empty output"),
                      ([], "no rows")):
    try:
        export_jobs.export_job(rule, bad_rows)
        check("export_job rejects " + why, False)
    except ValueError:
        check("export_job rejects " + why, True)
try:
    export_jobs.export_job(rule, rows, bake=True, channels=[])
    check("export_job bake needs channels", False)
except ValueError:
    check("export_job bake needs channels", True)
check("export only without channels ok", export_jobs.export_job(rule, rows, bake=False, channels=[])["bake"] is False)
check("report_path", os.path.basename(export_jobs.report_path("o")).startswith("_bake_export_report_"))
check("summarize", export_jobs.summarize({"exported": 1, "skipped": 2, "failed": 0, "cancelled": True}) == "1 exported, 2 skipped, 0 failed (cancelled)")
check("json serializable", json.dumps(ej) and json.dumps(j))

shutil.rmtree(tmpd, ignore_errors=True)
print("\nRESULT %d/%d" % (sum(R), len(R)))
sys.exit(0 if all(R) else 1)
