# Python Script by Ji Hun Park
# last Update date : 2026-11-05
# A00210_FileManager - Sync 탭 공유 설정 (UI/DCC 비의존)
#
# v01.47 : PC 간 작업 파일 동기화 추적(Sync Tracker). 계획 docs/plans/A00210_FileManager_sync_tracker_plan.md
#
#   <데이터 폴더>/manifests/
#       _sync_settings.json      ← 모든 PC 가 공유(git 으로 전달): 추적 루트 · 루트별 제외 경로 · 무시 패턴
#       <root_id>/<PC>.json      ← PC 마다 하나(sync_manifest)
#
# _sync_settings.json
#   {"schema": 1,
#    "roots": [{"id": "jun_mue", "name": "JUN_MUE", "default_path": "C:/JUN/JUN_MUE",
#               "excluded_paths": ["00_00_02_자료/", "x/y.mb"], "follow_junctions": false}],
#    "ignore_patterns": ["**/backup/**", ...],
#    "pc_names": {"P4T7MBN": "Office"}}      ← v01.50 PC 표시 이름(툴 안에서만). 매니페스트 파일 이름은 그대로 PC id.
#
# PC 마다 다른 값(루트의 실제 경로, 이 PC 만의 제외 경로)은 공유하지 않는다 - A00210 프로파일(prefs)에 둔다.
#
# 경로 표기: 루트 기준 **상대 경로, 슬래시(/)**. 폴더 제외 항목은 끝에 "/" 를 붙인다.
# 비교는 Windows 기준 대소문자 무시(normcase).

import copy
import fnmatch
import json
import os
import re
import socket

SCHEMA = 1
MANIFESTS_DIR = "manifests"
SETTINGS_FILE = "_sync_settings.json"

# 도구가 만드는 잡파일 - PC 마다 달라도 정상인 것들(계획서 4-6 (b)).
DEFAULT_IGNORE = [
    "**/backup/**",
    "**/incrementalSave/**",
    "**/.mayaSwatches/**",
    "**/*.swatches",
    "**/Thumbs.db",
    "**/desktop.ini",
    "**/~$*",
]


# ---------------------------------------------------------------- PC

def this_pc():
    """이 PC 이름(매니페스트 파일 이름). Windows 는 COMPUTERNAME."""
    name = os.environ.get("COMPUTERNAME") or socket.gethostname() or "PC"
    return safe_file_name(name)


def clean_pc_names(data):
    """{pc_id: 표시 이름} 정리 - 빈 이름은 뺀다(= id 로 보인다). 키 비교는 대소문자 무시."""
    out = {}
    seen = set()
    if isinstance(data, dict):
        for pc, name in data.items():
            pc = str(pc or "").strip()
            name = " ".join(str(name or "").split())
            if not pc or not name or pc.lower() in seen:
                continue
            seen.add(pc.lower())
            out[pc] = name
    return out


def pc_label(settings, pc):
    """화면에 보일 PC 이름 - 붙인 이름이 있으면 그것, 없으면 PC id(COMPUTERNAME)."""
    names = (settings or {}).get("pc_names") or {}
    if pc in names:
        return names[pc]
    low = str(pc or "").lower()
    for k, v in names.items():
        if k.lower() == low:
            return v
    return pc


def safe_file_name(name):
    """파일 이름으로 못 쓰는 글자를 _ 로."""
    s = re.sub(r'[\\/:*?"<>|]+', "_", str(name or "").strip())
    return s or "PC"


# ---------------------------------------------------------------- paths

def manifests_dir(data_dir):
    return os.path.join(data_dir, MANIFESTS_DIR) if data_dir else ""


def settings_path(data_dir):
    d = manifests_dir(data_dir)
    return os.path.join(d, SETTINGS_FILE) if d else ""


def norm_rel(rel, is_dir=False):
    """상대 경로 표기 정리: 슬래시 · 앞쪽 ./ / 제거 · 폴더는 끝에 '/'."""
    s = str(rel or "").replace("\\", "/").strip()
    while s.startswith("./"):
        s = s[2:]
    s = s.lstrip("/")
    s = re.sub(r"/{2,}", "/", s)
    if is_dir or s.endswith("/"):
        s = s.rstrip("/")
        return s + "/" if s else ""
    return s


def rel_key(rel):
    """비교용 열쇠(대소문자 무시)."""
    return os.path.normcase(norm_rel(rel)).replace("\\", "/")


def rel_of(root_abs, abs_path):
    """루트 아래 절대 경로 -> 상대 경로(슬래시). 루트 밖이면 None."""
    if not root_abs or not abs_path:
        return None
    try:
        rel = os.path.relpath(os.path.abspath(abs_path), os.path.abspath(root_abs))
    except ValueError:      # 드라이브가 다르다
        return None
    rel = rel.replace("\\", "/")
    if rel == "." or rel.startswith("../") or rel == "..":
        return None
    return rel


# ---------------------------------------------------------------- exclude / ignore

def is_excluded(rel, excluded):
    """rel 이 제외 목록에 걸리는가. 폴더 항목('a/b/')은 그 아래 전부, 파일 항목은 그 파일만.

    경계는 '/' 까지 포함해 비교한다 - 'scenes/0010_test/' 는 'scenes/0010_test_02/x.mb' 를 빼지 않는다."""
    if not excluded:
        return False
    key = rel_key(rel)
    key_dir = key.rstrip("/") + "/"
    for item in excluded:
        e = rel_key(item)
        if not e:
            continue
        if e.endswith("/"):
            if key_dir.startswith(e):
                return True
        elif key == e or key_dir.startswith(e + "/"):
            # 파일 항목인데 같은 이름 폴더가 있으면 그 폴더도 뺀다(항목에 '/' 를 깜빡한 경우)
            return True
    return False


def is_ignored(rel, patterns):
    """glob 무시 패턴. '**/x' 는 맨 위 'x' 에도 걸리게 'x/' 를 붙여 한 번 더 본다."""
    if not patterns:
        return False
    key = rel_key(rel)
    for p in patterns:
        pk = os.path.normcase(str(p or "").strip()).replace("\\", "/")
        if not pk:
            continue
        if fnmatch.fnmatchcase(key, pk) or fnmatch.fnmatchcase("_/" + key, pk):
            return True
    return False


# ---------------------------------------------------------------- roots

def make_root_id(name, existing=()):
    """루트 이름 -> 폴더 이름으로 쓸 id(영숫자 · _ 소문자). 겹치면 _2, _3 ..."""
    base = re.sub(r"[^0-9A-Za-z_-]+", "_", str(name or "")).strip("_").lower() or "root"
    taken = {str(e).lower() for e in existing}
    rid, n = base, 2
    while rid in taken:
        rid = "{0}_{1}".format(base, n)
        n += 1
    return rid


def new_root(name, default_path, existing_ids=()):
    return {
        "id": make_root_id(name, existing_ids),
        "name": str(name or "").strip() or "Root",
        "default_path": str(default_path or "").replace("\\", "/"),
        "excluded_paths": [],
        "follow_junctions": False,
    }


def find_root(settings, root_id):
    for r in (settings or {}).get("roots", []):
        if r.get("id") == root_id:
            return r
    return None


def root_path(root, local_paths):
    """이 PC 에서 루트의 실제 경로 = 이 PC 값(prefs) 이 있으면 그것, 없으면 공유 default_path."""
    if not root:
        return ""
    local = (local_paths or {}).get(root.get("id"), "")
    return str(local or root.get("default_path") or "").replace("\\", "/")


def overlap(path_a, path_b):
    """두 루트 경로가 겹치면 'inside'(a 가 b 안) / 'contains'(b 가 a 안) / 'same', 아니면 None."""
    if not path_a or not path_b:
        return None
    a = os.path.normcase(os.path.abspath(path_a)).rstrip("\\/") + os.sep
    b = os.path.normcase(os.path.abspath(path_b)).rstrip("\\/") + os.sep
    if a == b:
        return "same"
    if a.startswith(b):
        return "inside"
    if b.startswith(a):
        return "contains"
    return None


# ---------------------------------------------------------------- load / save

def default_settings():
    return {"schema": SCHEMA, "roots": [], "ignore_patterns": list(DEFAULT_IGNORE), "pc_names": {}}


def _clean(data):
    out = default_settings()
    if isinstance(data, dict):
        roots = []
        seen = set()
        for r in data.get("roots", []) or []:
            if not isinstance(r, dict) or not r.get("id"):
                continue
            rid = str(r["id"])
            if rid.lower() in seen:
                continue
            seen.add(rid.lower())
            ex = []
            for e in r.get("excluded_paths", []) or []:
                n = norm_rel(e)
                if n and n not in ex:
                    ex.append(n)
            roots.append({
                "id": rid,
                "name": str(r.get("name") or rid),
                "default_path": str(r.get("default_path") or "").replace("\\", "/"),
                "excluded_paths": ex,
                "follow_junctions": bool(r.get("follow_junctions", False)),
            })
        out["roots"] = roots
        if isinstance(data.get("ignore_patterns"), list):
            out["ignore_patterns"] = [str(p) for p in data["ignore_patterns"] if str(p).strip()]
        out["pc_names"] = clean_pc_names(data.get("pc_names"))
    return out


def load_settings(data_dir):
    path = settings_path(data_dir)
    if not path or not os.path.isfile(path):
        return default_settings()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return _clean(json.load(f))
    except (OSError, ValueError):
        return default_settings()


def save_settings(data_dir, settings):
    path = settings_path(data_dir)
    if not path:
        raise ValueError("Data folder is not set.")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = _clean(copy.deepcopy(settings))
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)
    return path
