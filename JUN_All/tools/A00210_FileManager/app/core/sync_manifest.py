# Python Script by Ji Hun Park
# last Update date : 2026-11-05
# A00210_FileManager - Sync 탭: PC 매니페스트 스캔 · 저장 (UI/DCC 비의존)
#
# v01.47 : 한 PC 가 한 추적 루트 아래에 가진 파일 목록 = 매니페스트(json 하나).
#   <데이터 폴더>/manifests/<root_id>/<PC>.json - PC 마다 자기 파일만 쓰므로 git 충돌이 나지 않는다.
#
#   {"schema": 1, "pc": "DESKTOP-ABC", "user": "...", "root_id": "jun_mue", "root": "C:/JUN/JUN_MUE",
#    "scanned_at": "2026-11-05 08:10:00", "scanned_epoch": 1730000000.0,
#    "files": {"<rel>": {"size": 1, "mtime": "2026-11-05 07:54:00", "mtime_ns": 0,
#                        "sha256": "...", "history": ["<옛 해시>", "<지금 해시>"]}}}
#
# - 크기 + 수정 시각(ns)이 직전 매니페스트와 같으면 해시를 다시 계산하지 않는다(캐시). 바뀐 파일만 SHA-256.
# - 해시 전후로 크기 · 시각이 바뀌면(마야가 저장 중) 그 파일은 건너뛰고 직전 값을 유지한다.
# - history = 이 PC 에서 이 경로가 가졌던 해시(최근 HISTORY_MAX 개, 마지막이 지금 것). 앞뒤 판정의 근거.
# - 루트 **안의** 정션 · 심볼릭 링크 폴더는 기본으로 따라 들어가지 않는다(루트별 follow_junctions).
#   루트 자체가 정션인 것은 상관없다(C:/JUN/JUN_MUE).
# - 구글 드라이브 웹 다운로드는 수정 시각을 지키지 않는다 → 같음 · 앞뒤 판정은 해시로(sync_compare).

import hashlib
import json
import os
import stat as stat_mod
import time

from . import sync_settings as ss

SCHEMA = 1
HISTORY_MAX = 10
_CHUNK = 1024 * 1024
_REPARSE = getattr(stat_mod, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


class ScanCancelled(Exception):
    pass


# ---------------------------------------------------------------- paths / io

def manifest_dir(data_dir, root_id):
    d = ss.manifests_dir(data_dir)
    return os.path.join(d, root_id) if d and root_id else ""


def manifest_path(data_dir, root_id, pc):
    d = manifest_dir(data_dir, root_id)
    return os.path.join(d, ss.safe_file_name(pc) + ".json") if d else ""


def load_manifest(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("files"), dict):
        return None
    return data


def load_root_manifests(data_dir, root_id):
    """{pc: manifest} - 그 루트 폴더의 모든 PC 매니페스트."""
    d = manifest_dir(data_dir, root_id)
    out = {}
    if not d or not os.path.isdir(d):
        return out
    for fn in sorted(os.listdir(d), key=str.lower):
        if not fn.lower().endswith(".json") or fn.startswith("_"):
            continue
        m = load_manifest(os.path.join(d, fn))
        if m is None:
            continue
        out[m.get("pc") or fn[:-5]] = m
    return out


def known_pcs(data_dir):
    """모든 루트 폴더의 매니페스트에 나온 PC id -> {pc: [root_id, ...]} (PC 이름 붙이기 창용)."""
    d = ss.manifests_dir(data_dir)
    out = {}
    if not d or not os.path.isdir(d):
        return out
    for rid in sorted(os.listdir(d), key=str.lower):
        sub = os.path.join(d, rid)
        if rid.startswith("_") or not os.path.isdir(sub):
            continue
        for pc in load_root_manifests(data_dir, rid):
            out.setdefault(pc, []).append(rid)
    return out


def save_manifest(data_dir, manifest):
    path = manifest_path(data_dir, manifest.get("root_id"), manifest.get("pc"))
    if not path:
        raise ValueError("Data folder or root is not set.")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # 키 정렬 · 들여쓰기 고정 → git diff 가 '어떤 파일이 늘고 바뀌었는지' 로 그대로 읽힌다.
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)
    return path


# ---------------------------------------------------------------- scan

def _fmt_time(epoch):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(epoch))


def _is_link_dir(entry):
    """정션 · 심볼릭 링크 폴더인가(따라 들어가지 않을 대상)."""
    try:
        if entry.is_symlink():
            return True
        st = entry.stat(follow_symlinks=False)
    except OSError:
        return False
    return bool(getattr(st, "st_file_attributes", 0) & _REPARSE)


def list_files(root_abs, excluded=(), ignore=(), follow_junctions=False, cancel=None):
    """(rel, abs_path, os.stat_result) 목록. 제외 폴더 안으로는 들어가지 않는다."""
    out = []
    errors = []
    stack = [("", root_abs)]
    while stack:
        if cancel and cancel():
            raise ScanCancelled()
        rel_dir, abs_dir = stack.pop()
        try:
            entries = list(os.scandir(abs_dir))
        except OSError as exc:
            errors.append("{0}: {1}".format(rel_dir or ".", exc))
            continue
        for entry in entries:
            rel = (rel_dir + "/" + entry.name) if rel_dir else entry.name
            try:
                is_dir = entry.is_dir()
            except OSError:
                continue
            if is_dir:
                if ss.is_excluded(rel + "/", excluded) or ss.is_ignored(rel + "/", ignore):
                    continue
                if not follow_junctions and _is_link_dir(entry):
                    continue
                stack.append((rel, entry.path))
                continue
            if ss.is_excluded(rel, excluded) or ss.is_ignored(rel, ignore):
                continue
            if entry.name.endswith(".tmp") and entry.name.startswith("~"):
                continue
            try:
                st = entry.stat()
            except OSError as exc:
                errors.append("{0}: {1}".format(rel, exc))
                continue
            out.append((rel, entry.path, st))
    out.sort(key=lambda t: t[0].lower())
    return out, errors


def sha256_of(path, progress=None, cancel=None):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            if cancel and cancel():
                raise ScanCancelled()
            b = f.read(_CHUNK)
            if not b:
                break
            h.update(b)
            if progress:
                progress(len(b))
    return h.hexdigest()


def _prev_index(prev):
    """직전 매니페스트 files -> {rel_key: (rel, entry)}."""
    out = {}
    for rel, e in ((prev or {}).get("files") or {}).items():
        if isinstance(e, dict):
            out[ss.rel_key(rel)] = (rel, e)
    return out


def scan(root_abs, root_id, pc, user="", excluded=(), ignore=(), prev=None,
         follow_junctions=False, progress=None, cancel=None):
    """루트를 스캔해 새 매니페스트와 보고(dict)를 돌려준다.

    progress(done_bytes, total_bytes, rel) - 해시할 바이트 기준. cancel() 이 True 면 ScanCancelled."""
    if not root_abs or not os.path.isdir(root_abs):
        raise OSError("Root folder not found: {0}".format(root_abs))

    files, errors = list_files(root_abs, excluded, ignore, follow_junctions, cancel)
    prev_idx = _prev_index(prev)

    todo = []                        # 해시가 필요한 것
    result = {}
    reused = 0
    for rel, abs_path, st in files:
        old = prev_idx.get(ss.rel_key(rel))
        old_e = old[1] if old else None
        if (old_e and old_e.get("sha256") and old_e.get("size") == st.st_size
                and old_e.get("mtime_ns") == st.st_mtime_ns):
            e = dict(old_e)
            e["history"] = list(old_e.get("history") or [old_e["sha256"]])[-HISTORY_MAX:]
            result[rel] = e
            reused += 1
        else:
            todo.append((rel, abs_path, st, old_e))

    total = sum(t[2].st_size for t in todo)
    done = [0]
    busy = []
    hashed = 0

    def _tick(n, rel):
        done[0] += n
        if progress:
            progress(done[0], total, rel)

    for rel, abs_path, st, old_e in todo:
        try:
            digest = sha256_of(abs_path, progress=lambda n, r=rel: _tick(n, r), cancel=cancel)
            st2 = os.stat(abs_path)
        except ScanCancelled:
            raise
        except OSError as exc:
            errors.append("{0}: {1}".format(rel, exc))
            if old_e:
                result[rel] = dict(old_e)
            continue
        if st2.st_size != st.st_size or st2.st_mtime_ns != st.st_mtime_ns:
            # 해시하는 동안 바뀌었다(저장 중) - 다음 스캔으로. 직전 값이 있으면 유지.
            busy.append(rel)
            if old_e:
                result[rel] = dict(old_e)
            continue
        hashed += 1
        history = list((old_e or {}).get("history") or ([old_e["sha256"]] if old_e and old_e.get("sha256") else []))
        if not history or history[-1] != digest:
            if digest in history:
                history.remove(digest)       # 예전 버전으로 되돌린 파일 - 지금 것으로 맨 뒤에
            history.append(digest)
        result[rel] = {
            "size": st.st_size,
            "mtime": _fmt_time(st.st_mtime),
            "mtime_ns": st.st_mtime_ns,
            "sha256": digest,
            "history": history[-HISTORY_MAX:],
        }

    now = time.time()
    manifest = {
        "schema": SCHEMA,
        "pc": pc,
        "user": user or "",
        "root_id": root_id,
        "root": str(root_abs).replace("\\", "/"),
        "scanned_at": _fmt_time(now),
        "scanned_epoch": now,
        "files": result,
    }
    report = {
        "files": len(result),
        "hashed": hashed,
        "reused": reused,
        "busy": busy,
        "errors": errors,
        "hashed_bytes": done[0],
    }
    return manifest, report
