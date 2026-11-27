# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-11-27
# A00210_FileManager v01.60 - 일회성 이전: profiles/<folder>/path_structures/*.json -> <repo>/path_structures/
#
#   python migrate_structure_library.py <repo_dir>            (dry-run: 계획만 출력)
#   python migrate_structure_library.py <repo_dir> --apply    (git mv + 카테고리 + 로컬 커밋, 푸시는 하지 않는다)
#
# - 옛 데이터 폴더 이름(Dnable · JUN · MUE · SA ...) = 첫 카테고리. 같은 이름 카테고리가 있으면 재사용 -> 재실행해도 안전(멱등).
# - 이름 충돌(이미 path_structures/ 에 같은 파일)이면 <stem>_<folder>.json, 표시 이름도 같은 접미사.
# - 스테이징은 path_structures/ 와 profiles/*/path_structures/ 만 - records 등 다른 미커밋 변경은 건드리지 않는다.
# - 원격 반영은 툴의 Path Structure 탭 Push(로컬 커밋 전부를 보낸다) 또는 git push.

import os
import sys
import json
import argparse
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
JUN_ALL = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if JUN_ALL not in sys.path:
    sys.path.insert(0, JUN_ALL)

from tools.A00210_FileManager.app.core import path_structure as ps_mod          # noqa: E402
from tools.A00210_FileManager.app.core import structure_library as lib_mod     # noqa: E402

COMMIT_MESSAGE = "Move path structures to shared library (A00210 v01.60) [path_structures]"
LEGACY_GLOB = "profiles/*/" + lib_mod.LIB_DIR


def git(repo, *args):
    proc = subprocess.run(["git"] + list(args), cwd=repo, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    return proc.returncode == 0, ((proc.stdout or "") + (proc.stderr or "")).strip()


def check_repo(repo, branch):
    """이전 전 검사. 문제 목록(비면 통과)."""
    problems = []
    if not os.path.isdir(os.path.join(repo, ".git")):
        return ["Not a git clone: " + repo]
    ok, cur = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    if cur.strip() != branch:
        problems.append("Clone is on branch '{0}', expected '{1}'.".format(cur.strip(), branch))
    gd = os.path.join(repo, ".git")
    if os.path.isdir(os.path.join(gd, "rebase-merge")) or os.path.isdir(os.path.join(gd, "rebase-apply")):
        problems.append("A rebase is in progress - finish or abort it first.")
    ok, out = git(repo, "status", "--porcelain", "--", lib_mod.LIB_DIR, LEGACY_GLOB)
    if out.strip():
        problems.append("Uncommitted changes under path_structures - commit or discard them first:\n" + out)
    return problems


def make_plan(repo):
    """[(folder, src_abs, dst_abs, new_name or None)] - dst 이름 충돌은 접미사."""
    lib = lib_mod.StructureLibrary(repo)
    taken = {fn.lower() for fn in os.listdir(lib.lib_dir())} if os.path.isdir(lib.lib_dir()) else set()
    plan = []
    for folder, src in lib.legacy_files():
        fname = os.path.basename(src)
        new_name = None
        if fname.lower() in taken:
            stem = fname[:-5]
            n = 0
            while True:
                cand = "{0}_{1}{2}.json".format(stem, folder, "" if n == 0 else "_{0}".format(n))
                if cand.lower() not in taken:
                    break
                n += 1
            try:
                with open(src, "r", encoding="utf-8") as f:
                    shown = json.load(f).get("name") or stem
            except (OSError, ValueError):
                shown = stem
            new_name = "{0}_{1}{2}".format(shown, folder, "" if n == 0 else "_{0}".format(n))
            fname = cand
        taken.add(fname.lower())
        plan.append((folder, src, os.path.join(lib.lib_dir(), fname), new_name))
    return plan


def apply_plan(repo, plan, author):
    lib = lib_mod.StructureLibrary(repo)
    cat_ids = {}
    for folder in sorted({p[0] for p in plan}, key=str.lower):
        cat = lib.find_category(folder) or lib.create_category(folder, author=author)
        cat_ids[folder] = cat.id
        print("  category {0} = {1}".format(cat.name, cat.id))

    os.makedirs(lib.lib_dir(), exist_ok=True)
    for folder, src, dst, new_name in plan:
        rel_src = os.path.relpath(src, repo).replace("\\", "/")
        rel_dst = os.path.relpath(dst, repo).replace("\\", "/")
        ok, out = git(repo, "mv", rel_src, rel_dst)
        if not ok:
            raise RuntimeError("git mv failed: {0} -> {1}\n{2}".format(rel_src, rel_dst, out))
        with open(dst, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["category"] = cat_ids[folder]
        if new_name:
            data["name"] = new_name
        with open(dst, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("  {0} -> {1}{2}".format(rel_src, rel_dst, "  (renamed '{0}')".format(new_name) if new_name else ""))

    ok, out = git(repo, "add", "-A", "--", lib_mod.LIB_DIR)
    if not ok:
        raise RuntimeError("git add failed\n" + out)
    ok, out = git(repo, "commit", "-m", COMMIT_MESSAGE)
    if not ok:
        raise RuntimeError("git commit failed\n" + out)
    ok, head = git(repo, "rev-parse", "--short", "HEAD")
    return head.strip()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Move A00210 path structures to the shared library folder.")
    ap.add_argument("repo_dir", help="local clone of the data repo (Store Repo)")
    ap.add_argument("--apply", action="store_true", help="really move + commit (default: dry-run)")
    ap.add_argument("--branch", default="main")
    ap.add_argument("--author", default=os.environ.get("USERNAME", ""))
    ap.add_argument("--no-pull", action="store_true", help="skip 'git pull --rebase' before migrating")
    args = ap.parse_args(argv)

    repo = os.path.abspath(args.repo_dir)
    problems = check_repo(repo, args.branch)
    if problems:
        for p in problems:
            print("[Error] " + p)
        return 1

    if args.apply and not args.no_pull:
        ok, out = git(repo, "pull", "--rebase", "--autostash", "origin", args.branch)
        print(out)
        if not ok:
            print("[Error] Pull failed - nothing was migrated.")
            return 1

    plan = make_plan(repo)
    if not plan:
        print("Nothing to migrate - no structures under profiles/*/path_structures.")
        return 0

    folders = sorted({p[0] for p in plan}, key=str.lower)
    print("{0} structure(s) in {1} folder(s): {2}".format(len(plan), len(folders), ", ".join(folders)))
    if not args.apply:
        for folder, src, dst, new_name in plan:
            print("  [{0}] {1} -> {2}{3}".format(
                folder, os.path.relpath(src, repo).replace("\\", "/"),
                os.path.relpath(dst, repo).replace("\\", "/"),
                "  (renamed '{0}')".format(new_name) if new_name else ""))
        print("Dry-run only. Add --apply to move and commit (no push).")
        return 0

    head = apply_plan(repo, plan, args.author)
    print("Committed {0} ({1} structure(s)). Not pushed - use the Path Structure tab's Push "
          "(or git push) when ready.".format(head, len(plan)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
