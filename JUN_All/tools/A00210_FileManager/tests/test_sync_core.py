# -*- coding: utf-8 -*-
# A00210_FileManager - Sync Tracker 코어 시험 (v01.47). Qt 없이 돈다.
#   python test_sync_core.py
import os
import sys
import json
import shutil
import tempfile
import time

JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, JUN_ALL)
from tools.A00210_FileManager.app.core import sync_settings as ss  # noqa: E402
from tools.A00210_FileManager.app.core import sync_manifest as sm  # noqa: E402
from tools.A00210_FileManager.app.core import sync_compare as sc  # noqa: E402

R = []


def check(name, cond, extra=""):
    R.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("  | " + str(extra) if extra else ""))


work = tempfile.mkdtemp(prefix="a00210_sync_")


def write(root, rel, data, mtime=None):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write(data)
    if mtime is not None:
        os.utime(p, (mtime, mtime))
    return p


def by_rel(rows):
    return {r.rel: r for r in rows}


try:
    # ================================================================ settings: exclude / ignore
    ex = ["scenes/0010_test/", "sound/bgm_tmp.wav", "00_00_02_자료/"]
    check("exclude folder subtree", ss.is_excluded("scenes/0010_test/a/b.mb", ex))
    check("exclude folder itself", ss.is_excluded("scenes/0010_test/", ex))
    check("exclude boundary (0010_test_02 kept)", not ss.is_excluded("scenes/0010_test_02/x.mb", ex))
    check("exclude file", ss.is_excluded("sound/bgm_tmp.wav", ex))
    check("exclude file - sibling kept", not ss.is_excluded("sound/bgm.wav", ex))
    check("exclude case-insensitive + backslash", ss.is_excluded("Scenes\\0010_TEST\\x.mb", ex))
    check("exclude korean folder", ss.is_excluded("00_00_02_자료/계약.pdf", ex))
    check("exclude folder given without slash", ss.is_excluded("a/b/c.mb", ["a/b"]))
    ig = ss.DEFAULT_IGNORE
    check("ignore backup deep", ss.is_ignored("p/scenes/k/backup/x_BU.mb", ig))
    check("ignore backup at top", ss.is_ignored("backup/x.mb", ig))
    check("ignore Thumbs.db top", ss.is_ignored("Thumbs.db", ig))
    check("ignore swatches", ss.is_ignored("a/.mayaSwatches/x.swatch", ig) and ss.is_ignored("a/b.swatches", ig))
    check("ignore keeps scene", not ss.is_ignored("p/scenes/k/00010_cleanup_KANA_00080.mb", ig))
    check("norm_rel", ss.norm_rel(".\\a\\\\b\\", ) == "a/b/" and ss.norm_rel("/a/b.mb") == "a/b.mb")
    check("make_root_id", ss.make_root_id("JUN MUE!") == "jun_mue" and ss.make_root_id("jun_mue", ["jun_mue"]) == "jun_mue_2"
          and ss.make_root_id("자료") == "root")
    check("root_path local wins", ss.root_path({"id": "m", "default_path": "D:/a"}, {"m": "E:/a"}) == "E:/a"
          and ss.root_path({"id": "m", "default_path": "D:\\a"}, {}) == "D:/a")
    check("overlap", ss.overlap("C:/a/b", "C:/a") == "inside" and ss.overlap("C:/a", "C:/a/b") == "contains"
          and ss.overlap("C:/a", "C:/ab") is None and ss.overlap("C:/a/", "c:/A") == "same")

    data_dir = os.path.join(work, "data")
    s0 = ss.load_settings(data_dir)
    check("settings default", s0["roots"] == [] and s0["ignore_patterns"] == ss.DEFAULT_IGNORE)
    r = ss.new_root("JUN_MUE", "C:\\JUN\\JUN_MUE")
    r["excluded_paths"] = ["a\\b\\", "a/b/", "x.mb"]
    s0["roots"].append(r)
    ss.save_settings(data_dir, s0)
    s1 = ss.load_settings(data_dir)
    check("settings round trip", s1["roots"][0]["default_path"] == "C:/JUN/JUN_MUE"
          and s1["roots"][0]["excluded_paths"] == ["a/b/", "x.mb"], s1["roots"][0])

    # ================================================================ scan
    root_a = os.path.join(work, "pcA")
    root_b = os.path.join(work, "pcB")
    T0 = time.time() - 3600
    for root in (root_a, root_b):
        write(root, "scenes/k/00010_cleanup_KANA_00070.mb", b"v70", T0)
        write(root, "scenes/k/backup/00010_cleanup_KANA_00070_BU.mb", b"bu" + root.encode(), T0)
        write(root, "scenes/0010_test/t.mb", b"t", T0)
        write(root, "sound/a.wav", b"wav", T0)
    write(root_a, "scenes/k/00010_cleanup_KANA_00080.mb", b"v80", T0 + 10)
    excluded = ["scenes/0010_test/"]

    prog = []
    ma, rep = sm.scan(root_a, "jun_mue", "PCA", "me", excluded, ss.DEFAULT_IGNORE,
                      progress=lambda d, t, rel: prog.append((d, t)))
    check("scan files (backup/excluded skipped)", sorted(ma["files"]) == [
        "scenes/k/00010_cleanup_KANA_00070.mb", "scenes/k/00010_cleanup_KANA_00080.mb", "sound/a.wav"], sorted(ma["files"]))
    check("scan hashed all first", rep["hashed"] == 3 and rep["reused"] == 0, rep)
    check("progress reaches total", prog and prog[-1][0] == prog[-1][1] == 9, prog[-1:])
    e = ma["files"]["sound/a.wav"]
    check("entry fields", e["size"] == 3 and len(e["sha256"]) == 64 and e["history"] == [e["sha256"]] and e["mtime_ns"] > 0)

    ma2, rep2 = sm.scan(root_a, "jun_mue", "PCA", "me", excluded, ss.DEFAULT_IGNORE, prev=ma)
    check("rescan reuses cache", rep2["hashed"] == 0 and rep2["reused"] == 3, rep2)

    # 내용 변경 → history 쌓임
    write(root_a, "sound/a.wav", b"wav2", T0 + 20)
    ma3, rep3 = sm.scan(root_a, "jun_mue", "PCA", "me", excluded, ss.DEFAULT_IGNORE, prev=ma2)
    h = ma3["files"]["sound/a.wav"]["history"]
    check("changed file rehashed + history 2", rep3["hashed"] == 1 and len(h) == 2 and h[0] == e["sha256"], rep3)

    # 해시 중 바뀐 파일(저장 중) - 직전 값 유지 + busy
    orig = sm.sha256_of
    def flaky(path, progress=None, cancel=None):
        d = orig(path, progress, cancel)
        if path.endswith("a.wav"):
            with open(path, "ab") as f:
                f.write(b"more")
        return d
    write(root_a, "sound/a.wav", b"wav3", T0 + 30)
    sm.sha256_of = flaky
    try:
        ma4, rep4 = sm.scan(root_a, "jun_mue", "PCA", "me", excluded, ss.DEFAULT_IGNORE, prev=ma3)
    finally:
        sm.sha256_of = orig
    check("busy file skipped, prev kept", rep4["busy"] == ["sound/a.wav"]
          and ma4["files"]["sound/a.wav"]["sha256"] == ma3["files"]["sound/a.wav"]["sha256"], rep4)

    # 되돌린 파일: 옛 해시가 history 맨 뒤로
    write(root_a, "sound/a.wav", b"wav", T0 + 40)
    ma5, _ = sm.scan(root_a, "jun_mue", "PCA", "me", excluded, ss.DEFAULT_IGNORE, prev=ma4)
    h5 = ma5["files"]["sound/a.wav"]["history"]
    check("revert moves hash to end", h5[-1] == e["sha256"] and len(h5) == 2, h5)

    # 취소
    try:
        sm.scan(root_a, "jun_mue", "PCA", cancel=lambda: True)
        check("cancel raises", False)
    except sm.ScanCancelled:
        check("cancel raises", True)

    # 저장 / 읽기
    p = sm.save_manifest(data_dir, ma5)
    check("manifest path", p.replace("\\", "/").endswith("manifests/jun_mue/PCA.json"))
    loaded = sm.load_root_manifests(data_dir, "jun_mue")
    check("load_root_manifests", list(loaded) == ["PCA"] and loaded["PCA"]["files"] == ma5["files"])
    check("settings file not read as manifest", "_sync_settings" not in loaded)

    # 루트 안 정션은 기본으로 안 따라감
    if os.name == "nt":
        import subprocess
        target = os.path.join(work, "outside")
        write(target, "far.mb", b"far")
        link = os.path.join(root_b, "linked")
        subprocess.run(["cmd", "/c", "mklink", "/J", link, target], capture_output=True)
        if os.path.isdir(link):
            mb, _ = sm.scan(root_b, "jun_mue", "PCB", excluded=excluded, ignore=ss.DEFAULT_IGNORE)
            mbf, _ = sm.scan(root_b, "jun_mue", "PCB", excluded=excluded, ignore=ss.DEFAULT_IGNORE, follow_junctions=True)
            check("junction inside root skipped by default", "linked/far.mb" not in mb["files"] and "linked/far.mb" in mbf["files"])
            os.rmdir(link)       # 정션만 지운다(대상은 그대로)
            check("junction target intact", os.path.isfile(os.path.join(target, "far.mb")))
        else:
            print("SKIP junction test (mklink failed)")

    # ================================================================ compare - 2 PCs
    mb, _ = sm.scan(root_b, "jun_mue", "PCB", "you", excluded, ss.DEFAULT_IGNORE)
    rows = by_rel(sc.compare({"PCA": ma, "PCB": mb}, "PCB"))
    r80 = rows["scenes/k/00010_cleanup_KANA_00080.mb"]
    check("2PC: new file on A = Missing on B", r80.status == sc.MISSING and r80.pc_status["PCA"] == sc.ONLY_HERE, r80)
    check("2PC: same file OK", rows["scenes/k/00010_cleanup_KANA_00070.mb"].status == sc.OK)
    check("2PC: backup differs but ignored", not any("backup" in k for k in rows))
    rows_a = by_rel(sc.compare({"PCA": ma, "PCB": mb}, "PCA"))
    check("2PC: A sees its new file as Only here", rows_a["scenes/k/00010_cleanup_KANA_00080.mb"].status == sc.ONLY_HERE)

    # A 가 a.wav 를 고침(ma3) → B 는 Outdated(확실)
    rows = by_rel(sc.compare({"PCA": ma3, "PCB": mb}, "PCB"))
    ra = rows["sound/a.wav"]
    check("2PC: edited on A = Outdated on B (certain)", ra.status == sc.OUTDATED and not ra.uncertain["PCB"]
          and ra.pc_status["PCA"] == sc.AHEAD, ra)

    # 구글 드라이브 다운로드: B 가 A 의 새 버전을 받음(시각은 받은 시각) → OK
    write(root_b, "sound/a.wav", b"wav2", time.time())
    mb2, _ = sm.scan(root_b, "jun_mue", "PCB", "you", excluded, ss.DEFAULT_IGNORE, prev=mb)
    rows = by_rel(sc.compare({"PCA": ma3, "PCB": mb2}, "PCB"))
    check("2PC: downloaded copy (new mtime) = OK by hash", rows["sound/a.wav"].status == sc.OK)

    # 양쪽이 따로 고침(둘 다 이력 2개 이상) → Conflict
    write(root_a, "sound/a.wav", b"A-edit", T0 + 50)
    ma6, _ = sm.scan(root_a, "jun_mue", "PCA", "me", excluded, ss.DEFAULT_IGNORE, prev=ma3)
    write(root_b, "sound/a.wav", b"B-edit", T0 + 60)
    mb3, _ = sm.scan(root_b, "jun_mue", "PCB", "you", excluded, ss.DEFAULT_IGNORE, prev=mb2)
    rows = by_rel(sc.compare({"PCA": ma6, "PCB": mb3}, "PCB"))
    check("2PC: both edited = Conflict both", rows["sound/a.wav"].pc_status == {"PCA": sc.CONFLICT, "PCB": sc.CONFLICT},
          rows["sound/a.wav"].pc_status)

    # 처음 보는 파일인데 내용이 다름 → 시각으로 '아마' (uncertain)
    fa = {"pc": "PCA", "files": {"x.mb": {"sha256": "aa", "history": ["aa"], "mtime_ns": 100}}}
    fb = {"pc": "PCB", "files": {"x.mb": {"sha256": "bb", "history": ["bb"], "mtime_ns": 200}}}
    rx = sc.compare({"PCA": fa, "PCB": fb}, "PCA")[0]
    check("first sight differs: older = Outdated?", rx.status == sc.OUTDATED and rx.uncertain["PCA"]
          and rx.pc_status["PCB"] == sc.AHEAD and rx.uncertain["PCB"], (rx.pc_status, rx.uncertain))

    # Only here / 단독 PC
    fo = {"pc": "PCA", "files": {"only.mb": {"sha256": "cc", "history": ["cc"]}}}
    fe = {"pc": "PCB", "files": {}}
    ro = sc.compare({"PCA": fo, "PCB": fe}, "PCA")[0]
    check("Only here", ro.status == sc.ONLY_HERE and ro.pc_status["PCB"] == sc.MISSING)
    check("single PC = OK", sc.compare({"PCA": fo}, "PCA")[0].status == sc.OK)
    check("this PC without manifest = Missing", sc.compare({"PCA": fo}, "PCZ")[0].status == sc.MISSING)

    # 비교 때도 제외 적용(다른 PC 의 옛 매니페스트에 남아 있어도)
    rows = sc.compare({"PCA": ma, "PCB": mb}, "PCB", excluded=["scenes/k/"])
    check("compare-time exclude", all(not r.rel.startswith("scenes/k/") for r in rows), [r.rel for r in rows])
    rows = sc.compare({"PCA": ma, "PCB": mb}, "PCB", ignore=["**/*.wav"])
    check("compare-time ignore", all(not r.rel.endswith(".wav") for r in rows))

    # 대소문자만 다른 경로 = 같은 파일
    fa = {"files": {"Scenes/A.mb": {"sha256": "aa", "history": ["aa"]}}}
    fb = {"files": {"scenes/a.mb": {"sha256": "aa", "history": ["aa"]}}}
    rc = sc.compare({"PCA": fa, "PCB": fb}, "PCA")
    check("case-insensitive merge", len(rc) == 1 and rc[0].status == sc.OK)

    # ================================================================ compare - 3 / 5 PCs
    def m(files):
        return {"files": files}

    def ent(sha, hist):
        return {"sha256": sha, "history": hist, "mtime_ns": 1}

    # A: v1 → v2 → v3, B: v2, C: v3, D: 없음, E: v1
    man = {
        "A": m({"f.mb": ent("v3", ["v1", "v2", "v3"])}),
        "B": m({"f.mb": ent("v2", ["v1", "v2"])}),
        "C": m({"f.mb": ent("v3", ["v3"])}),
        "D": m({}),
        "E": m({"f.mb": ent("v1", ["v1"])}),
    }
    r5 = sc.compare(man, "C")[0]
    check("5PC statuses", r5.pc_status == {"A": sc.AHEAD, "B": sc.OUTDATED, "C": sc.AHEAD, "D": sc.MISSING, "E": sc.OUTDATED},
          r5.pc_status)
    check("5PC latest_on / missing_on", sorted(r5.latest_on()) == ["A", "C"] and r5.pcs_with(sc.MISSING) == ["D"]
          and sorted(r5.pcs_with(sc.OUTDATED)) == ["B", "E"])
    check("5PC is_problem", r5.is_problem())

    man3 = {"A": m({"f.mb": ent("v2", ["v1", "v2"])}), "B": m({"f.mb": ent("v2", ["v2"])}), "C": m({"f.mb": ent("v2", ["v2"])})}
    r3 = sc.compare(man3, "B")[0]
    check("3PC all same = OK, not problem", r3.status == sc.OK and not r3.is_problem(), r3.pc_status)
    # 3대 중 두 대가 같은 옛것에서 각자 고침 → 둘은 Conflict, 옛것 가진 PC 는 Outdated
    man3c = {"A": m({"f.mb": ent("a", ["o", "a"])}), "B": m({"f.mb": ent("b", ["o", "b"])}), "C": m({"f.mb": ent("o", ["o"])})}
    r3c = sc.compare(man3c, "C")[0]
    check("3PC fork: A/B Conflict, C Outdated", r3c.pc_status == {"A": sc.CONFLICT, "B": sc.CONFLICT, "C": sc.OUTDATED},
          r3c.pc_status)

    cnt = sc.summarize(sc.compare(man, "D"))
    check("summarize", cnt[sc.MISSING] == 1, cnt)

finally:
    shutil.rmtree(work, ignore_errors=True)

print("\n{0}/{1} passed".format(sum(R), len(R)))
sys.exit(0 if all(R) else 1)
